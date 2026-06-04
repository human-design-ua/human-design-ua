"""
Human Design UA — Local SQLite database for DEV
Mirrors production Supabase schema locally.
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'dev.db')


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            email         TEXT NOT NULL,
            name          TEXT,
            created_at    TEXT DEFAULT (datetime('now')),
            plan          TEXT CHECK(plan IN ('basic','full')),
            status        TEXT DEFAULT 'paid',
            birth_date    TEXT,
            birth_time    TEXT,
            birth_place   TEXT,
            life_area     TEXT,
            challenge     TEXT,
            hd_type       TEXT,
            hd_authority  TEXT,
            hd_profile    TEXT,
            reading_text  TEXT,
            reading_generated_at TEXT,
            liqpay_order_id TEXT,
            amount_paid   REAL,
            paid_at       TEXT,
            upsell_sent_at TEXT,
            upsell_converted INTEGER DEFAULT 0,
            utm_source    TEXT,
            utm_campaign  TEXT,
            locale        TEXT DEFAULT 'ua',
            env           TEXT DEFAULT 'dev'
        );

        CREATE TABLE IF NOT EXISTS orders (
            id              TEXT PRIMARY KEY,
            user_id         TEXT REFERENCES users(id),
            created_at      TEXT DEFAULT (datetime('now')),
            plan            TEXT,
            amount          REAL,
            currency        TEXT DEFAULT 'UAH',
            payment_status  TEXT DEFAULT 'success',
            provider_order_id TEXT,
            email_sent_at   TEXT
        );
    """)
    conn.commit()
    conn.close()


