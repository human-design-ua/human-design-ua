/**
 * PDF Generator — Human Design Reading
 * Dark navy aesthetic · Playfair Display headers · DejaVu body (Cyrillic)
 * Space/Hubble imagery · Auto-pagination
 */
'use strict';
const PDFDocument = require('pdfkit');
const path = require('path');
const fs   = require('fs');

// ── Colour palette ────────────────────────────────────────────
const C = {
  bg:       '#0F1A2E',   // deep navy
  surface:  '#162138',   // slightly lighter navy
  cream:    '#E8DCC8',   // warm cream — main text
  gold:     '#C9A860',   // amber gold — accents
  muted:    '#8A8070',   // warm grey — labels
  line:     '#263552',   // subtle divider
  white:    '#F5F0E8',   // near-white
};

const UTILS = path.join(__dirname);

// ── Color helper ──────────────────────────────────────────────
function lightenHex(hex, amt = 70) {
  const r = Math.min(255, parseInt(hex.slice(1,3),16) + amt);
  const g = Math.min(255, parseInt(hex.slice(3,5),16) + amt);
  const b = Math.min(255, parseInt(hex.slice(5,7),16) + amt);
  return '#' + [r,g,b].map(v => v.toString(16).padStart(2,'0')).join('');
}

// ── Font loader (Buffer — works in Lambda) ────────────────────
function loadBuf(filename) {
  const candidates = [
    path.join(UTILS, filename),
    path.join(process.cwd(), 'netlify/functions/utils', filename),
    path.join('/var/task/netlify/functions/utils', filename),
  ];
  for (const p of candidates) {
    try { return fs.readFileSync(p); } catch(e) {}
  }
  console.warn('Font/image not found:', filename);
  return null;
}

// Pre-load at module level
const FONTS = {
  display:  loadBuf('PlayfairDisplay-Black.ttf'),
  bold:     loadBuf('PlayfairDisplay-Bold.ttf'),
  serif:    loadBuf('PlayfairDisplay-Regular.ttf'),
  sans:     loadBuf('DejaVuSans.ttf'),
  sansBold: loadBuf('DejaVuSans-Bold.ttf'),
};

// Space images (used as chapter dividers / cover)
const SPACE_IMGS = ['space_pillars.jpg','space_nebula_orion.jpg','space_andromeda.jpg',
                    'space_butterfly.jpg','space_cluster.jpg','space_cone.jpg'];

// ════════════════════════════════════════════════════════════════
//  PDFFlow — renderer with auto-pagination
// ════════════════════════════════════════════════════════════════
class PDFFlow {
  constructor(doc) {
    this.doc  = doc;
    this.pg   = 0;
    this.L    = 55;   // left margin
    this.W    = 485;  // content width
    this.SAFE = 800;  // page bottom limit

    // Register fonts
    const reg = (name, buf) => { if (buf) doc.registerFont(name, buf); };
    reg('PF-Display', FONTS.display);
    reg('PF-Bold',    FONTS.bold);
    reg('PF',         FONTS.serif);
    reg('DV',         FONTS.sans);
    reg('DV-Bold',    FONTS.sansBold);

    // Choose fallbacks if a font failed to load
    this.FD  = FONTS.display  ? 'PF-Display' : 'Helvetica-Bold';
    this.FB  = FONTS.bold     ? 'PF-Bold'    : 'Helvetica-Bold';
    this.FS  = FONTS.serif    ? 'PF'         : 'Helvetica';
    this.FDV = FONTS.sans     ? 'DV'         : 'Helvetica';
    this.FDB = FONTS.sansBold ? 'DV-Bold'    : 'Helvetica-Bold';

    doc.font(this.FDV); // default
    this._dirty = false; // tracks if current page has any content
  }

  // ── Page helpers ────────────────────────────────────────────
  _header() {
    this.doc.rect(0, 0, 595, 3).fill(C.gold);
    this.doc.rect(0, 3, 595, 842).fill(C.bg);
  }
  _footer(name) {
    const d = this.doc;
    d.rect(0, 818, 595, 24).fill(C.surface);
    d.font(this.FDV).fontSize(7).fillColor(C.muted)
     .text(`HUMAN DESIGN UA  ·  ${(name||'').toUpperCase()}  ·  ${this.pg}`,
           55, 825, { align: 'center', width: 485 });
  }

  newPage(name) {
    if (this.pg > 0) {
      if (!this._dirty) return this; // skip empty page
      this._footer(name || this._name);
    }
    this._myAddingPage = true;
    this.doc.addPage();
    this._myAddingPage = false;
    this.pg++;
    this._dirty = false;
    this._header();
    this.doc.y = 22;
    return this;
  }

  setName(n) { this._name = n; return this; }

  ensure(h) {
    if (this.doc.y + h > this.SAFE) this.newPage();
    return this;
  }

  // ── Typography ──────────────────────────────────────────────

  // Big chapter opener — full width title
  chapterTitle(line1, line2) {
    this.ensure(90);
    this._dirty = true;
    const d = this.doc;
    const y = d.y;
    d.font(this.FD).fontSize(38).fillColor(C.cream)
     .text(line1.toUpperCase(), this.L, y, { width: this.W });
    if (line2) {
      d.font(this.FS).fontSize(22).fillColor(C.gold)
       .text(line2, this.L, d.y + 2, { width: this.W });
    }
    d.rect(this.L, d.y + 8, this.W, 0.5).fill(C.gold);
    d.y += 18;
    return this;
  }

  // Section label (small uppercase)
  label(text) {
    this.ensure(22);
    this._dirty = true;
    this.doc.font(this.FDB).fontSize(8).fillColor(C.gold)
       .text(text.toUpperCase(), this.L, this.doc.y, { characterSpacing: 2, width: this.W });
    this.doc.y += 6;
    return this;
  }

  // Sub-heading inside section
  heading(text) {
    this.ensure(30);
    this._dirty = true;
    this.doc.y += 8;
    this.doc.font(this.FB).fontSize(14).fillColor(C.cream)
       .text(text, this.L, this.doc.y, { width: this.W });
    this.doc.y += 4;
    return this;
  }

  // Body paragraph — DejaVu for Cyrillic
  para(text, opts = {}) {
    if (!text) return this;
    const clean = String(text)
      .replace(/Мінімум \d+ слів\.?/gi, '')
      .replace(/Минимум \d+ слов\.?/gi, '')
      .trim();
    if (clean.length < 4) return this;
    this._dirty = true;
    this.ensure(44);
    this.doc.font(this.FDV).fontSize(10).fillColor(C.cream)
       .text(clean, this.L + (opts.indent||0), this.doc.y, {
         width: this.W - (opts.indent||0),
         align: 'justify',
         lineGap: 3.5,
         paragraphGap: 0,
       });
    this.doc.y += 10;
    return this;
  }

