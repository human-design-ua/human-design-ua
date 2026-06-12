// PDF Generator — Human Design Reading (rich content, auto-pagination)
// Full reading: ~50 pages | Basic reading: ~20 pages
const PDFDocument = require('pdfkit');
const path = require('path');
const { generateBodygraph } = require('./bodygraph');

// ── Light theme palette ───────────────────────────────────────
const C = {
  bg:       '#FFFFFF',
  primary:  '#4B3F8A',
  gold:     '#B8892A',
  text:     '#1A1530',
  muted:    '#6B6090',
  light:    '#F0EDF8',
  lightGold:'#FFF8E7',
  border:   '#DDD8F0',
  borderGold:'#E8D8A0',
  white:    '#FFFFFF',
};

// ── Font paths ────────────────────────────────────────────────
function getFontPath(filename) {
  const candidates = [
    path.join(__dirname, filename),
    path.join(process.cwd(), 'netlify/functions/utils', filename),
    path.join('/var/task/netlify/functions/utils', filename),
  ];
  for (const p of candidates) {
    try { require('fs').accessSync(p); return p; } catch(e) {}
  }
  return null;
}

// ════════════════════════════════════════════════════════════════
//  PDF Flow — auto-paginating renderer
// ════════════════════════════════════════════════════════════════
class PDFFlow {
  constructor(doc, name, plan) {
    this.doc = doc;
    this.name = name;
    this.plan = plan;
    this.pageNum = 0;
    this.LEFT = 50;
    this.RIGHT = 50;
    this.WIDTH = 595 - this.LEFT - this.RIGHT; // 495
    this.BOTTOM_LIMIT = 810;
    this.hasCustomFonts = false;

    // Register DejaVu fonts (mandatory for Cyrillic support)
    const boldPath = getFontPath('DejaVuSans-Bold.ttf');
    const regPath  = getFontPath('DejaVuSans.ttf');
    if (boldPath && regPath) {
      try {
        doc.registerFont('HDSans',      regPath);
        doc.registerFont('HDSans-Bold', boldPath);
        this.F  = 'HDSans';
        this.FB = 'HDSans-Bold';
        this.hasCustomFonts = true;
      } catch(e) {
        this.F  = 'Helvetica';
        this.FB = 'Helvetica-Bold';
      }
    } else {
      this.F  = 'Helvetica';
      this.FB = 'Helvetica-Bold';
    }
    // Set default font immediately
    doc.font(this.F);
  }

  font(bold = false) {
    this.doc.font(bold ? this.FB : this.F);
    return this;
  }

  // Shorthand — apply font and return doc for chaining
  f(bold = false) {
    return this.doc.font(bold ? this.FB : this.F);
  }

  _drawPageChrome() {
    this.doc.rect(0, 0, 595, 8).fill(C.primary);
    this.doc.rect(0, 8, 595, 3).fill(C.gold);
  }

  _drawFooter() {
    this.doc.rect(0, 820, 595, 22).fill(C.primary);
    this.doc.fontSize(7).fillColor('#F0ECE8').font(this.F)
       .text(
         `Human Design UA  ·  ${this.name || ''}  ·  Сторінка ${this.pageNum}`,
         50, 826, { align: 'center', width: 495 }
       );
  }

  newPage() {
    if (this.pageNum > 0) this._drawFooter();
    this.doc.addPage();
    this.pageNum++;
    this._drawPageChrome();
    this.doc.y = 20;
  }

  ensureSpace(needed) {
    if (this.doc.y + needed > this.BOTTOM_LIMIT) {
      this.newPage();
    }
    return this;
  }

  // ── Section title ───────────────────────────────────────────
  sectionTitle(title, style = 'primary') {
    this.ensureSpace(36);
    const y = this.doc.y;
    if (style === 'gold') {
      this.doc.rect(this.LEFT, y, this.WIDTH, 26).fill(C.lightGold);
      this.doc.rect(this.LEFT, y, 4, 26).fill(C.gold);
      this.doc.fontSize(11).fillColor(C.gold);
    } else {
      this.doc.rect(this.LEFT, y, this.WIDTH, 26).fill(C.light);
      this.doc.rect(this.LEFT, y, 4, 26).fill(C.primary);
      this.doc.fontSize(11).fillColor(C.primary);
    }
    this.font(true).text(title.toUpperCase(), this.LEFT + 12, y + 8, { width: this.WIDTH - 16 });
    this.doc.y = y + 33;
    return this;
  }

  // ── Sub-section heading ─────────────────────────────────────
  subHeading(title) {
    this.ensureSpace(28);
    this.doc.y += 6;
    this.font(true).fontSize(10).fillColor(C.primary)
       .text('▸  ' + title, this.LEFT, this.doc.y, { width: this.WIDTH });
    this.doc.y += 4;
    return this;
  }

