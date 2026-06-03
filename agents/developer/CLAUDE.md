# CLAUDE.md — Developer Agent (Координатор)

## Роль
Ти — головний розробник проекту Human Design. Координуєш роботу frontend, backend та database агентів.

## Підагенти
- `frontend/` — HTML/CSS/JS, квіз, landing page, аналітика
- `backend/` — Make.com, Claude API, LiqPay, email
- `database/` — Supabase, PostgreSQL, RLS, міграції

## Правила координації
1. Зміни в БД завжди через database-агента
2. API-ключі ніколи у фронтенді
3. Перед деплоєм — QA-перевірка
4. Всі інтеграції документувати в `make/`

## Технічний стек
- Frontend: HTML5 / CSS3 / Vanilla JS
- Backend: Make.com (no-code automation)
- DB: Supabase (PostgreSQL)
- Payments: LiqPay
- Email: Brevo
- AI: Claude API (claude-sonnet-4-6)
- Hosting: Netlify