  // Key=Value info row
  kv(key, val) {
    if (!val) return this;
    this.ensure(18);
    const d = this.doc;
    const y = d.y;
    d.font(this.FDB).fontSize(8).fillColor(C.muted)
     .text(key.toUpperCase() + '  ', this.L, y, { continued: true, characterSpacing: 1.5 });
    d.font(this.FDV).fontSize(10).fillColor(C.cream)
     .text(String(val), { width: this.W - 120 });
    d.y += 2;
    return this;
  }

  // Checkmark item
  check(text) {
    if (!text) return this;
    const clean = String(text).replace(/Мінімум \d+ слів\.?/gi,'').trim();
    if (!clean) return this;
    this._dirty = true;
    this.ensure(22);
    const d = this.doc, y = d.y;
    d.font(this.FB).fontSize(11).fillColor(C.gold).text('✦', this.L, y, { continued: true });
    d.font(this.FDV).fontSize(10).fillColor(C.cream)
     .text('  ' + clean, { width: this.W - 18, lineGap: 2 });
    d.y += 4;
    return this;
  }

  // Numbered step
  step(n, text) {
    if (!text) return this;
    this.ensure(20);
    const d = this.doc;
    d.font(this.FD).fontSize(13).fillColor(C.gold)
     .text(String(n).padStart(2,'0'), this.L, d.y, { continued: true, width: 28 });
    d.font(this.FDV).fontSize(10).fillColor(C.cream)
     .text('  ' + text, { width: this.W - 30, lineGap: 2 });
    d.y += 4;
    return this;
  }

  // Highlight quote box
  quote(text, style = 'gold') {
    if (!text) return this;
    const clean = String(text).replace(/Мінімум \d+ слів\.?/gi,'').trim();
    this._dirty = true;
    this.ensure(60);
    const d = this.doc;
    const y  = d.y;
    const lineHeight = 14;
    const rows = Math.ceil(clean.length / 55) + 1;
    const h  = Math.max(48, rows * lineHeight + 20);
    const accent = style === 'gold' ? C.gold : C.cream;
    d.rect(this.L, y, this.W, h).fill(C.surface);
    d.rect(this.L, y, 3, h).fill(accent);
    d.font(this.FDV).fontSize(10).fillColor(C.cream)
     .text(clean, this.L + 14, y + 12, { width: this.W - 20, lineGap: 3 });
    d.y = y + h + 10;
    return this;
  }

  // Thin divider line
  rule() {
    if (this.doc.y + 8 < this.SAFE) {
      this.doc.rect(this.L, this.doc.y + 4, this.W, 0.5).fill(C.line);
      this.doc.y += 14;
    }
    return this;
  }

  space(h = 10) {
    if (this.doc.y + h < this.SAFE) this.doc.y += h;
    return this;
  }

  // ── Space image divider ──────────────────────────────────────
  imageBreak(imgFile, caption) {
    this.newPage();
    const d = this.doc;
    const imgBuf = loadBuf(imgFile);
    if (imgBuf) {
      try {
        d.image(imgBuf, 0, 0, { width: 595, height: 220, align: 'center', valign: 'center' });
      } catch(e) {}
    }
    // Dark overlay
    d.rect(0, 0, 595, 220).fillOpacity(0.5).fill(C.bg);
    d.fillOpacity(1);
    if (caption) {
      d.font(this.FD).fontSize(32).fillColor(C.cream)
       .text(caption.toUpperCase(), 55, 80, { align: 'center', width: 485 });
    }
    d.y = 235;
    this._dirty = true; // image page always has content
    return this;
  }

  // ── Center block ─────────────────────────────────────────────
  centerBlock(cd, isDefined) {
    if (!cd) return this;
    this.ensure(50);
    const d   = this.doc;
    const y   = d.y;
    const acc = isDefined ? C.gold : C.muted;
    const status = isDefined ? 'ВИЗНАЧЕНИЙ' : 'ВІДКРИТИЙ';

    // Title bar
    d.rect(this.L, y, this.W, 28).fill(C.surface);
    d.rect(this.L, y, 3, 28).fill(acc);
    d.font(this.FB).fontSize(12).fillColor(isDefined ? C.cream : C.muted)
     .text((cd.title||'').toUpperCase(), this.L + 12, y + 8, { width: this.W - 100 });
    d.font(this.FDB).fontSize(7).fillColor(acc)
     .text(`[${status}]`, this.L + 12, y + 8, { align: 'right', width: this.W - 20 });
    d.y = y + 36;

    this.para(cd.description);
    if (cd.gifts) {
      this.label('Твої дари');
      this.para(cd.gifts, { indent: 8 });
    }
    if (cd.shadow) {
      this.label('Зона уважності');
      this.para(cd.shadow, { indent: 8 });
    }
    if (cd.practice) {
      this.label('Практика');
      this.quote(cd.practice, 'gold');
    }
    this.space(8);
    return this;
  }

  // ── Channel block ────────────────────────────────────────────
  channelBlock(ch) {
    if (!ch || !ch.description) return this;
    this.ensure(50);
    const d = this.doc, y = d.y;
    d.rect(this.L, y, this.W, 30).fill(C.surface);
    d.rect(this.L, y, 3, 30).fill(C.gold);
    d.font(this.FDB).fontSize(9).fillColor(C.gold)
     .text(`КАНАЛ ${ch.channel_id||''}`, this.L + 12, y + 6, { characterSpacing: 1 });
    d.font(this.FB).fontSize(13).fillColor(C.cream)
     .text(ch.channel_name||'', this.L + 12, y + 16, { width: this.W - 20 });
    d.y = y + 38;
    this.para(ch.description);
    if (ch.gifts) { this.label('Природні дари'); this.para(ch.gifts, { indent: 8 }); }
    if (ch.shadow) { this.label('Зона уважності'); this.para(ch.shadow, { indent: 8 }); }
    if (ch.how_to_use) { this.label('Як використовувати'); this.quote(ch.how_to_use); }
    this.space(10);
    return this;
  }

  // ── Planet entry ─────────────────────────────────────────────
  planet(title, text) {
    if (!text) return this;
    this.ensure(40);
    const d = this.doc;
    d.font(this.FB).fontSize(11).fillColor(C.gold)
     .text('◈  ' + title, this.L, d.y, { width: this.W });
    d.y += 2;
    this.para(text, { indent: 16 });
    return this;
  }