def save_order(order_data: dict) -> str:
    import uuid
    conn = get_conn()

    user_id  = str(uuid.uuid4())
    order_id = str(uuid.uuid4())
    now      = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn.execute("""
        INSERT OR REPLACE INTO users
        (id, email, name, plan, status, birth_date, birth_time, birth_place,
         life_area, challenge, liqpay_order_id, amount_paid, paid_at,
         utm_source, utm_campaign, locale, env)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id,
        order_data.get('email', ''),
        order_data.get('name', ''),
        order_data.get('plan', 'basic'),
        'paid',
        order_data.get('birth_date', ''),
        order_data.get('birth_time', ''),
        order_data.get('birth_place', ''),
        order_data.get('life_area', ''),
        order_data.get('challenge', ''),
        order_data.get('order_id', ''),
        float(order_data.get('amount', 399)),
        order_data.get('paid_at', now),
        order_data.get('utm_source', ''),
        order_data.get('utm_campaign', ''),
        order_data.get('locale', 'ua'),
        order_data.get('env', 'dev'),
    ))

    conn.execute("""
        INSERT INTO orders
        (id, user_id, plan, amount, payment_status, provider_order_id, email_sent_at)
        VALUES (?,?,?,?,?,?,?)
    """, (
        order_id, user_id,
        order_data.get('plan', 'basic'),
        float(order_data.get('amount', 399)),
        'success',
        order_data.get('order_id', ''),
        now,
    ))

    conn.commit()
    conn.close()
    print(f'💾 Saved to DB: {user_id[:8]}… | {order_data.get("email")} | {order_data.get("plan")}')
    return user_id


def get_orders(limit=100):
    conn = get_conn()
    rows = conn.execute("""
        SELECT u.*, o.id as order_db_id, o.payment_status, o.email_sent_at
        FROM users u
        LEFT JOIN orders o ON o.user_id = u.id
        ORDER BY u.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_conn()
    stats = conn.execute("""
        SELECT
            COUNT(*)                              AS total_orders,
            SUM(amount_paid)                      AS revenue,
            COUNT(CASE WHEN plan='basic' THEN 1 END) AS basic_count,
            COUNT(CASE WHEN plan='full'  THEN 1 END) AS full_count,
            COUNT(CASE WHEN upsell_converted=1 THEN 1 END) AS upsells,
            AVG(amount_paid)                      AS avg_order
        FROM users
    """).fetchone()
    conn.close()
    return dict(stats)


def seed_test_data():
    """Insert realistic test orders."""
    import uuid
    conn = get_conn()

    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        print(f'ℹ️  DB already has {existing} records — skipping seed')
        conn.close()
        return

    test_orders = [
        ('olena.kovalenko@gmail.com',  'Олена Коваленко',  'full',  799, '1990-05-15', '14:30', 'Київ, Україна',    'career',        'decisions', 'ua', '2026-05-28 10:12:00'),
        ('maria.savchenko@gmail.com',  'Марія Савченко',   'basic', 399, '1995-11-22', '08:00', 'Львів, Україна',   'relationships', 'fatigue',   'ua', '2026-05-29 14:45:00'),
        ('oksana.petrenko@ukr.net',    'Оксана Петренко',  'full',  799, '1988-03-07', '22:15', 'Одеса, Україна',   'self',          'purpose',   'ua', '2026-05-30 09:20:00'),
        ('anna.ivanova@mail.ru',       'Анна Іванова',     'basic', 399, '1993-08-14', '',      'Харків, Україна',  'energy',        'people',    'ru', '2026-05-31 16:33:00'),
        ('tetyana.bondar@gmail.com',   'Тетяна Бондар',    'full',  799, '1985-12-01', '06:45', 'Дніпро, Україна',  'career',        'fatigue',   'ua', '2026-06-01 11:05:00'),
        ('natalia.lysenko@gmail.com',  'Наталія Лисенко',  'basic', 399, '1997-04-19', '11:00', 'Запоріжжя, Україна','self',         'decisions', 'ua', '2026-06-01 18:22:00'),
        ('iryna.melnyk@gmail.com',     'Ірина Мельник',    'full',  799, '1991-09-30', '03:20', 'Вінниця, Україна', 'relationships', 'purpose',   'ua', '2026-06-02 08:47:00'),
        ('svitlana.kravchuk@ukr.net',  'Світлана Кравчук', 'basic', 399, '1986-06-25', '19:50', 'Полтава, Україна', 'energy',        'people',    'ua', '2026-06-02 21:10:00'),
        ('elena.sorokina@gmail.com',   'Елена Сорокина',   'full',  799, '1994-02-11', '07:30', 'Київ, Україна',    'career',        'fatigue',   'ru', '2026-06-03 13:15:00'),
        ('yulia.tkachenko@gmail.com',  'Юлія Ткаченко',    'basic', 399, '1999-07-08', '15:45', 'Маріуполь, Україна','self',         'decisions', 'ua', '2026-06-04 07:55:00'),
    ]

    hd_types = ['Генератор','Маніфестуючий Генератор','Проектор','Маніфестор','Рефлектор']
    hd_auths = ['Сакральний','Емоційний','Селезінковий','Его-Маніфестований']
    hd_profiles = ['1/3','2/4','3/5','4/6','5/1','6/2']

    import random
    random.seed(42)

    for i, (email, name, plan, amount, bd, bt, bp, la, ch, locale, paid_at) in enumerate(test_orders):
        uid = str(uuid.uuid4())
        oid = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO users
            (id, email, name, plan, status, birth_date, birth_time, birth_place,
             life_area, challenge, hd_type, hd_authority, hd_profile,
             liqpay_order_id, amount_paid, paid_at, locale, env, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            uid, email, name, plan, 'paid', bd, bt, bp, la, ch,
            random.choice(hd_types), random.choice(hd_auths), random.choice(hd_profiles),
            f'HD-TEST-{1000+i}', float(amount), paid_at, locale, 'dev', paid_at
        ))
        conn.execute("""
            INSERT INTO orders (id, user_id, plan, amount, payment_status,
                                provider_order_id, email_sent_at, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (oid, uid, plan, float(amount), 'success', f'HD-TEST-{1000+i}', paid_at, paid_at))

    conn.commit()
    conn.close()
    print(f'✅ Seeded {len(test_orders)} test orders into dev.db')


if __name__ == '__main__':
    init_db()
    seed_test_data()
    print('\n📊 Stats:', get_stats())
    print(f'📋 Orders: {len(get_orders())} records')
