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



def send_reading_email(order_data: dict, reading_path: str) -> bool:
    """Send the reading PDF as a separate email 1-2 min after receipt."""

    if not GMAIL_PASSWORD:
        return False

    locale    = order_data.get('locale', 'ua')
    name      = order_data.get('name', '')
    plan      = order_data.get('plan', 'basic')
    to_email  = order_data['email']

    SUBJECTS = {
        'ua': f'✦ Ваш персональний розрахунок Дизайну Людини готовий',
        'ru': f'✦ Ваш персональный расчёт Дизайна Человека готов',
        'en': f'✦ Your personal Human Design reading is ready',
    }

    BODIES = {
        'ua': f"""{name + ", т" if name else "Т"}римайте свій персональний розрахунок Дизайну Людини!

У вкладенні — ваша персональна розшифровка бодіграфу.
Вона створена спеціально для вас на основі точних астрологічних даних вашого народження.

Рекомендуємо читати у спокійній обстановці — це ваша карта, ваш унікальний код.

З теплом,
Human Design UA
humandesign.finance@gmail.com

⚠ DEV РЕЖИМ — тестовий лист.""" if order_data.get('env') == 'dev' else f"""{name + ", т" if name else "Т"}римайте свій персональний розрахунок Дизайну Людини!

У вкладенні — ваша персональна розшифровка бодіграфу.

З теплом,
Human Design UA
humandesign.finance@gmail.com""",

        'ru': f"""{name + ", д" if name else "Д"}ержите свой персональный расчёт Дизайна Человека!

Во вложении — ваша персональная расшифровка бодиграфа.
Она создана специально для вас на основе точных астрологических данных вашего рождения.

Рекомендуем читать в спокойной обстановке — это ваша карта, ваш уникальный код.

С теплом,
Human Design UA
humandesign.finance@gmail.com""",

        'en': f"""{"Hey " + name + ", y" if name else "Y"}our personal Human Design reading is ready!

Attached is your personal bodygraph reading.
It was created specifically for you based on your exact birth data.

We recommend reading it in a calm environment — this is your map, your unique code.

With warmth,
Human Design UA
humandesign.finance@gmail.com""",
    }

    plan_names_map = PLAN_NAMES.get(locale, PLAN_NAMES['ua'])
    plan_name = plan_names_map.get(plan, plan)

    msg = MIMEMultipart()
    msg['From']     = f'Human Design UA <{GMAIL_USER}>'
    msg['To']       = to_email
    msg['Subject']  = Header(SUBJECTS.get(locale, SUBJECTS['ua']), 'utf-8')
    msg['Reply-To'] = GMAIL_USER

    body = BODIES.get(locale, BODIES['ua']).replace('\xa0', ' ')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Attach reading PDF
    if reading_path and os.path.exists(reading_path):
        rname = 'rozshyfrovka_povna.pdf' if plan == 'full' else 'rozshyfrovka_bazova.pdf'
        with open(reading_path, 'rb') as f:
            att = MIMEApplication(f.read(), _subtype='pdf')
            att.add_header('Content-Disposition', 'attachment', filename=rname)
            msg.attach(att)
    else:
        print(f'⚠ Reading PDF not found: {reading_path}')
        return False

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, local_hostname='localhost') as server:
            server.ehlo('localhost')
            server.starttls()
            server.ehlo('localhost')
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, [to_email], msg.as_bytes(),
                            mail_options=['BODY=8BITMIME'])
        print(f'✅ Reading email sent to {to_email}')
        return True
    except Exception as e:
        print(f'❌ Reading email failed: {e}')
        return False


def send_failed_payment_email(order_data: dict) -> bool:
    """Send a payment failure email with a retry link."""

    if not GMAIL_PASSWORD:
        print('❌ GMAIL_APP_PASSWORD не вказано — failed payment email не надіслано')
        return False

    locale    = order_data.get('locale', 'ua')
    name      = order_data.get('name', '')
    plan      = order_data.get('plan', 'full')
    to_email  = order_data.get('email', '')
    site_url  = order_data.get('site_url', 'https://human-design-ua.netlify.app')

    if not to_email:
        print('❌ Email відсутній — failed payment email не надіслано')
        return False

    # Retry URL — direct link to the pricing step with pre-selected plan
    retry_url = f'{site_url}/quiz.html?plan={plan}#pricing'

    SUBJECTS = {
        'ua': 'Оплата не пройшла — спробуйте ще раз',
        'ru': 'Оплата не прошла — попробуйте ещё раз',
        'en': 'Payment failed — please try again',
    }

    BODIES = {
        'ua': f"""Добрий день{(', ' + name) if name else ''}!

На жаль, ваша оплата не пройшла. Можливі причини:
  • Недостатньо коштів на картці
  • Карта заблокована для онлайн-платежів
  • Помилка банку (спробуйте ще раз)

Щоб завершити замовлення, перейдіть за посиланням:
{retry_url}

Якщо виникнуть питання — напишіть нам:
humandesign.finance@gmail.com

З повагою,
Human Design UA""",

        'ru': f"""Добрый день{(', ' + name) if name else ''}!

К сожалению, ваша оплата не прошла. Возможные причины:
  • Недостаточно средств на карте
  • Карта заблокирована для онлайн-платежей
  • Ошибка банка (попробуйте ещё раз)

Чтобы завершить заказ, перейдите по ссылке:
{retry_url}

Если возникнут вопросы — напишите нам:
humandesign.finance@gmail.com

С уважением,
Human Design UA""",

        'en': f"""Hello{(', ' + name) if name else ''}!

Unfortunately your payment was not successful. Possible reasons:
  • Insufficient funds on the card
  • Card blocked for online payments
  • Bank error (please try again)

To complete your order, please follow this link:
{retry_url}

If you have any questions, contact us:
humandesign.finance@gmail.com

Best regards,
Human Design UA""",
    }

    subject = SUBJECTS.get(locale, SUBJECTS['ua'])
    body    = BODIES.get(locale, BODIES['ua']).replace('\xa0', ' ')

    msg = MIMEMultipart()
    msg['From']     = f'Human Design UA <{GMAIL_USER}>'
    msg['To']       = to_email
    msg['Subject']  = Header(subject, 'utf-8')
    msg['Reply-To'] = GMAIL_USER
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, local_hostname='localhost') as server:
            server.ehlo('localhost')
            server.starttls()
            server.ehlo('localhost')
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, [to_email], msg.as_bytes(),
                            mail_options=['BODY=8BITMIME'])
        print(f'✅ Failed payment email sent to {to_email}')
        return True
    except smtplib.SMTPAuthenticationError:
        print('❌ Gmail auth failed — перевір GMAIL_APP_PASSWORD')
        return False
    except Exception as e:
        print(f'❌ Failed payment email error: {e}')
        return False


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