  // ── Small label ─────────────────────────────────────────────
  label(text) {
    this.ensureSpace(16);
    this.font(true).fontSize(8).fillColor(C.muted)
       .text(text.toUpperCase(), this.LEFT, this.doc.y, { width: this.WIDTH });
    this.doc.y += 3;
    return this;
  }

  // ── Body paragraph ──────────────────────────────────────────
  para(text, indent = 0) {
    if (!text || text.length < 5) return this;
    // Remove any JSON artifact artifacts
    const clean = String(text).replace(/Мінімум \d+ слів\./gi, '').trim();
    if (!clean) return this;

    this.ensureSpace(40);
    this.font(false).fontSize(10).fillColor(C.text)
       .text(clean, this.LEFT + indent, this.doc.y, {
         width: this.WIDTH - indent,
         align: 'justify',
         lineGap: 3,
       });
    this.doc.y += 8;
    return this;
  }

  // ── Key-value row ────────────────────────────────────────────
  keyValue(label, value) {
    if (!value) return this;
    this.ensureSpace(20);
    const y = this.doc.y;
    this.font(true).fontSize(9).fillColor(C.muted)
       .text(label + ':', this.LEFT, y, { continued: true });
    this.font(true).fontSize(9).fillColor(C.primary)
       .text('  ' + String(value), { width: this.WIDTH - 120 });
    this.doc.y += 3;
    return this;
  }

  // ── Check item (✓ list) ──────────────────────────────────────
  checkItem(text) {
    if (!text || text.length < 3) return this;
    const clean = String(text).replace(/Мінімум \d+ слів\./gi, '').trim();
    if (!clean) return this;
    this.ensureSpace(22);
    const y = this.doc.y;
    this.doc.fontSize(10).fillColor(C.gold).font(this.FB)
       .text('✓', this.LEFT, y, { continued: true });
    this.font(false).fontSize(9).fillColor(C.text)
       .text('  ' + clean, { width: this.WIDTH - 20, lineGap: 2 });
    this.doc.y += 3;
    return this;
  }

  // ── Bullet item ──────────────────────────────────────────────
  bullet(text) {
    if (!text || text.length < 3) return this;
    const clean = String(text).replace(/Мінімум \d+ слів\./gi, '').trim();
    this.ensureSpace(20);
    this.font(false).fontSize(9).fillColor(C.text)
       .text('•  ' + clean, this.LEFT + 12, this.doc.y, { width: this.WIDTH - 12, lineGap: 2 });
    this.doc.y += 3;
    return this;
  }

  // ── Numbered step ────────────────────────────────────────────
  step(n, text) {
    if (!text) return this;
    this.ensureSpace(20);
    this.font(true).fontSize(9).fillColor(C.primary)
       .text(`${n}.`, this.LEFT + 8, this.doc.y, { continued: true });
    this.font(false).fontSize(9).fillColor(C.text)
       .text('  ' + text, { width: this.WIDTH - 20, lineGap: 2 });
    this.doc.y += 3;
    return this;
  }

  // ── Spacer ───────────────────────────────────────────────────
  space(h = 10) {
    if (this.doc.y + h < this.BOTTOM_LIMIT) this.doc.y += h;
    return this;
  }

  // ── Horizontal rule ──────────────────────────────────────────
  rule(color = C.border) {
    this.ensureSpace(10);
    this.doc.rect(this.LEFT, this.doc.y, this.WIDTH, 1).fill(color);
    this.doc.y += 8;
    return this;
  }

  // ── Highlight box ────────────────────────────────────────────
  highlight(text, style = 'primary') {
    if (!text) return this;
    const clean = String(text).replace(/Мінімум \d+ слів\./gi, '').trim();
    this.ensureSpace(50);
    const y = this.doc.y;
    // Estimate height
    const lineH = 14;
    const chars = clean.length;
    const lines = Math.ceil(chars / 60) + 1;
    const h = Math.max(40, lines * lineH + 16);

    const bgColor = style === 'gold' ? C.lightGold : C.light;
    const accentColor = style === 'gold' ? C.gold : C.primary;
    this.doc.rect(this.LEFT, y, this.WIDTH, h).fill(bgColor);
    this.doc.rect(this.LEFT, y, 4, h).fill(accentColor);
    this.font(false).fontSize(10).fillColor(C.text)
       .text(clean, this.LEFT + 14, y + 10, { width: this.WIDTH - 20, lineGap: 3 });
    this.doc.y = y + h + 8;
    return this;
  }

