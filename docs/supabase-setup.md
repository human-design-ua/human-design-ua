# Налаштування Supabase — Human Design UA

> Повний покроковий гайд. Час: ~30 хвилин.

---

## Крок 1 — Створити проект

1. Зайди на [supabase.com](https://supabase.com) → **Start your project**
2. **Organization** → Create new → назви `human-design-ua`
3. **New project**:
   - Name: `human-design-ua`
   - Database Password: згенеруй надійний (збережи в 1Password / Notion!)
   - Region: `West EU (Ireland)` — найближче до UA
4. Жди ~2 хвилини поки проект створюється

---

## Крок 2 — Запустити схему бази даних

### 2.1 Основна схема

1. Зайди: **SQL Editor** (іконка `<>` зліва)
2. Натисни **New query**
3. Скопіюй весь вміст файлу `db/schema.sql`
4. Натисни **Run** (Ctrl+Enter)
5. Перевір — має з'явитись:
   ```
   ✓ users created
   ✓ orders created  
   ✓ upsell_events created
   ✓ error_logs created
   ```

### 2.2 RLS Policies (безпека)

1. **New query**
2. Скопіюй вміст `db/rls-policies.sql`
3. **Run**

### 2.3 Quiz sessions + аналітика

1. **New query**
2. Скопіюй вміст `db/migrations/002_quiz_sessions_and_views.sql`
3. **Run**

### 2.4 Перевірка

Виконай у SQL Editor:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
```

Має бути 5 таблиць:
- `error_logs`
- `orders`
- `quiz_sessions`
- `upsell_events`
- `users`

---

## Крок 3 — Отримати ключі доступу

1. **Settings** → **API**
2. Скопіюй та збережи:

```
Project URL:    https://ТВІЙ_ID.supabase.co
anon (public):  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  (довгий ключ)
service_role:   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  (СЕКРЕТНИЙ!)
```

> ⚠️ `service_role` — НІКОЛИ не публікуй у фронтенді! Тільки в Make.com та сервері.

---

## Крок 4 — Підключити до сайту

Відкрий `site/config.js` і замість REPLACE встав реальні ключі:

```javascript
// DEV
supabaseUrl:    'https://ТВІЙ_ID.supabase.co',
supabaseAnonKey:'eyJhbGciO...',  // anon key

// PROD (той самий проект або окремий)
supabaseUrl:    'https://ТВІЙ_ID.supabase.co',
supabaseAnonKey:'eyJhbGciO...',
```

---

## Крок 5 — Підключити до Make.com

У Make.com при створенні Supabase модуля:
- **URL**: `https://ТВІЙ_ID.supabase.co`
- **API Key**: `service_role` ключ (НЕ anon!)

---

## Таблиці — що де зберігається

```
quiz_sessions  ← Кожен хто ПОЧАВ квіз (навіть без оплати)
               ← Використовується для ретаргетингу
               
users          ← Кожен хто ОПЛАТИВ
               ← Містить дані народження + розшифровку
               
orders         ← Кожна транзакція LiqPay
               ← Статус: pending → success / failed
               
upsell_events  ← Відстеження апсейл воронки
               ← Коли надіслано, відкрито, конвертовано
               
error_logs     ← Помилки Make.com / Claude API / LiqPay
               ← Для дебагу і моніторингу
```

---

## Корисні SQL запити для дашборду

```sql
-- Замовлення за сьогодні
SELECT * FROM v_orders_dashboard
WHERE DATE(created_at) = CURRENT_DATE;

-- Доход за 30 днів
SELECT * FROM get_revenue_summary();

-- Воронка за тиждень
SELECT * FROM v_funnel_stats
WHERE day >= CURRENT_DATE - 7;

-- Скільки людей кинули квіз на якому кроці
SELECT step_reached, COUNT(*) 
FROM quiz_sessions 
WHERE converted = false
GROUP BY step_reached 
ORDER BY step_reached;

-- Топ UTM джерела
SELECT utm_source, utm_campaign, 
       COUNT(*) as sessions,
       COUNT(*) FILTER (WHERE converted) as paid,
       SUM(u.amount_paid) as revenue
FROM quiz_sessions qs
LEFT JOIN users u ON u.email = qs.email
GROUP BY utm_source, utm_campaign
ORDER BY paid DESC;
```

---

## Наступний крок

Після налаштування Supabase → **підключити LiqPay** (отримати production ключі на кабінеті ФОП).

---

*Дата: 2026-06-04 | Supabase версія: v2*
