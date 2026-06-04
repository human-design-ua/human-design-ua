"""
Human Design UA — Receipt Email Sender (DEV)
Sends a payment receipt PDF to the customer via Gmail SMTP.

Usage:
    python3 scripts/send_receipt.py --order HD-1234 --email customer@gmail.com \
        --plan basic --name "Олена"

Setup (one time):
    1. Enable 2FA on humandesign.finance@gmail.com
    2. Go to: myaccount.google.com → Security → App Passwords
    3. Create App Password for "Mail" → copy the 16-char code
    4. Add to .env:  GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

Requirements:
    pip install fpdf2 python-dotenv
"""

import argparse
import os
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from generate_receipt import generate_receipt, PLAN_NAMES, PLAN_AMOUNTS

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Config ────────────────────────────────────────────────────
GMAIL_USER = 'humandesign.finance@gmail.com'

# App Password (16 chars, no spaces) — DEV only, never commit to prod
# Get it: myaccount.google.com → Security → App Passwords
DEV_APP_PASSWORD = ''  # ← вставь сюда: 'xxxx xxxx xxxx xxxx'

GMAIL_PASSWORD = DEV_APP_PASSWORD or os.getenv('GMAIL_APP_PASSWORD', '')
SMTP_HOST      = 'smtp.gmail.com'
SMTP_PORT      = 587


def build_email_body(order_data: dict) -> str:
    plan      = order_data.get('plan', 'basic')
    name      = order_data.get('name', '')
    order_id  = order_data.get('order_id', '')
    amount    = order_data.get('amount', PLAN_AMOUNTS.get(plan, 399))
    greeting  = f'Вітаємо, {name}!' if name else 'Вітаємо!'
    plan_name = PLAN_NAMES.get(plan, 'Розшифровка бодіграфу')
    dev_note  = '\n⚠ DEV РЕЖИМ — тестовий лист. Реальні гроші не списувались.\n' \
                if order_data.get('env') == 'dev' else ''

    return f"""
{dev_note}
{greeting}

Ваша оплата успішно прийнята. Деталі замовлення:

  Номер замовлення : {order_id}
  Послуга          : {plan_name}
  Сума             : {amount} грн
  Статус           : ✓ Оплачено

Ваша персональна розшифровка Дизайну Людини вже генерується
і буде надіслана на цю адресу протягом 5–10 хвилин.

У вкладенні — чек про оплату у форматі PDF.

З повагою,
Human Design UA
humandesign.finance@gmail.com
""".strip()


def send_receipt_email(order_data: dict, pdf_path: str) -> bool:
    """Send receipt email with PDF attachment."""

    if not GMAIL_PASSWORD:
        print('❌ GMAIL_APP_PASSWORD не вказано в .env')
        print('   Додай: GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx')
        return False

    to_email  = order_data['email']
    plan      = order_data.get('plan', 'basic')
    plan_name = PLAN_NAMES.get(plan, 'Розшифровка бодіграфу')

    # Build message
    msg = MIMEMultipart()
    msg['From']    = f'Human Design UA <{GMAIL_USER}>'
    msg['To']      = to_email
    msg['Subject'] = f'✦ Чек про оплату — {plan_name}'
    msg['Reply-To'] = GMAIL_USER

    # Body
    msg.attach(MIMEText(build_email_body(order_data), 'plain', 'utf-8'))

    # Attach PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition', 'attachment',
                filename=f'receipt_{order_data["order_id"]}.pdf'
            )
            msg.attach(pdf_attachment)
    else:
        print(f'⚠ PDF not found: {pdf_path}')

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())

        print(f'✅ Receipt sent to {to_email}')
        return True

    except smtplib.SMTPAuthenticationError:
        print('❌ Gmail auth failed. Перевір GMAIL_APP_PASSWORD в .env')
        print('   Інструкція: myaccount.google.com → Security → App Passwords')
        return False
    except Exception as e:
        print(f'❌ Send failed: {e}')
        return False


def run(order_data: dict):
    """Full flow: generate PDF → send email."""
    print(f'\n📋 Order: {order_data["order_id"]}')
    print(f'   Email:  {order_data["email"]}')
    print(f'   Plan:   {order_data["plan"]}  |  {order_data["amount"]} грн')
    print(f'   Env:    {order_data.get("env", "dev")}\n')

    # Step 1: Generate PDF
    pdf_path = generate_receipt(order_data)

    # Step 2: Send email
    send_receipt_email(order_data, pdf_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send HD receipt via Gmail')
    parser.add_argument('--order',  required=True)
    parser.add_argument('--email',  required=True)
    parser.add_argument('--plan',   default='basic', choices=['basic', 'full'])
    parser.add_argument('--amount', type=int)
    parser.add_argument('--name',   default='')
    parser.add_argument('--env',    default='dev', choices=['dev', 'prod'])
    args = parser.parse_args()

    order_data = {
        'order_id': args.order,
        'email':    args.email,
        'name':     args.name,
        'plan':     args.plan,
        'amount':   args.amount or PLAN_AMOUNTS[args.plan],
        'paid_at':  datetime.now().strftime('%d.%m.%Y %H:%M'),
        'env':      args.env,
    }

    run(order_data)