  // ── Center block (for center sections) ──────────────────────
  centerBlock(centerData, isDefined) {
    if (!centerData) return this;
    const statusColor = isDefined ? C.primary : C.muted;
    const statusText  = isDefined ? 'ВИЗНАЧЕНИЙ' : 'ВІДКРИТИЙ';
    const bgColor     = isDefined ? C.light : '#F9F8FE';

    this.ensureSpace(36);
    const y = this.doc.y;
    this.doc.rect(this.LEFT, y, this.WIDTH, 26).fill(bgColor);
    this.doc.rect(this.LEFT, y, 4, 26).fill(statusColor);

    // Title
    this.font(true).fontSize(11).fillColor(statusColor)
       .text((centerData.title || '').toUpperCase(), this.LEFT + 12, y + 4, {
         width: this.WIDTH - 100, continued: true
       });

    // Status badge
    this.font(true).fontSize(8).fillColor(statusColor)
       .text(`  [${statusText}]`, { align: 'right', width: 80 });

    this.doc.y = y + 33;

    this.para(centerData.description);
    if (centerData.gifts) {
      this.subHeading('Дари та переваги');
      this.para(centerData.gifts, 12);
    }
    if (centerData.shadow) {
      this.subHeading('Тіньовий бік та виклики');
      this.para(centerData.shadow, 12);
    }
    if (centerData.practice) {
      this.subHeading('Практика');
      this.highlight(centerData.practice, 'gold');
    }
    this.space(12);
    return this;
  }

  // ── Channel block ────────────────────────────────────────────
  channelBlock(ch) {
    if (!ch || !ch.description) return this;
    this.ensureSpace(50);
    const y = this.doc.y;
    this.doc.rect(this.LEFT, y, this.WIDTH, 28).fill(C.light);
    this.doc.rect(this.LEFT, y, 4, 28).fill(C.gold);
    this.font(true).fontSize(11).fillColor(C.gold)
       .text(`Канал ${ch.channel_id || ''} — ${ch.channel_name || ''}`, this.LEFT + 12, y + 8, { width: this.WIDTH - 20 });
    this.doc.y = y + 35;
    this.para(ch.description);
    if (ch.gifts) { this.subHeading('Дари каналу'); this.para(ch.gifts, 12); }
    if (ch.shadow) { this.subHeading('Виклики'); this.para(ch.shadow, 12); }
    if (ch.how_to_use) { this.subHeading('Як використовувати'); this.highlight(ch.how_to_use, 'gold'); }
    this.space(12);
    return this;
  }

  // ── Planet row ───────────────────────────────────────────────
  planetBlock(label, text) {
    if (!text) return this;
    this.ensureSpace(30);
    const y = this.doc.y;
    this.font(true).fontSize(10).fillColor(C.primary)
       .text(`♦ ${label}`, this.LEFT, y, { width: 130, continued: false });
    const afterLabel = y + 16;
    this.font(false).fontSize(9.5).fillColor(C.text)
       .text(String(text).replace(/Мінімум \d+ слів\./gi,'').trim(), this.LEFT + 16, afterLabel, {
         width: this.WIDTH - 16, align: 'justify', lineGap: 2
       });
    this.doc.y += 6;
    return this;
  }

  // ── Practice block ───────────────────────────────────────────
  practiceBlock(practice, index) {
    if (!practice) return this;
    this.ensureSpace(50);
    const y = this.doc.y;
    this.doc.rect(this.LEFT, y, this.WIDTH, 28).fill(C.light);
    this.doc.rect(this.LEFT, y, 4, 28).fill(C.primary);
    this.font(true).fontSize(10).fillColor(C.primary)
       .text(`Практика ${index}: ${practice.title || ''}`, this.LEFT + 12, y + 8, { width: this.WIDTH - 20 });
    this.doc.y = y + 35;
    this.para(practice.description);
    if (Array.isArray(practice.steps) && practice.steps.length) {
      this.subHeading('Як виконувати:');
      practice.steps.forEach((step, i) => this.step(i + 1, step));
    }
    this.space(12);
    return this;
  }

  // ── Plan week/month block ────────────────────────────────────
  planBlock(period, text) {
    if (!text) return this;
    this.ensureSpace(40);
    const y = this.doc.y;
    this.doc.rect(this.LEFT, y, this.WIDTH, 24).fill(C.lightGold);
    this.doc.rect(this.LEFT, y, 4, 24).fill(C.gold);
    this.font(true).fontSize(10).fillColor(C.gold)
       .text(period.toUpperCase(), this.LEFT + 12, y + 7, { width: this.WIDTH - 20 });
    this.doc.y = y + 31;
    this.para(text);
    return this;
  }
}

