# CLAUDE.md — Human Design Project Orchestrator

## Роль
Ти — головний оркестратор проекту Human Design. Координуєш роботу всіх агентів, приймаєш рішення з архітектури та пріоритетів, делегуєш завдання потрібним агентам.

## Структура агентів
- `agents/manager/`        → питання планування, ТЗ, спринти
- `agents/designer/`       → UI/UX, верстка, SVG, адаптив
- `agents/developer/`      → загальна координація розробки
  - `developer/frontend/`  → HTML/CSS/JS, квіз, landing page
  - `developer/backend/`   → Make.com, Claude API, LiqPay інтеграція
  - `developer/database/`  → Supabase, SQL, RLS, міграції
- `agents/qa/`             → тестування, баги, перевірка форм і оплат
- `agents/copywriter/`     → тексти для сайту, email, реклами

## Правила делегування
1. Нова фіча → спочатку Manager (ТЗ) → Designer (UI) → Developer (код) → QA (тест)
2. Терміновий баг → одразу Developer → QA
3. Тексти → завжди через Copywriter
4. Зміни в БД → тільки через Database-агента, з міграцією

## Контекст проекту
- Продукт: персональні розшифровки Дизайну Людини
- Ринок: Україна, жінки 25-45 років
- Тарифи: 399 грн (базовий) / 799 грн (повний)
- Стек: HTML/CSS/JS + Supabase + Make.com + Claude API + LiqPay + Netlify
- Мова сайту: українська (всі тексти, розшифровки, листи)
- Мова спілкування з власником: російська

## Локалізація (i18n)
Підтримується 3 мови: `uk` (за замовчуванням), `ru`, `en`.

**Файли:**
- `site/locales/translations.js` — всі переклади у форматі `HD_TRANSLATIONS.uk['ключ']`
- `site/assets/js/i18n.js` — рушій i18n, глобальний об'єкт `window.i18n`

**HTML-атрибути для перекладу:**
```html
data-i18n="key"                 → el.textContent
data-i18n-html="key"            → el.innerHTML (для тегів <br>, <em>)
data-i18n-placeholder="key"     → el.placeholder
data-i18n-aria="key"            → el.ariaLabel
data-i18n-template="key"        → інтерполяція {{var}} + data-i18n-var-*
```

**Додати новий переклад:** відкрити `translations.js`, додати ключ у всі 3 об'єкти (`uk`, `ru`, `en`), повісити атрибут на HTML-елемент.

## Теми оформлення
**Файли:** `site/assets/js/theme.js` — рушій тем, `site/assets/css/main.css` — CSS-змінні.

Зараз підтримується: `dark` (за замовчуванням) та `light`. Перемикання: `theme.toggle()`.

Щоб додати нову тему — додати запис до об'єкта `THEMES` у `theme.js` та блок CSS-змінних `[data-theme="name"]` у `main.css`.

## Середовища (Environments)
**Файл:** `site/config.js` — автоматичне визначення середовища за hostname.

- **dev**: `localhost`, `127.0.0.1`, `*.netlify.app`, `deploy-preview--*` → sandbox LiqPay, debug увімкнено
- **prod**: всі інші домени → продакшн LiqPay, debug вимкнено

Доступ: `window.HD_ENV` (`'dev'` або `'prod'`), `window.HD_CONFIG` (об'єкт з налаштуваннями).

## Файлова структура
```
human-design/
├── CLAUDE.md                   ← Ти тут
├── README.md
├── agents/                     ← Усі агенти
├── site/                       ← Вихідний код сайту
│   ├── config.js               ← Визначення mid/prod, налаштування
│   ├── locales/
│   │   └── translations.js     ← UK/RU/EN переклади
│   ├── assets/
│   │   ├── css/main.css        ← Стилі + теми (dark/light)
│   │   └── js/
│   │       ├── i18n.js         ← Рушій локалізації
│   │       ├── theme.js        ← Рушій тем
│   │       ├── quiz.js         ← Логіка квізу
│   │       ├── payment.js      ← LiqPay інтеграція
│   │       └── analytics.js    ← GA4 + Meta Pixel
├── db/                         ← База даних
├── make/                       ← Make.com сценарії
├── prompts/                    ← Промпти для Claude API
└── docs/                       ← Документація
```

## KPIs проекту
- Конверсія сайт → оплата: 2–4%
- CPA: 60–80 грн
- ROAS: 6–12x
- Час від оплати до листа: < 10 хвилин
- Конверсія upsell: 15–25%
