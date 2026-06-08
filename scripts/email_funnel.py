"""
Human Design UA — Email Funnel
Two funnels, 7 emails total, AIDA copywriting.

FUNNEL A: upsell_basic — for customers who bought the BASIC plan
  Email 1 — sent immediately after purchase (15-min urgency timer)
  Email 2 — sent 24h later if no upgrade (story + social proof)
  Email 3 — sent 48h later if no upgrade (scarcity)
  Email 4 — sent 72h later if no upgrade (final goodbye)

FUNNEL B: abandoned_payment — for customers whose payment FAILED
  Email 1 — sent 15 min after failure (HD is ready, just pay)
  Email 2 — sent 24h later if still unpaid
  Email 3 — sent 48h later if still unpaid (final)
"""

import os
import sqlite3
import smtplib
import json
import sys
from datetime import datetime, timedelta
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Config ──────────────────────────────────────────────────
GMAIL_USER = 'humandesign.finance@gmail.com'
DEV_APP_PASSWORD = 'ohqw npmh jtlh gzuq'
_raw = DEV_APP_PASSWORD or os.getenv('GMAIL_APP_PASSWORD', '')
GMAIL_PASSWORD = _raw.replace('\xa0', '').replace(' ', '')
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587

SITE_URL = os.getenv('SITE_URL', 'http://localhost:4000')
DB_PATH  = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'dev.db')

# Delays (in minutes — easy to change for prod: 60*24 = 1440)
DELAYS = {
    'upsell_1':    0,       # immediately
    'upsell_2':    60*24,   # 24h
    'upsell_3':    60*48,   # 48h
    'upsell_4':    60*72,   # 72h
    'abandoned_1': 15,      # 15 min
    'abandoned_2': 60*24,   # 24h
    'abandoned_3': 60*48,   # 48h
}


# ══════════════════════════════════════════════════════════════
# EMAIL COPY  (AIDA formula: Attention → Interest → Desire → Action)
# ══════════════════════════════════════════════════════════════

