# Повна розшифровка — «Повна карта твоєї природи» (~50 сторінок)

> Реальна логіка генерації — у `netlify/functions/utils/claude.js` (6 API-викликів).
> Цей файл — документація: що входить у тариф і чому.

## Що обіцяє тариф

| # | Розділ | Що отримує клієнтка |
|---|--------|---------------------|
| 1 | Розшифровка бодиграфа | Персональна карта з 9 центрами, каналами, воротами |
| 2 | Тип та його особливості | Робота, розвиток, стосунки, сон, управління енергією |
| 3 | Авторитет | Конкретний спосіб приймати правильні рішення |
| 4 | Стратегія | Коли діяти, коли чекати — з прикладами з реального життя |
| 5 | Профіль | Природна роль, де легко, де нав'язані шаблони |
| 6 | 9 Центрів — 9 сфер | Де вона впливає на інших, де уразлива (всі 9) |
| 7 | Планети та вузли | Характер, доля, Сонце/Земля/Місяць/Вузли + особисті планети |
| 8 | Розбір каналів | Природні переваги — де та як їх використовувати |
| 9 | Автоматичні реакції | Що бачать інші, але вона не помічає — скриті козирі |
| 10 | Інкарнаційний хрест | Глобальний сенс її життя та внесок у світ |
| 11 | Самодостатність | Наскільки самодостатня, чи потрібні їй інші люди |
| 🎁 | **Бонус** при оплаті за 15 хв: | |
| — | Практики декондиціювання | 5 конкретних практик зі покроковими інструкціями |
| — | Особистий план на 90 днів | Тиждень 1–4 + Місяць 2–3 з конкретними завданнями |

## Структура генерації (6 частин)

### Part 1 — Вступ + Тип
Поля: `intro_text`, `type_aura`, `type_nature`, `type_strengths`, `type_challenges`,
`type_work`, `type_relationships`, `type_sleep`, `type_energy`, `type_shadow`

**Тон**: звернення до неї по імені, конкретні приклади з реального життя, аналогії
(«Ти як потужна електростанція...»), що зміниться коли вона почне жити своїм дизайном.

### Part 2 — Авторитет + Стратегія
Поля: `authority_nature`, `authority_recognition`, `authority_practice`, `authority_mistakes`,
`authority_decisions`, `strategy_explanation`, `strategy_examples`, `strategy_life_area`,
`signature`, `not_self`, `not_self_signs[]`

**Ключово**: авторитет вже розрахований — не «дізнайся», а «ось як він звучить у тебе».
Порівняння: «Сценарій 1 — слідуєш стратегії: [результат]. Сценарій 2 — ні: [результат]».

### Part 3 — Профіль
Поля: `profile_overview`, `profile_line1_name`, `profile_line1`, `profile_line2_name`,
`profile_line2`, `profile_interaction`, `profile_life_role`, `profile_relationships`,
`profile_career`, `profile_conditioning`, `profile_authentic`

**Мінімум** 150–200 слів на поле. Дві лінії: свідома + несвідома. Взаємодія.

### Part 4 — Усі 9 Центрів
Поля: `centers_intro`, `center_head`, `center_ajna`, `center_throat`, `center_g`,
`center_heart`, `center_sp`, `center_sacral`, `center_spleen`, `center_root`

Кожен центр — об'єкт: `{ title, description, gifts, shadow, practice }`

**Після генерації** центри маппяться у `reading.centers.head` тощо (пост-обробка у claude.js).

Визначений центр → стабільна сила що впливає на оточуючих.
Відкритий центр → місце навчання та кондиціювання.

### Part 5 — Канали + Планети/Вузли
Поля: `channels_intro`, `channels_detail[]` (масив об'єктів для КОЖНОГО активного каналу),
`planets_intro`, `planet_sun_p`, `planet_earth_p`, `planet_sun_d`, `planet_earth_d`,
`planet_moon`, `planet_nodes`, `planet_mercury`, `planet_venus`, `planet_mars`,
`planet_jupiter`, `planet_saturn`

Канал → об'єкт: `{ channel_id, channel_name, description, gifts, shadow, how_to_use }`

### Part 6 — Хрест + Просунуте + План
Поля: `incarnation_cross_intro`, `incarnation_cross_meaning`, `incarnation_cross_gates`,
`incarnation_cross_mission`, `auto_reactions`, `auto_examples[]`, `self_sufficiency`,
`self_resource`, `deconditioning_intro`, `deconditioning_practices[]`,
`plan_intro`, `plan_week1..4`, `plan_month2..3`, `recommendations[]`,
`life_theme`, `closing_message`

Практика → об'єкт: `{ title, description, steps[] }`

## Тон та стиль (обов'язково)

1. **Простою мовою** — кожне поняття з нуля, ніби людина вперше чує
2. **Конкретні приклади** — НЕ «ти маєш сильну волю», а «наприклад, коли всі кидають проект, ти доводиш до кінця навіть якщо важко»
3. **Що конкретно робити** — кожен розділ завершується практичним кроком
4. **Авторитет вже відомий** — ніколи не пиши «дізнайся свій авторитет»
5. **На «ти»** (жіночий рід), тепло, як найближча подруга
6. **Мінімум 3 абзаци** на кожне поле: (1) що це таке, (2) конкретно у неї, (3) що робити