  // ── Practice block ───────────────────────────────────────────
  practiceBlock(p, i) {
    if (!p) return this;
    this.ensure(60);
    const d = this.doc, y = d.y;
    d.rect(this.L, y, this.W, 30).fill(C.surface);
    d.rect(this.L, y, 3, 30).fill(C.gold);
    d.font(this.FDB).fontSize(8).fillColor(C.gold)
     .text(`ПРАКТИКА ${i}`, this.L + 12, y + 5, { characterSpacing: 2 });
    d.font(this.FB).fontSize(12).fillColor(C.cream)
     .text(p.title||'', this.L + 12, y + 16, { width: this.W - 20 });
    d.y = y + 38;
    this.para(p.description);
    if (Array.isArray(p.steps) && p.steps.length) {
      this.label('Як виконувати:');
      p.steps.forEach((s, n) => this.step(n+1, s));
    }
    this.space(10);
    return this;
  }

  // ── 90-day plan block ────────────────────────────────────────
  planBlock(period, text) {
    if (!text) return this;
    this.ensure(50);
    const d = this.doc, y = d.y;
    d.rect(this.L, y, this.W, 26).fill(C.surface);
    d.rect(this.L, y, 3, 26).fill(C.gold);
    d.font(this.FDB).fontSize(9).fillColor(C.gold)
     .text(period.toUpperCase(), this.L + 12, y + 8, { characterSpacing: 2 });
    d.y = y + 33;
    this.para(text);
    return this;
  }
}

// ════════════════════════════════════════════════════════════════
//  COVER PAGE
// ════════════════════════════════════════════════════════════════
function renderCover(doc, flow, order, reading) {
  const { name, birth_date, birth_time, birth_place, plan } = order;
  const planLabel = plan === 'full' ? 'ПОВНА РОЗШИФРОВКА' : 'БАЗОВА РОЗШИФРОВКА';
  const pages     = plan === 'full' ? '~50 СТОРІНОК' : '~20 СТОРІНОК';

  // Full-page navy bg
  doc.rect(0, 0, 595, 842).fill(C.bg);
  doc.rect(0, 0, 595, 3).fill(C.gold);

  // Top space image with overlay
  const imgBuf = loadBuf('space_pillars.jpg');
  if (imgBuf) {
    try {
      doc.image(imgBuf, 0, 3, { width: 595, height: 260 });
      doc.rect(0, 3, 595, 260).fillOpacity(0.45).fill(C.bg);
      doc.fillOpacity(1);
    } catch(e) {}
  }

  // Brand label
  doc.font(flow.FDB).fontSize(9).fillColor(C.gold)
     .text('HUMAN DESIGN UA', 55, 30, { align: 'center', width: 485, characterSpacing: 4 });

  // Main title
  doc.font(flow.FD).fontSize(56).fillColor(C.cream)
     .text('ТВІЙ', 55, 60, { align: 'center', width: 485 });
  doc.font(flow.FD).fontSize(56).fillColor(C.cream)
     .text('ДИЗАЙН', 55, 116, { align: 'center', width: 485 });
  doc.font(flow.FS).fontSize(26).fillColor(C.gold)
     .text('Людини', 55, 175, { align: 'center', width: 485 });

  // Gold divider
  doc.rect(130, 215, 335, 0.8).fill(C.gold);

  // Name
  doc.font(flow.FB).fontSize(22).fillColor(C.cream)
     .text(name || '', 55, 228, { align: 'center', width: 485 });

  // Params grid — 2×2
  const params = [
    ['ТИП',          reading.hd_type  || '—'],
    ['ПРОФІЛЬ',      reading.profile  || '—'],
    ['АВТОРИТЕТ',    reading.authority|| '—'],
    ['ВИЗНАЧЕНІСТЬ', reading.definition||'—'],
  ];

  let gy = 280;
  params.forEach(([k, v], i) => {
    const gx = i % 2 === 0 ? 90 : 340;
    if (i === 2) gy = 340;
    doc.font(flow.FDB).fontSize(7.5).fillColor(C.muted)
       .text(k, gx, gy, { characterSpacing: 1.5 });
    doc.font(flow.FB).fontSize(17).fillColor(C.cream)
       .text(v, gx, gy + 11);
  });

  // Cross
  doc.rect(90, 398, 415, 0.5).fill(C.line);
  doc.font(flow.FDB).fontSize(7.5).fillColor(C.muted)
     .text('ІНКАРНАЦІЙНИЙ ХРЕСТ', 90, 410, { characterSpacing: 1.5 });
  doc.font(flow.FB).fontSize(13).fillColor(C.gold)
     .text(reading.incarnation_cross || '—', 90, 424);

  // Birth data
  const bd = [birth_date, birth_time, birth_place].filter(Boolean).join('  ·  ');
  doc.font(flow.FDV).fontSize(9).fillColor(C.muted)
     .text(bd, 90, 455);

  // Bottom bodygraph area
  drawCoverBodygraph(doc, flow, reading.activated_gates || [], 90, 490, 200, 165);

  // Bottom right — plan info
  const bx = 320, by = 500;
  doc.rect(bx, by, 185, 140).fill(C.surface);
  doc.rect(bx, by, 2, 140).fill(C.gold);
  doc.font(flow.FDB).fontSize(7.5).fillColor(C.gold)
     .text(planLabel, bx + 12, by + 14, { characterSpacing: 1.5 });
  doc.font(flow.FDV).fontSize(8.5).fillColor(C.cream)
     .text(pages, bx + 12, by + 30);

  doc.rect(bx + 12, by + 50, 161, 0.5).fill(C.line);

  const includes = plan === 'full'
    ? ['Розшифровка бодиграфа','Тип та стратегія','Авторитет','Профіль',
       '9 Центрів','Планети','Канали','Хрест','90-денний план']
    : ['Розшифровка бодиграфа','Тип та стратегія','Авторитет','Профіль','Ключові центри'];
  let iy = by + 60;
  includes.forEach(item => {
    doc.font(flow.FDV).fontSize(7.5).fillColor(C.muted)
       .text('✦  ' + item, bx + 12, iy);
    iy += 13;
  });

  // Bottom gold line
  doc.rect(0, 829, 595, 13).fill(C.surface);
  doc.font(flow.FDV).fontSize(7).fillColor(C.muted)
     .text('humandesign.finance@gmail.com', 55, 836, { align: 'center', width: 485 });

  flow.pg = 1;
}