def _upsell_1(name, retry_url, locale='ru'):
    """AIDA #1 — Attention: you got basic. Interest: what's missing. Desire: feature list. Action: 15-min offer."""
    n = name or 'Дорогой читатель'
    texts = {
        'ua': {
            'subject': f'✦ {name}, твоя базова розшифровка готова + пропозиція на 15 хвилин',
            'body': f"""✦ {n.upper()}, ТВІЙ БАЗОВИЙ ДИЗАЙН ЛЮДИНИ РОЗРАХОВАНО

Ти щойно дізналась своє ядро — тип, стратегію та авторитет.
Це вже змінює багато. Але знаєш, що залишилось за кадром?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЗА 400 ГРН ТИ ОТРИМАЄШ ПОВНИЙ РОЗБІР:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Профіль
  Які ролі тобі легко даються, а де приймаєш нав'язані рішення

✓ 9 Центрів — 9 сфер життя
  Де ти впливаєш на оточуючих і де вразлива

✓ Планети та вузли
  Що стоїть за твоїм характером і куди веде тебе життя

✓ Розбір каналів
  Твої природні переваги — де і як їх використати

✓ Автоматичні реакції
  Що бачать у тебе інші, але ти не помічаєш — твої приховані козирі

✓ Інкарнаційний хрест
  Глобальний сенс твого життя і твій внесок у світ

✓ Самодостатність
  Наскільки ти самодостатня і чи потрібні тобі інші люди

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ ТІЛЬКИ ЗАРАЗ — ПРОТЯГОМ 15 ХВИЛИН:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

При оплаті зараз ти також отримаєш БЕЗКОШТОВНО:

✓ Практики декондиціонування
✓ Особистий план на 90 днів

→ ОТРИМАТИ ПОВНУ РОЗШИФРОВКУ ЗА 400 ГРН:
{retry_url}

З теплом,
Human Design UA
humandesign.finance@gmail.com""",
        },
        'ru': {
            'subject': f'✦ {name}, твоя базовая расшифровка готова + предложение на 15 минут',
            'body': f"""✦ {n.upper()}, ТВОЙ БАЗОВЫЙ ДИЗАЙН ЧЕЛОВЕКА РАССЧИТАН

Ты только что узнала своё ядро — тип, стратегию и авторитет.
Это уже меняет многое. Но знаешь, что осталось за кадром?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЗА 400 ГРН ТЫ ПОЛУЧИШЬ ПОЛНЫЙ РАЗБОР:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Профиль
  Какие роли тебе легко даются, а где принимаешь навязанные решения

✓ 9 Центров — 9 сфер жизни
  Где ты оказываешь влияние на окружающих и где уязвима

✓ Планеты и узлы
  Что стоит за твоим характером и куда тебя ведёт жизнь

✓ Разбор каналов
  Твои природные преимущества — где и как их использовать

✓ Автоматические реакции
  Что видят в тебе другие, но ты не замечаешь — твои скрытые козыри

✓ Инкарнационный крест
  Глобальный смысл твоей жизни и твой вклад в мир

✓ Самодостаточность
  Насколько ты самодостаточна и нужны ли тебе другие люди

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ ТОЛЬКО СЕЙЧАС — В ТЕЧЕНИЕ 15 МИНУТ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

При оплате прямо сейчас ты также получишь БЕСПЛАТНО:

✓ Практики декондиционирования
✓ Личный план на 90 дней

→ ПОЛУЧИТЬ ПОЛНУЮ РАСШИФРОВКУ ЗА 400 ГРН:
{retry_url}

С теплом,
Human Design UA
humandesign.finance@gmail.com""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _upsell_2(name, retry_url, locale='ru'):
    """AIDA #2 — Day 1. Attention: story hook. Interest: "what you're missing". Desire: transformation. Action."""
    n = name or ''
    texts = {
        'ua': {
            'subject': f'{name}, ти дізналась базу. Але ось що ти ще не знаєш про себе...',
            'body': f"""Привіт, {n}!

Вчора ти отримала базову розшифровку свого Дизайну Людини.
Сподіваюсь, ти вже відчула: «Так, це про мене!»

Але я хочу розповісти тобі одну річ.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЧОМУ ОДНОГО ТИПУ ЗАМАЛО
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Знати свій тип — це як знати свій знак зодіаку.
Цікаво? Так. Корисно для реального життя? Лише частково.

Справжні зміни починаються, коли ти бачиш повну карту:
  → Чому в одних стосунках тобі легко, а в інших — виснаження
  → Чому певна робота приносить потік, а інша — пустоту
  → Де твої автоматичні реакції грають проти тебе

Це не в базовій розшифровці. Це у повній.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
І ТИ МОЖЕШ ОТРИМАТИ ЇЇ ЗА 400 ГРН
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ ПЕРЕЙТИ ДО ПОВНОЇ РОЗШИФРОВКИ:
{retry_url}

З теплом,
Human Design UA""",
        },
        'ru': {
            'subject': f'{name}, ты узнала базу. Но вот что ты ещё не знаешь о себе...',
            'body': f"""Привет, {n}!

Вчера ты получила базовую расшифровку своего Дизайна Человека.
Надеюсь, ты уже почувствовала: «Да, это про меня!»

Но я хочу рассказать тебе кое-что важное.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПОЧЕМУ ОДНОГО ТИПА НЕДОСТАТОЧНО
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Знать свой тип — это как знать свой знак зодиака.
Интересно? Да. Полезно для реальной жизни? Лишь частично.

Настоящие изменения начинаются, когда ты видишь полную карту:
  → Почему в одних отношениях тебе легко, а в других — истощение
  → Почему определённая работа приносит поток, а другая — пустоту
  → Где твои автоматические реакции работают против тебя

Этого нет в базовой расшифровке. Это — в полной.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
И ТЫ МОЖЕШЬ ПОЛУЧИТЬ ЕЁ ЗА 400 ГРН
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ ПЕРЕЙТИ К ПОЛНОЙ РАСШИФРОВКЕ:
{retry_url}

С теплом,
Human Design UA""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _upsell_3(name, retry_url, locale='ru'):
    """AIDA #3 — Day 2. Scarcity + social proof."""
    n = name or ''
    texts = {
        'ua': {
            'subject': f'Останній шанс отримати повний розбір за 400 грн, {name}',
            'body': f"""{n}, залишається зовсім мало часу.

Ми тримаємо ціну апгрейду на рівні 400 грн лише для тих,
хто вже придбав базову розшифровку.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЩО КАЖУТЬ НАШІ КЛІЄНТКИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

«Базова дала мені напрямок, але повна — це інший рівень.
Я нарешті зрозуміла, чому виснажуюся в певних стосунках.»
— Олена, Київ

«Після розбору каналів я перестала боротись із собою.
Виявляється, я так і маю діяти — це моя природа.»
— Марія, Львів

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПОВНА РОЗШИФРОВКА ЗА 400 ГРН → ТІЛЬКИ СЬОГОДНІ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{retry_url}

Human Design UA""",
        },
        'ru': {
            'subject': f'Последний шанс получить полный разбор за 400 грн, {name}',
            'body': f"""{n}, времени остаётся совсем мало.

Мы держим цену апгрейда на уровне 400 грн только для тех,
кто уже приобрёл базовую расшифровку.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЧТО ГОВОРЯТ НАШИ КЛИЕНТКИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

«Базовая дала мне направление, но полная — это другой уровень.
Я наконец поняла, почему истощаюсь в определённых отношениях.»
— Елена, Киев

«После разбора каналов я перестала бороться с собой.
Оказывается, я так и должна действовать — это моя природа.»
— Мария, Львов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПОЛНАЯ РАСШИФРОВКА ЗА 400 ГРН → ТОЛЬКО СЕГОДНЯ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{retry_url}

Human Design UA""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _upsell_4(name, retry_url, locale='ru'):
    """AIDA #4 — Day 3. Final farewell."""
    n = name or ''
    texts = {
        'ua': {
            'subject': f'{name}, це наш останній лист',
            'body': f"""{n}, привіт.

Ми більше не будемо нагадувати про повну розшифровку.
Це наш останній лист із цією пропозицією.

Якщо ти вирішиш повернутись — пропозиція апгрейду за 400 грн
буде доступна ще 24 години. Після цього — лише повна ціна 799 грн.

→ ЗАБРАТИ ПОВНУ РОЗШИФРОВКУ ЗА 400 ГРН:
{retry_url}

Що б ти не вирішила — дякуємо, що довірила нам свій розрахунок.

З теплом,
Human Design UA""",
        },
        'ru': {
            'subject': f'{name}, это наше последнее письмо',
            'body': f"""{n}, привет.

Мы больше не будем напоминать о полной расшифровке.
Это наше последнее письмо с этим предложением.

Если ты решишь вернуться — предложение апгрейда за 400 грн
будет доступно ещё 24 часа. После этого — только полная цена 799 грн.

→ ЗАБРАТЬ ПОЛНУЮ РАСШИФРОВКУ ЗА 400 ГРН:
{retry_url}

Что бы ты ни решила — спасибо, что доверила нам свой расчёт.

С теплом,
Human Design UA""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _abandoned_1(name, retry_url, locale='ru'):
    """Abandoned #1 — 15 min after fail. HD is calculated, just pay."""
    n = name or ''
    texts = {
        'ua': {
            'subject': '✦ Твій Дизайн Людини розраховано — залишилось лише оплатити',
            'body': f"""Добрий день{(', ' + n) if n else ''}!

Ти щойно намагалась отримати розшифровку Дизайну Людини.
Схоже, оплата не пройшла — але твій розрахунок вже готовий.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТВІЙ ПЕРСОНАЛЬНИЙ БОДИГРАФ ЧЕКАЄ НА ТЕБЕ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ми вже розрахували твій Дизайн Людини на основі твоїх даних.
Як тільки ти завершиш оплату — розшифровка одразу надійде на пошту.

Можливі причини, чому оплата не пройшла:
  • Недостатньо коштів на картці
  • Карта заблокована для онлайн-платежів
  • Тимчасова помилка банку

→ ЗАВЕРШИТИ ОПЛАТУ І ОТРИМАТИ РОЗШИФРОВКУ:
{retry_url}

З теплом,
Human Design UA
humandesign.finance@gmail.com""",
        },
        'ru': {
            'subject': '✦ Твой Дизайн Человека рассчитан — осталось только оплатить',
            'body': f"""Добрый день{(', ' + n) if n else ''}!

Ты только что пыталась получить расшифровку Дизайна Человека.
Похоже, оплата не прошла — но твой расчёт уже готов.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТВОЙ ПЕРСОНАЛЬНЫЙ БОДИГРАФ ЖДЁТ ТЕБЯ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Мы уже рассчитали твой Дизайн Человека на основе твоих данных.
Как только ты завершишь оплату — расшифровка сразу придёт на почту.

Возможные причины, почему оплата не прошла:
  • Недостаточно средств на карте
  • Карта заблокирована для онлайн-платежей
  • Временная ошибка банка

→ ЗАВЕРШИТЬ ОПЛАТУ И ПОЛУЧИТЬ РАСШИФРОВКУ:
{retry_url}

С теплом,
Human Design UA
humandesign.finance@gmail.com""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _abandoned_2(name, retry_url, locale='ru'):
    """Abandoned #2 — Day 1. Softer reminder."""
    n = name or ''
    texts = {
        'ua': {
            'subject': f'{name}, твій розрахунок ще чекає на тебе',
            'body': f"""Привіт{(', ' + n) if n else ''}!

Вчора ти почала оформлювати розшифровку Дизайну Людини,
але щось завадило завершити оплату.

Ми нікуди не ділись — і твій персональний бодиграф теж.

Просто перейди за посиланням і заверши оплату.
Розшифровка надійде на пошту протягом 10 хвилин.

→ ЗАВЕРШИТИ ЗАМОВЛЕННЯ:
{retry_url}

Human Design UA""",
        },
        'ru': {
            'subject': f'{name}, твой расчёт всё ещё ждёт тебя',
            'body': f"""Привет{(', ' + n) if n else ''}!

Вчера ты начала оформлять расшифровку Дизайна Человека,
но что-то помешало завершить оплату.

Мы никуда не делись — и твой персональный бодиграф тоже.

Просто перейди по ссылке и заверши оплату.
Расшифровка придёт на почту в течение 10 минут.

→ ЗАВЕРШИТЬ ЗАКАЗ:
{retry_url}

Human Design UA""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _abandoned_3(name, retry_url, locale='ru'):
    """Abandoned #3 — Day 2. Final nudge."""
    n = name or ''
    texts = {
        'ua': {
            'subject': f'Останнє нагадування — твій Дизайн Людини готовий',
            'body': f"""{n}, це наше останнє нагадування.

Два дні тому ти намагалась отримати розшифровку Дизайну Людини.
Твій персональний розрахунок досі готовий і чекає.

Після сьогодні ми більше не будемо нагадувати.

→ ОТРИМАТИ РОЗШИФРОВКУ ЗАРАЗ:
{retry_url}

Human Design UA""",
        },
        'ru': {
            'subject': f'Последнее напоминание — твой Дизайн Человека готов',
            'body': f"""{n}, это наше последнее напоминание.

Два дня назад ты пыталась получить расшифровку Дизайна Человека.
Твой персональный расчёт до сих пор готов и ждёт.

После сегодня мы больше не будем напоминать.

→ ПОЛУЧИТЬ РАСШИФРОВКУ СЕЙЧАС:
{retry_url}

Human Design UA""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


# ══════════════════════════════════════════════════════════════
# DATABASE — funnel state tracking
# ══════════════════════════════════════════════════════════════

def init_funnel_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS email_funnel (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id     TEXT NOT NULL,
            email        TEXT NOT NULL,
            name         TEXT DEFAULT '',
            plan         TEXT DEFAULT 'basic',
            locale       TEXT DEFAULT 'ru',
            funnel_type  TEXT NOT NULL,   -- 'upsell_basic' | 'abandoned_payment'
            step         INTEGER DEFAULT 0,
            next_send_at TEXT,            -- ISO datetime
            done         INTEGER DEFAULT 0,  -- 1 = no more emails
            converted    INTEGER DEFAULT 0,  -- 1 = upgraded / paid
            created_at   TEXT DEFAULT (datetime('now')),
            last_sent_at TEXT,
            site_url     TEXT DEFAULT 'http://localhost:4000'
        );
        CREATE INDEX IF NOT EXISTS idx_funnel_next
            ON email_funnel(done, converted, next_send_at);
    """)
    conn.commit()
    conn.close()


def enqueue_funnel(order_id, email, name, plan, locale, funnel_type, site_url=None):
    """Add an order to a funnel. Call once after purchase or fail."""
    init_funnel_db()
    url = site_url or SITE_URL

    # delay_key for first email
    first_key = 'upsell_1' if funnel_type == 'upsell_basic' else 'abandoned_1'
    delay_min = DELAYS[first_key]
    send_at   = (datetime.now() + timedelta(minutes=delay_min)).strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    # Avoid duplicate funnels for same order+type
    exists = conn.execute(
        "SELECT id FROM email_funnel WHERE order_id=? AND funnel_type=?",
        (order_id, funnel_type)
    ).fetchone()
    if not exists:
        conn.execute("""
            INSERT INTO email_funnel
                (order_id, email, name, plan, locale, funnel_type, step, next_send_at, site_url)
            VALUES (?,?,?,?,?,?,0,?,?)
        """, (order_id, email, name, plan, locale, funnel_type, send_at, url))
        conn.commit()
        print(f'📬 Funnel enqueued: {funnel_type} for {email} — first email in {delay_min}m')
    else:
        print(f'ℹ️  Funnel {funnel_type} already exists for {order_id}')
    conn.close()


def mark_converted(email, funnel_type):
    """Mark all funnels for this email as converted (stop sending)."""
    init_funnel_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        UPDATE email_funnel SET converted=1, done=1
        WHERE email=? AND funnel_type=?
    """, (email, funnel_type))
    conn.commit()
    conn.close()
    print(f'✅ Funnel {funnel_type} marked converted for {email}')


# ══════════════════════════════════════════════════════════════
# SEND ENGINE
# ══════════════════════════════════════════════════════════════

def _build_retry_url(row):
    plan     = row['plan'] if isinstance(row, dict) else row[3]
    site_url = row['site_url'] if isinstance(row, dict) else row[13]
    return f'{site_url}/quiz.html?plan={plan}#pricing'


def _send(to_email, subject, body):
    """Low-level SMTP send."""
    if not GMAIL_PASSWORD:
        print('❌ GMAIL_APP_PASSWORD not set')
        return False
    msg = MIMEMultipart()
    msg['From']     = f'Human Design UA <{GMAIL_USER}>'
    msg['To']       = to_email
    msg['Subject']  = Header(subject, 'utf-8')
    msg['Reply-To'] = GMAIL_USER
    msg.attach(MIMEText(body.replace('\xa0', ' '), 'plain', 'utf-8'))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, local_hostname='localhost') as s:
            s.ehlo('localhost'); s.starttls(); s.ehlo('localhost')
            s.login(GMAIL_USER, GMAIL_PASSWORD)
            s.sendmail(GMAIL_USER, [to_email], msg.as_bytes(),
                       mail_options=['BODY=8BITMIME'])
        print(f'✉️  Sent [{subject[:50]}] → {to_email}')
        return True
    except Exception as e:
        print(f'❌ Send error: {e}')
        return False


# Map funnel_type + step → (content_fn, next_delay_key or None)
FUNNEL_STEPS = {
    'upsell_basic': [
        (_upsell_1, 'upsell_2'),
        (_upsell_2, 'upsell_3'),
        (_upsell_3, 'upsell_4'),
        (_upsell_4, None),        # final — done after this
    ],
    'abandoned_payment': [
        (_abandoned_1, 'abandoned_2'),
        (_abandoned_2, 'abandoned_3'),
        (_abandoned_3, None),     # final
    ],
}


def process_due_emails():
    """Check DB for emails due now and send them. Call on a timer."""
    init_funnel_db()
    now  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    due = conn.execute("""
        SELECT * FROM email_funnel
        WHERE done=0 AND converted=0
          AND next_send_at <= ?
        ORDER BY next_send_at ASC
    """, (now,)).fetchall()

    for row in due:
        row = dict(row)
        ftype = row['funnel_type']
        step  = row['step']
        steps = FUNNEL_STEPS.get(ftype, [])

        if step >= len(steps):
            conn.execute("UPDATE email_funnel SET done=1 WHERE id=?", (row['id'],))
            conn.commit()
            continue

        content_fn, next_delay_key = steps[step]
        retry_url = _build_retry_url(row)
        subject, body = content_fn(row['name'], retry_url, row['locale'])

        ok = _send(row['email'], subject, body)
        now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if ok:
            next_step = step + 1
            if next_delay_key is None or next_step >= len(steps):
                # No more emails
                conn.execute("""
                    UPDATE email_funnel
                    SET step=?, done=1, last_sent_at=?
                    WHERE id=?
                """, (next_step, now_ts, row['id']))
            else:
                delay_min = DELAYS[next_delay_key]
                next_at   = (datetime.now() + timedelta(minutes=delay_min)).strftime('%Y-%m-%d %H:%M:%S')
                conn.execute("""
                    UPDATE email_funnel
                    SET step=?, next_send_at=?, last_sent_at=?
                    WHERE id=?
                """, (next_step, next_at, now_ts, row['id']))
            conn.commit()

    conn.close()
    return len(due)


# ══════════════════════════════════════════════════════════════
# BACKGROUND SCHEDULER (runs inside dev_server)
# ══════════════════════════════════════════════════════════════

def start_scheduler(interval_seconds=60):
    """Start background thread that calls process_due_emails every N seconds."""
    import threading

    def _loop():
        import time
        print(f'📅 Email funnel scheduler started (every {interval_seconds}s)')
        while True:
            try:
                sent = process_due_emails()
                if sent:
                    print(f'📬 Funnel tick: sent {sent} email(s)')
            except Exception as e:
                print(f'⚠️  Funnel scheduler error: {e}')
            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


# ══════════════════════════════════════════════════════════════
# CLI  — manual test
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse, time
    parser = argparse.ArgumentParser()
    parser.add_argument('--funnel', choices=['upsell_basic','abandoned_payment'], required=True)
    parser.add_argument('--email',  required=True)
    parser.add_argument('--name',   default='Натали')
    parser.add_argument('--plan',   default='basic')
    parser.add_argument('--locale', default='ru')
    parser.add_argument('--step',   type=int, default=0, help='Send specific step immediately')
    args = parser.parse_args()

    retry_url = f'{SITE_URL}/quiz.html?plan={args.plan}#pricing'
    steps     = FUNNEL_STEPS[args.funnel]
    content_fn, _ = steps[args.step]
    subject, body = content_fn(args.name, retry_url, args.locale)

    print(f'\n📧 Sending {args.funnel} step {args.step} to {args.email}')
    print(f'   Subject: {subject}')
    ok = _send(args.email, subject, body)
    print('Result:', '✅ sent' if ok else '❌ failed')
