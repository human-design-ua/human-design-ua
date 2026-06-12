// Email via Gmail SMTP — nodemailer
// Supports 3 locales: uk (Ukrainian), ru (Russian), en (English)
const nodemailer = require('nodemailer');
const { generateReadingPDF } = require('./pdf');

const GMAIL_USER = process.env.GMAIL_USER || 'humandesign.finance@gmail.com';
const GMAIL_PASS = (process.env.GMAIL_APP_PASSWORD || '').replace(/\s/g, '');
const SITE_URL   = process.env.SITE_URL || 'https://human-design-ua.netlify.app';

// ── Normalise locale ──────────────────────────────────────────
function normLang(locale) {
  if (!locale) return 'uk';
  const l = String(locale).toLowerCase().slice(0, 2);
  if (l === 'ru') return 'ru';
  if (l === 'en') return 'en';
  return 'uk'; // ua / uk → uk
}

// ── i18n strings ──────────────────────────────────────────────
const T = {
  uk: {
    planFull:  'Повна розшифровка',
    planBasic: 'Базова розшифровка',
    // Receipt email
    receiptTitle:   'Оплату отримано ✦',
    receiptSubject: (id) => `✦ Замовлення ${id} — оплату прийнято`,
    receiptBody:    (name) => name
      ? `${name}, вашу оплату успішно прийнято.`
      : 'Вашу оплату успішно прийнято.',
    receiptSub:     'Розшифровка вже генерується і надійде на цей email протягом <strong style="color:#D4A830;">5–10 хвилин</strong>.',
    orderNum:   'Номер замовлення',
    service:    'Послуга',
    amount:     'Сума',
    // Reading email
    readySubject: (name) => `✦ ${name ? name + ', т' : 'Т'}воя розшифровка Дизайну Людини готова`,
    readyHeader:  (name) => `✦ ${name || ''}, твій Дизайн готовий`,
    readyPlan:    (plan) => plan === 'full' ? 'Повна розшифровка' : 'Базова розшифровка',
    readyBody1: 'Вітаємо з придбанням персональної розшифровки Дизайну Людини!',
    readyBody2: 'Ці знання вже змінили життя більш ніж 2&nbsp;000 наших клієнток. Тепер твоя черга відкрити свою справжню природу — розшифровка складена виключно для тебе, на основі точної дати, часу та місця народження.',
    readyBody3: 'Твоя розшифровка додана до цього листа у форматі <strong style="color:#D4A830;">PDF</strong>.',
    readyBody4: 'Відкрий PDF, заваривши чашку чаю — і дозволь собі побути з цими знаннями. 🌿',
    pdfNote:    (plan) => plan === 'full' ? '~50 сторінок' : '~20 сторінок',
    signoff:    'З теплом і повагою до твого унікального Дизайну,',
    // Upsell
    upsellBadge: 'Спеціальна пропозиція',
    upsellText:  'Хочеш отримати повну картину? Повна розшифровка містить детальний розбір 9 центрів, планет, каналів та інкарнаційного хреста.',
    upsellBtn:   'Отримати повну версію за +400 грн →',
    // Failed
    failedSubject: 'Оплата не пройшла — спробуйте ще раз',
    failedTitle:   'Оплата не пройшла',
    failedBody:    (name) => `${name ? name + ', на' : 'На'} жаль, оплата не пройшла. Можливі причини:`,
    failedReasons: ['Недостатньо коштів на картці', 'Картка заблокована для онлайн-платежів', 'Технічна помилка банку'],
    failedBtn:     'Спробувати ще раз →',
    footerPrivacy: 'Конфіденційність',
  },
  ru: {
    planFull:  'Полная расшифровка',
    planBasic: 'Базовая расшифровка',
    receiptTitle:   'Оплата получена ✦',
    receiptSubject: (id) => `✦ Заказ ${id} — оплата принята`,
    receiptBody:    (name) => name
      ? `${name}, ваш платёж успешно принят.`
      : 'Ваш платёж успешно принят.',
    receiptSub:     'Расшифровка уже генерируется и поступит на этот email в течение <strong style="color:#D4A830;">5–10 минут</strong>.',
    orderNum:   'Номер заказа',
    service:    'Услуга',
    amount:     'Сумма',
    readySubject: (name) => `✦ ${name ? name + ', т' : 'Т'}воя расшифровка Дизайна Человека готова`,
    readyHeader:  (name) => `✦ ${name || ''}, твой Дизайн готов`,
    readyPlan:    (plan) => plan === 'full' ? 'Полная расшифровка' : 'Базовая расшифровка',
    readyBody1: 'Поздравляем с приобретением персональной расшифровки Дизайна Человека!',
    readyBody2: 'Эти знания уже изменили жизнь более 2&nbsp;000 наших клиенток. Теперь твоя очередь открыть свою истинную природу — расшифровка составлена исключительно для тебя, на основе точной даты, времени и места рождения.',
    readyBody3: 'Твоя расшифровка прикреплена к этому письму в формате <strong style="color:#D4A830;">PDF</strong>.',
    readyBody4: 'Открой PDF, заварив чашку чая — и позволь себе побыть с этими знаниями. 🌿',
    pdfNote:    (plan) => plan === 'full' ? '~50 страниц' : '~20 страниц',
    signoff:    'С теплом и уважением к твоему уникальному Дизайну,',
    upsellBadge: 'Специальное предложение',
    upsellText:  'Хочешь получить полную картину? Полная расшифровка содержит детальный разбор 9 центров, планет, каналов и инкарнационного креста.',
    upsellBtn:   'Получить полную версию за +400 грн →',
    failedSubject: 'Оплата не прошла — попробуйте ещё раз',
    failedTitle:   'Оплата не прошла',
    failedBody:    (name) => `${name ? name + ', к' : 'К'} сожалению, оплата не прошла. Возможные причины:`,
    failedReasons: ['Недостаточно средств на карте', 'Карта заблокирована для онлайн-платежей', 'Техническая ошибка банка'],
    failedBtn:     'Попробовать ещё раз →',
    footerPrivacy: 'Конфиденциальность',
  },
  en: {
    planFull:  'Full reading',
    planBasic: 'Basic reading',
    receiptTitle:   'Payment received ✦',
    receiptSubject: (id) => `✦ Order ${id} — payment confirmed`,
    receiptBody:    (name) => name
      ? `${name}, your payment has been successfully accepted.`
      : 'Your payment has been successfully accepted.',
    receiptSub:     'Your reading is being generated and will arrive in this email within <strong style="color:#D4A830;">5–10 minutes</strong>.',
    orderNum:   'Order number',
    service:    'Service',
    amount:     'Amount',
    readySubject: (name) => `✦ ${name ? name + ', y' : 'Y'}our Human Design reading is ready`,
    readyHeader:  (name) => `✦ ${name || ''}, your Design is ready`,
    readyPlan:    (plan) => plan === 'full' ? 'Full reading' : 'Basic reading',
    readyBody1: 'Congratulations on getting your personal Human Design reading!',
    readyBody2: 'This knowledge has already changed the lives of more than 2&nbsp;000 of our clients. Now it\'s your turn to discover your true nature — this reading was created exclusively for you, based on your exact date, time and place of birth.',
    readyBody3: 'Your reading is attached to this email as a <strong style="color:#D4A830;">PDF</strong>.',
    readyBody4: 'Open the PDF, brew a cup of tea — and allow yourself to sit with this knowledge. 🌿',
    pdfNote:    (plan) => plan === 'full' ? '~50 pages' : '~20 pages',
    signoff:    'With warmth and respect for your unique Design,',
    upsellBadge: 'Special offer',
    upsellText:  'Want the full picture? The full reading includes a detailed analysis of all 9 centers, planets, channels and incarnation cross.',
    upsellBtn:   'Get the full version for +400 UAH →',
    failedSubject: 'Payment failed — please try again',
    failedTitle:   'Payment failed',
    failedBody:    (name) => `${name ? name + ', u' : 'U'}nfortunately, your payment did not go through. Possible reasons:`,
    failedReasons: ['Insufficient funds on the card', 'Card blocked for online payments', 'Bank technical error'],
    failedBtn:     'Try again →',
    footerPrivacy: 'Privacy',
  },
};

