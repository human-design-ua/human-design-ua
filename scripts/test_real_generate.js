// Calls the real Claude API via generateReading() and writes the result + PDF.
// Usage: node scripts/test_real_generate.js [full|basic]
const fs = require('fs');
const path = require('path');
// Load .env manually (no dotenv dependency)
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  fs.readFileSync(envPath, 'utf8').split('\n').forEach(line => {
    const m = line.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
  });
}
const { generateReading } = require('../netlify/functions/utils/claude');
const { generateReadingPDF } = require('../netlify/functions/utils/pdf');

const plan = process.argv[2] === 'basic' ? 'basic' : 'full';

const order = {
  order_id: 'TEST-' + Date.now(),
  email: 'test@example.com',
  name: 'Олена',
  birth_date: '1990-03-15',
  birth_time: '14:30',
  birth_place: 'Київ, Україна',
  plan,
  locale: 'uk',
  life_area: 'career',
  challenge: 'self_doubt',
};

(async () => {
  console.log(`Generating ${plan.toUpperCase()} reading via Claude API for ${order.name}...`);
  const t0 = Date.now();
  const reading = await generateReading(order);
  console.log(`Done in ${((Date.now()-t0)/1000).toFixed(1)}s. hd_type=${reading.hd_type} profile=${reading.profile}`);

  const outJson = path.join(__dirname, `real_${plan}.json`);
  fs.writeFileSync(outJson, JSON.stringify(reading, null, 2));
  console.log('Saved JSON:', outJson);

  const pdfBuf = await generateReadingPDF(order, reading);
  const outPdf = path.join(__dirname, `real_${plan}.pdf`);
  fs.writeFileSync(outPdf, pdfBuf);
  console.log('Saved PDF:', outPdf, `(${(pdfBuf.length/1024).toFixed(0)} KB)`);
})().catch(e => {
  console.error('FAILED:', e);
  process.exit(1);
});
