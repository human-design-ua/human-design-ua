// Database via Netlify Blobs — no external service needed
const { getStore } = require('@netlify/blobs');

function ordersStore() {
  return getStore({ name: 'orders', consistency: 'strong' });
}

async function saveOrder(order) {
  const store = ordersStore();
  await store.setJSON(order.order_id, {
    ...order,
    created_at: new Date().toISOString(),
  });
}

async function getOrder(orderId) {
  const store = ordersStore();
  return store.get(orderId, { type: 'json' });
}

async function updateOrder(orderId, patch) {
  const store = ordersStore();
  const existing = await store.get(orderId, { type: 'json' });
  if (!existing) return;
  await store.setJSON(orderId, { ...existing, ...patch, updated_at: new Date().toISOString() });
}

// List all orders for admin panel — returns array sorted newest first
async function listOrders() {
  const store = ordersStore();
  const { blobs } = await store.list();
  const orders = await Promise.all(
    blobs.map(b => store.get(b.key, { type: 'json' }))
  );
  return orders
    .filter(Boolean)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

module.exports = { saveOrder, getOrder, updateOrder, listOrders };