// ── Simplified bodygraph for cover ───────────────────────────
function drawCoverBodygraph(doc, flow, gates, x, y, w, h) {
  try {
    const { getDefinedCenters, CENTER_GATES, CHANNELS } = require('./bodygraph');
    const defined = getDefinedCenters(gates);
    const scale   = w / 420;
    const centers = {
      head:   [180,20,60,36], ajna:   [180,76,60,36],
      throat: [175,150,70,36], g:      [165,218,90,46],
      heart:  [287,218,60,36], sp:     [287,290,60,50],
      sacral: [165,304,90,46], spleen: [58,218,62,50],
      root:   [165,388,90,42],
    };
    const lbls = {
      head:'Голова', ajna:'Аджна', throat:'Горло', g:'G',
      heart:'Серце', sp:'Емоції', sacral:'Сакрал', spleen:'Сел.', root:'Корінь',
    };
    // Channels
    for (const ch of CHANNELS) {
      if (!gates.includes(ch[0]) || !gates.includes(ch[1])) continue;
      const c1 = Object.keys(CENTER_GATES).find(c => CENTER_GATES[c].includes(ch[0]));
      const c2 = Object.keys(CENTER_GATES).find(c => CENTER_GATES[c].includes(ch[1]));
      if (!c1||!c2||c1===c2||!centers[c1]||!centers[c2]) continue;
      const [cx1,cy1,cw1,ch1]=centers[c1], [cx2,cy2,cw2,ch2]=centers[c2];
      doc.moveTo(x+(cx1+cw1/2)*scale, y+(cy1+ch1/2)*scale)
         .lineTo(x+(cx2+cw2/2)*scale, y+(cy2+ch2/2)*scale)
         .lineWidth(1.5).stroke(C.gold);
    }
    // Centers
    for (const [nm,[cx,cy,cw,ch]] of Object.entries(centers)) {
      const px=x+cx*scale, py=y+cy*scale, pw=cw*scale, ph=ch*scale;
      const def=defined.has(nm);
      doc.roundedRect(px,py,pw,ph,3)
         .fillAndStroke(def?'#1E3560':'#152030', def?C.gold:C.line);
      doc.font(flow.FDV).fontSize(6).fillColor(def?C.gold:C.muted)
         .text(lbls[nm]||nm, px, py+ph/2-4, { width:pw, align:'center' });
    }
  } catch(e) {}
}