// ════════════════════════════════════════════════════════════════
//  Cover page
// ════════════════════════════════════════════════════════════════
function renderCover(doc, flow, order, reading) {
  const { name, birth_date, birth_time, birth_place } = order;
  const planName = order.plan === 'full' ? 'Повна розшифровка' : 'Базова розшифровка';
  const pages = order.plan === 'full' ? '~50 сторінок' : '~20 сторінок';

  // Cover gradient bg
  doc.rect(0, 0, 595, 842).fill('#FAFAFA');
  doc.rect(0, 0, 595, 8).fill(C.primary);
  doc.rect(0, 8, 595, 3).fill(C.gold);
  doc.rect(0, 829, 595, 13).fill(C.primary);

  // Decorative center strip
  doc.rect(0, 200, 595, 300).fill(C.light);
  doc.rect(0, 200, 595, 4).fill(C.primary);
  doc.rect(0, 496, 595, 4).fill(C.primary);

  const fb = flow.FB; // bold font name
  const fr = flow.F;  // regular font name

  // Logo
  doc.fontSize(10).fillColor(C.primary).font(fb)
     .text('HUMAN DESIGN UA', 50, 35, { align: 'center', width: 495 });
  doc.fontSize(8).fillColor(C.gold).font(fr)
     .text('ПЕРСОНАЛЬНА РОЗШИФРОВКА ДИЗАЙНУ ЛЮДИНИ', 50, 50, { align: 'center', width: 495 });

  // Title
  doc.fontSize(9).fillColor(C.gold).font(fb)
     .text(planName.toUpperCase(), 50, 120, { align: 'center', width: 495 });
  doc.fontSize(30).fillColor(C.primary).font(fb)
     .text('Твій Дизайн', 50, 140, { align: 'center', width: 495 });
  doc.fontSize(30).fillColor(C.primary).font(fb)
     .text('Людини', 50, 174, { align: 'center', width: 495 });

  // Name block
  doc.fontSize(22).fillColor(C.gold).font(fr)
     .text(name || 'Клієнт', 50, 230, { align: 'center', width: 495 });

  // Parameters table
  const params = [
    ['Тип',          reading.hd_type || '—'],
    ['Профіль',      reading.profile || '—'],
    ['Авторитет',    reading.authority || '—'],
    ['Визначеність', reading.definition || '—'],
  ];
  let py = 285;
  params.forEach(([k, v]) => {
    doc.fontSize(8).fillColor(C.muted).font(fb)
       .text(k.toUpperCase() + ':', 100, py, { continued: true, width: 130 });
    doc.fontSize(9).fillColor(C.primary).font(fb)
       .text('  ' + v, { width: 300 });
    py = doc.y + 3;
  });

  // Cross
  if (reading.incarnation_cross) {
    doc.fontSize(8).fillColor(C.muted).font(fr)
       .text('ІНКАРНАЦІЙНИЙ ХРЕСТ', 50, py + 8, { align: 'center', width: 495 });
    doc.fontSize(11).fillColor(C.primary).font(fb)
       .text(reading.incarnation_cross, 50, py + 22, { align: 'center', width: 495 });
  }

  // Birth data
  const birthStr = [birth_date, birth_time, birth_place].filter(Boolean).join('  ·  ');
  doc.fontSize(8).fillColor(C.muted).font(fr)
     .text(birthStr, 50, 520, { align: 'center', width: 495 });

  // Pages note
  doc.fontSize(8).fillColor(C.muted).font(fr)
     .text(pages + '  ·  PDF на пошту', 50, 540, { align: 'center', width: 495 });

  // Bodygraph
  drawCoverBodygraph(doc, flow, reading.activated_gates || [], 170, 575, 255, 200);

  flow.pageNum = 1;
}

