// Netlify Function: sign LiqPay payment form
// Frontend calls this instead of Make.com webhook
const { encode, sign } = require('./utils/liqpay');
const { saveOrder }    = require('./utils/db');

const LIQPAY_PUBLIC_KEY  = process.env.LIQPAY_PUBLIC_KEY;
const LIQPAY_PRIVATE_KEY = process.env.LIQPAY_PRIVATE_KEY;
const SITE_URL           = process.env.SITE_URL || 'https://human-design-ua.netlify.app';

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return cors(200, '');
  }
  if (event.httpMethod !== 'POST') {
    return cors(405, JSON.stringify({ error: 'Method not allowed' }));
  }

  // If LiqPay keys not configured yet — return test mode flag
  if (!LIQPAY_PUBLIC_KEY || LIQPAY_PUBLIC_KEY === 'your_liqpay_public_key') {
    return cors(200, JSON.stringify({ test_mode: true }));
  }

  let body;
  try {
    body = JSON.parse(event.body);
  } catch {
    return cors(400, JSON.stringify({ error: 'Invalid JSON' }));
  }

  const {
    order_id, amount, plan, email, name,
    birth_date, birth_time, birth_place,
    life_area, challenge, hd_knowledge,
    utm_source, utm_campaign, locale,
  } = body;

  if (!order_id || !amount || !email) {
    return cors(400, JSON.stringify({ error: 'order_id, amount and email are required' }));
  }

  // Save order as pending before redirecting to LiqPay
  try {
    await saveOrder({
      order_id, email, name: name || '', plan: plan || 'basic',
      amount: Number(amount), birth_date, birth_time, birth_place,
      life_area, challenge, hd_knowledge,
      utm_source, utm_campaign, locale: locale || 'uk',
      payment_status: 'pending',
    });
  } catch (err) {
    console.error('DB save error (non-fatal):', err.message);
  }

  // Build LiqPay data object
  const liqpayData = {
    public_key:  LIQPAY_PUBLIC_KEY,
    version:     '3',
    action:      'pay',
    amount:      String(amount),
    currency:    'UAH',
    description: `Human Design UA — ${plan === 'full' ? 'Повна розшифровка' : 'Базова розшифровка'}`,
    order_id,
    result_url:  `${SITE_URL}/success.html?order_id=${order_id}&status=success`,
    server_url:  `${SITE_URL}/.netlify/functions/liqpay-webhook`,
    language:    'uk',
  };

  const data      = encode(liqpayData);
  const signature = sign(LIQPAY_PRIVATE_KEY, data);

  return cors(200, JSON.stringify({ data, signature }));
};

function cors(status, body) {
  return {
    statusCode: status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
    },
    body,
  };
}
