// Human Design — Payment Integration (LiqPay)
// DEV mode: uses mock payment, no real money charged
// PROD mode: real LiqPay via Make.com webhook

const MAKE_WEBHOOK_URL = 'YOUR_MAKE_WEBHOOK_URL_HERE';

// ── DEV MOCK ──────────────────────────────────────────────
// ── DEV Card input screen ─────────────────────────────────
function showDevCardScreen(quizData, orderId, amount) {
  document.getElementById('devCardScreen')?.remove();

  const T = window.t || (k => k);

  const overlay = document.createElement('div');
  overlay.id = 'devCardScreen';
  overlay.style.cssText = `
    position:fixed; inset:0; background:rgba(0,0,0,0.88);
    display:flex; align-items:center; justify-content:center;
    z-index:9998; font-family:Inter,sans-serif;
  `;

  overlay.innerHTML = `
    <div style="background:#fff; border-radius:16px; padding:0;
                max-width:400px; width:92%; overflow:hidden; box-shadow:0 24px 60px rgba(0,0,0,0.5);">

      <!-- Header -->
      <div style="background:#1A1440; padding:1.25rem 1.5rem; display:flex; align-items:center; justify-content:space-between;">
        <div style="color:#D4A830; font-size:0.7rem; letter-spacing:0.1em; text-transform:uppercase; font-weight:700;">
          🛠 DEV — Тестова форма оплати
        </div>
        <div style="color:#F0ECE8; font-size:1rem; font-weight:700;">${amount} грн</div>
      </div>

      <!-- Alt pay buttons -->
      <div style="padding:1rem 1.5rem 0; display:flex; gap:0.75rem;">
        <button onclick="devAltPay('apple', '${orderId}')"
          style="flex:1; background:#000; color:#fff; border:none; border-radius:8px;
                 padding:0.65rem; font-size:0.9rem; cursor:pointer; display:flex;
                 align-items:center; justify-content:center; gap:0.4rem;">
          🍎 Apple Pay
        </button>
        <button onclick="devAltPay('google', '${orderId}')"
          style="flex:1; background:#fff; color:#000; border:1px solid #ddd; border-radius:8px;
                 padding:0.65rem; font-size:0.9rem; cursor:pointer; display:flex;
                 align-items:center; justify-content:center; gap:0.4rem;">
          <span style="font-size:1rem;">G</span> Google Pay
        </button>
      </div>

      <div style="display:flex; align-items:center; gap:0.75rem; padding:0.75rem 1.5rem;">
        <div style="flex:1; height:1px; background:#eee;"></div>
        <div style="font-size:0.75rem; color:#999;">або картою</div>
        <div style="flex:1; height:1px; background:#eee;"></div>
      </div>

      <!-- Card form -->
      <div style="padding:0 1.5rem 1.5rem;">

        <!-- Card number -->
        <div style="margin-bottom:0.85rem;">
          <label style="font-size:0.75rem; color:#666; display:block; margin-bottom:0.3rem;">Номер картки</label>
          <div style="position:relative;">
            <input id="devCardNum" type="text" value="4242 4242 4242 4242"
              style="width:100%; padding:0.65rem 3rem 0.65rem 0.75rem; border:1.5px solid #ddd;
                     border-radius:8px; font-size:1rem; letter-spacing:0.12em; box-sizing:border-box;
                     outline:none; font-family:monospace;"
              oninput="this.style.borderColor='#9B6EE0'"
              maxlength="19"
              placeholder="0000 0000 0000 0000">
            <span style="position:absolute; right:0.75rem; top:50%; transform:translateY(-50%);
                         font-size:1.1rem;">💳</span>
          </div>
        </div>

        <!-- Card holder -->
        <div style="margin-bottom:0.85rem;">
          <label style="font-size:0.75rem; color:#666; display:block; margin-bottom:0.3rem;">Ім'я власника картки</label>
          <input id="devCardHolder" type="text" value="TEST USER"
            style="width:100%; padding:0.65rem 0.75rem; border:1.5px solid #ddd;
                   border-radius:8px; font-size:0.95rem; text-transform:uppercase;
                   box-sizing:border-box; outline:none;"
            oninput="this.style.borderColor='#9B6EE0'"
            placeholder="IVAN IVANOV">
        </div>

        <!-- Expiry + CVV -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem; margin-bottom:1.25rem;">
          <div>
            <label style="font-size:0.75rem; color:#666; display:block; margin-bottom:0.3rem;">Термін дії</label>
            <input id="devCardExpiry" type="text" value="12/28"
              style="width:100%; padding:0.65rem 0.75rem; border:1.5px solid #ddd;
                     border-radius:8px; font-size:0.95rem; box-sizing:border-box; outline:none;"
              oninput="this.style.borderColor='#9B6EE0'"
              maxlength="5" placeholder="MM/YY">
          </div>
          <div>
            <label style="font-size:0.75rem; color:#666; display:block; margin-bottom:0.3rem;">CVV</label>
            <input id="devCardCvv" type="password" value="123"
              style="width:100%; padding:0.65rem 0.75rem; border:1.5px solid #ddd;
                     border-radius:8px; font-size:0.95rem; box-sizing:border-box; outline:none;"
              oninput="this.style.borderColor='#9B6EE0'"
              maxlength="4" placeholder="•••">
          </div>
        </div>

        <!-- Pay button -->
        <button onclick="devConfirmCard('${orderId}')"
          style="width:100%; background:#D4A830; color:#0D0B1E; border:none; border-radius:10px;
                 padding:0.9rem; font-size:1rem; font-weight:700; cursor:pointer;">
          Оплатити ${amount} грн →
        </button>

        <!-- Security note -->
        <div style="text-align:center; margin-top:0.75rem; font-size:0.72rem; color:#aaa; display:flex; align-items:center; justify-content:center; gap:0.3rem;">
          🔒 Тестова форма · DEV · дані не зберігаються
        </div>

        <!-- Test cards hint -->
        <div style="margin-top:0.75rem; padding:0.6rem 0.75rem; background:#f8f5ff; border-radius:8px; border-left:3px solid #9B6EE0;">
          <div style="font-size:0.7rem; color:#9B6EE0; font-weight:700; margin-bottom:0.3rem;">Тестові картки:</div>
          <div style="font-size:0.7rem; color:#555; line-height:1.6;">
            ✅ Успішна:   4242 4242 4242 4242<br>
            ❌ Відхилена: 4000 0000 0000 0002<br>
            ⏳ 3D-Secure:  4000 0027 6000 3184
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
}

function devConfirmCard(orderId) {
  const num    = document.getElementById('devCardNum')?.value.replace(/\s/g, '');
  const holder = document.getElementById('devCardHolder')?.value;

  document.getElementById('devCardScreen')?.remove();

  // Simulate card decline for test decline number
  if (num === '4000000000000002') {
    showDevResultModal(false, orderId, '❌ Картка відхилена банком');
    return;
  }
  // Simulate 3DS for specific number
  if (num === '4000002760003184') {
    show3DSModal(orderId);
    return;
  }
  // Default — success
  showDevResultModal(true, orderId);
}

function devAltPay(method, orderId) {
  document.getElementById('devCardScreen')?.remove();
  // Simulate slight delay for realism
  const label = method === 'apple' ? 'Apple Pay' : 'Google Pay';
  showDevResultModal(true, orderId, `✅ ${label} авторизовано`);
}

function show3DSModal(orderId) {
  const m = document.createElement('div');
  m.id = 'dev3dsModal';
  m.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.88);display:flex;align-items:center;justify-content:center;z-index:9999;font-family:Inter,sans-serif;';
  m.innerHTML = `
    <div style="background:#fff;border-radius:12px;padding:2rem;max-width:340px;width:90%;text-align:center;">
      <div style="font-size:1.5rem;margin-bottom:0.75rem;">🏦</div>
      <div style="font-size:1rem;font-weight:700;color:#1A1440;margin-bottom:0.5rem;">3D Secure підтвердження</div>
      <div style="font-size:0.85rem;color:#666;margin-bottom:1.25rem;">Введіть код з SMS від банку</div>
      <input type="text" value="123456" maxlength="6"
        style="width:100%;padding:0.75rem;border:1.5px solid #9B6EE0;border-radius:8px;font-size:1.1rem;text-align:center;letter-spacing:0.2em;box-sizing:border-box;">
      <button onclick="document.getElementById('dev3dsModal').remove(); showDevResultModal(true,'${orderId}')"
        style="width:100%;margin-top:1rem;background:#1A1440;color:#fff;border:none;border-radius:8px;padding:0.75rem;cursor:pointer;font-weight:600;">
        Підтвердити
      </button>
    </div>
  `;
  document.body.appendChild(m);
}

function showDevResultModal(success, orderId, note) {
  const T = window.t || (k => k);
  document.getElementById('devPayModal')?.remove();
  const modal = document.createElement('div');
  modal.id = 'devPayModal';
  modal.style.cssText = `
    position:fixed; inset:0; background:rgba(0,0,0,0.85);
    display:flex; align-items:center; justify-content:center;
    z-index:9999; font-family:Inter,sans-serif;
  `;
  const planName = quizData.plan === 'full'
    ? (window.t ? window.t('quiz.pricing.full.name')  : 'Full')
    : (window.t ? window.t('quiz.pricing.basic.name') : 'Basic');

  const noteHtml = note ? `<div style="font-size:0.8rem;color:#A090C0;margin-bottom:1rem;">${note}</div>` : '';
  modal.innerHTML = `
    <div style="background:#1A1440; border:1px solid #D4A830; border-radius:16px;
                padding:2rem; max-width:420px; width:90%; text-align:center;">
      <div style="font-size:0.75rem; color:#D4A830; letter-spacing:0.1em;
                  text-transform:uppercase; margin-bottom:1rem;">
        ${T('dev.modal.title')}
      </div>
      ${noteHtml}
      <div style="font-size:1.5rem; font-weight:600; color:#F0ECE8; margin-bottom:0.5rem;">
        ${amount} грн
      </div>
      <div style="font-size:0.9rem; color:#A090C0; margin-bottom:0.25rem;">
        ${T('dev.modal.plan')} <strong style="color:#F0ECE8">${planName}</strong>
      </div>
      <div style="font-size:0.85rem; color:#A090C0; margin-bottom:0.25rem;">
        ${T('dev.modal.email')} ${quizData.email}
      </div>
      <div style="font-size:0.8rem; color:#6B5F80; margin-bottom:1.5rem;">
        ${T('dev.modal.order')} ${orderId}
      </div>
      <div style="display:flex; gap:0.75rem; justify-content:center;">
        <button onclick="devPaymentResult(true, '${orderId}')"
          style="background:#D4A830; color:#0D0B1E; border:none; border-radius:8px;
                 padding:0.75rem 1.5rem; font-weight:600; cursor:pointer; font-size:0.95rem;">
          ${T('dev.modal.success')}
        </button>
        <button onclick="devPaymentResult(false, '${orderId}')"
          style="background:transparent; color:#E05050; border:1px solid #E05050;
                 border-radius:8px; padding:0.75rem 1.5rem; cursor:pointer; font-size:0.95rem;">
          ${T('dev.modal.fail')}
        </button>
      </div>
      <div style="margin-top:1rem;">
        <button onclick="document.getElementById('devPayModal').remove()"
          style="background:none; border:none; color:#6B5F80; cursor:pointer; font-size:0.8rem;">
          ${T('dev.modal.cancel')}
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

async function devPaymentResult(result, orderId, note) {
  document.getElementById('devPayModal')?.remove();
  if (result === 'success' || result === true) {
    localStorage.setItem('hd_order_id', orderId);
    localStorage.setItem('hd_payment_status', 'success');

    // Send to local dev server → generates PDF + sends email
    const quizData = JSON.parse(localStorage.getItem('hd_quiz_data') || '{}');
    const amount   = quizData.plan === 'full' ? 799 : 399;

    try {
      const res = await fetch('http://localhost:4000/pay', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id:    orderId,
          email:       quizData.email      || '',
          name:        quizData.name       || '',
          plan:        quizData.plan       || 'basic',
          amount:      amount,
          birth_date:  quizData.birthDate  || '',
          birth_time:  quizData.birthTime  || '',
          birth_place: quizData.birthPlace || '',
          life_area:   quizData.lifeArea   || '',
          challenge:   quizData.challenge  || '',
          utm_source:  getUTM('utm_source'),
          utm_campaign:getUTM('utm_campaign'),
          locale:      window.i18n ? window.i18n.current() : localStorage.getItem('hd_lang') || 'ua',
        }),
      });
      const json = await res.json();
      if (json.status === 'partial') {
        console.warn('[DEV] PDF ok but email failed:', json.message);
      } else {
        console.log('[DEV] Receipt sent:', json);
      }
    } catch (e) {
      console.warn('[DEV] Dev server not running on :4000 — start with: python3 scripts/dev_server.py');
    }

    window.location.href = 'success.html?order_id=' + orderId + '&status=success';
  } else {
    showPaymentError('[DEV] Симуляція помилки оплати');
    const btn = document.getElementById('payBtn');
    setLoading(btn, false);
  }
}

