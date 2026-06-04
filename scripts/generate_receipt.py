"""
Human Design UA — PDF Receipt Generator
Generates a payment receipt PDF for a given order.

Usage:
    python3 scripts/generate_receipt.py --order HD-1234 --email test@gmail.com \
        --plan basic --amount 399 --name "Олена"

Requirements:
    pip install fpdf2
"""

import argparse
import os
from datetime import datetime
from fpdf import FPDF

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FONT_DIR     = os.path.join(BASE_DIR, 'fonts')
FONT_REG     = os.path.join(FONT_DIR, 'DejaVuSans.ttf')
FONT_BOLD    = os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf')
LOGO_PATH    = os.path.join(BASE_DIR, '..', 'site', 'assets', 'img', 'logo.png')
OUTPUT_DIR   = os.path.join(BASE_DIR, '..', 'tmp', 'receipts')

# ── Config ────────────────────────────────────────────────────
COMPANY_NAME = "Human Design UA"
COMPANY_EMAIL= "humandesign.finance@gmail.com"
COMPANY_SITE = "humandesign.ua"

PLAN_NAMES = {
    'basic': 'Базова розшифровка бодіграфу',
    'full':  'Повна розшифровка бодіграфу',
}
PLAN_AMOUNTS = {'basic': 399, 'full': 799}

# ── Colors (R, G, B) ──────────────────────────────────────────
C_DARK   = (13,  11,  30)
C_CARD   = (26,  20,  64)
C_GOLD   = (212, 168, 48)
C_PURPLE = (155, 110, 224)
C_MUTED  = (107, 95,  128)
C_LIGHT  = (240, 236, 232)
C_WHITE  = (255, 255, 255)