// ── Simplified bodygraph for cover ───────────────────────────
function drawCoverBodygraph(doc, flow, gates, x, y, w, h) {
  try {
    const { getDefinedCenters, CENTER_GATES, CHANNELS } = require('./bodygraph');
    const defined = getDefinedCenters(gates);
    const scale = w / 420;

    const centers = {
      head:   [180, 20,  60, 38],
      ajna:   [180, 78,  60, 38],
      throat: [175,152,  70, 38],
      g:      [165,222,  90, 48],
      heart:  [285,222,  60, 38],
      sp:     [285,294,  60, 52],
      sacral: [165,308,  90, 48],
      spleen: [ 60,222,  60, 52],
      root:   [165,392,  90, 44],
    };
    const labels = {
      head:'Голова', ajna:'Аджна', throat:'Горло', g:'G', heart:'Серце',
      sp:'Емоції', sacral:'Сакрал', spleen:'Сел.', root:'Корінь'
    };

    // Channels
    for (const ch of CHANNELS) {
      if (!gates.includes(ch[0]) || !gates.includes(ch[1])) continue;
      const c1 = Object.keys(CENTER_GATES).find(c => CENTER_GATES[c].includes(ch[0]));
      const c2 = Object.keys(CENTER_GATES).find(c => CENTER_GATES[c].includes(ch[1]));
      if (!c1 || !c2 || c1 === c2 || !centers[c1] || !centers[c2]) continue;
      const [cx1, cy1, cw1, ch1] = centers[c1];
      const [cx2, cy2, cw2, ch2] = centers[c2];
      doc.moveTo(x + (cx1+cw1/2)*scale, y + (cy1+ch1/2)*scale)
         .lineTo(x + (cx2+cw2/2)*scale, y + (cy2+ch2/2)*scale)
         .lineWidth(2).stroke(C.gold);
    }

    // Centers
    for (const [name, [cx, cy, cw, ch]] of Object.entries(centers)) {
      const px = x + cx*scale, py2 = y + cy*scale;
      const pw = cw*scale, ph = ch*scale;
      const isDef = defined.has(name);
      doc.roundedRect(px, py2, pw, ph, 4)
         .fillAndStroke(isDef ? '#E4DEF8' : '#F5F3FC', isDef ? C.primary : '#C8C0E0');
      doc.fontSize(6.5).fillColor(isDef ? C.primary : C.muted).font(flow ? flow.F : 'Helvetica')
         .text(labels[name]||name, px, py2+ph/2-4, { width: pw, align: 'center' });
    }
  } catch(e) {
    // Silently skip if bodygraph module not available
  }
}

