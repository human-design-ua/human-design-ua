// Email via Gmail SMTP — nodemailer, no external service
const nodemailer = require('nodemailer');

const GMAIL_USER = process.env.GMAIL_USER || 'humandesign.finance@gmail.com';
const GMAIL_PASS = (process.env.GMAIL_APP_PASSWORD || '').replace(/\s/g, '');
const SITE_URL   = process.env.SITE_URL || 'https://human-design-ua.netlify.app';

function createTransport() {
  return nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: { user: GMAIL_USER, pass: GMAIL_PASS },
  });
}

// ── Receipt email (sent immediately after payment) ─────────
async function sendReceiptEmail(order) {
  const { order_id, email, name, plan, amount } = order;
  const planName = plan === 'full' ? 'Повна розшифровка' : 'Базова розшифровка';
  const greeting = name ? `${name}, в` : 'В';

  const html = `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0D0B1E;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0D0B1E;padding:40px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr><td style="background:#1A1440;border-radius:16px 16px 0 0;padding:32px 40px;text-align:center;border-bottom:1px solid #2D2560;">
          <div style="font-size:11px;letter-spacing:3px;color:#D4A830;text-transform:uppercase;font-family:Arial,sans-serif;">Human Design UA</div>
          <div style="font-size:28px;color:#F0ECE8;margin-top:8px;font-weight:400;">Оплату отримано ✦</div>
        </td></tr>

        <!-- Body -->
        <tr><td style="background:#120F2D;padding:40px;border-radius:0 0 16px 16px;">
          <p style="color:#F0ECE8;font-size:17px;line-height:1.7;margin:0 0 24px;">
            ${greeting}аша оплата успішно прийнята.<br>
            Розшифровка вже генерується і надійде на цей email протягом <strong style="color:#D4A830;">5–10 хвилин</strong>.
          </p>

          <!-- Order details -->
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#1A1440;border-radius:12px;padding:24px;margin-bottom:32px;">
            <tr><td style="padding:8px 0;border-bottom:1px solid #2D2560;">
              <span style="color:#8B7FAA;font-size:13px;font-family:Arial,sans-serif;">Номер замовлення</span><br>
              <span style="color:#F0ECE8;font-size:15px;">${order_id}</span>
            </td></tr>
            <tr><td style="padding:8px 0;border-bottom:1px solid #2D2560;">
              <span style="color:#8B7FAA;font-size:13px;font-family:Arial,sans-serif;">Послуга</span><br>
              <span style="color:#F0ECE8;font-size:15px;">${planName}</span>
            </td></tr>
            <tr><td style="padding:8px 0;">
              <span style="color:#8B7FAA;font-size:13px;font-family:Arial,sans-serif;">Сума</span><br>
              <span style="color:#D4A830;font-size:20px;font-weight:bold;">${amount} грн</span>
            </td></tr>
          </table>

          <p style="color:#8B7FAA;font-size:14px;line-height:1.6;margin:0 0 8px;font-family:Arial,sans-serif;">
            З теплом,<br>
            <strong style="color:#F0ECE8;">Human Design UA</strong><br>
            <a href="mailto:${GMAIL_USER}" style="color:#D4A830;">${GMAIL_USER}</a>
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="text-align:center;padding:24px 0;">
          <p style="color:#3D3560;font-size:12px;margin:0;font-family:Arial,sans-serif;">
            © 2026 Human Design UA · <a href="${SITE_URL}/privacy.html" style="color:#3D3560;">Конфіденційність</a>
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;

  const transport = createTransport();
  await transport.sendMail({
    from: `"Human Design UA" <${GMAIL_USER}>`,
    to: email,
    subject: `✦ Замовлення ${order_id} — оплату прийнято`,
    html,
  });
}

// ── Reading email (sent with full reading content) ─────────
async function sendReadingEmail(order, reading) {
  const { email, name, plan } = order;
  const planName = plan === 'full' ? 'Повна розшифровка' : 'Базова розшифровка';
  const greeting = name ? name : 'Дорога';
  const upsellBlock = plan === 'basic' ? `
    <tr><td style="padding:32px 40px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#1A1440;border:1px solid #D4A830;border-radius:12px;padding:28px;">
        <tr><td>
          <div style="font-size:11px;letter-spacing:2px;color:#D4A830;text-transform:uppercase;font-family:Arial,sans-serif;margin-bottom:8px;">Спеціальна пропозиція</div>
          <p style="color:#F0ECE8;font-size:16px;margin:0 0 16px;line-height:1.6;">
            Хочеш дізнатися більше? Повна розшифровка містить детальний аналіз 9 центрів, планет, каналів та інкарнаційного хреста.
          </p>
          <a href="${SITE_URL}/upsell.html" style="display:inline-block;background:#D4A830;color:#0D0B1E;font-weight:700;font-size:15px;padding:14px 32px;border-radius:8px;text-decoration:none;font-family:Arial,sans-serif;">
            Отримати повну версію за +400 грн →
          </a>
        </td></tr>
      </table>
    </td></tr>` : '';

  const html = `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0D0B1E;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0D0B1E;padding:40px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr><td style="background:#1A1440;border-radius:16px 16px 0 0;padding:32px 40px;text-align:center;border-bottom:1px solid #2D2560;">
          <div style="font-size:11px;letter-spacing:3px;color:#D4A830;text-transform:uppercase;font-family:Arial,sans-serif;">Human Design UA</div>
          <div style="font-size:28px;color:#F0ECE8;margin-top:8px;font-weight:400;">✦ ${greeting}, твій Дизайн готовий</div>
          <div style="font-size:14px;color:#8B7FAA;margin-top:8px;font-family:Arial,sans-serif;">${planName}</div>
        </td></tr>

        <!-- Intro -->
        <tr><td style="background:#120F2D;padding:40px 40px 24px;">
          <p style="color:#F0ECE8;font-size:17px;line-height:1.8;margin:0;">
            ${reading.intro_text || ''}
          </p>
        </td></tr>

        <!-- Type & Strategy -->
        ${readingSection('✦ Твій тип — ' + reading.hd_type, [
          reading.type_description,
          reading.type_benefit,
        ])}
        ${readingSection('Стратегія: ' + reading.strategy, [
          reading.strategy_description,
          reading.strategy_benefit,
        ])}

        <!-- Authority -->
        ${readingSection('Авторитет: ' + reading.authority, [
          reading.authority_description,
          reading.authority_how_to,
          reading.authority_benefit,
        ])}

        <!-- Profile -->
        ${readingSection('Профіль ' + reading.profile, [
          reading.profile_description,
          reading.profile_role,
          reading.profile_benefit,
        ])}

        <!-- Centers -->
        ${readingSection('Твої центри', [
          reading.centers_overview,
          reading.centers_life_areas,
          reading.center1_name ? `<strong style="color:#D4A830;">${reading.center1_name}</strong><br>${reading.center1_description}` : '',
          reading.center2_name ? `<strong style="color:#D4A830;">${reading.center2_name}</strong><br>${reading.center2_description}` : '',
          reading.center3_name ? `<strong style="color:#D4A830;">${reading.center3_name}</strong><br>${reading.center3_description}` : '',
          reading.center4_name ? `<strong style="color:#D4A830;">${reading.center4_name}</strong><br>${reading.center4_description}` : '',
          reading.open_centers_description,
        ])}

        <!-- Life Theme -->
        ${readingSection('Твоя тема', [reading.life_theme])}

        <!-- Signature & Not-self -->
        ${readingSection('Твій підпис і сигнал', [
          reading.signature ? `<strong style="color:#9B6EE0;">Підпис (ти в потоці):</strong><br>${reading.signature}` : '',
          reading.not_self  ? `<strong style="color:#E05050;">Не-Я сигнал:</strong><br>${reading.not_self}` : '',
        ])}

        <!-- Recommendations -->
        ${readingRecommendations(reading.recommendations)}

        <!-- Full plan extras (channels, planets, etc.) -->
        ${plan === 'full' ? readingFullExtras(reading) : ''}

        <!-- Upsell (basic only) -->
        ${upsellBlock}

        <!-- Sign-off -->
        <tr><td style="background:#120F2D;padding:32px 40px;border-radius:0 0 16px 16px;">
          <p style="color:#8B7FAA;font-size:14px;line-height:1.7;margin:0;font-family:Arial,sans-serif;">
            З теплом і повагою до твого унікального Дизайну,<br>
            <strong style="color:#F0ECE8;">Human Design UA</strong><br>
            <a href="mailto:${GMAIL_USER}" style="color:#D4A830;">${GMAIL_USER}</a>
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="text-align:center;padding:24px 0;">
          <p style="color:#3D3560;font-size:12px;margin:0;font-family:Arial,sans-serif;">
            © 2026 Human Design UA · <a href="${SITE_URL}/privacy.html" style="color:#3D3560;">Конфіденційність</a>
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;

  const transport = createTransport();
  await transport.sendMail({
    from: `"Human Design UA" <${GMAIL_USER}>`,
    to: email,
    subject: `✦ ${greeting}, твоя розшифровка Дизайну Людини готова`,
    html,
  });
}