// ── Email base HTML wrapper ───────────────────────────────────
function emailWrap(body) {
  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0D0B1E;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0D0B1E;padding:40px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        ${body}
        <tr><td style="text-align:center;padding:24px 0;">
          <p style="color:#3D3560;font-size:12px;margin:0;font-family:Arial,sans-serif;">
            © ${new Date().getFullYear()} Human Design UA
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

function createTransport() {
  return nodemailer.createTransport({
    host: 'smtp.gmail.com', port: 587, secure: false,
    auth: { user: GMAIL_USER, pass: GMAIL_PASS },
  });
}

// ── 1. Receipt email (immediately after payment) ──────────────
async function sendReceiptEmail(order) {
  const { order_id, email, name, plan, amount, locale } = order;
  const lang = normLang(locale);
  const t = T[lang];
  const planName = plan === 'full' ? t.planFull : t.planBasic;

  const html = emailWrap(`
    <tr><td style="background:#1A1440;border-radius:16px 16px 0 0;padding:32px 40px;text-align:center;border-bottom:1px solid #2D2560;">
      <div style="font-size:11px;letter-spacing:3px;color:#D4A830;text-transform:uppercase;font-family:Arial,sans-serif;">Human Design UA</div>
      <div style="font-size:28px;color:#F0ECE8;margin-top:8px;font-weight:400;">${t.receiptTitle}</div>
    </td></tr>
    <tr><td style="background:#120F2D;padding:40px;border-radius:0 0 16px 16px;">
      <p style="color:#F0ECE8;font-size:17px;line-height:1.8;margin:0 0 8px;">${t.receiptBody(name)}</p>
      <p style="color:#D8D0E8;font-size:15px;line-height:1.7;margin:0 0 28px;">${t.receiptSub}</p>
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#1A1440;border-radius:12px;padding:24px;margin-bottom:32px;">
        <tr><td style="padding:10px 0;border-bottom:1px solid #2D2560;">
          <span style="color:#8B7FAA;font-size:13px;font-family:Arial,sans-serif;">${t.orderNum}</span><br>
          <span style="color:#F0ECE8;font-size:15px;">${order_id}</span>
        </td></tr>
        <tr><td style="padding:10px 0;border-bottom:1px solid #2D2560;">
          <span style="color:#8B7FAA;font-size:13px;font-family:Arial,sans-serif;">${t.service}</span><br>
          <span style="color:#F0ECE8;font-size:15px;">${planName}</span>
        </td></tr>
        <tr><td style="padding:10px 0;">
          <span style="color:#8B7FAA;font-size:13px;font-family:Arial,sans-serif;">${t.amount}</span><br>
          <span style="color:#D4A830;font-size:22px;font-weight:bold;">${amount} грн</span>
        </td></tr>
      </table>
      <p style="color:#8B7FAA;font-size:14px;line-height:1.6;margin:0;font-family:Arial,sans-serif;">
        ${t.signoff}<br>
        <strong style="color:#F0ECE8;">Human Design UA</strong><br>
        <a href="mailto:${GMAIL_USER}" style="color:#D4A830;">${GMAIL_USER}</a>
      </p>
    </td></tr>`);

  await createTransport().sendMail({
    from: `"Human Design UA" <${GMAIL_USER}>`,
    to: email,
    subject: t.receiptSubject(order_id),
    html,
  });
}

// ── 2. Reading email (with PDF attachment) ────────────────────
async function sendReadingEmail(order, reading) {
  const { email, name, plan, locale } = order;
  const lang = normLang(locale);
  const t = T[lang];

  // Upsell block (basic only)
  const upsellBlock = plan === 'basic' ? `
    <tr><td style="padding:8px 40px 32px;">
      <table width="100%" cellpadding="0" cellspacing="0"
        style="background:#1A1440;border:1px solid #D4A830;border-radius:12px;padding:28px;">
        <tr><td>
          <div style="font-size:11px;letter-spacing:2px;color:#D4A830;text-transform:uppercase;
                      font-family:Arial,sans-serif;margin-bottom:10px;">${t.upsellBadge}</div>
          <p style="color:#F0ECE8;font-size:16px;margin:0 0 18px;line-height:1.6;">${t.upsellText}</p>
          <a href="${SITE_URL}/upsell.html"
             style="display:inline-block;background:#D4A830;color:#0D0B1E;font-weight:700;
                    font-size:15px;padding:14px 32px;border-radius:8px;text-decoration:none;
                    font-family:Arial,sans-serif;">${t.upsellBtn}</a>
        </td></tr>
      </table>
    </td></tr>` : '';

  const html = emailWrap(`
    <tr><td style="background:#1A1440;border-radius:16px 16px 0 0;padding:32px 40px;
                   text-align:center;border-bottom:1px solid #2D2560;">
      <div style="font-size:11px;letter-spacing:3px;color:#D4A830;text-transform:uppercase;
                  font-family:Arial,sans-serif;">Human Design UA</div>
      <div style="font-size:28px;color:#F0ECE8;margin-top:8px;font-weight:400;">
        ${t.readyHeader(name)}
      </div>
      <div style="font-size:13px;color:#8B7FAA;margin-top:8px;font-family:Arial,sans-serif;">
        ${t.readyPlan(plan)}
      </div>
    </td></tr>

    <tr><td style="background:#120F2D;padding:40px 40px 32px;">
      <p style="color:#F0ECE8;font-size:18px;font-weight:600;margin:0 0 18px;line-height:1.5;">
        ${t.readyBody1}
      </p>
      <p style="color:#D8D0E8;font-size:16px;line-height:1.85;margin:0 0 18px;">
        ${t.readyBody2}
      </p>
      <p style="color:#F0ECE8;font-size:16px;line-height:1.85;margin:0 0 12px;">
        ${t.readyBody3}
      </p>
      <p style="color:#D8D0E8;font-size:16px;line-height:1.85;margin:0 0 28px;">
        ${t.readyBody4}
      </p>

      <!-- PDF badge -->
      <table cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
        <tr>
          <td style="background:#1A1440;border:1px solid #4B3F8A;border-radius:10px;
                     padding:16px 24px;text-align:center;">
            <div style="font-size:28px;margin-bottom:6px;">📎</div>
            <div style="color:#D4A830;font-size:14px;font-weight:700;font-family:Arial,sans-serif;">
              PDF · ${t.pdfNote(plan)}
            </div>
            <div style="color:#8B7FAA;font-size:12px;font-family:Arial,sans-serif;margin-top:4px;">
              ${t.readyPlan(plan)} — ${name || ''}
            </div>
          </td>
        </tr>
      </table>

      <p style="color:#8B7FAA;font-size:14px;line-height:1.6;margin:0;font-family:Arial,sans-serif;">
        ${t.signoff}<br>
        <strong style="color:#F0ECE8;">Human Design UA</strong><br>
        <a href="mailto:${GMAIL_USER}" style="color:#D4A830;">${GMAIL_USER}</a>
      </p>
    </td></tr>

    ${upsellBlock}`);

  // Generate PDF
  let pdfBuffer;
  try {
    pdfBuffer = await generateReadingPDF(order, reading);
    console.log('PDF generated, size:', pdfBuffer.length, 'bytes');
  } catch(err) {
    console.error('PDF generation failed:', err.message);
  }

  const planLabel = plan === 'full' ? 'rozshyfrovka_povnaUA' : 'rozshyfrovka_bazovaUA';
  const safeName  = (name || 'HD').replace(/\s+/g, '_').replace(/[^\w]/g, '');
  const attachments = pdfBuffer ? [{
    filename: `${planLabel}_${safeName}.pdf`,
    content:  pdfBuffer,
    contentType: 'application/pdf',
  }] : [];

  await createTransport().sendMail({
    from: `"Human Design UA" <${GMAIL_USER}>`,
    to: email,
    subject: t.readySubject(name),
    html,
    attachments,
  });
}

// ── 3. Failed payment email ───────────────────────────────────
async function sendFailedPaymentEmail(order) {
  const { email, name, plan, order_id, locale } = order;
  const lang = normLang(locale);
  const t = T[lang];
  const retryUrl = `${SITE_URL}/quiz.html?plan=${plan}#pricing`;

  const html = emailWrap(`
    <tr><td style="background:#1A1440;border-radius:16px 16px 0 0;padding:32px 40px;
                   text-align:center;border-bottom:1px solid #2D2560;">
      <div style="font-size:11px;letter-spacing:3px;color:#D4A830;text-transform:uppercase;
                  font-family:Arial,sans-serif;">Human Design UA</div>
      <div style="font-size:24px;color:#F0ECE8;margin-top:8px;">${t.failedTitle}</div>
    </td></tr>
    <tr><td style="background:#120F2D;padding:40px;border-radius:0 0 16px 16px;">
      <p style="color:#F0ECE8;font-size:16px;line-height:1.8;margin:0 0 20px;">
        ${t.failedBody(name)}
      </p>
      <ul style="color:#8B7FAA;font-size:15px;line-height:2;margin:0 0 32px;font-family:Arial,sans-serif;">
        ${t.failedReasons.map(r => `<li>${r}</li>`).join('')}
      </ul>
      <a href="${retryUrl}"
         style="display:inline-block;background:#D4A830;color:#0D0B1E;font-weight:700;
                font-size:16px;padding:16px 40px;border-radius:10px;text-decoration:none;
                font-family:Arial,sans-serif;">${t.failedBtn}</a>
      <p style="color:#3D3560;font-size:13px;margin:24px 0 0;font-family:Arial,sans-serif;">
        ${order_id}
      </p>
    </td></tr>`);

  await createTransport().sendMail({
    from: `"Human Design UA" <${GMAIL_USER}>`,
    to: email,
    subject: t.failedSubject,
    html,
  });
}

module.exports = { sendReceiptEmail, sendReadingEmail, sendFailedPaymentEmail };
