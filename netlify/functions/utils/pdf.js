// PDF Generator — Human Design Reading
// Uses pdfkit to generate styled PDF with bodygraph SVG
const PDFDocument = require('pdfkit');
const { generateBodygraph } = require('./bodygraph');

// Light theme colors
const C = {
  bg:       '#FFFFFF',
  primary:  '#4B3F8A',
  gold:     '#B8892A',
  text:     '#1A1530',
  muted:    '#6B6090',
  light:    '#F0EDF8',
  border:   '#DDD8F0',
};

function addPage(doc) {
  doc.addPage();
  // Light header bar
  doc.rect(0, 0, 595, 8).fill(C.primary);
  doc.rect(0, 8, 595, 3).fill(C.gold);
  return doc;
}

function header(doc, name, plan) {
  doc.rect(0, 0, 595, 8).fill(C.primary);
  doc.rect(0, 8, 595, 3).fill(C.gold);
  doc.rect(0, 11, 595, 789).fill(C.bg);

  // Logo text
  doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold')
     .text('HUMAN DESIGN UA', 50, 30, { align: 'center', width: 495 });

  const planName = plan === 'full' ? 'Повна розшифровка' : 'Базова розшифровка';
  doc.fontSize(8).fillColor(C.gold).font('Helvetica')
     .text(planName.toUpperCase(), 50, 45, { align: 'center', width: 495 });

  // Main title
  doc.fontSize(22).fillColor(C.primary).font('Helvetica-Bold')
     .text(`Персональна розшифровка`, 50, 75, { align: 'center', width: 495 });
  doc.fontSize(18).fillColor(C.gold).font('Helvetica')
     .text(name || 'Твій Дизайн Людини', 50, 102, { align: 'center', width: 495 });

  // Divider
  doc.rect(50, 130, 495, 1).fill(C.border);
}

function sectionTitle(doc, title, y) {
  doc.rect(50, y, 495, 24).fill(C.light);
  doc.rect(50, y, 4, 24).fill(C.primary);
  doc.fontSize(11).fillColor(C.primary).font('Helvetica-Bold')
     .text(title.toUpperCase(), 62, y + 7);
  return y + 32;
}

function bodyText(doc, text, y, options = {}) {
  if (!text) return y;
  doc.fontSize(10).fillColor(C.text).font('Helvetica')
     .text(text, 50, y, { width: 495, align: 'justify', lineGap: 3, ...options });
  return doc.y + 8;
}

function keyValue(doc, label, value, y) {
  doc.fontSize(9).fillColor(C.muted).font('Helvetica-Bold')
     .text(label + ':', 50, y, { continued: true });
  doc.fontSize(9).fillColor(C.primary).font('Helvetica-Bold')
     .text(' ' + (value || '—'));
  return doc.y + 4;
}

function checkItem(doc, text, y) {
  if (!text) return y;
  doc.fontSize(9).fillColor(C.gold).font('Helvetica-Bold')
     .text('✓', 50, y, { continued: true });
  doc.fontSize(9).fillColor(C.text).font('Helvetica')
     .text('  ' + text, { width: 480 });
  return doc.y + 3;
}

function footer(doc, pageNum) {
  doc.rect(0, 820, 595, 22).fill(C.primary);
  doc.fontSize(7).fillColor('#F0ECE8').font('Helvetica')
     .text('Human Design UA  ·  humandesign.finance@gmail.com', 50, 826, { align: 'center', width: 495 });
}