// ── Failed payment email ───────────────────────────────────
async function sendFailedPaymentEmail(order) {
  const { email, name, plan, order_id } = order;
  const greeting = name ? name : '';
  const retryUrl = `${SITE_URL}/quiz.html?plan=${plan}#pricing`;

  const html = `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0D0B1E;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0D0B1E;padding:40px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        <tr><td style="background:#1A1440;border-radius:16px 16px 0 0;padding:32px 40px;text-align:center;border-bottom:1px solid #2D2560;">
          <div style="font-size:11px;letter-spacing:3px;color:#D4A830;text-transform:uppercase;font-family:Arial,sans-serif;">Human Design UA</div>
          <div style="font-size:24px;color:#F0ECE8;margin-top:8px;">Оплата не пройшла</div>
        </td></tr>
        <tr><td style="background:#120F2D;padding:40px;border-radius:0 0 16px 16px;">
          <p style="color:#F0ECE8;font-size:16px;line-height:1.8;margin:0 0 24px;">
            ${greeting ? `${greeting}, н` : 'На жаль, н'}а жаль, оплата не пройшла. Можливі причини:
          </p>
          <ul style="color:#8B7FAA;font-size:15px;line-height:2;margin:0 0 32px;font-family:Arial,sans-serif;">
            <li>Недостатньо коштів на картці</li>
            <li>Картка заблокована для онлайн-платежів</li>
            <li>Технічна помилка банку</li>
          </ul>
          <a href="${retryUrl}" style="display:inline-block;background:#D4A830;color:#0D0B1E;font-weight:700;font-size:16px;padding:16px 40px;border-radius:10px;text-decoration:none;font-family:Arial,sans-serif;">
            Спробувати ще раз →
          </a>
          <p style="color:#3D3560;font-size:13px;margin:24px 0 0;font-family:Arial,sans-serif;">
            Замовлення ${order_id} · Якщо потрібна допомога — напишіть нам
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;

  const transport = createTransport();
  await transport.sendMail({
    from: `"Human Design UA" <${GMAIL_USER}>`,
    to: email,
    subject: 'Оплата не пройшла — спробуйте ще раз',
    html,
  });
}

// ── HTML building helpers ──────────────────────────────────
function readingSection(title, paragraphs) {
  const content = paragraphs
    .filter(Boolean)
    .map(p => `<p style="color:#D8D0E8;font-size:15px;line-height:1.85;margin:0 0 16px;">${p}</p>`)
    .join('');
  return `
    <tr><td style="background:#120F2D;padding:32px 40px;border-top:1px solid #1E1B3A;">
      <h2 style="color:#D4A830;font-size:16px;letter-spacing:1px;margin:0 0 20px;font-family:Arial,sans-serif;font-weight:600;text-transform:uppercase;">${title}</h2>
      ${content}
    </td></tr>`;
}

function readingRecommendations(recs) {
  if (!recs || !recs.length) return '';
  const items = recs.map(r =>
    `<li style="color:#D8D0E8;font-size:15px;line-height:1.8;margin-bottom:10px;">${r}</li>`
  ).join('');
  return `
    <tr><td style="background:#120F2D;padding:32px 40px;border-top:1px solid #1E1B3A;">
      <h2 style="color:#D4A830;font-size:16px;letter-spacing:1px;margin:0 0 20px;font-family:Arial,sans-serif;font-weight:600;text-transform:uppercase;">Рекомендації для тебе</h2>
      <ul style="margin:0;padding-left:20px;">${items}</ul>
    </td></tr>`;
}

function readingFullExtras(reading) {
  const sections = [];

  if (reading.channels_description) {
    sections.push(readingSection('Твої канали та Gates', [reading.channels_description]));
  }
  if (reading.planets_description) {
    sections.push(readingSection('Планети та вузли', [reading.planets_description]));
  }
  if (reading.incarnation_cross_description) {
    sections.push(readingSection(`Інкарнаційний хрест: ${reading.incarnation_cross || ''}`, [reading.incarnation_cross_description]));
  }
  if (reading.conditioning_description) {
    sections.push(readingSection('Декондиціювання', [reading.conditioning_description]));
  }
  if (reading.relationships_description) {
    sections.push(readingSection('Стосунки та аура', [reading.relationships_description]));
  }
  if (reading.self_sufficiency) {
    sections.push(readingSection('Самодостатність', [reading.self_sufficiency]));
  }

  return sections.join('');
}

module.exports = { sendReceiptEmail, sendReadingEmail, sendFailedPaymentEmail };
