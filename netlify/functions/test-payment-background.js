// Background Function — runs up to 15 minutes (no timeout!)
// Generates HD reading + sends emails after test payment
const { saveOrder }       = require('./utils/db');
const { generateReading } = require('./utils/claude');
const { sendReceiptEmail, sendReadingEmail } = require('./utils/email');

exports.handler = async (event) => {
  let order;
  try {
    order = JSON.parse(event.body);
  } catch (e) {
    console.error('Background: invalid JSON', e.message);
    return;
  }

  if (!order.email) {
    console.error('Background: no email in order');
    return;
  }

  console.log(`Background: starting for ${order.email} plan=${order.plan}`);

  // Save order
  try {
    await saveOrder({ ...order, payment_status: 'success', paid_at: new Date().toISOString() });
    console.log('Background: order saved');
  } catch (err) {
    console.error('Background: save failed:', err.message);
  }

  // Step 1 — send receipt immediately
  try {
    await sendReceiptEmail(order);
    console.log('Background: receipt sent to', order.email);
  } catch (err) {
    console.error('Background: receipt failed:', err.message);
  }

  // Step 2 — generate reading
  let reading;
  try {
    console.log('Background: generating reading with Claude API...');
    reading = await generateReading(order);
    console.log('Background: reading generated! hd_type=', reading?.hd_type);
  } catch (err) {
    console.error('Background: reading generation FAILED:', err.message);
    console.error('Background: full error:', err.stack);
    // Still continue — don't return silently
    return;
  }

  if (!reading || !reading.hd_type) {
    console.error('Background: reading is empty or missing hd_type');
    return;
  }

  // Step 3 — send reading email
  try {
    console.log('Background: sending reading email to', order.email);
    await sendReadingEmail(order, reading);
    console.log('Background: reading email sent successfully to', order.email);
  } catch (err) {
    console.error('Background: reading email FAILED:', err.message);
    console.error('Background: email error stack:', err.stack);
  }
};
