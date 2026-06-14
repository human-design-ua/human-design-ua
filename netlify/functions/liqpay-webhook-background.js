// Background Function — runs up to 15 minutes (no timeout!)
// Generates HD reading + sends reading email after successful payment.
// Triggered by liqpay-webhook.js (which handles signature check, receipt email, fast response to LiqPay).
const { updateOrder }      = require('./utils/db');
const { generateReading }  = require('./utils/claude');
const { sendReadingEmail } = require('./utils/email');

exports.handler = async (event) => {
  let order;
  try {
    order = JSON.parse(event.body);
  } catch (e) {
    console.error('Webhook background: invalid JSON', e.message);
    return;
  }

  const { order_id } = order;
  if (!order_id) {
    console.error('Webhook background: no order_id');
    return;
  }

  console.log(`Webhook background: generating reading for ${order_id}`);

  let reading;
  try {
    reading = await generateReading(order);
    await updateOrder(order_id, {
      reading_json:         JSON.stringify(reading),
      reading_status:       'done',
      reading_generated_at: new Date().toISOString(),
    });
    console.log(`Webhook background: reading generated for ${order_id} | type:`, reading?.hd_type);
  } catch (err) {
    console.error(`Webhook background: reading generation failed for ${order_id}:`, err.message);
    await updateOrder(order_id, { reading_status: 'error', reading_error: err.message });
    return;
  }

  try {
    await sendReadingEmail(order, reading);
    await updateOrder(order_id, { reading_sent_at: new Date().toISOString() });
    console.log(`Webhook background: reading email sent to ${order.email}`);
  } catch (err) {
    console.error(`Webhook background: reading email failed for ${order_id}:`, err.message);
  }
};