async function generateReadingPDF(order, reading) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({
        size: 'A4', margins: { top: 20, bottom: 40, left: 50, right: 50 },
        info: {
          Title: `Розшифровка Дизайну Людини — ${order.name || ''}`,
          Author: 'Human Design UA',
        }
      });

      const chunks = [];
      doc.on('data', chunk => chunks.push(chunk));
      doc.on('end', () => resolve(Buffer.concat(chunks)));
      doc.on('error', reject);

      const name = order.name || 'Клієнт';
      const plan = order.plan || 'basic';

      // ── PAGE 1: Cover ────────────────────────────────────
      header(doc, name, plan);

      let y = 148;

      // Параметри
      y = sectionTitle(doc, 'Твої параметри', y);
      y = keyValue(doc, 'Тип', reading.hd_type, y);
      y = keyValue(doc, 'Стратегія', reading.strategy, y);
      y = keyValue(doc, 'Авторитет', reading.authority, y);
      y = keyValue(doc, 'Профіль', reading.profile, y);
      y = keyValue(doc, 'Визначеність', reading.definition, y);
      y = keyValue(doc, 'Інкарнаційний хрест', reading.incarnation_cross, y);
      y = keyValue(doc, 'Дата народження', order.birth_date + (order.birth_time ? ' ' + order.birth_time : ''), y);
      y = keyValue(doc, 'Місце народження', order.birth_place, y);
      y += 10;

      // Бодиграф SVG → embed as description (pdfkit SVG support limited)
      y = sectionTitle(doc, 'Бодиграф', y);
      const gates = reading.activated_gates || [];
      doc.fontSize(9).fillColor(C.muted).font('Helvetica')
         .text(`Активованих воріт: ${gates.length} · Активованих центрів: ${getActiveCenters(gates)} з 9`, 50, y);
      y = doc.y + 6;

      // Draw simplified bodygraph as vector shapes in PDF
      drawPDFBodygraph(doc, gates, 50, y, 220, 160);
      y += 175;

      // Вступ
      y = sectionTitle(doc, 'Персональний вступ', y);
      y = bodyText(doc, reading.intro_text, y);

      footer(doc, 1);

      // ── PAGE 2: Тип, Стратегія, Авторитет ──────────────
      addPage(doc);
      y = 20;

      y = sectionTitle(doc, `✦ Твій тип — ${reading.hd_type}`, y);
      y = bodyText(doc, reading.type_description, y);
      if (reading.type_work) y = bodyText(doc, '👔 Робота: ' + reading.type_work, y);
      if (reading.type_relationships) y = bodyText(doc, '❤️ Стосунки: ' + reading.type_relationships, y);
      if (reading.type_sleep) y = bodyText(doc, '🌙 Сон: ' + reading.type_sleep, y);
      y += 8;

      y = sectionTitle(doc, `Стратегія: ${reading.strategy}`, y);
      y = bodyText(doc, reading.strategy_description, y);
      y = bodyText(doc, reading.strategy_benefit, y);
      y += 8;

      y = sectionTitle(doc, `Авторитет: ${reading.authority}`, y);
      y = bodyText(doc, reading.authority_description, y);
      if (reading.authority_how_to) y = bodyText(doc, reading.authority_how_to, y);
      y = bodyText(doc, reading.authority_benefit, y);

      footer(doc, 2);

      // ── PAGE 3: Профіль + Центри ─────────────────────────
      addPage(doc);
      y = 20;

      y = sectionTitle(doc, `Профіль ${reading.profile}`, y);
      y = bodyText(doc, reading.profile_description, y);
      y = bodyText(doc, reading.profile_role, y);
      if (reading.profile_benefit) y = bodyText(doc, reading.profile_benefit, y);
      y += 8;

      y = sectionTitle(doc, '9 Центрів — 9 сфер життя', y);
      y = bodyText(doc, reading.centers_overview, y);
      y = bodyText(doc, reading.centers_life_areas, y);
      for (let i = 1; i <= 4; i++) {
        const cn = reading[`center${i}_name`];
        const cd = reading[`center${i}_description`];
        if (cn && cd) {
          doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold').text('▸ ' + cn, 50, doc.y + 6);
          y = bodyText(doc, cd, doc.y + 2);
        }
      }
      if (reading.open_centers_description) {
        doc.fontSize(10).fillColor(C.muted).font('Helvetica-Bold').text('◦ Відкриті центри:', 50, doc.y + 6);
        y = bodyText(doc, reading.open_centers_description, doc.y + 2);
      }

      footer(doc, 3);

      // ── PAGE 4: Теми + Рекомендації ──────────────────────
      addPage(doc);
      y = 20;

      y = sectionTitle(doc, 'Підпис та Не-Я сигнал', y);
      if (reading.signature) y = bodyText(doc, '✦ Підпис: ' + reading.signature, y);
      if (reading.not_self)   y = bodyText(doc, '⚠ Не-Я: ' + reading.not_self, y);
      y += 8;

      y = sectionTitle(doc, 'Твоя тема', y);
      y = bodyText(doc, reading.life_theme, y);
      y += 8;

      y = sectionTitle(doc, 'Рекомендації', y);
      for (const rec of (reading.recommendations || [])) {
        y = checkItem(doc, rec, doc.y + 2);
      }

      footer(doc, 4);

      // ── FULL PLAN extras ─────────────────────────────────
      if (plan === 'full') {

        // PAGE 5: Планети, Канали, Хрест
        addPage(doc);
        y = 20;

        if (reading.channels_description) {
          y = sectionTitle(doc, 'Розбір каналів', y);
          y = bodyText(doc, reading.channels_description, y);
          y += 8;
        }
        if (reading.planets_description) {
          y = sectionTitle(doc, 'Планети та вузли', y);
          y = bodyText(doc, reading.planets_description, y);
          y += 8;
        }
        if (reading.auto_reactions) {
          y = sectionTitle(doc, 'Автоматичні реакції', y);
          y = bodyText(doc, reading.auto_reactions, y);
          y += 8;
        }
        if (reading.incarnation_cross_description) {
          y = sectionTitle(doc, `Інкарнаційний хрест: ${reading.incarnation_cross || ''}`, y);
          y = bodyText(doc, reading.incarnation_cross_description, y);
          y += 8;
        }
        if (reading.self_sufficiency) {
          y = sectionTitle(doc, 'Самодостатність', y);
          y = bodyText(doc, reading.self_sufficiency, y);
        }
        footer(doc, 5);

        // PAGE 6: ПОДАРУНКИ — Практики + План 90 днів
        addPage(doc);
        y = 20;

        // Gift banner
        doc.rect(50, y, 495, 30).fill('#FFF8E7');
        doc.rect(50, y, 4, 30).fill(C.gold);
        doc.fontSize(12).fillColor(C.gold).font('Helvetica-Bold')
           .text('🎁 ПОДАРУНОК — Практики декондиціювання', 62, y + 9);
        y += 38;

        y = bodyText(doc, 'Ці практики допоможуть звільнитись від чужих програм та повернутись до своєї справжньої природи:', y);
        y += 4;
        for (const p of (reading.deconditioning_practices || [])) {
          y = checkItem(doc, p, doc.y + 4);
        }
        y += 12;

        // Plan 90 days
        doc.rect(50, y, 495, 30).fill('#F0EDF8');
        doc.rect(50, y, 4, 30).fill(C.primary);
        doc.fontSize(12).fillColor(C.primary).font('Helvetica-Bold')
           .text('🗓 ПОДАРУНОК — Особистий план на 90 днів', 62, y + 9);
        y += 38;

        if (reading.plan_week1) { doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold').text('Тиждень 1', 50, y); y = bodyText(doc, reading.plan_week1, doc.y + 2); y += 4; }
        if (reading.plan_week2) { doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold').text('Тиждень 2', 50, y); y = bodyText(doc, reading.plan_week2, doc.y + 2); y += 4; }
        if (reading.plan_week3) { doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold').text('Тиждень 3', 50, y); y = bodyText(doc, reading.plan_week3, doc.y + 2); y += 4; }
        if (reading.plan_week4) { doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold').text('Тиждень 4', 50, y); y = bodyText(doc, reading.plan_week4, doc.y + 2); y += 4; }
        if (reading.plan_month2) { doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold').text('Місяць 2', 50, y); y = bodyText(doc, reading.plan_month2, doc.y + 2); y += 4; }
        if (reading.plan_month3) { doc.fontSize(10).fillColor(C.primary).font('Helvetica-Bold').text('Місяць 3', 50, y); y = bodyText(doc, reading.plan_month3, doc.y + 2); }

        footer(doc, 6);
      }

      // ── Last page: closing ───────────────────────────────
      addPage(doc);
      y = 150;

      doc.rect(50, y, 495, 2).fill(C.gold);
      y += 16;
      doc.fontSize(16).fillColor(C.primary).font('Helvetica-Bold')
         .text('З теплом та повагою', 50, y, { align: 'center', width: 495 });
      y += 24;
      y = bodyText(doc, reading.closing_message, y);
      y += 20;
      doc.fontSize(11).fillColor(C.gold).font('Helvetica-Bold')
         .text('Human Design UA', 50, y, { align: 'center', width: 495 });
      doc.fontSize(9).fillColor(C.muted).font('Helvetica')
         .text('humandesign.finance@gmail.com', 50, doc.y + 4, { align: 'center', width: 495 });

      footer(doc, 99);
      doc.end();

    } catch(err) {
      reject(err);
    }
  });
}

function getActiveCenters(gates) {
  const { getDefinedCenters } = require('./bodygraph');
  return getDefinedCenters(gates).size;
}

// Draw simplified bodygraph in PDF using pdfkit shapes
function drawPDFBodygraph(doc, gates, x, y, w, h) {
  const { getDefinedCenters, CENTER_GATES, CHANNELS } = require('./bodygraph');
  const defined = getDefinedCenters(gates);
  const scale = w / 420;

  const centers = {
    head:   [180, 20, 60, 40],
    ajna:   [180, 80, 60, 40],
    throat: [175, 155, 70, 40],
    g:      [165, 230, 90, 50],
    heart:  [285, 230, 60, 40],
    sp:     [285, 305, 60, 55],
    sacral: [165, 320, 90, 50],
    spleen: [60, 230, 60, 55],
    root:   [165, 405, 90, 45],
  };

  const labels = { head:'Голова', ajna:'Аджна', throat:'Горло', g:'G', heart:'Серце',
                   sp:'СС', sacral:'Сакрал', spleen:'Сел.', root:'Корінь' };

  // Draw channels
  for (const ch of CHANNELS) {
    if (!gates.includes(ch[0]) || !gates.includes(ch[1])) continue;
    const c1 = Object.keys(CENTER_GATES).find(c => CENTER_GATES[c].includes(ch[0]));
    const c2 = Object.keys(CENTER_GATES).find(c => CENTER_GATES[c].includes(ch[1]));
    if (!c1 || !c2 || c1 === c2 || !centers[c1] || !centers[c2]) continue;
    const [cx1, cy1, cw1, ch1] = centers[c1];
    const [cx2, cy2, cw2, ch2] = centers[c2];
    doc.moveTo(x + (cx1 + cw1/2) * scale, y + (cy1 + ch1/2) * scale)
       .lineTo(x + (cx2 + cw2/2) * scale, y + (cy2 + ch2/2) * scale)
       .stroke('#8B6ECC');
  }

  // Draw centers
  for (const [name, [cx, cy, cw, ch]] of Object.entries(centers)) {
    const px = x + cx * scale;
    const py = y + cy * scale;
    const pw = cw * scale;
    const ph = ch * scale;
    const isDef = defined.has(name);
    doc.rect(px, py, pw, ph)
       .fillAndStroke(isDef ? '#E8E2FF' : '#F5F3FA', isDef ? '#4B3F8A' : '#C0B8E0');
    doc.fontSize(6).fillColor(isDef ? '#4B3F8A' : '#9B90C0').font('Helvetica')
       .text(labels[name] || name, px, py + ph/2 - 3, { width: pw, align: 'center' });
  }
}

module.exports = { generateReadingPDF };
