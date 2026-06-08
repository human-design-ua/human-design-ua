"""
Human Design UA — Local DEV server
Simulates Make.com webhook in development environment.

Handles:
  POST /pay      — mock payment: generate receipt + send email
  POST /pay/fail — failed payment: send retry email to customer
  POST /webhook  — same as /pay (Make.com webhook format)
  GET  /health   — health check

Usage:
    python3 scripts/dev_server.py

Then open site/quiz.html in browser.
The dev payment mock will POST to http://localhost:4000/pay
"""

import json
import os
import sys
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Allow importing sibling scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threading
from generate_receipt import generate_receipt
from send_receipt import send_receipt_email, send_reading_email, send_failed_payment_email
from dev_db import init_db, save_order, get_orders, get_stats
from generate_reading import generate_reading_with_ai

PORT = 4000

# Init DB
init_db()


class DevHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f'[{datetime.now().strftime("%H:%M:%S")}] {fmt % args}')

    def send_cors(self):
        """Allow requests from file:// and localhost"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/health':
            self._json(200, {'status': 'ok', 'env': 'dev', 'port': PORT})
        elif path == '/admin/orders':
            self._json(200, {'orders': get_orders()})
        elif path == '/admin/stats':
            self._json(200, get_stats())
        elif path in ('/admin', '/admin/'):
            self._serve_admin()
        else:
            self._json(404, {'error': 'Not found'})

    def do_POST(self):
        path = urlparse(self.path).path

        # Read body
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            self._json(400, {'error': 'Invalid JSON'})
            return

        if path in ('/pay', '/webhook'):
            self._handle_payment(data)
        elif path == '/pay/fail':
            self._handle_payment_fail(data)
        else:
            self._json(404, {'error': 'Not found'})

    def _handle_payment(self, data: dict):
        print('\n' + '─' * 50)
        print(f'💳 New DEV payment received')
        print(f'   Order:  {data.get("order_id", "—")}')
        print(f'   Email:  {data.get("email", "—")}')
        print(f'   Plan:   {data.get("plan", "—")}  |  {data.get("amount", "—")} грн')
        print('─' * 50)

        order_data = {
            'order_id':    data.get('order_id', f'HD-DEV-{int(datetime.now().timestamp())}'),
            'email':       data.get('email', ''),
            'name':        data.get('name', ''),
            'plan':        data.get('plan', 'basic'),
            'amount':      data.get('amount', 399),
            'birth_date':  data.get('birth_date', ''),
            'birth_time':  data.get('birth_time', ''),
            'birth_place': data.get('birth_place', ''),
            'life_area':   data.get('life_area', ''),
            'challenge':   data.get('challenge', ''),
            'utm_source':  data.get('utm_source', ''),
            'utm_campaign':data.get('utm_campaign', ''),
            'locale':      data.get('locale', 'ua'),
            'paid_at':     datetime.now().strftime('%d.%m.%Y %H:%M'),
            'env':         'dev',
        }

        # Validate email
        if not order_data['email']:
            self._json(400, {'error': 'Email is required'})
            return

        try:
            # Save to DB
            save_order(order_data)

            # Step 1: Generate receipt PDF
            print('\n📄 Generating receipt PDF...')
            pdf_path = generate_receipt(order_data)

            # Step 2: Send receipt immediately
            print(f'\n📧 Sending receipt to {order_data["email"]}...')
            sent = send_receipt_email(order_data, pdf_path)

            # Step 3: Generate reading + send after 90s delay
            def send_reading_delayed(od):
                import time, traceback as tb
                delay = 60  # 1 min delay before sending reading
                print(f'\n⏳ [{od.get("order_id")}] Reading will be sent in {delay}s...')
                time.sleep(delay)
                print(f'\n📖 [{od.get("order_id")}] Generating reading PDF with Claude AI...')
                try:
                    rpath = generate_reading_with_ai(od)
                    print(f'✅ [{od.get("order_id")}] Reading generated: {rpath}')
                    ok = send_reading_email(od, rpath)
                    if ok:
                        print(f'✅ [{od.get("order_id")}] Reading email sent to {od.get("email")}')
                    else:
                        print(f'❌ [{od.get("order_id")}] Reading email FAILED (check Gmail password)')
                except Exception as e:
                    print(f'❌ [{od.get("order_id")}] Reading failed: {e}')
                    tb.print_exc()

            # daemon=False so thread survives even if main thread is idle
            t = threading.Thread(target=send_reading_delayed, args=(order_data,), daemon=False)
            t.start()
            print(f'🕐 Reading will be sent in ~60 seconds to {order_data["email"]}...')

            if sent:
                print(f'\n✅ DEV flow complete!')
                self._json(200, {
                    'status':   'success',
                    'order_id': order_data['order_id'],
                    'pdf':      pdf_path,
                    'email':    order_data['email'],
                    'message':  'Receipt generated and sent',
                })
            else:
                # Email failed but PDF exists
                print(f'\n⚠ PDF generated but email NOT sent (check .env)')
                self._json(200, {
                    'status':   'partial',
                    'order_id': order_data['order_id'],
                    'pdf':      pdf_path,
                    'message':  'PDF ok, email failed — check GMAIL_APP_PASSWORD in .env',
                })

        except Exception as e:
            traceback.print_exc()
            self._json(500, {'error': str(e)})

    def _handle_payment_fail(self, data: dict):
        """Handle failed payment — send retry email to customer."""
        print('\n' + '─' * 50)
        print(f'❌ DEV payment FAILED — sending retry email')
        print(f'   Order:  {data.get("order_id", "—")}')
        print(f'   Email:  {data.get("email", "—")}')
        print(f'   Plan:   {data.get("plan", "—")}')
        print('─' * 50)

        email = data.get('email', '')
        if not email:
            self._json(400, {'error': 'Email is required'})
            return

        order_data = {
            'order_id': data.get('order_id', f'HD-FAIL-{int(datetime.now().timestamp())}'),
            'email':    email,
            'name':     data.get('name', ''),
            'plan':     data.get('plan', 'full'),
            'amount':   data.get('amount', 799),
            'locale':   data.get('locale', 'ua'),
            'env':      'dev',
            'site_url': 'http://localhost:4000',
        }

        ok = send_failed_payment_email(order_data)
        if ok:
            self._json(200, {'status': 'fail_email_sent', 'email': email})
        else:
            self._json(500, {'status': 'fail_email_error', 'email': email})

    def _serve_admin(self):
        admin_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'site', 'admin.html'
        )
        try:
            with open(admin_path, 'rb') as f:
                body = f.read()
            # Patch fetch URLs to use relative paths
            body = body.replace(
                b"fetch('http://localhost:4000/admin/orders')",
                b"fetch('/admin/orders')"
            ).replace(
                b"fetch('http://localhost:4000/admin/stats')",
                b"fetch('/admin/stats')"
            )
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self._json(404, {'error': 'admin.html not found'})

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)


def main():
    print('─' * 50)
    print('🚀 Human Design UA — DEV Server')
    print(f'   Listening on http://localhost:{PORT}')
    print(f'   Endpoints:')
    print(f'     POST http://localhost:{PORT}/pay     — payment mock')
    print(f'     GET  http://localhost:{PORT}/health  — health check')
    print('─' * 50)
    print('\nOpen site/quiz.html in browser and complete the quiz.\n')

    server = HTTPServer(('localhost', PORT), DevHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n\nServer stopped.')


if __name__ == '__main__':
    main()
