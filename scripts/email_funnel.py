"""
Human Design UA — Email Funnel
Two funnels, 7 emails total, AIDA copywriting, UA/RU/EN.

FUNNEL A: upsell_basic — for customers who bought the BASIC plan
  Email 1 — sent immediately (15-min urgency timer)
  Email 2 — sent 24h later if no upgrade
  Email 3 — sent 48h later if no upgrade
  Email 4 — sent 72h later if no upgrade (final)

FUNNEL B: abandoned_payment — for customers whose payment FAILED
  Email 1 — sent 15 min after failure
  Email 2 — sent 24h later if still unpaid
  Email 3 — sent 48h later if still unpaid (final)

Basic plan includes: Тип, Стратегія, Авторитет, Профіль, Ключові центри
Full plan adds:      9 Центрів (детально), Планети і вузли, Канали,
                     Автоматичні реакції, Інкарнаційний хрест, Самодостатність
"""

import os
import sqlite3
import smtplib
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

# Delays in minutes
DELAYS = {
    'upsell_1':    0,
    'upsell_2':    60 * 24,
    'upsell_3':    60 * 48,
    'upsell_4':    60 * 72,
    'abandoned_1': 15,
    'abandoned_2': 60 * 24,
    'abandoned_3': 60 * 48,
}


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _hi(name, locale):
    """Personalised greeting prefix."""
    if not name:
        return {'ua': 'Привіт!', 'ru': 'Привет!', 'en': 'Hello!'}[locale]
    return {'ua': f'Привіт, {name}!', 'ru': f'Привет, {name}!', 'en': f'Hello, {name}!'}[locale]

def _sign(locale):
    return {
        'ua': 'З теплом,\nHuman Design UA\nhumandesign.finance@gmail.com',
        'ru': 'С теплом,\nHuman Design UA\nhumandesign.finance@gmail.com',
        'en': 'With warmth,\nHuman Design UA\nhumandesign.finance@gmail.com',
    }[locale]


# ══════════════════════════════════════════════════════════════
# UPSELL EMAILS  (basic → full, +400 UAH)
# What FULL adds over BASIC:
#   9 Центрів детально · Планети і вузли · Канали · Автоматичні реакції
#   Інкарнаційний хрест · Самодостатність
# ══════════════════════════════════════════════════════════════