class ReceiptPDF(FPDF):
    def __init__(self, order_data: dict):
        super().__init__()
        self.order = order_data
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)
        # Register Unicode fonts
        self.add_font('DejaVu',     '', FONT_REG,  )
        self.add_font('DejaVu',     'B', FONT_BOLD, )

    def _set_color(self, color, stroke=False):
        if stroke:
            self.set_draw_color(*color)
        else:
            self.set_text_color(*color)

    def header(self):
        # Logo
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=20, y=12, w=28)
            self.set_xy(52, 12)
        else:
            self.set_xy(20, 12)

        # Company name
        self.set_font('DejaVu', 'B', 16)
        self._set_color(C_DARK)
        self.cell(0, 8, COMPANY_NAME, new_x='LMARGIN', new_y='NEXT')

        # Subtitle
        self.set_font('DejaVu', '', 9)
        self._set_color(C_MUTED)
        self.cell(0, 5, f'{COMPANY_EMAIL}  ·  {COMPANY_SITE}',
                  new_x='LMARGIN', new_y='NEXT')
        self.ln(4)

        # Gold divider
        self._set_color(C_GOLD, stroke=True)
        self.set_line_width(0.6)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-18)
        self.set_font('DejaVu', '', 8)
        self._set_color(C_MUTED)
        self.cell(0, 5,
            f'{COMPANY_NAME}  ·  {COMPANY_EMAIL}  ·  Дякуємо за довіру ✦',
            align='C'
        )

    def build(self) -> str:
        self.add_page()
        o = self.order

        # ── Title ──────────────────────────────────────────
        self.set_font('DejaVu', 'B', 22)
        self._set_color(C_DARK)
        self.cell(0, 12, 'Чек про оплату', new_x='LMARGIN', new_y='NEXT')

        self.set_font('DejaVu', '', 10)
        self._set_color(C_MUTED)
        now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
        self.cell(0, 6, f'Документ сформовано: {now_str}',
                  new_x='LMARGIN', new_y='NEXT')
        self.ln(8)

        # ── Order details ──────────────────────────────────
        self._section('Деталі замовлення')
        paid_method = 'LiqPay (Visa/Mastercard)' if o.get('env') != 'dev' \
                      else 'DEV — тестовий платіж'
        self._row('Номер замовлення', o.get('order_id', '—'))
        self._row('Дата оплати',      o.get('paid_at', now_str))
        self._row('Статус',           '✓ Оплачено')
        self._row('Спосіб оплати',    paid_method)
        self.ln(6)

        # ── Customer ───────────────────────────────────────
        self._section('Інформація про клієнта')
        self._row("Ім'я",  o.get('name',  '—'))
        self._row('Email', o.get('email', '—'))
        self.ln(6)

        # ── Product table ──────────────────────────────────
        self._section('Послуга')

        plan     = o.get('plan', 'basic')
        amount   = o.get('amount', PLAN_AMOUNTS.get(plan, 399))
        prod_name = PLAN_NAMES.get(plan, 'Розшифровка бодіграфу')

        # Header row
        self.set_fill_color(*C_CARD)
        self.set_font('DejaVu', 'B', 9)
        self._set_color(C_GOLD)
        self.cell(110, 8, 'Назва послуги', fill=True, border=0)
        self.cell(30,  8, 'К-сть', align='C', fill=True, border=0)
        self.cell(40,  8, 'Сума',  align='R', fill=True, border=0)
        self.ln()

        # Product row
        self.set_fill_color(240, 238, 255)
        self.set_font('DejaVu', '', 10)
        self._set_color(C_DARK)
        self.cell(110, 9, prod_name,           fill=True, border=0)
        self.cell(30,  9, '1',  align='C',     fill=True, border=0)
        self.cell(40,  9, f'{amount} грн',     align='R', fill=True, border=0)
        self.ln()

        # Total row
        self.set_fill_color(*C_GOLD)
        self.set_font('DejaVu', 'B', 11)
        self._set_color(C_DARK)
        self.cell(140, 10, 'Разом до сплати:', fill=True, border=0)
        self.cell(40,  10, f'{amount} грн',    fill=True, border=0, align='R')
        self.ln(14)

        # ── DEV notice ─────────────────────────────────────
        if o.get('env') == 'dev':
            self.set_fill_color(255, 240, 200)
            self.set_font('DejaVu', 'B', 9)
            self.set_text_color(160, 90, 0)
            self.cell(0, 8,
                '⚠  DEV РЕЖИМ — Цей чек є тестовим. Реальні гроші не списувались.',
                fill=True, align='C', new_x='LMARGIN', new_y='NEXT'
            )
            self.ln(5)

        # ── Thank you ──────────────────────────────────────
        self.set_font('DejaVu', '', 10)
        self._set_color(C_MUTED)
        self.multi_cell(0, 6,
            'Дякуємо за замовлення!\n'
            'Ваша персональна розшифровка Дизайну Людини буде надіслана '
            'на вказану email-адресу протягом 10 хвилин.\n\n'
            f'Питання? Пишіть: {COMPANY_EMAIL}'
        )

        # ── Save ───────────────────────────────────────────
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        safe_id = o.get('order_id', 'unknown').replace('/', '-')
        path = os.path.join(OUTPUT_DIR, f'receipt_{safe_id}.pdf')
        self.output(path)
        return path

    def _section(self, title: str):
        self.set_font('DejaVu', 'B', 11)
        self._set_color(C_PURPLE)
        self.cell(0, 7, title, new_x='LMARGIN', new_y='NEXT')
        self._set_color(C_PURPLE, stroke=True)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)

    def _row(self, label: str, value: str):
        self.set_font('DejaVu', '', 10)
        self._set_color(C_MUTED)
        self.cell(55, 7, f'{label}:', border=0)
        self.set_font('DejaVu', 'B', 10)
        self._set_color(C_DARK)
        self.cell(0, 7, str(value), border=0, new_x='LMARGIN', new_y='NEXT')


def generate_receipt(order_data: dict) -> str:
    pdf  = ReceiptPDF(order_data)
    path = pdf.build()
    print(f'✅ Receipt: {path}')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate HD receipt PDF')
    parser.add_argument('--order',  required=True)
    parser.add_argument('--email',  required=True)
    parser.add_argument('--plan',   default='basic', choices=['basic', 'full'])
    parser.add_argument('--amount', type=int)
    parser.add_argument('--name',   default='')
    parser.add_argument('--env',    default='dev',  choices=['dev', 'prod'])
    args = parser.parse_args()

    data = {
        'order_id': args.order,
        'email':    args.email,
        'name':     args.name,
        'plan':     args.plan,
        'amount':   args.amount or PLAN_AMOUNTS[args.plan],
        'paid_at':  datetime.now().strftime('%d.%m.%Y %H:%M'),
        'env':      args.env,
    }
    print(generate_receipt(data))
