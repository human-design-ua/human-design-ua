// Human Design — Payment Integration (LiqPay)
// DEV mode: uses mock payment, no real money charged
// PROD mode: real LiqPay via Make.com webhook

const MAKE_WEBHOOK_URL = 'YOUR_MAKE_WEBHOOK_URL_HERE';

// ── DEV MOCK ──────────────────────────────────────────────
function showDevPaymentModal(quizData, orderId, amount) {
  // Remove existing modal
  document.getElementById('devPayModal')?.remove();

  const modal = document.createElement('div');
  modal.id = 'devPayModal';
  modal.style.cssText = `
    position:fixed; inset:0; background:rgba(0,0,0,0.85);
    display:flex; align-items:center; justify-content:center;
    z-index:9999; font-family:Inter,sans-serif;
  `;
  modal.innerHTML = `
    <div style="background:#1A1440; border:1px solid #D4A830; border-radius:16px;
                padding:2rem; max-width:420px; width:90%; text-align:center;">
      <div style="font-size:0.75rem; color:#D4A830; letter-spacing:0.1em;
                  text-transform:uppercase; margin-bottom:1rem;">
        🛠 DEV MODE — Тестовий платіж
      </div>
      <div style="font-size:1.5rem; font-weight:600; color:#F0ECE8; margin-bottom:0.5rem;">
        ${amount} грн
      </div>
      <div style="font-size:0.9rem; color:#A090C0; margin-bottom:0.25rem;">
        Тариф: <strong style="color:#F0ECE8">${quizData.plan === 'full' ? 'Повний' : 'Базовий'}</strong>
      </div>
      <div style="font-size:0.85rem; color:#A090C0; margin-bottom:1.5rem;">
        Email: ${quizData.email}
      </div>
      <div style="font-size:0.8rem; color:#6B5F80; margin-bottom:1.5rem;">
        Order ID: ${orderId}
      </div>
      <div style="display:flex; gap:0.75rem; justify-content:center;">
        <button onclick="devPaymentResult('success', '${orderId}')"
          style="background:#D4A830; color:#0D0B1E; border:none; border-radius:8px;
                 padding:0.75rem 1.5rem; font-weight:600; cursor:pointer; font-size:0.95rem;">
          ✓ Оплата успішна
        </button>
        <button onclick="devPaymentResult('failure', '${orderId}')"
          style="background:transparent; color:#E05050; border:1px solid #E05050;
                 border-radius:8px; padding:0.75rem 1.5rem; cursor:pointer; font-size:0.95rem;">
          ✗ Помилка оплати
        </button>
      </div>
      <div style="margin-top:1rem;">
        <button onclick="document.getElementById('devPayModal').remove()"
          style="background:none; border:none; color:#6B5F80; cursor:pointer; font-size:0.8rem;">
          Скасувати
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function devPaymentResult(result, orderId) {
  document.getElementById('devPayModal')?.remove();
  if (result === 'success') {
    localStorage.setItem('hd_order_id', orderId);
    localStorage.setItem('hd_payment_status', 'success');
    // Trigger receipt generation via Python script (dev only)
    console.log('[DEV] Payment success. Order:', orderId);
    console.log('[DEV] Run: python3 scripts/send_receipt.py --order', orderId);
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
    showDevPaymentModal(quizData, orderId, amount);
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
    showPaymentError('Сталася помилка. Спробуй ще раз або напиши нам.');
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
    showPaymentError('Сталася помилка. Спробуй ще раз.');
  }
}

// ── Helpers ───────────────────────────────────────────────
function setLoading(btn, loading) {
  if (!btn) return;
  btn.classList.toggle('btn-loading', loading);
  btn.disabled = loading;
  if (loading) {
    btn.dataset.originalText = btn.textContent;
    btn.textContent = 'Обробляємо...';
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
