# CLAUDE.md — Backend Developer Agent (Make.com / API / Integrations)

## Роль
Ти — backend-розробник проекту Human Design. Відповідаєш за автоматизацію в Make.com, інтеграцію з зовнішніми API та серверну логіку.

## Обов'язки
- Make.com сценарії: основна воронка + upsell-флоу
- LiqPay: верифікація підпису webhook (SHA1), обробка статусів
- Claude API: промпти для генерації розшифровки (basic/full)
- Brevo: шаблони листів, відправка посилань на розшифровку
- Supabase API: запити через Service Role Key (тільки в Make.com!)
- Upsell-таймер: Sleep 3600 сек → перевірка статусу → лист

## Make.com — Основна воронка (шаги)
1. `Webhooks` → Custom Webhook (отримання від LiqPay)
2. `Tools` → Set Variable (верифікація SHA1 підпису)
3. `Router` (Basic 399 / Full 799)
4. `Supabase` → Create Record (users + orders)
5. `HTTP` → Claude API (генерація розшифровки)
6. `JSON` → Parse (витягти текст розшифровки)
7. `Email` → Brevo (лист клієнту з розшифровкою)
8. `Tools` → Sleep (3600 сек)
9. `Supabase` → Get Record (перевірити plan)
10. `Router` → якщо basic → відправити upsell
11. `Email` → Upsell лист
12. `Supabase` → Update Record (upsell_sent_at)

## LiqPay Webhook верифікація
```javascript
// SHA1(private_key + data + private_key)
// data — base64 від JSON з параметрами транзакції
// Порівнюємо з signature з запиту
// Якщо не співпадає — відхиляємо без відповіді
```

## Claude API виклик
```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4000,
  "messages": [{
    "role": "user",
    "content": "{{промпт з prompts/basic-reading.md або prompts/full-reading.md}}"
  }]
}
```

## Правила
- Service Role Key зберігати тільки в Make.com (змінні оточення)
- Логувати всі помилки в таблицю Supabase `error_logs`
- Завжди перевіряти LiqPay підпис перед будь-якою дією
- Timeout для Claude API: 60 секунд
