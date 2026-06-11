// Background function: generates reading + saves result to Blobs (no timeout!)
const { getOrder, updateOrder } = require('./utils/db');
const { generateReading }       = require('./utils/claude');

exports.handler = async (event) => {
  let order;
  try { order = JSON.parse(event.body); }
  catch(e) { console.error('Invalid JSON:', e.message); return; }

  const { order_id } = order;
  if (!order_id) { console.error('No order_id'); return; }

  console.log('Background: generating for', order_id);

  try {
    const reading = await generateReading(order);
    await updateOrder(order_id, {
      reading_json:          JSON.stringify(reading),
      reading_status:        'done',
      reading_generated_at:  new Date().toISOString(),
    });
    console.log('Background: done for', order_id, '| type:', reading.hd_type);
  } catch(err) {
    console.error('Background: failed for', order_id, '|', err.message);
    await updateOrder(order_id, { reading_status: 'error', reading_error: err.message });
  }
};
