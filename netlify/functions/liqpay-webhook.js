// Netlify Function: LiqPay payment callback
// LiqPay calls this after payment → generate reading → send emails → save to DB
const { verify, decode }          = require('./utils/liqpay');
const { getOrder, updateOrder }   = require('./utils/db');
const { sendReceiptEmail, sendFailedPaymentEmail } = require('./utils/email');

const LIQPAY_PRIVATE_KEY = process.env.LIQPAY_PRIVATE_KEY;
const SITE_URL           = process.env.SITE_URL || 'https://human-design-ua.netlify.app';

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method not allowed' };
  }

  // LiqPay sends data as application/x-www-form-urlencoded
  const params = new URLSearchParams(event.body);
  const data      = params.get('data');
  const signature = params.get('signature');

  if (!data || !signature) {
    console.error('Webhook: missing data or signature');
    return { statusCode: 400, body: 'Bad request' };
  }

  // Verify signature
  if (!verify(LIQPAY_PRIVATE_KEY, data, signature)) {
    console.error('Webhook: invalid signature');
    return { statusCode: 403, body: 'Invalid signature' };
  }

  let payload;
  try {
    payload = decode(data);
  } catch (err) {
    console.error('Webhook: decode failed', err);
    return { statusCode: 400, body: 'Decode error' };
  }

  const { order_id, status, amount, payment_id } = payload;
  console.log(`Webhook: order=${order_id} status=${status} amount=${amount}`);

  // ── Payment failed / reversed ──────────────────────────
  if (['failure', 'error', 'reversed'].includes(status)) {
    const order = await getOrder(order_id);
    if (order?.email) {
      await sendFailedPaymentEmail(order).catch(e =>
        console.error('Failed payment email error:', e.message)
      );
    }
    await updateOrder(order_id, { payment_status: status, liqpay_payment_id: payment_id });
    return { statusCode: 200, body: 'ok' };
  }

  // ── Payment success ────────────────────────────────────
  if (status !== 'success' && status !== 'sandbox') {
    // Waiting / processing — do nothing yet
    return { statusCode: 200, body: 'ok' };
  }

  // Retrieve saved order data
  const order = await getOrder(order_id);
  if (!order) {
    console.error(`Webhook: order not found in DB: ${order_id}`);
    return { statusCode: 200, body: 'ok' };
  }

  // Idempotency — don't process twice
  if (order.payment_status === 'success') {
    console.log(`Webhook: already processed ${order_id}`);
    return { statusCode: 200, body: 'ok' };
  }

  await updateOrder(order_id, {
    payment_status: 'success',
    liqpay_payment_id: payment_id,
    paid_at: new Date().toISOString(),
  });

  // Step 1 — send receipt immediately
  try {
    await sendReceiptEmail(order);
    console.log(`Receipt sent to ${order.email}`);
  } catch (err) {
    console.error('Receipt email failed:', err.message);
  }

  // Step 2 — trigger background function for reading generation + email
  // (generateReading does 6 Claude API calls and can take minutes — far longer
  // than this webhook's execution limit, so it must run in a background function)
  try {
    await fetch(`${SITE_URL}/.netlify/functions/liqpay-webhook-background`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    });
    console.log(`Background reading generation triggered for ${order_id}`);
  } catch (err) {
    console.error('Failed to trigger background reading generation:', err.message);
  }

  return { statusCode: 200, body: 'ok' };
};
