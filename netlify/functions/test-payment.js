// Test function — simulates successful payment for testing
// Only works in non-production environment (netlify.app domain)
const { saveOrder }       = require('./utils/db');
const { generateReading } = require('./utils/claude');
const { sendReceiptEmail, sendReadingEmail } = require('./utils/email');

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return cors(200, '');
  }
  if (event.httpMethod !== 'POST') {
    return cors(405, JSON.stringify({ error: 'Method not allowed' }));
  }

  let order;
  try {
    order = JSON.parse(event.body);
  } catch {
    return cors(400, JSON.stringify({ error: 'Invalid JSON' }));
  }

  if (!order.email) {
    return cors(400, JSON.stringify({ error: 'Email required' }));
  }

  // Save order to DB
  await saveOrder({ ...order, payment_status: 'success', paid_at: new Date().toISOString() });

  // Step 1 — send receipt
  try {
    await sendReceiptEmail(order);
    console.log('Test: receipt sent to', order.email);
  } catch (err) {
    console.error('Test: receipt failed:', err.message);
    return cors(500, JSON.stringify({ error: 'Receipt failed: ' + err.message }));
  }

  // Step 2 — generate reading
  let reading;
  try {
    reading = await generateReading(order);
    console.log('Test: reading generated for', order.order_id);
  } catch (err) {
    console.error('Test: reading failed:', err.message);
    return cors(500, JSON.stringify({ error: 'Reading failed: ' + err.message }));
  }

  // Step 3 — send reading email
  try {
    await sendReadingEmail(order, reading);
    console.log('Test: reading email sent to', order.email);
  } catch (err) {
    console.error('Test: reading email failed:', err.message);
    return cors(500, JSON.stringify({ error: 'Reading email failed: ' + err.message }));
  }

  return cors(200, JSON.stringify({
    status: 'success',
    message: 'Receipt + reading sent to ' + order.email,
  }));
};

function cors(status, body) {
  return {
    statusCode: status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
    body,
  };
}