def _upsell_1(name, retry_url, locale='ru'):
    """
    AIDA #1 — Immediate.
    Attention: name + "your basic is ready".
    Interest: what's STILL hidden.
    Desire: full list of extra features + 15-min bonus.
    Action: pay now.
    """
    hi   = _hi(name, locale)
    sign = _sign(locale)

    texts = {
        'ua': {
            'subject': f'✦ Твоя базова розшифровка готова + пропозиція на 15 хвилин',
            'body': f"""{hi}

Твій базовий Дизайн Людини вже у тебе — тип, стратегія, авторитет, профіль і ключові центри.
Це справжній фундамент для розуміння себе.

Але ось що залишилось поза кадром...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЗА ДОПЛАТУ 400 ГРН ТИ ВІДКРИЄШ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ 9 Центрів — 9 сфер життя
  Де ти оказуєш вплив на оточуючих і де вразлива

✓ Планети та вузли
  Що стоїть за твоїм характером і куди тебе веде життя

✓ Розбір каналів
  Твої природні переваги — де і як їх використати

✓ Автоматичні реакції
  Що бачать у тебе інші, але ти не помічаєш — твої приховані козирі

✓ Інкарнаційний хрест
  Глобальний сенс твого життя і твій внесок у світ

✓ Самодостатність
  Наскільки ти самодостатня і чи потрібні тобі інші люди

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ ТІЛЬКИ ПРОТЯГОМ 15 ХВИЛИН — БЕЗКОШТОВНО:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Практики декондиціонування
✓ Особистий план на 90 днів

→ ОТРИМАТИ ПОВНУ РОЗШИФРОВКУ ЗА 400 ГРН:
{retry_url}

{sign}""",
        },
        'ru': {
            'subject': f'✦ Твоя базовая расшифровка готова + предложение на 15 минут',
            'body': f"""{hi}

Твой базовый Дизайн Человека уже у тебя — тип, стратегия, авторитет, профиль и ключевые центры.
Это настоящий фундамент для понимания себя.

Но вот что осталось за кадром...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЗА ДОПЛАТУ 400 ГРН ТЫ ОТКРОЕШЬ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
⏰ ТОЛЬКО В ТЕЧЕНИЕ 15 МИНУТ — БЕСПЛАТНО:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Практики декондиционирования
✓ Личный план на 90 дней

→ ПОЛУЧИТЬ ПОЛНУЮ РАСШИФРОВКУ ЗА 400 ГРН:
{retry_url}

{sign}""",
        },
        'en': {
            'subject': f'✦ Your basic reading is ready + 15-minute offer',
            'body': f"""{hi}

Your basic Human Design reading is with you — type, strategy, authority, profile and key centres.
That's a real foundation for understanding yourself.

But here's what's still hidden...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOR AN EXTRA 400 UAH YOU'LL UNLOCK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ 9 Centres — 9 areas of life
  Where you influence others and where you're vulnerable

✓ Planets and nodes
  What's behind your character and where life is leading you

✓ Channel analysis
  Your natural advantages — where and how to use them

✓ Automatic reactions
  What others see in you that you don't notice — your hidden strengths

✓ Incarnation cross
  The global meaning of your life and your contribution to the world

✓ Self-sufficiency
  How self-sufficient you are and whether you need others

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ ONLY FOR THE NEXT 15 MINUTES — FREE BONUS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Deconditioning practices
✓ Personal 90-day plan

→ GET THE FULL READING FOR 400 UAH:
{retry_url}

{sign}""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _upsell_2(name, retry_url, locale='ru'):
    """AIDA #2 — Day 1. Story hook about what's missing."""
    hi   = _hi(name, locale)
    sign = _sign(locale)

    texts = {
        'ua': {
            'subject': 'Ти дізналась базу. Але ось що ти ще не знаєш про себе...',
            'body': f"""{hi}

Учора ти отримала базову розшифровку свого Дизайну Людини.
Сподіваюсь, ти вже відчула: «Так, це про мене!»

Але є дещо важливе, що хочу тобі розповісти.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЧОМУ ОДНОГО ТИПУ ЗАМАЛО
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Знати свій тип — це як знати свій знак зодіаку.
Цікаво? Так. Корисно для реального життя? Лише частково.

Справжні зміни починаються, коли ти бачиш повну карту:
  → Чому в одних стосунках тобі легко, а в інших — виснаження
  → Чому певна робота дає потік, а інша — пустоту
  → Де твої автоматичні реакції грають проти тебе

Це — у повній розшифровці. І зараз вона коштує лише +400 грн.

→ ПЕРЕЙТИ ДО ПОВНОЇ РОЗШИФРОВКИ:
{retry_url}

{sign}""",
        },
        'ru': {
            'subject': 'Ты узнала базу. Но вот что ты ещё не знаешь о себе...',
            'body': f"""{hi}

Вчера ты получила базовую расшифровку своего Дизайна Человека.
Надеюсь, ты уже почувствовала: «Да, это про меня!»

Но есть кое-что важное, что хочу тебе рассказать.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПОЧЕМУ ОДНОГО ТИПА НЕДОСТАТОЧНО
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Знать свой тип — это как знать свой знак зодиака.
Интересно? Да. Полезно для реальной жизни? Лишь частично.

Настоящие изменения начинаются, когда ты видишь полную карту:
  → Почему в одних отношениях тебе легко, а в других — истощение
  → Почему определённая работа даёт поток, а другая — пустоту
  → Где твои автоматические реакции работают против тебя

Это — в полной расшифровке. И сейчас она стоит всего +400 грн.

→ ПЕРЕЙТИ К ПОЛНОЙ РАСШИФРОВКЕ:
{retry_url}

{sign}""",
        },
        'en': {
            'subject': "You learned the basics. But here's what you still don't know about yourself...",
            'body': f"""{hi}

Yesterday you received your basic Human Design reading.
I hope you already felt: "Yes, this is me!"

But there's something important I want to share with you.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHY YOUR TYPE ALONE ISN'T ENOUGH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Knowing your type is like knowing your star sign.
Interesting? Yes. Useful for real life? Only partly.

Real change begins when you see the full picture:
  → Why some relationships feel easy and others drain you
  → Why certain work brings flow and other work feels empty
  → Where your automatic reactions work against you

That's in the full reading. And right now it's only +400 UAH.

→ GO TO THE FULL READING:
{retry_url}

{sign}""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _upsell_3(name, retry_url, locale='ru'):
    """AIDA #3 — Day 2. Scarcity + social proof."""
    hi   = _hi(name, locale)
    sign = _sign(locale)

    texts = {
        'ua': {
            'subject': 'Останній шанс отримати повний розбір за 400 грн',
            'body': f"""{hi}

Ціна апгрейду 400 грн діє тільки для тих,
хто вже придбав базову розшифровку. Залишилось зовсім мало часу.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЩО КАЖУТЬ НАШІ КЛІЄНТКИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

«Базова дала мені напрямок, але повна — це зовсім інший рівень.
Я нарешті зрозуміла, чому виснажуюсь у певних стосунках.»
— Олена, Київ

«Після розбору каналів я перестала боротись із собою.
Виявляється, я саме так і маю діяти — це моя природа.»
— Марія, Львів

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПОВНА РОЗШИФРОВКА ЗА 400 ГРН → ТІЛЬКИ СЬОГОДНІ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{retry_url}

{sign}""",
        },
        'ru': {
            'subject': 'Последний шанс получить полный разбор за 400 грн',
            'body': f"""{hi}

Цена апгрейда 400 грн действует только для тех,
кто уже приобрёл базовую расшифровку. Времени остаётся совсем мало.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ЧТО ГОВОРЯТ НАШИ КЛИЕНТКИ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

«Базовая дала мне направление, но полная — это совсем другой уровень.
Я наконец поняла, почему истощаюсь в определённых отношениях.»
— Елена, Киев

«После разбора каналов я перестала бороться с собой.
Оказывается, я именно так и должна действовать — это моя природа.»
— Мария, Львов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ПОЛНАЯ РАСШИФРОВКА ЗА 400 ГРН → ТОЛЬКО СЕГОДНЯ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{retry_url}

{sign}""",
        },
        'en': {
            'subject': 'Last chance to get the full reading for 400 UAH',
            'body': f"""{hi}

The 400 UAH upgrade price is only available for those
who have already purchased the basic reading. Very little time left.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT OUR CLIENTS SAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"The basic gave me direction, but the full reading is a whole other level.
I finally understood why I get drained in certain relationships."
— Elena, Kyiv

"After the channel analysis I stopped fighting myself.
Turns out I'm meant to act this way — it's just my nature."
— Maria, Lviv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FULL READING FOR 400 UAH → TODAY ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{retry_url}

{sign}""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _upsell_4(name, retry_url, locale='ru'):
    """AIDA #4 — Day 3. Final farewell."""
    hi   = _hi(name, locale)
    sign = _sign(locale)

    texts = {
        'ua': {
            'subject': 'Це наш останній лист',
            'body': f"""{hi}

Ми більше не будемо нагадувати про повну розшифровку.
Це наш останній лист із цією пропозицією.

Якщо ти повернешся сьогодні — апгрейд за 400 грн ще доступний.
Завтра — тільки повна ціна 799 грн.

→ ЗАБРАТИ ПОВНУ РОЗШИФРОВКУ ЗА 400 ГРН:
{retry_url}

Що б ти не вирішила — дякуємо, що довірила нам свій розрахунок.

{sign}""",
        },
        'ru': {
            'subject': 'Это наше последнее письмо',
            'body': f"""{hi}

Мы больше не будем напоминать о полной расшифровке.
Это наше последнее письмо с этим предложением.

Если ты вернёшься сегодня — апгрейд за 400 грн ещё доступен.
Завтра — только полная цена 799 грн.

→ ЗАБРАТЬ ПОЛНУЮ РАСШИФРОВКУ ЗА 400 ГРН:
{retry_url}

Что бы ты ни решила — спасибо, что доверила нам свой расчёт.

{sign}""",
        },
        'en': {
            'subject': 'This is our last email',
            'body': f"""{hi}

We won't be reminding you about the full reading anymore.
This is our last email with this offer.

If you come back today — the 400 UAH upgrade is still available.
Tomorrow — only the full price of 799 UAH.

→ GET THE FULL READING FOR 400 UAH:
{retry_url}

Whatever you decide — thank you for trusting us with your reading.

{sign}""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


# ══════════════════════════════════════════════════════════════
# ABANDONED PAYMENT EMAILS
# ══════════════════════════════════════════════════════════════

def _abandoned_1(name, retry_url, locale='ru'):
    """Abandoned #1 — 15 min. HD is ready, just pay."""
    sign = _sign(locale)

    texts = {
        'ua': {
            'subject': '✦ Твій Дизайн Людини розраховано — залишилось лише оплатити',
            'body': f"""Добрий день{(', ' + name) if name else ''}!

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

{sign}""",
        },
        'ru': {
            'subject': '✦ Твой Дизайн Человека рассчитан — осталось только оплатить',
            'body': f"""Добрый день{(', ' + name) if name else ''}!

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

{sign}""",
        },
        'en': {
            'subject': '✦ Your Human Design is calculated — just complete your payment',
            'body': f"""Hello{(', ' + name) if name else ''}!

You just tried to get your Human Design reading.
It looks like the payment didn't go through — but your reading is already calculated.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PERSONAL BODYGRAPH IS WAITING FOR YOU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We've already calculated your Human Design based on your birth data.
As soon as you complete payment — your reading will arrive in your inbox immediately.

Possible reasons the payment didn't go through:
  • Insufficient funds on the card
  • Card blocked for online payments
  • Temporary bank error

→ COMPLETE PAYMENT AND GET YOUR READING:
{retry_url}

{sign}""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _abandoned_2(name, retry_url, locale='ru'):
    """Abandoned #2 — Day 1. Softer reminder."""
    sign = _sign(locale)

    texts = {
        'ua': {
            'subject': 'Твій розрахунок ще чекає на тебе',
            'body': f"""Привіт{(', ' + name) if name else ''}!

Учора ти почала оформлювати розшифровку Дизайну Людини,
але щось завадило завершити оплату.

Ми нікуди не ділись — і твій персональний бодиграф теж.

Просто перейди за посиланням і заверши оплату.
Розшифровка надійде на пошту протягом 10 хвилин.

→ ЗАВЕРШИТИ ЗАМОВЛЕННЯ:
{retry_url}

{sign}""",
        },
        'ru': {
            'subject': 'Твой расчёт всё ещё ждёт тебя',
            'body': f"""Привет{(', ' + name) if name else ''}!

Вчера ты начала оформлять расшифровку Дизайна Человека,
но что-то помешало завершить оплату.

Мы никуда не делись — и твой персональный бодиграф тоже.

Просто перейди по ссылке и заверши оплату.
Расшифровка придёт на почту в течение 10 минут.

→ ЗАВЕРШИТЬ ЗАКАЗ:
{retry_url}

{sign}""",
        },
        'en': {
            'subject': 'Your reading is still waiting for you',
            'body': f"""Hello{(', ' + name) if name else ''}!

Yesterday you started ordering your Human Design reading,
but something got in the way of completing the payment.

We're still here — and so is your personal bodygraph.

Just follow the link and complete the payment.
Your reading will arrive within 10 minutes.

→ COMPLETE YOUR ORDER:
{retry_url}

{sign}""",
        },
    }
    t = texts.get(locale, texts['ru'])
    return t['subject'], t['body']


def _abandoned_3(name, retry_url, locale='ru'):
    """Abandoned #3 — Day 2. Final nudge."""
    sign = _sign(locale)

    texts = {
        'ua': {
            'subject': 'Останнє нагадування — твій Дизайн Людини готовий',
            'body': f"""Привіт{(', ' + name) if name else ''}!

Два дні тому ти намагалась отримати розшифровку Дизайну Людини.
Твій персональний розрахунок досі готовий і чекає.

Після сьогодні ми більше не будемо нагадувати.

→ ОТРИМАТИ РОЗШИФРОВКУ ЗАРАЗ:
{retry_url}

{sign}""",
        },
        'ru': {
            'subject': 'Последнее напоминание — твой Дизайн Человека готов',
            'body': f"""Привет{(', ' + name) if name else ''}!

Два дня назад ты пыталась получить расшифровку Дизайна Человека.
Твой персональный расчёт до сих пор готов и ждёт.

После сегодня мы больше не будем напоминать.

→ ПОЛУЧИТЬ РАСШИФРОВКУ СЕЙЧАС:
{retry_url}

{sign}""",
        },
        'en': {
            'subject': 'Last reminder — your Human Design reading is ready',
            'body': f"""Hello{(', ' + name) if name else ''}!

Two days ago you tried to get your Human Design reading.
Your personal calculation is still ready and waiting.

After today we won't be sending any more reminders.

→ GET YOUR READING NOW:
{retry_url}

{sign}""",
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
            locale       TEXT DEFAULT 'ua',
            funnel_type  TEXT NOT NULL,
            step         INTEGER DEFAULT 0,
            next_send_at TEXT,
            done         INTEGER DEFAULT 0,
            converted    INTEGER DEFAULT 0,
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

    first_key = 'upsell_1' if funnel_type == 'upsell_basic' else 'abandoned_1'
    delay_min = DELAYS[first_key]
    send_at   = (datetime.now() + timedelta(minutes=delay_min)).strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
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
        print(f'📬 Funnel [{funnel_type}] queued for {email} (locale={locale}) — first in {delay_min}m')
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
    print(f'✅ Funnel [{funnel_type}] converted for {email}')


# ══════════════════════════════════════════════════════════════
# SEND ENGINE
# ══════════════════════════════════════════════════════════════

def _build_retry_url(row):
    plan     = row['plan']
    site_url = row['site_url']
    return f'{site_url}/quiz.html?plan={plan}#pricing'


def _load_header_b64():
    """Load SVG header as base64 data URI (works in all email clients)."""
    svg_path = os.path.join(os.path.dirname(__file__),
                            '..', 'site', 'assets', 'img', 'email', 'email-header.svg')
    try:
        import base64
        with open(svg_path, 'rb') as f:
            return 'data:image/svg+xml;base64,' + base64.b64encode(f.read()).decode()
    except Exception:
        return ''


def _build_html(body_text, cta_url=None, cta_label=None):
    """Wrap plain text body in branded HTML template."""
    header_src = _load_header_b64()
    header_img = (
        f'<img src="{header_src}" width="600" alt="Human Design UA" '
        f'style="display:block;width:100%;max-width:600px;border:0;"/>'
        if header_src else
        '<div style="background:#1A1440;padding:40px 0;text-align:center;'
        'font-size:22px;letter-spacing:6px;color:#F0ECE8;font-family:Georgia,serif;">'
        '✦ HUMAN DESIGN UA</div>'
    )

    # Convert plain text to HTML paragraphs
    lines = body_text.replace('\xa0', ' ').strip().split('\n')
    html_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('━'):
            html_lines.append(
                '<hr style="border:none;border-top:1px solid #2A2060;margin:20px 0;"/>'
            )
        elif stripped.startswith('→'):
            # CTA line — already handled below if cta_url given
            pass
        elif stripped.startswith('✓'):
            html_lines.append(
                f'<p style="margin:6px 0;padding-left:8px;'
                f'color:#E8C55A;font-size:15px;">{stripped}</p>'
            )
        elif stripped.startswith('•'):
            html_lines.append(
                f'<p style="margin:4px 0 4px 16px;color:#A090C0;font-size:14px;">{stripped}</p>'
            )
        elif stripped == '':
            html_lines.append('<br/>')
        else:
            color = '#F0ECE8' if stripped else '#A090C0'
            html_lines.append(
                f'<p style="margin:6px 0;color:{color};font-size:15px;'
                f'line-height:1.6;">{stripped}</p>'
            )

    # CTA button
    cta_html = ''
    if cta_url:
        label = cta_label or 'Перейти →'
        cta_html = f'''
        <div style="text-align:center;margin:28px 0 16px;">
          <a href="{cta_url}"
             style="display:inline-block;background:linear-gradient(135deg,#D4A830,#E8C55A);
                    color:#0D0B1E;font-weight:700;font-size:16px;
                    padding:14px 36px;border-radius:8px;text-decoration:none;
                    letter-spacing:0.5px;">
            {label}
          </a>
        </div>'''

    body_html = '\n'.join(html_lines)

    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Human Design UA</title>
</head>
<body style="margin:0;padding:0;background:#0A0818;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#0A0818;padding:24px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;width:100%;">

        <!-- HEADER / LOGO -->
        <tr><td style="padding:0;">{header_img}</td></tr>

        <!-- BODY -->
        <tr><td style="background:#0D0B1E;padding:32px 40px 8px;">
          {body_html}
          {cta_html}
        </td></tr>

        <!-- FOOTER -->
        <tr><td style="background:#090718;padding:20px 40px;border-top:1px solid #1A1440;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="color:#4A3F6B;font-size:12px;line-height:1.6;">
                ✦ Human Design UA<br/>
                <a href="mailto:{GMAIL_USER}"
                   style="color:#6B5F80;text-decoration:none;">{GMAIL_USER}</a>
              </td>
              <td align="right" style="color:#4A3F6B;font-size:11px;">
                Персональний розрахунок<br/>Дизайну Людини
              </td>
            </tr>
          </table>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _extract_cta(body_text):
    """Pull the first → URL line out of plain text body."""
    for line in body_text.split('\n'):
        s = line.strip()
        if s.startswith('→') and ('http' in s or 'localhost' in s):
            # e.g. "→ ОТРИМАТИ ПОВНУ РОЗШИФРОВКУ ЗА 400 ГРН:\nhttp://..."
            pass
        if s.startswith('http://') or s.startswith('https://'):
            return s
    return None


def _send(to_email, subject, body):
    if not GMAIL_PASSWORD:
        print('❌ GMAIL_APP_PASSWORD not set')
        return False

    cta_url = _extract_cta(body)

    # Build HTML version
    html = _build_html(body, cta_url=cta_url)

    msg = MIMEMultipart('alternative')
    msg['From']     = f'Human Design UA <{GMAIL_USER}>'
    msg['To']       = to_email
    msg['Subject']  = Header(subject, 'utf-8')
    msg['Reply-To'] = GMAIL_USER

    # Plain text fallback
    msg.attach(MIMEText(body.replace('\xa0', ' '), 'plain', 'utf-8'))
    # HTML version (email clients prefer the last part)
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, local_hostname='localhost') as s:
            s.ehlo('localhost'); s.starttls(); s.ehlo('localhost')
            s.login(GMAIL_USER, GMAIL_PASSWORD)
            s.sendmail(GMAIL_USER, [to_email], msg.as_bytes(),
                       mail_options=['BODY=8BITMIME'])
        print(f'✉️  [{subject[:45]}] → {to_email}')
        return True
    except Exception as e:
        print(f'❌ Send error: {e}')
        return False


FUNNEL_STEPS = {
    'upsell_basic': [
        (_upsell_1, 'upsell_2'),
        (_upsell_2, 'upsell_3'),
        (_upsell_3, 'upsell_4'),
        (_upsell_4, None),
    ],
    'abandoned_payment': [
        (_abandoned_1, 'abandoned_2'),
        (_abandoned_2, 'abandoned_3'),
        (_abandoned_3, None),
    ],
}


def process_due_emails():
    """Check DB for emails due now and send them. Called every minute."""
    init_funnel_db()
    now  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    due = conn.execute("""
        SELECT * FROM email_funnel
        WHERE done=0 AND converted=0 AND next_send_at <= ?
        ORDER BY next_send_at ASC
    """, (now,)).fetchall()

    for row in due:
        row   = dict(row)
        ftype = row['funnel_type']
        step  = row['step']
        steps = FUNNEL_STEPS.get(ftype, [])

        if step >= len(steps):
            conn.execute("UPDATE email_funnel SET done=1 WHERE id=?", (row['id'],))
            conn.commit()
            continue

        content_fn, next_delay_key = steps[step]
        retry_url = _build_retry_url(row)
        locale    = row.get('locale') or 'ua'
        subject, body = content_fn(row['name'], retry_url, locale)

        ok      = _send(row['email'], subject, body)
        now_ts  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        next_step = step + 1

        if ok:
            if next_delay_key is None or next_step >= len(steps):
                conn.execute(
                    "UPDATE email_funnel SET step=?, done=1, last_sent_at=? WHERE id=?",
                    (next_step, now_ts, row['id'])
                )
            else:
                next_at = (datetime.now() + timedelta(minutes=DELAYS[next_delay_key]))\
                          .strftime('%Y-%m-%d %H:%M:%S')
                conn.execute(
                    "UPDATE email_funnel SET step=?, next_send_at=?, last_sent_at=? WHERE id=?",
                    (next_step, next_at, now_ts, row['id'])
                )
            conn.commit()

    conn.close()
    return len(due)


# ══════════════════════════════════════════════════════════════
# BACKGROUND SCHEDULER
# ══════════════════════════════════════════════════════════════

def start_scheduler(interval_seconds=60):
    import threading, time

    def _loop():
        print(f'📅 Email funnel scheduler started (every {interval_seconds}s)')
        while True:
            try:
                sent = process_due_emails()
                if sent:
                    print(f'📬 Funnel tick: {sent} email(s) sent')
            except Exception as e:
                print(f'⚠️  Funnel scheduler error: {e}')
            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


# ══════════════════════════════════════════════════════════════
# CLI — manual test:
#   python3 scripts/email_funnel.py --funnel upsell_basic --step 0 \
#       --email you@gmail.com --name Натали --locale ru
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--funnel', choices=['upsell_basic', 'abandoned_payment'], required=True)
    parser.add_argument('--email',  required=True)
    parser.add_argument('--name',   default='Натали')
    parser.add_argument('--plan',   default='basic')
    parser.add_argument('--locale', default='ru', choices=['ua', 'ru', 'en'])
    parser.add_argument('--step',   type=int, default=0)
    args = parser.parse_args()

    retry_url = f'{SITE_URL}/quiz.html?plan={args.plan}#pricing'
    steps     = FUNNEL_STEPS[args.funnel]
    content_fn, _ = steps[args.step]
    subject, body = content_fn(args.name, retry_url, args.locale)

    print(f'\n📧 {args.funnel} step {args.step} | locale={args.locale} → {args.email}')
    print(f'   Subject: {subject}\n')
    ok = _send(args.email, subject, body)
    print('Result:', '✅ sent' if ok else '❌ failed')