// ════════════════════════════════════════════════════════════════
//  FULL READING renderer
// ════════════════════════════════════════════════════════════════
function renderFull(flow, reading, order) {
  const { name } = order;

  // ── CHAPTER 1: Вступ + Тип ──────────────────────────────────
  flow.newPage();
  flow.sectionTitle(`✦ Персональний вступ`, 'gold');
  flow.para(reading.intro_text);
  flow.space(8);

  flow.sectionTitle(`Твій тип — ${reading.hd_type}`);
  flow.para(reading.type_aura);
  flow.space(4);
  flow.subHeading('Твоя природа та внутрішній устрій');
  flow.para(reading.type_nature);
  flow.subHeading('Твої природні сильні сторони');
  flow.para(reading.type_strengths);
  flow.subHeading('Виклики та зони росту');
  flow.para(reading.type_challenges);

  flow.newPage();
  flow.sectionTitle(`Тип у різних сферах — ${reading.hd_type}`);
  flow.subHeading('Кар\'єра та реалізація');
  flow.para(reading.type_work);
  flow.subHeading('Стосунки та близькість');
  flow.para(reading.type_relationships);
  flow.subHeading('Сон та відновлення');
  flow.para(reading.type_sleep);
  flow.subHeading('Управління енергією');
  flow.para(reading.type_energy);
  flow.subHeading('Тіньовий бік — коли живеш не своїм дизайном');
  flow.para(reading.type_shadow);

  // ── CHAPTER 2: Авторитет ────────────────────────────────────
  flow.newPage();
  flow.sectionTitle(`✦ Твій авторитет — ${reading.authority}`);
  flow.para(reading.authority_nature);
  flow.subHeading('Як розпізнати сигнал авторитету');
  flow.para(reading.authority_recognition);
  flow.subHeading('Типові помилки');
  flow.para(reading.authority_mistakes);

  flow.newPage();
  flow.sectionTitle(`Практика роботи з авторитетом`);
  flow.para(reading.authority_practice);
  flow.subHeading('Авторитет у прийнятті рішень');
  flow.para(reading.authority_decisions);
  flow.space(10);
  flow.rule(C.borderGold);

  // ── CHAPTER 3: Стратегія ────────────────────────────────────
  flow.sectionTitle(`✦ Стратегія — ${reading.strategy}`);
  flow.para(reading.strategy_explanation);
  flow.subHeading('Приклади у житті');
  flow.para(reading.strategy_examples);
  flow.subHeading(`Стратегія у сфері "${LIFE_AREA_UA_[order.life_area] || order.life_area || ''}"`);
  flow.para(reading.strategy_life_area);

  flow.newPage();
  flow.sectionTitle('Підпис та Не-Я тема');
  flow.subHeading(`✦ Підпис (ти у потоці)`);
  flow.highlight(reading.signature, 'gold');
  flow.space(8);
  flow.subHeading('⚑ Не-Я тема (ти поза своїм дизайном)');
  flow.highlight(reading.not_self, 'primary');
  flow.space(10);
  if (Array.isArray(reading.not_self_signs) && reading.not_self_signs.length) {
    flow.label('Конкретні ознаки Не-Я стану:');
    reading.not_self_signs.forEach(s => flow.checkItem(s));
  }

  // ── CHAPTER 4: Профіль ──────────────────────────────────────
  flow.newPage();
  flow.sectionTitle(`✦ Профіль ${reading.profile} — Твоя роль у цьому житті`);
  flow.para(reading.profile_overview);

  flow.subHeading(`Перша лінія — ${reading.profile_line1_name || ''}`);
  flow.para(reading.profile_line1);

  flow.newPage();
  flow.subHeading(`Друга лінія — ${reading.profile_line2_name || ''}`);
  flow.para(reading.profile_line2);
  flow.subHeading('Взаємодія ліній');
  flow.para(reading.profile_interaction);

  flow.newPage();
  flow.sectionTitle('Профіль у різних сферах');
  flow.subHeading('Твоя роль у житті');
  flow.para(reading.profile_life_role);
  flow.subHeading('Профіль у стосунках');
  flow.para(reading.profile_relationships);
  flow.subHeading('Профіль у кар\'єрі');
  flow.para(reading.profile_career);
  flow.subHeading('Кондиціювання профілю');
  flow.para(reading.profile_conditioning);
  flow.subHeading('Автентичне вираження');
  flow.highlight(reading.profile_authentic, 'gold');

  // ── CHAPTER 5: Центри ───────────────────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ 9 Центрів — 9 сфер твого життя');
  flow.para(reading.centers_intro);

  const centerOrder = ['head','ajna','throat','g','heart','sp','sacral','spleen','root'];
  const definedSet  = new Set(reading.defined_centers || []);
  const centersData = reading.centers || {};

  for (const key of centerOrder) {
    flow.newPage();
    const cd = centersData[key];
    if (cd) {
      flow.centerBlock(cd, definedSet.has(key));
    } else {
      // Fallback for old field format
      const idx = centerOrder.indexOf(key) + 1;
      const oldName = reading[`center${idx}_name`];
      const oldDesc = reading[`center${idx}_description`];
      if (oldName) {
        flow.centerBlock({
          title: oldName,
          description: oldDesc,
          gifts: '',
          shadow: '',
          practice: ''
        }, definedSet.has(key));
      }
    }
  }

  // ── CHAPTER 6: Канали ───────────────────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ Твої активні канали — природні переваги');
  flow.para(reading.channels_intro);
  flow.space(8);

  const channelDetails = reading.channels_detail || [];
  if (channelDetails.length) {
    channelDetails.forEach(ch => {
      flow.newPage();
      flow.channelBlock(ch);
    });
  } else if (reading.channels_description) {
    flow.para(reading.channels_description);
  } else {
    flow.para('Канали визначають фіксовані енергії у твоїй карті. Детальний аналіз активних каналів доступний у повній версії.');
  }

  // ── CHAPTER 7: Планети ──────────────────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ Планети та вузли — глибше розуміння');
  flow.para(reading.planets_intro);
  flow.space(8);

  const planets = reading.planets || {};
  const planetRows = [
    ['Сонце Особистості', reading.planet_sun_p || planets.sun_personality],
    ['Земля Особистості', reading.planet_earth_p || planets.earth_personality],
    ['Сонце Дизайну',    reading.planet_sun_d  || planets.sun_design],
    ['Земля Дизайну',    reading.planet_earth_d|| planets.earth_design],
    ['Місяць',           reading.planet_moon   || planets.moon],
    ['Вузли (Північ/Південь)', reading.planet_nodes || planets.north_node],
  ];
  for (const [lbl, txt] of planetRows) {
    if (txt) {
      flow.planetBlock(lbl, txt);
      flow.space(6);
    }
  }

  flow.newPage();
  flow.sectionTitle('Особисті планети — характер та поведінка');
  const personalPlanets = [
    ['Меркурій — Комунікація', reading.planet_mercury || planets.mercury],
    ['Венера — Цінності та краса', reading.planet_venus || planets.venus],
    ['Марс — Рушійна сила', reading.planet_mars || planets.mars],
    ['Юпітер — Удача та мудрість', reading.planet_jupiter || planets.jupiter],
    ['Сатурн — Структура та уроки', reading.planet_saturn || planets.saturn],
  ];
  for (const [lbl, txt] of personalPlanets) {
    if (txt) {
      flow.planetBlock(lbl, txt);
      flow.space(6);
    }
  }

  // ── CHAPTER 8: Інкарнаційний хрест ─────────────────────────
  flow.newPage();
  flow.sectionTitle(`✦ Інкарнаційний хрест — ${reading.incarnation_cross || ''}`);
  flow.para(reading.incarnation_cross_intro);
  flow.space(6);

  flow.sectionTitle('Значення твого хреста', 'gold');
  flow.para(reading.incarnation_cross_meaning || reading.incarnation_cross_description);
  flow.subHeading('Ворота хреста та їх значення');
  flow.para(reading.incarnation_cross_gates);
  flow.subHeading('Місія та внесок у світ');
  flow.para(reading.incarnation_cross_mission);

  // ── CHAPTER 9: Автоматичні реакції ─────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ Автоматичні реакції — скриті козирі');
  flow.para(reading.auto_reactions);
  flow.space(6);
  if (Array.isArray(reading.auto_examples) && reading.auto_examples.length) {
    flow.label('Конкретні прояви:');
    reading.auto_examples.forEach(ex => flow.checkItem(ex));
  }
  flow.space(10);
  flow.sectionTitle('✦ Самодостатність');
  flow.para(reading.self_sufficiency);
  flow.subHeading('Джерела ресурсності');
  flow.para(reading.self_resource);

  // ── CHAPTER 10: Декондиціювання ─────────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ Практики декондиціювання', 'gold');
  flow.para(reading.deconditioning_intro);
  flow.space(8);

  const practices = reading.deconditioning_practices || [];
  practices.forEach((p, i) => flow.practiceBlock(p, i + 1));

  // ── CHAPTER 11: 90-денний план ──────────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ Особистий план на 90 днів', 'gold');
  flow.para(reading.plan_intro);
  flow.space(8);
  flow.planBlock('Тиждень 1 — Спостереження', reading.plan_week1);
  flow.planBlock('Тиждень 2 — Стратегія у дії', reading.plan_week2);
  flow.newPage();
  flow.planBlock('Тиждень 3 — Робота з центрами', reading.plan_week3);
  flow.planBlock('Тиждень 4 — Інтеграція', reading.plan_week4);
  flow.planBlock('Місяць 2 — Поглиблення', reading.plan_month2);
  flow.planBlock('Місяць 3 — Нова ідентичність', reading.plan_month3);

  // ── CHAPTER 12: Рекомендації ────────────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ Персональні рекомендації');
  flow.para(reading.life_theme);
  flow.space(8);
  flow.label('Конкретні кроки для тебе:');
  (reading.recommendations || []).forEach(r => flow.checkItem(r));
}