// ════════════════════════════════════════════════════════════════
//  FULL READING — renderer
// ════════════════════════════════════════════════════════════════
function renderFull(flow, reading, order) {
  const name = order.name || '';
  const spaceImgs = SPACE_IMGS.filter(f => loadBuf(f));
  let imgIdx = 0;
  const nextImg = () => spaceImgs[imgIdx++ % spaceImgs.length];

  // ─── 1. Вступ ────────────────────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Персональний', 'вступ');
  flow.para(reading.intro_text);

  // ─── 2. Тип ──────────────────────────────────────────────────
  flow.imageBreak(nextImg(), `Твій тип — ${reading.hd_type||''}`);

  flow.label('Твоя аура');
  flow.para(reading.type_aura);
  flow.heading('Твоя природа');
  flow.para(reading.type_nature);
  flow.heading('Природні сильні сторони');
  flow.para(reading.type_strengths);
  flow.heading('Виклики');
  flow.para(reading.type_challenges);

  flow.newPage();
  flow.chapterTitle(`Тип у різних`, 'сферах життя');
  flow.heading('Кар\'єра та реалізація');
  flow.para(reading.type_work);
  flow.heading('Стосунки та любов');
  flow.para(reading.type_relationships);
  flow.heading('Сон та відновлення');
  flow.para(reading.type_sleep);
  flow.heading('Управління енергією');
  flow.para(reading.type_energy);
  flow.heading('Тіньовий бік');
  flow.para(reading.type_shadow);

  // ─── 3. Авторитет ────────────────────────────────────────────
  flow.imageBreak(nextImg(), `Авторитет — ${reading.authority||''}`);

  flow.para(reading.authority_nature);
  flow.heading('Як розпізнати свій авторитет');
  flow.para(reading.authority_recognition);
  flow.heading('Типові помилки');
  flow.para(reading.authority_mistakes);
  flow.heading('Практика прийняття рішень');
  flow.para(reading.authority_practice);
  flow.para(reading.authority_decisions);

  // ─── 4. Стратегія ────────────────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Стратегія', reading.strategy||'');
  flow.para(reading.strategy_explanation);
  flow.heading('Приклади у реальному житті');
  flow.para(reading.strategy_examples);
  flow.para(reading.strategy_life_area);

  flow.newPage();
  flow.label('Твій підпис — ти у потоці');
  flow.quote(reading.signature, 'gold');
  flow.space(8);
  flow.label('Не-Я тема — коли ти не своя');
  flow.quote(reading.not_self, 'cream');
  flow.space(8);
  if (Array.isArray(reading.not_self_signs) && reading.not_self_signs.length) {
    flow.label('Конкретні ознаки');
    reading.not_self_signs.forEach(s => flow.check(s));
  }

  // ─── 5. Профіль ──────────────────────────────────────────────
  flow.imageBreak(nextImg(), `Профіль ${reading.profile||''}`);

  flow.para(reading.profile_overview);
  flow.heading(`Лінія 1 — ${reading.profile_line1_name||''}`);
  flow.para(reading.profile_line1);
  flow.newPage();
  flow.heading(`Лінія 2 — ${reading.profile_line2_name||''}`);
  flow.para(reading.profile_line2);
  flow.heading('Як лінії взаємодіють');
  flow.para(reading.profile_interaction);
  flow.heading('Твоя роль у житті');
  flow.para(reading.profile_life_role);
  flow.newPage();
  flow.heading('Профіль у стосунках');
  flow.para(reading.profile_relationships);
  flow.heading('Профіль у кар\'єрі');
  flow.para(reading.profile_career);
  flow.heading('Кондиціювання профілю');
  flow.para(reading.profile_conditioning);
  flow.heading('Як виглядає автентична ти');
  flow.quote(reading.profile_authentic, 'gold');

  // ─── 6. Центри ───────────────────────────────────────────────
  flow.imageBreak(nextImg(), '9 Центрів — 9 сфер');

  flow.para(reading.centers_intro);
  flow.space(8);

  const centersOrder = ['head','ajna','throat','g','heart','sp','sacral','spleen','root'];
  const definedSet   = new Set(reading.defined_centers || []);
  const centersData  = reading.centers || {};

  centersOrder.forEach(key => {
    flow.newPage();
    const cd = centersData[key];
    if (cd) {
      flow.centerBlock(cd, definedSet.has(key));
    } else {
      // fallback
      const i = centersOrder.indexOf(key) + 1;
      const cn = reading[`center${i}_name`], cdesc = reading[`center${i}_description`];
      if (cn) flow.centerBlock({ title: cn, description: cdesc }, definedSet.has(key));
    }
  });

  // ─── 7. Канали ───────────────────────────────────────────────
  flow.imageBreak(nextImg(), 'Твої канали');

  flow.para(reading.channels_intro);
  flow.space(8);
  const chDetails = reading.channels_detail || [];
  if (chDetails.length) {
    chDetails.forEach(ch => { flow.newPage(); flow.channelBlock(ch); });
  } else if (reading.channels_description) {
    flow.para(reading.channels_description);
  }

  // ─── 8. Планети ──────────────────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Планети', 'та вузли');
  flow.para(reading.planets_intro);
  flow.space(8);

  const planetRows = [
    ['Сонце Особистості — свідома тема',  reading.planet_sun_p],
    ['Земля Особистості — заземлення',    reading.planet_earth_p],
    ['Сонце Дизайну — несвідома тема',    reading.planet_sun_d],
    ['Земля Дизайну — тілесна мудрість',  reading.planet_earth_d],
    ['Місяць — рушійна сила',             reading.planet_moon],
    ['Вузли Місяця — напрямок та коріння', reading.planet_nodes],
  ];
  planetRows.forEach(([t, v]) => v && flow.planet(t, v));

  flow.newPage();
  flow.label('Особисті планети — характер');
  [
    ['Меркурій — комунікація та мислення', reading.planet_mercury],
    ['Венера — цінності та краса',         reading.planet_venus],
    ['Марс — рушійна сила та пристрасть',  reading.planet_mars],
    ['Юпітер — удача та мудрість',         reading.planet_jupiter],
    ['Сатурн — структура та уроки',        reading.planet_saturn],
  ].forEach(([t, v]) => v && flow.planet(t, v));

  // ─── 9. Інкарнаційний хрест ──────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Інкарнаційний', `хрест — ${reading.incarnation_cross||''}`);
  flow.para(reading.incarnation_cross_intro);
  flow.heading('Значення твого хреста');
  flow.para(reading.incarnation_cross_meaning || reading.incarnation_cross_description);
  flow.heading('Ворота хреста');
  flow.para(reading.incarnation_cross_gates);
  flow.heading('Твоя місія у світі');
  flow.para(reading.incarnation_cross_mission);

  // ─── 10. Автоматичні реакції ─────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Автоматичні', 'реакції');
  flow.para(reading.auto_reactions);
  flow.space(8);
  if (Array.isArray(reading.auto_examples)) {
    flow.label('Конкретні прояви');
    reading.auto_examples.forEach(e => flow.check(e));
  }
  flow.space(12);
  flow.chapterTitle('Самодостатність', '');
  flow.para(reading.self_sufficiency);
  flow.heading('Джерела ресурсності');
  flow.para(reading.self_resource);

  // ─── 11. Декондиціювання ─────────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Практики', 'декондиціювання');
  flow.para(reading.deconditioning_intro);
  flow.space(10);
  (reading.deconditioning_practices || []).forEach((p, i) => {
    flow.practiceBlock(p, i + 1);
  });

  // ─── 12. 90-денний план ──────────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Твій план', 'на 90 днів');
  flow.para(reading.plan_intro);
  flow.space(10);
  [
    ['Тиждень 1 — Спостереження', reading.plan_week1],
    ['Тиждень 2 — Стратегія у дії', reading.plan_week2],
    ['Тиждень 3 — Робота з центрами', reading.plan_week3],
    ['Тиждень 4 — Інтеграція', reading.plan_week4],
  ].forEach(([p, t]) => flow.planBlock(p, t));
  flow.newPage();
  [
    ['Місяць 2 — Поглиблення', reading.plan_month2],
    ['Місяць 3 — Нова ідентичність', reading.plan_month3],
  ].forEach(([p, t]) => flow.planBlock(p, t));

  // ─── 13. Рекомендації ────────────────────────────────────────
  flow.newPage();
  flow.chapterTitle('Персональні', 'рекомендації');
  flow.para(reading.life_theme);
  flow.space(12);
  flow.label('Конкретні кроки для тебе');
  (reading.recommendations || []).forEach(r => flow.check(r));
}

// ════════════════════════════════════════════════════════════════
//  BASIC READING — renderer
// ════════════════════════════════════════════════════════════════
function renderBasic(flow, reading, order) {
  const spaceImgs = SPACE_IMGS.filter(f => loadBuf(f));
  let imgIdx = 0;
  const nextImg = () => spaceImgs[imgIdx++ % spaceImgs.length];

  flow.newPage();
  flow.chapterTitle('Персональний', 'вступ');
  flow.para(reading.intro_text);

  flow.imageBreak(nextImg(), `Тип — ${reading.hd_type||''}`);
  flow.para(reading.type_aura);
  flow.heading('Твоя природа');
  flow.para(reading.type_nature);
  flow.heading('Кар\'єра');
  flow.para(reading.type_work);
  flow.heading('Стосунки');
  flow.para(reading.type_relationships);
  flow.heading('Сон та енергія');
  flow.para(reading.type_sleep);
  flow.para(reading.type_energy);
  flow.heading('Виклики');
  flow.para(reading.type_challenges);

  flow.newPage();
  flow.chapterTitle('Авторитет', reading.authority||'');
  flow.para(reading.authority_nature);
  flow.heading('Практика');
  flow.para(reading.authority_practice);
  flow.para(reading.authority_decisions);
  flow.rule();
  flow.chapterTitle('Стратегія', reading.strategy||'');
  flow.para(reading.strategy_explanation);
  flow.heading('Приклади');
  flow.para(reading.strategy_examples);

  flow.newPage();
  flow.label('Підпис — ти у потоці');
  flow.quote(reading.signature || reading.signature_extended, 'gold');
  flow.space(8);
  flow.label('Не-Я тема');
  flow.quote(reading.not_self, 'cream');
  if (Array.isArray(reading.not_self_signs)) {
    flow.space(6); reading.not_self_signs.forEach(s => flow.check(s));
  }

  flow.imageBreak(nextImg(), `Профіль ${reading.profile||''}`);
  flow.para(reading.profile_overview);
  flow.heading(`Лінія 1 — ${reading.profile_line1_name||''}`);
  flow.para(reading.profile_line1);
  flow.newPage();
  flow.heading(`Лінія 2 — ${reading.profile_line2_name||''}`);
  flow.para(reading.profile_line2);
  flow.heading('Профіль у стосунках');
  flow.para(reading.profile_relationships);
  flow.heading('Профіль у кар\'єрі');
  flow.para(reading.profile_career);

  flow.imageBreak(nextImg(), 'Центри');
  flow.para(reading.centers_intro);
  flow.space(8);
  const keyCenters = Array.isArray(reading.centers_key) ? reading.centers_key : [];
  const definedSet = new Set(reading.defined_centers || []);
  if (keyCenters.length) {
    keyCenters.forEach(cd => { flow.newPage(); flow.centerBlock(cd, cd.defined !== false); });
  } else {
    for (let i = 1; i <= 5; i++) {
      const cn = reading[`center${i}_name`], cd = reading[`center${i}_description`];
      if (cn) { flow.newPage(); flow.centerBlock({ title: cn, description: cd }, true); }
    }
  }

  flow.newPage();
  flow.chapterTitle('Тема', 'та призначення');
  flow.para(reading.life_theme);
  flow.space(12);
  flow.label('Персональні рекомендації');
  (reading.recommendations || []).forEach(r => flow.check(r));
}

