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
- Мова: українська (всі тексти та розшифровки)

## Файлова структура
```
human-design/
├── CLAUDE.md                   ← Ти тут
├── README.md
├── agents/                     ← Усі агенти
├── site/                       ← Вихідний код сайту
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
