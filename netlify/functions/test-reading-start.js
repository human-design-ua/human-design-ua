// Step 1: save order to Blobs + trigger background generation
const { saveOrder } = require('./utils/db');

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return cors(405, 'Method not allowed');

  let order;
  try { order = JSON.parse(event.body); }
  catch { return cors(400, JSON.stringify({ error: 'Invalid JSON' })); }

  if (!order.order_id) order.order_id = 'TEST-' + Date.now();

  // Save as "pending"
  await saveOrder({ ...order, reading_status: 'pending', payment_status: 'test' });
  console.log('Started reading for', order.order_id);

  return cors(200, JSON.stringify({ order_id: order.order_id, status: 'started' }));
};

function cors(status, body) {
  return { statusCode: status, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type' }, body: typeof body === 'string' ? body : JSON.stringify(body) };
}
