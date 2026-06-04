"""
Human Design UA — PDF Receipt Generator (localized)

Usage:
    python3 scripts/generate_receipt.py --order HD-1234 --email test@gmail.com \
        --plan basic --amount 399 --name "Олена" --locale ua

Requirements:
    pip install fpdf2
"""

import argparse
import os
from datetime import datetime
from fpdf import FPDF

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
FONT_REG   = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans.ttf')
FONT_BOLD  = os.path.join(BASE_DIR, 'fonts', 'DejaVuSans-Bold.ttf')
LOGO_PATH  = os.path.join(BASE_DIR, '..', 'site', 'assets', 'img', 'logo.png')
OUTPUT_DIR = os.path.join(BASE_DIR, '..', 'tmp', 'receipts')

COMPANY_NAME  = "Human Design UA"
COMPANY_EMAIL = "humandesign.finance@gmail.com"
COMPANY_SITE  = "humandesign.ua"

PLAN_NAMES = {
    'ua': {'basic': 'Базова розшифровка бодіграфу',  'full': 'Повна розшифровка бодіграфу'},
    'ru': {'basic': 'Базовая расшифровка бодиграфа', 'full': 'Полная расшифровка бодиграфа'},
    'en': {'basic': 'Basic Bodygraph Reading',        'full': 'Full Bodygraph Reading'},
}
PLAN_AMOUNTS = {'basic': 399, 'full': 799}

# ── Translations ──────────────────────────────────────────────
T = {
    'ua': {
        'title':         'Чек про оплату',
        'generated':     'Документ сформовано:',
        'order_section': 'Деталі замовлення',
        'order_id':      'Номер замовлення',
        'paid_at':       'Дата оплати',
        'status':        'Статус',
        'status_val':    'Оплачено',
        'pay_method':    'Спосіб оплати',
        'pay_liqpay':    'LiqPay (Visa/Mastercard)',
        'pay_dev':       'DEV — тестовий платіж',
        'customer':      "Інформація про клієнта",
        'name':          "Ім'я",
        'email':         'Email',
        'birth_date':    'Дата народження',
        'birth_time':    'Час народження',
        'birth_time_na': 'не вказано',
        'birth_place':   'Місце народження',
        'life_area':     'Сфера інтересу',
        'service':       'Послуга',
        'col_name':      'Назва послуги',
        'col_qty':       'К-сть',
        'col_total':     'Сума',
        'total':         'Разом до сплати:',
        'dev_note':      'DEV РЕЖИМ — Цей чек є тестовим. Реальні гроші не списувались.',
        'thanks':        'Дякуємо за замовлення! Ваша персональна розшифровка буде надіслана протягом 10 хвилин.',
        'contact':       'Питання? Пишіть:',
        'footer':        'Дякуємо за довіру',
        'life_areas':    {'career': "Кар'єра та покликання", 'relationships': 'Стосунки',
                          'energy': "Енергія та здоров'я",  'self': 'Пізнання себе'},
    },
    'ru': {
        'title':         'Чек об оплате',
        'generated':     'Документ сформирован:',
        'order_section': 'Детали заказа',
        'order_id':      'Номер заказа',
        'paid_at':       'Дата оплаты',
        'status':        'Статус',
        'status_val':    'Оплачено',
        'pay_method':    'Способ оплаты',
        'pay_liqpay':    'LiqPay (Visa/Mastercard)',
        'pay_dev':       'DEV — тестовый платёж',
        'customer':      'Информация о клиенте',
        'name':          'Имя',
        'email':         'Email',
        'birth_date':    'Дата рождения',
        'birth_time':    'Время рождения',
        'birth_time_na': 'не указано',
        'birth_place':   'Место рождения',
        'life_area':     'Сфера интереса',
        'service':       'Услуга',
        'col_name':      'Название услуги',
        'col_qty':       'Кол-во',
        'col_total':     'Сумма',
        'total':         'Итого к оплате:',
        'dev_note':      'DEV РЕЖИМ — Этот чек тестовый. Реальные деньги не списывались.',
        'thanks':        'Спасибо за заказ! Ваша персональная расшифровка будет отправлена в течение 10 минут.',
        'contact':       'Вопросы? Пишите:',
        'footer':        'Спасибо за доверие',
        'life_areas':    {'career': 'Карьера и призвание', 'relationships': 'Отношения',
                          'energy': 'Энергия и здоровье', 'self': 'Познание себя'},
    },
    'en': {
        'title':         'Payment Receipt',
        'generated':     'Generated:',
        'order_section': 'Order Details',
        'order_id':      'Order ID',
        'paid_at':       'Date',
        'status':        'Status',
        'status_val':    'Paid',
        'pay_method':    'Payment method',
        'pay_liqpay':    'LiqPay (Visa/Mastercard)',
        'pay_dev':       'DEV — test payment',
        'customer':      'Customer Information',
        'name':          'Name',
        'email':         'Email',
        'birth_date':    'Date of birth',
        'birth_time':    'Time of birth',
        'birth_time_na': 'not provided',
        'birth_place':   'Place of birth',
        'life_area':     'Area of interest',
        'service':       'Service',
        'col_name':      'Service name',
        'col_qty':       'Qty',
        'col_total':     'Amount',
        'total':         'Total:',
        'dev_note':      'DEV MODE — This is a test receipt. No real money was charged.',
        'thanks':        'Thank you for your order! Your personal Human Design reading will be sent within 10 minutes.',
        'contact':       'Questions? Contact us:',
        'footer':        'Thank you for your trust',
        'life_areas':    {'career': 'Career & purpose', 'relationships': 'Relationships',
                          'energy': 'Energy & health',  'self': 'Self-knowledge'},
    },
}