// ════════════════════════════════════════════════════════════════
//  CLOSING PAGE
// ════════════════════════════════════════════════════════════════
function renderClosing(flow, reading, order) {
  flow.newPage();
  const d = flow.doc;

  // Space image background
  const imgBuf = loadBuf('space_cluster.jpg') || loadBuf('space_andromeda.jpg');
  if (imgBuf) {
    try {
      d.image(imgBuf, 0, 0, { width: 595, height: 280 });
      d.rect(0, 0, 595, 280).fillOpacity(0.5).fill(C.bg);
      d.fillOpacity(1);
    } catch(e) {}
  }

  d.y = 60;
  d.font(flow.FD).fontSize(36).fillColor(C.cream)
   .text('З ТЕПЛОМ', 55, 70, { align: 'center', width: 485 });
  d.font(flow.FS).fontSize(20).fillColor(C.gold)
   .text('та повагою до твого унікального Дизайну', 55, 115, { align: 'center', width: 485 });

  d.rect(130, 150, 335, 0.8).fill(C.gold);
  d.y = 290;

  flow.para(reading.closing_message);
  d.y += 20;
  d.font(flow.FB).fontSize(14).fillColor(C.gold)
   .text('Human Design UA', 55, d.y, { align: 'center', width: 485 });
  d.font(flow.FDV).fontSize(10).fillColor(C.muted)
   .text('humandesign.finance@gmail.com', 55, d.y + 16, { align: 'center', width: 485 });
  d.font(flow.FDV).fontSize(8).fillColor(C.line)
   .text(`© ${new Date().getFullYear()} Human Design UA — персональна розшифровка для ${order.name||''}`,
         55, d.y + 32, { align: 'center', width: 485 });
}

// ════════════════════════════════════════════════════════════════
//  PROFESSIONAL BODYGRAPH PAGE
// ════════════════════════════════════════════════════════════════

// Center geometry (absolute A4 page coords, bodygraph centered at x=298)
// Follows standard HD bodygraph proportions
const BG_CENTERS = {
  head:   { x:298, y: 92, w: 78, h: 72, s:'tu', n:'Голова',    sub:'Натхнення' },
  ajna:   { x:298, y:183, w: 70, h: 62, s:'td', n:'Аджна',     sub:'Ментал' },
  throat: { x:298, y:268, w: 76, h: 44, s:'r',  n:'Горло',     sub:'Вираження' },
  g:      { x:298, y:360, w: 90, h: 74, s:'d',  n:'G-центр',   sub:'Ідентичність' },
  heart:  { x:372, y:325, w: 46, h: 46, s:'d',  n:'Серце',     sub:'Воля' },
  sp:     { x:375, y:422, w: 68, h: 72, s:'tu', n:'Емоції',    sub:'Почуття' },
  sacral: { x:298, y:450, w: 78, h: 52, s:'r',  n:'Сакрал',    sub:'Жива сила' },
  spleen: { x:222, y:408, w: 68, h: 72, s:'td', n:'Сел-ка',    sub:'Інстинкт' },
  root:   { x:298, y:535, w: 76, h: 46, s:'r',  n:'Корінь',    sub:'Адреналін' },
};

const BG_DEF_COLORS = {
  head:'#4A3E8A', ajna:'#4A3E8A', throat:'#1E5A62',
  g:'#1E5232',   heart:'#7A1E1E', sp:'#7A4010',
  sacral:'#1A2E7A', spleen:'#2A5A22', root:'#5A3010',
};

// Channel routes — connection points between center borders
// Recalculated for updated center positions
const BG_ROUTES = [
  { k:'head-ajna',     p:[[298,128],[298,152]] },
  { k:'ajna-throat',   p:[[298,214],[298,246]] },
  { k:'throat-g',      p:[[298,290],[298,323]] },
  { k:'throat-heart',  p:[[334,268],[349,302]] },
  { k:'throat-sp',     p:[[334,268],[341,386]] },
  { k:'throat-spleen', p:[[262,268],[256,372]] },
  { k:'g-heart',       p:[[342,360],[349,302]] },
  { k:'g-sacral',      p:[[298,397],[298,424]] },
  { k:'sacral-throat', p:[[298,424],[298,290]] }, // channel 34-20
  { k:'heart-sp',      p:[[372,348],[375,386]] },
  { k:'heart-spleen',  p:[[349,302],[256,372]] },
  { k:'sp-sacral',     p:[[341,458],[334,450]] },
  { k:'sacral-spleen', p:[[260,450],[256,444]] },
  { k:'sacral-root',   p:[[298,476],[298,512]] },
  { k:'spleen-root',   p:[[222,444],[262,512]] },
  { k:'root-sp',       p:[[334,512],[341,458]] },
];

// Build channel → route map at module load
const BG_CHANNEL_ROUTE = {};
const _BG_ROUTE_CHANNELS = {
  'head-ajna':[[64,47],[61,24],[63,4]],
  'ajna-throat':[[17,62],[43,23],[11,56]],
  'throat-g':[[20,10],[31,7],[8,1],[33,13]],
  'throat-heart':[[45,21]],
  'throat-sp':[[12,22],[35,36]],
  'throat-spleen':[[16,48]],
  'g-heart':[[51,25]],
  'g-sacral':[[29,46],[14,2],[5,15],[34,10]],
  'sacral-throat':[[34,20]],
  'heart-sp':[[40,37]],
  'heart-spleen':[[26,44]],
  'sp-sacral':[[6,59]],
  'sacral-spleen':[[34,57]],
  'sacral-root':[[42,53],[3,60],[9,52],[27,50]],
  'spleen-root':[[32,54],[28,38],[18,58]],
  'root-sp':[[41,30],[19,49],[39,55]],
};
for (const [rk, chs] of Object.entries(_BG_ROUTE_CHANNELS)) {
  for (const [g1,g2] of chs) {
    BG_CHANNEL_ROUTE[Math.min(g1,g2)+'-'+Math.max(g1,g2)] = rk;
  }
}