// ════════════════════════════════════════════════════════════════
//  BASIC READING renderer
// ════════════════════════════════════════════════════════════════
function renderBasic(flow, reading, order) {
  // ── CHAPTER 1: Вступ + Тип ──────────────────────────────────
  flow.newPage();
  flow.sectionTitle(`✦ Персональний вступ`, 'gold');
  flow.para(reading.intro_text);
  flow.space(8);

  flow.sectionTitle(`Твій тип — ${reading.hd_type}`);
  flow.para(reading.type_aura);
  flow.subHeading('Твоя природа');
  flow.para(reading.type_nature);
  flow.subHeading('Виклики та зони росту');
  flow.para(reading.type_challenges);

  flow.newPage();
  flow.sectionTitle('Тип у різних сферах');
  flow.subHeading('Кар\'єра');
  flow.para(reading.type_work);
  flow.subHeading('Стосунки');
  flow.para(reading.type_relationships);
  flow.subHeading('Сон та енергія');
  flow.para(reading.type_sleep);
  flow.para(reading.type_energy);

  // ── CHAPTER 2: Авторитет + Стратегія ───────────────────────
  flow.newPage();
  flow.sectionTitle(`✦ Авторитет — ${reading.authority}`);
  flow.para(reading.authority_nature);
  flow.subHeading('Практика роботи з авторитетом');
  flow.para(reading.authority_practice);
  flow.subHeading('Прийняття рішень');
  flow.para(reading.authority_decisions);
  flow.space(10);
  flow.rule();

  flow.sectionTitle(`✦ Стратегія — ${reading.strategy}`);
  flow.para(reading.strategy_explanation);
  flow.subHeading('Приклади');
  flow.para(reading.strategy_examples);

  flow.newPage();
  flow.sectionTitle('Підпис та Не-Я');
  flow.subHeading('✦ Підпис — ти у потоці');
  flow.highlight(reading.signature || reading.signature_extended, 'gold');
  flow.space(6);
  flow.subHeading('⚑ Не-Я тема');
  flow.highlight(reading.not_self, 'primary');
  if (Array.isArray(reading.not_self_signs)) {
    flow.space(4);
    reading.not_self_signs.forEach(s => flow.checkItem(s));
  }

  // ── CHAPTER 3: Профіль ──────────────────────────────────────
  flow.newPage();
  flow.sectionTitle(`✦ Профіль ${reading.profile}`);
  flow.para(reading.profile_overview);
  flow.subHeading(`Перша лінія — ${reading.profile_line1_name || ''}`);
  flow.para(reading.profile_line1);

  flow.newPage();
  flow.subHeading(`Друга лінія — ${reading.profile_line2_name || ''}`);
  flow.para(reading.profile_line2);
  flow.subHeading('Профіль у стосунках');
  flow.para(reading.profile_relationships);
  flow.subHeading('Профіль у кар\'єрі');
  flow.para(reading.profile_career);

  // ── CHAPTER 4: Центри ───────────────────────────────────────
  flow.newPage();
  flow.sectionTitle('✦ Ключові центри — сфери твого життя');
  flow.para(reading.centers_intro);
  flow.space(8);

  const keyCenters = Array.isArray(reading.centers_key) ? reading.centers_key : [];
  const definedSet = new Set(reading.defined_centers || []);

  if (keyCenters.length) {
    keyCenters.forEach(cd => {
      flow.newPage();
      flow.centerBlock(cd, cd.defined !== false);
    });
  } else {
    // Fallback to old format
    for (let i = 1; i <= 5; i++) {
      const cn = reading[`center${i}_name`];
      const cd = reading[`center${i}_description`];
      if (cn) {
        flow.newPage();
        flow.centerBlock({ title: cn, description: cd }, true);
      }
    }
    if (reading.open_centers_description) {
      flow.sectionTitle('Відкриті центри');
      flow.para(reading.open_centers_description);
    }
  }

  // ── CHAPTER 5: Рекомендації + Завершення ───────────────────
  flow.newPage();
  flow.sectionTitle('✦ Тема та призначення');
  flow.para(reading.life_theme);
  flow.space(10);
  flow.sectionTitle('✦ Персональні рекомендації', 'gold');
  (reading.recommendations || []).forEach(r => flow.checkItem(r));
}

