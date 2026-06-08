// Netlify Function: admin panel API — list orders
// Protected by ADMIN_SECRET env variable
const { listOrders } = require('./utils/db');

const ADMIN_SECRET = process.env.ADMIN_SECRET;

exports.handler = async (event) => {
  // Simple token auth
  const token = event.headers['x-admin-secret'] || event.queryStringParameters?.secret;
  if (ADMIN_SECRET && token !== ADMIN_SECRET) {
    return { statusCode: 401, body: JSON.stringify({ error: 'Unauthorized' }) };
  }

  try {
    const orders = await listOrders();
    const stats = {
      total:   orders.length,
      revenue: orders.reduce((s, o) => s + (o.amount || 0), 0),
      basic:   orders.filter(o => o.plan === 'basic').length,
      full:    orders.filter(o => o.plan === 'full').length,
    };
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ stats, orders }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message }),
    };
  }
};