function bgDrawCenter(d, key, c, isDefined, flow) {
  const { x, y, w, h, s, n, sub } = c;
  const x0 = x - w/2, y0 = y - h/2;
  const fill   = isDefined ? (BG_DEF_COLORS[key]||'#4A3E8A') : '#0D1628';
  const stroke = isDefined ? lightenHex(fill, 55) : '#1E2E46';

  switch(s) {
    case 'r':  d.roundedRect(x0, y0, w, h, 4); break;
    case 'd':  d.moveTo(x,y0).lineTo(x+w/2,y).lineTo(x,y0+h).lineTo(x-w/2,y).closePath(); break;
    case 'tu': d.moveTo(x,y0).lineTo(x+w/2,y0+h).lineTo(x-w/2,y0+h).closePath(); break;
    case 'td': d.moveTo(x,y0+h).lineTo(x+w/2,y0).lineTo(x-w/2,y0).closePath(); break;
  }
  d.fillAndStroke(fill, stroke);

  const labelY = s==='tu' ? y + h/2 - 18 : s==='td' ? y - h/2 + 5 : y - 8;
  d.font(flow.FDB).fontSize(6.5).fillColor(isDefined ? '#E8DCC8' : '#5A6A7A')
   .text(n, x0, labelY, { width:w, align:'center' });
  d.font(flow.FDV).fontSize(5).fillColor(isDefined ? '#C9A860' : '#2A3A4A')
   .text(sub, x0, labelY+9, { width:w, align:'center' });
}

