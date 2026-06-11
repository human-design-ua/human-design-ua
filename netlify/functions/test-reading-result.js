// Step 2: poll — returns reading when ready
const { getOrder } = require('./utils/db');

exports.handler = async (event) => {
  const order_id = event.queryStringParameters?.order_id;
  if (!order_id) return cors(400, JSON.stringify({ error: 'order_id required' }));

  const order = await getOrder(order_id);
  if (!order) return cors(404, JSON.stringify({ status: 'not_found' }));

  if (order.reading_status === 'error') {
    return cors(200, JSON.stringify({ status: 'error', error: order.reading_error }));
  }

  if (order.reading_status === 'done' && order.reading_json) {
    return cors(200, JSON.stringify({ status: 'done', reading: JSON.parse(order.reading_json) }));
  }

  return cors(200, JSON.stringify({ status: 'pending' }));
};

function cors(status, body) {
  return { statusCode: status, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }, body };
}
