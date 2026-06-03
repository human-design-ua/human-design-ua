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

## Ключові системи фронтенду

### Середовища (dev / prod)
`site/config.js` — runtime-визначення середовища за hostname. Не потребує build-кроку.
- dev: localhost / netlify.app / deploy-preview → LiqPay sandbox
- prod: всі інші домени → LiqPay production

### Локалізація (i18n)
`site/locales/translations.js` + `site/assets/js/i18n.js`
- Мови: `uk` (дефолт), `ru`, `en`
- Механізм: `data-i18n`-атрибути на HTML-елементах, рушій `window.i18n`
- Переклади — тільки у `translations.js`, не вбудовувати в HTML

### Теми оформлення
`site/assets/js/theme.js` + CSS-змінні в `main.css`
- Теми: `dark` (дефолт), `light`; розширювати через `THEMES` в `theme.js`
- `theme.js` виконується в `<head>` синхронно — запобігає flash при завантаженні
