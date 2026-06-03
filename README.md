# Human Design UA — Платформа персональних розшифровок

Автоматизований продукт для продажу персоналізованих розшифровок Дизайну Людини на ринку України.

## Технологічний стек

| Компонент | Технологія |
|---|---|
| Frontend | HTML5 / CSS3 / Vanilla JS |
| Автоматизація | Make.com |
| AI-генерація | Claude API (claude-sonnet-4-6) |
| Оплата | LiqPay |
| Email | Brevo |
| БД | Supabase (PostgreSQL) |
| Хостинг | Netlify |

## Структура

```
human-design/
├── CLAUDE.md                ← Оркестратор агентів
├── agents/                  ← Агенти (manager, designer, dev, qa, copywriter)
├── site/                    ← Вихідний код сайту
│   ├── index.html           ← Landing page (8 блоків)
│   ├── quiz.html            ← Квіз (9 кроків + оплата)
│   ├── success.html         ← Сторінка після оплати
│   ├── upsell.html          ← Upsell пропозиція
│   ├── privacy.html         ← Політика конфіденційності
│   ├── terms.html           ← Публічна оферта
│   └── assets/
│       ├── css/main.css
│       └── js/{quiz,payment,analytics}.js
├── db/                      ← SQL схема та RLS
├── make/                    ← Make.com сценарії (опис)
└── prompts/                 ← Claude API промпти
```

## Швидкий старт

### 1. Деплой на Netlify
```bash
# Перетягни папку site/ на netlify.com/drop
# або підключи GitHub репозиторій
```

### 2. Supabase
1. Створи проект на [supabase.com](https://supabase.com)
2. Виконай `db/schema.sql` у SQL Editor
3. Виконай `db/rls-policies.sql`
4. Скопіюй `anon key` та `service role key`

### 3. LiqPay
1. Зареєструйся на [liqpay.ua](https://www.liqpay.ua)
2. Отримай Public Key та Private Key
3. Вкажи webhook URL: твій Make.com webhook

### 4. Make.com
1. Створи сценарій за `make/main-funnel.json`
2. Додай змінні: `ANTHROPIC_API_KEY`, `SUPABASE_SERVICE_KEY`, `LIQPAY_PRIVATE_KEY`
3. Вкажи URL webhook у `site/assets/js/payment.js` → `MAKE_WEBHOOK_URL`

### 5. Аналітика
- Заміни `GA4_ID` і `PIXEL_ID` у `site/assets/js/analytics.js`

## Тарифи

| Тариф | Ціна | Обсяг |
|---|---|---|
| Базовий | 399 грн | ~20 сторінок |
| Повний | 799 грн | ~50 сторінок |
| Upsell | +400 грн | базовий → повний |

## KPIs

- Конверсія: 2–4%
- CPA: 60–80 грн  
- ROAS: 6–12x
- Час доставки: < 10 хвилин
- Upsell конверсія: 15–25%
