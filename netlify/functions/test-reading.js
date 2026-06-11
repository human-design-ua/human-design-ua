// Test function — generates reading and returns JSON directly (no email)
// Use to verify reading quality before connecting email
const { generateReading } = require('./utils/claude');

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return cors(200, '');
  if (event.httpMethod !== 'POST') return cors(405, JSON.stringify({ error: 'Method not allowed' }));

  let order;
  try {
    order = JSON.parse(event.body);
  } catch {
    return cors(400, JSON.stringify({ error: 'Invalid JSON' }));
  }

  console.log('Test reading for:', order.email, 'plan:', order.plan);

  try {
    const reading = await generateReading(order);
    return cors(200, JSON.stringify({ status: 'ok', reading }));
  } catch (err) {
    console.error('Reading generation failed:', err.message);
    return cors(500, JSON.stringify({ error: err.message }));
  }
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
