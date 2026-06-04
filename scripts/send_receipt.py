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
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from generate_receipt import generate_receipt, PLAN_NAMES, PLAN_AMOUNTS, T as RECEIPT_T

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Config ────────────────────────────────────────────────────
GMAIL_USER = 'humandesign.finance@gmail.com'

# App Password (16 chars, no spaces) — DEV only, never commit to prod
# Get it: myaccount.google.com → Security → App Passwords
DEV_APP_PASSWORD = 'ohqw npmh jtlh gzuq'  # ← вставь сюда: 'xxxx xxxx xxxx xxxx'

# Strip all spaces (including non-breaking \xa0 copied from Google UI)
_raw = DEV_APP_PASSWORD or os.getenv('GMAIL_APP_PASSWORD', '')
GMAIL_PASSWORD = _raw.replace('\xa0', '').replace(' ', '')
SMTP_HOST      = 'smtp.gmail.com'
SMTP_PORT      = 587


EMAIL_GREETINGS = {
    'ua': ('Вітаємо', 'Ваша оплата успішно прийнята.',
           'Ваша розшифровка вже генерується і буде надіслана протягом 5-10 хвилин.',
           'У вкладенні - чек про оплату.', 'З повагою,',
           'DEV - тестовий лист. Реальні гроші не списувались.'),
    'ru': ('Привет', 'Ваша оплата успешно принята.',
           'Ваша расшифровка уже генерируется и будет отправлена в течение 5-10 минут.',
           'Во вложении - чек об оплате.', 'С уважением,',
           'DEV - тестовое письмо. Реальные деньги не списывались.'),
    'en': ('Hello', 'Your payment has been successfully received.',
           'Your reading is being generated and will be sent within 5-10 minutes.',
           'Attached is your payment receipt.', 'Best regards,',
           'DEV - test email. No real money was charged.'),
}

def build_email_body(order_data: dict) -> str:
    plan      = order_data.get('plan', 'basic')
    name      = order_data.get('name', '')
    order_id  = order_data.get('order_id', '')
    amount    = order_data.get('amount', PLAN_AMOUNTS.get(plan, 399))
    locale    = order_data.get('locale', 'ua')
    g         = EMAIL_GREETINGS.get(locale, EMAIL_GREETINGS['ua'])
    greeting  = f'{g[0]}, {name}!' if name else f'{g[0]}!'
    plan_names= PLAN_NAMES.get(locale, PLAN_NAMES['ua'])
    plan_name = plan_names.get(plan, plan)
    dev_note  = f'\n⚠ {g[5]}\n' if order_data.get('env') == 'dev' else ''

    birth_date  = order_data.get('birth_date',  '')
    birth_time  = order_data.get('birth_time',  '')
    birth_place = order_data.get('birth_place', '')
    birth_block = ''
    if any([birth_date, birth_time, birth_place]):
        birth_block = (
            f"\n  Дата народження  : {birth_date}"
            f"\n  Час народження   : {birth_time or 'не вказано'}"
            f"\n  Місце народження : {birth_place}"
        )

    return f"""
{dev_note}
{greeting}

Ваша оплата успішно прийнята. Деталі замовлення:

  Номер замовлення : {order_id}
  Послуга          : {plan_name}
  Сума             : {amount} грн
  Статус           : Оплачено{birth_block}

Ваша персональна розшифровка Дизайну Людини вже генерується
і буде надіслана на цю адресу протягом 5-10 хвилин.

У вкладенні - чек про оплату у форматі PDF.

З повагою,
Human Design UA
humandesign.finance@gmail.com
""".strip()


def send_receipt_email(order_data: dict, pdf_path: str, reading_path: str = None) -> bool:
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
    msg['From']     = f'Human Design UA <{GMAIL_USER}>'
    msg['To']       = to_email
    msg['Subject']  = Header(f'Vasha rozshyfrovka - {plan_name}', 'utf-8')
    msg['Reply-To'] = GMAIL_USER

    # Body — strip any non-breaking spaces to avoid encoding issues
    body = build_email_body(order_data).replace('\xa0', ' ')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Attach receipt PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            att = MIMEApplication(f.read(), _subtype='pdf')
            att.add_header('Content-Disposition', 'attachment',
                           filename=f'receipt_{order_data["order_id"]}.pdf')
            msg.attach(att)
    else:
        print(f'⚠ Receipt PDF not found: {pdf_path}')

    # Attach reading PDF (if exists)
    if reading_path and os.path.exists(reading_path):
        plan  = order_data.get('plan', 'basic')
        rname = 'reading_full.pdf' if plan == 'full' else 'reading_basic.pdf'
        with open(reading_path, 'rb') as f:
            att2 = MIMEApplication(f.read(), _subtype='pdf')
            att2.add_header('Content-Disposition', 'attachment', filename=rname)
            msg.attach(att2)
        print(f'📎 Reading PDF attached: {rname}')
    elif reading_path:
        print(f'⚠ Reading PDF not found: {reading_path}')

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, local_hostname='localhost') as server:
            server.ehlo('localhost')
            server.starttls()
            server.ehlo('localhost')
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            # Use as_bytes() to avoid Python 3.9 ascii encoding issues
            server.sendmail(
                GMAIL_USER,
                [to_email],
                msg.as_bytes(),
                mail_options=['BODY=8BITMIME'],
            )

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