function renderBodygraphPage(doc, flow, reading, order) {
  flow.newPage();
  flow._dirty = true;
  const d = doc;

  // Header
  d.font(flow.FDB).fontSize(8).fillColor(C.gold)
   .text('БОДИГРАФ  ·  КАРТА ДИЗАЙНУ ЛЮДИНИ', 55, 18, { characterSpacing:2, align:'center', width:485 });
  d.font(flow.FDV).fontSize(7.5).fillColor(C.muted)
   .text([order.name, order.birth_date, order.birth_time, order.birth_place].filter(Boolean).join('  ·  '),
         55, 29, { align:'center', width:485 });
  d.rect(55, 41, 485, 0.5).fill(C.gold);

  // Parse personality/design gate data
  const pGateMap = {}, dGateMap = {};
  (reading.personality_gates||[]).forEach(s => {
    const m = s.match(/(.+): (\d+)\.(\d+)/);
    if (m) pGateMap[+m[2]] = { planet:m[1], line:+m[3] };
  });
  (reading.design_gates||[]).forEach(s => {
    const m = s.match(/(.+): (\d+)\.(\d+)/);
    if (m) dGateMap[+m[2]] = { planet:m[1], line:+m[3] };
  });

  const allGateNums = [...new Set([...Object.keys(pGateMap).map(Number), ...Object.keys(dGateMap).map(Number)])];
  const { getDefinedCenters, CENTER_GATES, CHANNELS } = require('./bodygraph');
  const definedCenters = getDefinedCenters(allGateNums);

  // Draw inactive channel routes — very thin, barely visible
  BG_ROUTES.forEach(r => {
    const [[x1,y1],[x2,y2]] = r.p;
    d.moveTo(x1,y1).lineTo(x2,y2).lineWidth(0.8).stroke('#1E3050');
  });

  // Draw active channels
  const activeRoutes = new Map();
  CHANNELS.forEach(([g1,g2]) => {
    const rk = BG_CHANNEL_ROUTE[Math.min(g1,g2)+'-'+Math.max(g1,g2)];
    if (!rk) return;
    const hasP = pGateMap[g1] && pGateMap[g2];
    const hasD = dGateMap[g1] && dGateMap[g2];
    const anyActive = (pGateMap[g1]||dGateMap[g1]) && (pGateMap[g2]||dGateMap[g2]);
    if (!anyActive) return;
    const col = (hasP && hasD) ? '#8B6EE0' : hasP ? '#D0C8A0' : '#CC4040';
    if (!activeRoutes.has(rk) || col==='#8B6EE0') activeRoutes.set(rk, col);
  });
  activeRoutes.forEach((col, rk) => {
    const r = BG_ROUTES.find(x=>x.k===rk);
    if (!r) return;
    const [[x1,y1],[x2,y2]] = r.p;
    d.moveTo(x1,y1).lineTo(x2,y2).lineWidth(5).stroke(col);
  });

  // Draw centers
  Object.entries(BG_CENTERS).forEach(([key, c]) => {
    bgDrawCenter(d, key, c, definedCenters.has(key), flow);
  });

  // Draw active gate numbers around centers
  const PLANET_SYM = { Sun:'☉', Earth:'⊕', Moon:'☽', Mercury:'☿', Venus:'♀',
                       Mars:'♂', Jupiter:'♃', Saturn:'♄', 'N.Node':'☊', 'S.Node':'☋' };

  allGateNums.forEach(g => {
    const centerKey = Object.keys(CENTER_GATES).find(c => CENTER_GATES[c].includes(g));
    if (!centerKey) return;
    const c = BG_CENTERS[centerKey];
    if (!c) return;
    const gateList = CENTER_GATES[centerKey];
    const idx = gateList.indexOf(g);
    const total = gateList.length;
    const angle = (idx / total) * 2 * Math.PI - Math.PI / 2;
    const radius = (Math.max(c.w, c.h) / 2) + 9;
    const gx = c.x + Math.cos(angle) * radius;
    const gy = c.y + Math.sin(angle) * radius;
    // Skip if outside visible area
    if (gx < 60 || gx > 530 || gy < 50 || gy > 610) return;
    const col = (pGateMap[g] && dGateMap[g]) ? '#C9A860' : pGateMap[g] ? '#D0C8A0' : '#CC4040';
    d.font(flow.FDB).fontSize(5.5).fillColor(col)
     .text(String(g), gx - 6, gy - 4, { width:12, align:'center' });
  });

  // Left: DESIGN gates
  d.font(flow.FDB).fontSize(7.5).fillColor('#CC4040').text('ДИЗАЙН', 55, 50, { characterSpacing:1.5 });
  d.font(flow.FDV).fontSize(6).fillColor(C.muted).text('Несвідоме (червоне)', 55, 61);
  let ly = 76;
  (reading.design_gates||[]).forEach(s => {
    const m = s.match(/(.+): (\d+)\.(\d+)/);
    if (!m || ly > 600) return;
    const sym = PLANET_SYM[m[1]] || m[1].slice(0,3);
    d.font(flow.FDB).fontSize(7.5).fillColor('#CC4040').text(sym, 55, ly, { continued:true });
    d.font(flow.FDV).fontSize(7).fillColor(C.muted).text(`  ${m[2]}.${m[3]}`, { width:85 });
    ly = d.y + 1.5;
  });

  // Right: PERSONALITY gates
  d.font(flow.FDB).fontSize(7.5).fillColor(C.cream).text('ОСОБИСТІСТЬ', 452, 50, { align:'right', width:88, characterSpacing:1 });
  d.font(flow.FDV).fontSize(6).fillColor(C.muted).text('Свідоме (чорне)', 452, 61, { align:'right', width:88 });
  let ry = 76;
  (reading.personality_gates||[]).forEach(s => {
    const m = s.match(/(.+): (\d+)\.(\d+)/);
    if (!m || ry > 600) return;
    const sym = PLANET_SYM[m[1]] || m[1].slice(0,3);
    d.font(flow.FDV).fontSize(7).fillColor(C.muted).text(`${m[2]}.${m[3]}  `, 452, ry, { continued:true, align:'right', width:88 });
    d.font(flow.FDB).fontSize(7.5).fillColor(C.cream).text(sym, { align:'right', width:88 });
    ry = d.y + 1.5;
  });

  // ── Legend ────────────────────────────────────────────────────
  const LY = 605; // legend Y — well above page bottom
  d.rect(55, LY, 485, 0.5).fill(C.line);
  [[55,'#D0C8A0','Особистість'],[150,'#CC4040','Дизайн'],[230,'#8B6EE0','Обидва']].forEach(([lx,col,lbl]) => {
    d.rect(lx, LY+6, 18, 4).fill(col);
    d.font(flow.FDV).fontSize(6.5).fillColor(C.muted).text(lbl, lx+22, LY+4);
  });
  d.roundedRect(330,LY+4,9,7,2).fillAndStroke('#4A3E8A','#8A7ACA');
  d.font(flow.FDV).fontSize(6.5).fillColor(C.muted).text('Визначений', 343, LY+4);
  d.roundedRect(415,LY+4,9,7,2).fillAndStroke('#0D1628','#1E2E46');
  d.font(flow.FDV).fontSize(6.5).fillColor(C.muted).text('Відкритий', 428, LY+4);

  // ── Key parameters ───────────────────────────────────────────
  const PY = 624;
  d.rect(55, PY, 485, 0.5).fill(C.gold);
  const params = [
    ['ТИП', reading.hd_type||'—'],
    ['АВТОРИТЕТ', reading.authority||'—'],
    ['ПРОФІЛЬ', reading.profile||'—'],
    ['ВИЗНАЧЕНІСТЬ', reading.definition||'—'],
    ['ХРЕСТ', (reading.incarnation_cross||'—').slice(0,20)],
  ];
  params.forEach(([k,v],i) => {
    const px = 55 + i*(485/5);
    d.font(flow.FDB).fontSize(6).fillColor(C.muted).text(k, px, PY+6, {characterSpacing:1});
    d.font(flow.FB).fontSize(8).fillColor(C.cream).text(v, px, PY+16, {width:90});
  });

  // ── Active channels ──────────────────────────────────────────
  const chs = reading.active_channels||[];
  d.font(flow.FDB).fontSize(6).fillColor(C.muted)
   .text('АКТИВНІ КАНАЛИ:', 55, PY+40, {characterSpacing:1.5});
  d.font(flow.FDV).fontSize(7).fillColor(C.gold)
   .text(chs.length ? chs.join('  ✦  ') : '—', 55, PY+50, {width:485, lineBreak:false});

  // ── Defined centers ──────────────────────────────────────────
  const defNames = [...definedCenters].map(k=>BG_CENTERS[k]?.n||k).join('  ·  ');
  d.font(flow.FDB).fontSize(6).fillColor(C.muted)
   .text('ВИЗНАЧЕНІ ЦЕНТРИ:', 55, PY+65, {characterSpacing:1.5});
  d.font(flow.FDV).fontSize(7).fillColor('#8B6EE0')
   .text(defNames||'—', 55, PY+75, {width:485, lineBreak:false});

  // Lock cursor to prevent auto-page-add
  d.y = 760;
}

// ════════════════════════════════════════════════════════════════
//  MAIN EXPORT
// ════════════════════════════════════════════════════════════════
async function generateReadingPDF(order, reading) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({
        size: 'A4',
        autoFirstPage: false,
        margins: { top: 20, bottom: 40, left: 55, right: 55 },
        info: {
          Title:   `Дизайн Людини — ${order.name||''}`,
          Author:  'Human Design UA',
          Subject: reading.hd_type || '',
        },
      });

      const chunks = [];
      doc.on('data', c => chunks.push(c));
      doc.on('end',  () => resolve(Buffer.concat(chunks)));
      doc.on('error', reject);

      const flow = new PDFFlow(doc);
      flow.setName(order.name || '');

      // ── Intercept pdfkit auto-pages (text overflow) ─────────
      // pdfkit adds a page when text overflows — draw our navy bg on it
      doc.on('pageAdded', () => {
        if (flow._myAddingPage) return; // we added it ourselves — skip
        // Auto-added by pdfkit: draw background, advance counter
        flow.doc.rect(0, 0, 595, 842).fill(C.bg);
        flow.doc.rect(0, 0, 595, 3).fill(C.gold);
        flow.pg++;
        flow._dirty = false;
        flow.doc.y = 22;
      });

      // Cover
      doc.addPage();
      flow.pg = 1;
      renderCover(doc, flow, order, reading);

      // Bodygraph page (right after cover)
      renderBodygraphPage(doc, flow, reading, order);

      // Content
      if (order.plan === 'full') renderFull(flow, reading, order);
      else                        renderBasic(flow, reading, order);

      // Closing
      renderClosing(flow, reading, order);
      flow._footer(order.name || '');

      doc.end();
    } catch(err) {
      reject(err);
    }
  });
}

module.exports = { generateReadingPDF };
