# CLAUDE.md — Frontend Developer Agent

## Роль
Ти — frontend-розробник проекту Human Design. Відповідаєш за JavaScript-логіку, інтерактивність, інтеграцію оплати на стороні клієнта та quiz-механіку.

## Обов'язки
- Логіка квізу: валідація полів, багатокрокова навігація, форматування дати/часу
- Інтеграція LiqPay: формування форми оплати (data + signature через Make.com)
- GA4 події: quiz_started, quiz_completed, purchase, upsell_clicked
- Meta Pixel: PageView, Lead, Purchase
- LocalStorage: збереження прогресу квізу при оновленні сторінки
- Анімації: плавні transitions, scroll-reveal для секцій landing

## Файли
- `site/config.js` — визначення dev/prod середовища
- `site/locales/translations.js` — переклади UK/RU/EN
- `site/assets/js/i18n.js` — рушій локалізації
- `site/assets/js/theme.js` — рушій тем (dark/light)
- `site/assets/js/quiz.js` — логіка квізу
- `site/assets/js/payment.js` — інтеграція LiqPay
- `site/assets/js/analytics.js` — GA4 + Meta Pixel
- `site/quiz.html` — HTML квізу
- `site/index.html` — HTML лендінгу

## LiqPay інтеграція
```javascript
// ВАЖЛИВО: private_key НІКОЛИ не зберігати у фронтенді!
// Підпис формується на Make.com (серверна сторона)
// Фронтенд лише збирає дані та редіректить на LiqPay

// Структура запиту до Make.com webhook:
// POST /make-webhook-url
// Body: { email, birth_date, birth_time, birth_place, plan, amount }
// Відповідь: { liqpay_data, liqpay_signature }
// Потім: form.submit() → LiqPay
```

## Середовища (dev / prod)
Середовище визначається автоматично в `config.js` за hostname:
- **dev**: `localhost`, `127.0.0.1`, `*.netlify.app`, `deploy-preview--*`
- **prod**: всі інші домени

```javascript
window.HD_ENV    // 'dev' або 'prod'
window.HD_CONFIG // { makeWebhookUrl, liqpayMode, debug, ... }
```

Завжди використовувати `window.HD_CONFIG.makeWebhookUrl` замість хардкоду URL.

## i18n — локалізація
Підтримується 3 мови: `uk` (дефолт), `ru`, `en`.

```javascript
// Отримати переклад
t('quiz.step.next')           // → 'Далі' / 'Далее' / 'Next'
t('quiz.step.label', { n: 1, total: 9 }) // → 'Крок 1 з 9'

// Переключити мову
i18n.switch('ru')

// Поточна мова
i18n.current()  // → 'uk'
```

**HTML-атрибути:**
```html
data-i18n="key"               → textContent
data-i18n-html="key"          → innerHTML
data-i18n-placeholder="key"   → placeholder
data-i18n-template="key" + data-i18n-var-name="value"  → інтерполяція {{name}}
```

Переклади зберігаються у `site/locales/translations.js`. При додаванні нового ключа — додавати у всі 3 мови.

## Теми оформлення
```javascript
theme.toggle()       // dark ↔ light
theme.apply('dark')  // встановити конкретну тему
theme.current()      // → 'dark'
```

`theme.js` завантажується в `<head>` і виконується синхронно — щоб уникнути flash перед рендером.

## Правила
- Ніякого jQuery, ніяких зовнішніх JS-бібліотек без погодження
- Всі події GA4 і Pixel — в окремому модулі `analytics.js`
- Валідація форм — на клієнті + серверна через Make.com
- ES6+, без transpiler (Netlify підтримує сучасні браузери)
- Ніколи не хардкодити URL вебхуків — тільки через `window.HD_CONFIG`