C_DARK   = (13,  11,  30)
C_CARD   = (26,  20,  64)
C_GOLD   = (212, 168, 48)
C_PURPLE = (155, 110, 224)
C_MUTED  = (107, 95,  128)


class ReceiptPDF(FPDF):
    def __init__(self, order_data: dict):
        super().__init__()
        self.order  = order_data
        locale      = order_data.get('locale', 'ua')
        self.tr     = T.get(locale, T['ua'])
        self.locale = locale
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font('DejaVu',  '',  FONT_REG)
        self.add_font('DejaVu',  'B', FONT_BOLD)

    def _color(self, c, stroke=False):
        if stroke: self.set_draw_color(*c)
        else:      self.set_text_color(*c)

    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=20, y=12, w=28)
            self.set_xy(52, 12)
        else:
            self.set_xy(20, 12)
        self.set_font('DejaVu', 'B', 16)
        self._color(C_DARK)
        self.cell(0, 8, COMPANY_NAME, new_x='LMARGIN', new_y='NEXT')
        self.set_font('DejaVu', '', 9)
        self._color(C_MUTED)
        self.cell(0, 5, f'{COMPANY_EMAIL}  ·  {COMPANY_SITE}', new_x='LMARGIN', new_y='NEXT')
        self.ln(4)
        self._color(C_GOLD, stroke=True)
        self.set_line_width(0.6)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-18)
        self.set_font('DejaVu', '', 8)
        self._color(C_MUTED)
        self.cell(0, 5, f"{COMPANY_NAME}  ·  {COMPANY_EMAIL}  ·  {self.tr['footer']} ✦", align='C')

    def build(self) -> str:
        self.add_page()
        o  = self.order
        tr = self.tr
        now_str = datetime.now().strftime('%d.%m.%Y %H:%M')

        # ── Title ──────────────────────────────────────────
        self.set_font('DejaVu', 'B', 22)
        self._color(C_DARK)
        self.cell(0, 12, tr['title'], new_x='LMARGIN', new_y='NEXT')
        self.set_font('DejaVu', '', 10)
        self._color(C_MUTED)
        self.cell(0, 6, f"{tr['generated']} {now_str}", new_x='LMARGIN', new_y='NEXT')
        self.ln(8)

        # ── Order details ──────────────────────────────────
        self._section(tr['order_section'])
        pay_method = tr['pay_liqpay'] if o.get('env') != 'dev' else tr['pay_dev']
        self._row(tr['order_id'],   o.get('order_id', '—'))
        self._row(tr['paid_at'],    o.get('paid_at',  now_str))
        self._row(tr['status'],     tr['status_val'])
        self._row(tr['pay_method'], pay_method)
        self.ln(6)

        # ── Customer ───────────────────────────────────────
        self._section(tr['customer'])
        self._row(tr['name'],  o.get('name',  '—'))
        self._row(tr['email'], o.get('email', '—'))
        if o.get('birth_date'):
            self._row(tr['birth_date'],  o['birth_date'])
        if o.get('birth_time') or o.get('birth_date'):
            self._row(tr['birth_time'],  o.get('birth_time') or tr['birth_time_na'])
        if o.get('birth_place'):
            self._row(tr['birth_place'], o['birth_place'])
        if o.get('life_area'):
            self._row(tr['life_area'], tr['life_areas'].get(o['life_area'], o['life_area']))
        self.ln(6)

        # ── Product ────────────────────────────────────────
        self._section(tr['service'])
        plan      = o.get('plan', 'basic')
        amount    = o.get('amount', PLAN_AMOUNTS.get(plan, 399))
        prod_name = PLAN_NAMES.get(self.locale, PLAN_NAMES['ua']).get(plan, plan)

        self.set_fill_color(*C_CARD)
        self.set_font('DejaVu', 'B', 9)
        self._color(C_GOLD)
        self.cell(110, 8, tr['col_name'],  fill=True, border=0)
        self.cell(30,  8, tr['col_qty'],   fill=True, border=0, align='C')
        self.cell(40,  8, tr['col_total'], fill=True, border=0, align='R')
        self.ln()

        self.set_fill_color(240, 238, 255)
        self.set_font('DejaVu', '', 10)
        self._color(C_DARK)
        self.cell(110, 9, prod_name,        fill=True, border=0)
        self.cell(30,  9, '1', fill=True,   border=0, align='C')
        self.cell(40,  9, f'{amount} UAH',  fill=True, border=0, align='R')
        self.ln()

        self.set_fill_color(*C_GOLD)
        self.set_font('DejaVu', 'B', 11)
        self._color(C_DARK)
        self.cell(140, 10, tr['total'],        fill=True, border=0)
        self.cell(40,  10, f'{amount} UAH',    fill=True, border=0, align='R')
        self.ln(14)

        # ── DEV notice ─────────────────────────────────────
        if o.get('env') == 'dev':
            self.set_fill_color(255, 240, 200)
            self.set_font('DejaVu', 'B', 9)
            self.set_text_color(160, 90, 0)
            self.cell(0, 8, f"⚠  {tr['dev_note']}", fill=True, align='C',
                      new_x='LMARGIN', new_y='NEXT')
            self.ln(5)

        # ── Thank you ──────────────────────────────────────
        self.set_font('DejaVu', '', 10)
        self._color(C_MUTED)
        self.multi_cell(0, 6, f"{tr['thanks']}\n\n{tr['contact']} {COMPANY_EMAIL}")

        # ── Save ───────────────────────────────────────────
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        safe_id = o.get('order_id', 'unknown').replace('/', '-')
        path = os.path.join(OUTPUT_DIR, f'receipt_{safe_id}.pdf')
        self.output(path)
        return path

    def _section(self, title: str):
        self.set_font('DejaVu', 'B', 11)
        self._color(C_PURPLE)
        self.cell(0, 7, title, new_x='LMARGIN', new_y='NEXT')
        self._color(C_PURPLE, stroke=True)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)

    def _row(self, label: str, value: str):
        self.set_font('DejaVu', '', 10)
        self._color(C_MUTED)
        self.cell(55, 7, f'{label}:', border=0)
        self.set_font('DejaVu', 'B', 10)
        self._color(C_DARK)
        self.cell(0, 7, str(value), border=0, new_x='LMARGIN', new_y='NEXT')


def generate_receipt(order_data: dict) -> str:
    pdf  = ReceiptPDF(order_data)
    path = pdf.build()
    print(f'✅ Receipt [{order_data.get("locale","ua")}]: {path}')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--order',  required=True)
    parser.add_argument('--email',  required=True)
    parser.add_argument('--plan',   default='basic', choices=['basic', 'full'])
    parser.add_argument('--amount', type=int)
    parser.add_argument('--name',   default='')
    parser.add_argument('--locale', default='ua', choices=['ua', 'ru', 'en'])
    parser.add_argument('--env',    default='dev', choices=['dev', 'prod'])
    args = parser.parse_args()

    data = {
        'order_id': args.order,
        'email':    args.email,
        'name':     args.name,
        'plan':     args.plan,
        'amount':   args.amount or PLAN_AMOUNTS[args.plan],
        'paid_at':  datetime.now().strftime('%d.%m.%Y %H:%M'),
        'locale':   args.locale,
        'env':      args.env,
    }
    print(generate_receipt(data))