// ════════════════════════════════════════════════════════════════
//  Closing page (shared)
// ════════════════════════════════════════════════════════════════
function renderClosing(flow, reading, order) {
  flow.newPage();
  const doc = flow.doc;
  const y = Math.max(doc.y, 120);

  doc.rect(50, y, 495, 2).fill(C.gold);

  flow.space(20);
  doc.fontSize(18).fillColor(C.primary).font(flow.FB)
     .text('З теплом та повагою ✦', 50, doc.y, { align: 'center', width: 495 });
  flow.space(20);
  flow.para(reading.closing_message);
  flow.space(20);

  doc.fontSize(12).fillColor(C.gold).font(flow.FB)
     .text('Human Design UA', 50, doc.y, { align: 'center', width: 495 });
  doc.fontSize(9).fillColor(C.muted).font(flow.F)
     .text('humandesign.finance@gmail.com', 50, doc.y + 8, { align: 'center', width: 495 });
  doc.fontSize(8).fillColor(C.muted).font(flow.F)
     .text(`© ${new Date().getFullYear()} Human Design UA — персональна розшифровка для ${order.name || ''}`, 50, doc.y + 8, { align: 'center', width: 495 });
}

// Helper to avoid undefined ref
const LIFE_AREA_UA_ = {
  career:'Кар\'єра та гроші', relationships:'Стосунки та любов',
  self:'Самопізнання', energy:'Здоров\'я та енергія', purpose:'Призначення',
};

// ════════════════════════════════════════════════════════════════
//  MAIN export
// ════════════════════════════════════════════════════════════════
async function generateReadingPDF(order, reading) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({
        size: 'A4',
        margins: { top: 20, bottom: 40, left: 50, right: 50 },
        info: {
          Title: `Розшифровка Дизайну Людини — ${order.name || ''}`,
          Author: 'Human Design UA',
          Subject: reading.hd_type || '',
        },
        autoFirstPage: false,
      });

      const chunks = [];
      doc.on('data', chunk => chunks.push(chunk));
      doc.on('end', () => resolve(Buffer.concat(chunks)));
      doc.on('error', reject);

      const flow = new PDFFlow(doc, order.name, order.plan);

      // First page: add manually (cover)
      doc.addPage();
      flow.pageNum = 1;
      renderCover(doc, flow, order, reading);

      // Content pages
      if (order.plan === 'full') {
        renderFull(flow, reading, order);
      } else {
        renderBasic(flow, reading, order);
      }

      // Closing page
      renderClosing(flow, reading, order);

      // Draw footer on last page
      flow._drawFooter();

      doc.end();

    } catch(err) {
      reject(err);
    }
  });
}

module.exports = { generateReadingPDF };