// ── Initiate payment ──────────────────────────────────────
async function initiatePayment(quizData) {
  const btn = document.getElementById('payBtn');
  setLoading(btn, true);

  const orderId = 'HD-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7).toUpperCase();
  const amount  = quizData.plan === 'full' ? 799 : 399;

  // ── DEV MODE: показати mock замість реального LiqPay ──
  if (window.HD_ENV === 'dev') {
    setLoading(btn, false);
    localStorage.setItem('hd_order_id', orderId);
    localStorage.setItem('hd_plan',     quizData.plan);
    localStorage.setItem('hd_email',    quizData.email);
    localStorage.setItem('hd_quiz_data', JSON.stringify(quizData));
    showDevCardScreen(quizData, orderId, amount);
    return;
  }

  const payload = {
    action:       'get_liqpay_form',
    order_id:     orderId,
    amount:       amount,
    plan:         quizData.plan,
    email:        quizData.email,
    name:         quizData.name || '',
    birth_date:   quizData.birthDate,
    birth_time:   quizData.birthTime,
    birth_place:  quizData.birthPlace,
    life_area:    quizData.lifeArea,
    challenge:    quizData.challenge,
    hd_knowledge: quizData.hdKnowledge,
    source:       quizData.source || 'direct',
    locale:       window.i18n ? window.i18n.current() : localStorage.getItem('hd_lang') || 'ua',
    utm_source:   getUTM('utm_source'),
    utm_campaign: getUTM('utm_campaign'),
  };

  // Save order ID for success page
  localStorage.setItem('hd_order_id', orderId);
  localStorage.setItem('hd_plan', quizData.plan);
  localStorage.setItem('hd_email', quizData.email);

  try {
    const res = await fetch(MAKE_WEBHOOK_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    if (!res.ok) throw new Error('Server error ' + res.status);

    const { data, signature } = await res.json();

    if (!data || !signature) throw new Error('Invalid server response');

    submitLiqPayForm(data, signature);

  } catch (err) {
    console.error('Payment init error:', err);
    setLoading(btn, false);
    showPaymentError(window.t ? window.t('pay.error.generic') : 'Сталася помилка. Спробуй ще раз або напиши нам.');
  }
}

// ── Build and submit LiqPay form ─────────────────────────
function submitLiqPayForm(data, signature) {
  // Remove old form if exists
  const old = document.getElementById('liqpay_form');
  if (old) old.remove();

  const form = document.createElement('form');
  form.id     = 'liqpay_form';
  form.method = 'POST';
  form.action = 'https://www.liqpay.ua/api/3/checkout';
  form.style.display = 'none';

  const dataInput = document.createElement('input');
  dataInput.type  = 'hidden';
  dataInput.name  = 'data';
  dataInput.value = data;

  const sigInput = document.createElement('input');
  sigInput.type  = 'hidden';
  sigInput.name  = 'signature';
  sigInput.value = signature;

  form.appendChild(dataInput);
  form.appendChild(sigInput);
  document.body.appendChild(form);
  form.submit();
}

// ── Upsell payment ────────────────────────────────────────
async function initiateUpsell(userId) {
  const btn = document.getElementById('upsellPayBtn');
  setLoading(btn, true);

  const orderId = 'HD-UP-' + Date.now();
  const payload = {
    action:   'upsell_payment',
    user_id:  userId,
    order_id: orderId,
    amount:   400,
    plan:     'full',
    email:    localStorage.getItem('hd_email') || '',
  };

  try {
    const res = await fetch(MAKE_WEBHOOK_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    if (!res.ok) throw new Error('Server error ' + res.status);
    const { data, signature } = await res.json();
    submitLiqPayForm(data, signature);

  } catch (err) {
    console.error('Upsell payment error:', err);
    setLoading(btn, false);
    showPaymentError(window.t ? window.t('pay.error.generic') : 'Сталася помилка. Спробуй ще раз.');
  }
}

// ── Helpers ───────────────────────────────────────────────
function setLoading(btn, loading) {
  if (!btn) return;
  btn.classList.toggle('btn-loading', loading);
  btn.disabled = loading;
  if (loading) {
    btn.dataset.originalText = btn.textContent;
    btn.textContent = window.t ? window.t('pay.processing') : 'Обробляємо...';
  } else {
    btn.textContent = btn.dataset.originalText || btn.textContent;
  }
}

function showPaymentError(msg) {
  let el = document.getElementById('paymentError');
  if (!el) {
    el = document.createElement('p');
    el.id = 'paymentError';
    el.style.cssText = 'color:#E05555; font-size:0.85rem; margin-top:0.75rem; text-align:center;';
    document.getElementById('payBtn')?.insertAdjacentElement('afterend', el);
  }
  el.textContent = msg;
}

function getUTM(param) {
  const url = new URLSearchParams(window.location.search);
  return url.get(param) || sessionStorage.getItem(param) || '';
}

// ── Save UTM to session ───────────────────────────────────
(function saveUTMs() {
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(p => {
    const v = new URLSearchParams(window.location.search).get(p);
    if (v) sessionStorage.setItem(p, v);
  });
})();
