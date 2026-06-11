// Step 1: just return order_id immediately — no Blobs needed
exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return cors(200, '');
  if (event.httpMethod !== 'POST') return cors(405, 'Method not allowed');

  let order;
  try { order = JSON.parse(event.body); }
  catch { return cors(400, JSON.stringify({ error: 'Invalid JSON' })); }

  if (!order.order_id) order.order_id = 'TEST-' + Date.now();

  console.log('Reading start requested for', order.order_id);
  return cors(200, JSON.stringify({ order_id: order.order_id, status: 'started' }));
};

function cors(s, b) {
  return { statusCode: s, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type' }, body: b };
}
