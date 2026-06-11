// Human Design Bodygraph SVG Generator
// Generates accurate bodygraph based on activated gates

// ── Center positions (x, y, width, height) ─────────────────
const CENTERS = {
  head:   { x: 180, y: 20,  w: 60, h: 40, label: 'Голова',    shape: 'triangle-up' },
  ajna:   { x: 180, y: 80,  w: 60, h: 40, label: 'Аджна',     shape: 'triangle-down' },
  throat: { x: 175, y: 155, w: 70, h: 40, label: 'Горло',      shape: 'rect' },
  g:      { x: 165, y: 230, w: 90, h: 50, label: 'G-центр',    shape: 'diamond' },
  heart:  { x: 285, y: 230, w: 60, h: 40, label: 'Серце',      shape: 'triangle-down' },
  sp:     { x: 285, y: 305, w: 60, h: 55, label: 'Сонячне\nСплетіння', shape: 'triangle-up' },
  sacral: { x: 165, y: 320, w: 90, h: 50, label: 'Сакральний', shape: 'rect' },
  spleen: { x: 60,  y: 230, w: 60, h: 55, label: 'Селезінка',  shape: 'triangle-up' },
  root:   { x: 165, y: 405, w: 90, h: 45, label: 'Коренів',    shape: 'rect' },
};

// ── Gates belonging to each center ──────────────────────────
const CENTER_GATES = {
  head:   [64, 61, 63],
  ajna:   [47, 24, 4, 17, 43, 11],
  throat: [62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16],
  g:      [1, 13, 25, 46, 10, 15, 2, 7],
  heart:  [51, 21, 40, 26],
  sp:     [6, 37, 36, 22, 30, 55, 49],
  sacral: [5, 14, 29, 59, 9, 3, 42, 27, 34],
  spleen: [48, 57, 44, 50, 32, 28, 18],
  root:   [60, 52, 19, 39, 53, 54, 58, 38, 41],
};

// ── Channels (gate pairs) ────────────────────────────────────
const CHANNELS = [
  [64, 47], [61, 24], [63, 4],           // Head-Ajna
  [17, 62], [43, 23], [11, 56], [4, 63], // Ajna-Throat
  [20, 10], [31, 7], [8, 1], [33, 13],   // Throat-G
  [12, 22], [35, 36],                     // Throat-SP
  [45, 21],                               // Throat-Heart
  [16, 48],                               // Throat-Spleen
  [26, 44],                               // Heart-Spleen
  [51, 25],                               // Heart-G
  [21, 45],                               // Heart-Throat
  [40, 37],                               // Heart-SP
  [6, 59],                                // SP-Sacral
  [29, 46], [14, 2], [5, 15], [34, 10],  // Sacral-G
  [34, 20],                               // Sacral-Throat
  [42, 53], [3, 60], [9, 52], [27, 50],  // Sacral-Root
  [34, 57],                               // Sacral-Spleen
  [48, 16], [57, 34], [44, 26], [50, 27],// Spleen
  [32, 54], [28, 38], [18, 58],           // Spleen-Root
  [41, 30], [19, 49], [39, 55], [53, 42],// Root
  [54, 32], [58, 18], [38, 28], [60, 3], [52, 9],
];

// Build reverse: gate → center name
const GATE_TO_CENTER = {};
for (const [center, gates] of Object.entries(CENTER_GATES)) {
  for (const g of gates) GATE_TO_CENTER[g] = center;
}

// Center connection points for drawing channels
const CENTER_CONNECT = {
  head:   { bottom: [210, 60] },
  ajna:   { top: [210, 80], bottom: [210, 120] },
  throat: { top: [210, 155], bottom: [210, 195], left: [175, 175], right: [245, 175] },
  g:      { top: [210, 230], bottom: [210, 280], left: [165, 255], right: [255, 255] },
  heart:  { left: [285, 250], bottom: [315, 270], top: [315, 230] },
  sp:     { top: [315, 305], left: [285, 332] },
  sacral: { top: [210, 320], bottom: [210, 370], left: [165, 345], right: [255, 345] },
  spleen: { right: [120, 258], top: [90, 230], bottom: [90, 285] },
  root:   { top: [210, 405] },
};

function getCenterMidpoint(name) {
  const c = CENTERS[name];
  if (!c) return [210, 250];
  return [c.x + c.w / 2, c.y + c.h / 2];
}

function isChannelActive(ch, gates) {
  return gates.includes(ch[0]) && gates.includes(ch[1]);
}

function getDefinedCenters(gates) {
  const defined = new Set();
  for (const ch of CHANNELS) {
    if (isChannelActive(ch, gates)) {
      const c1 = GATE_TO_CENTER[ch[0]];
      const c2 = GATE_TO_CENTER[ch[1]];
      if (c1) defined.add(c1);
      if (c2) defined.add(c2);
    }
  }
  return defined;
}

function drawCenter(name, isDefined) {
  const c = CENTERS[name];
  const cx = c.x + c.w / 2;
  const cy = c.y + c.h / 2;
  const fill    = isDefined ? '#4B3F8A' : 'none';
  const stroke  = isDefined ? '#8B7FCC' : '#5A5080';
  const textCol = isDefined ? '#F0ECE8' : '#6B6090';
  const label   = c.label;

  let shape = '';
  if (c.shape === 'rect') {
    shape = `<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="6" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`;
  } else if (c.shape === 'diamond') {
    const pts = `${cx},${c.y} ${c.x + c.w},${cy} ${cx},${c.y + c.h} ${c.x},${cy}`;
    shape = `<polygon points="${pts}" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`;
  } else if (c.shape === 'triangle-up') {
    const pts = `${cx},${c.y} ${c.x + c.w},${c.y + c.h} ${c.x},${c.y + c.h}`;
    shape = `<polygon points="${pts}" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`;
  } else if (c.shape === 'triangle-down') {
    const pts = `${cx},${c.y + c.h} ${c.x + c.w},${c.y} ${c.x},${c.y}`;
    shape = `<polygon points="${pts}" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`;
  }

  const lines = label.split('\n');
  const textY = lines.length > 1 ? cy - 6 : cy;
  const text = lines.map((l, i) =>
    `<text x="${cx}" y="${textY + i * 12}" text-anchor="middle" fill="${textCol}" font-size="9" font-family="Arial,sans-serif">${l}</text>`
  ).join('');

  return shape + text;
}

function drawChannels(gates) {
  const lines = [];
  for (const ch of CHANNELS) {
    if (!isChannelActive(ch, gates)) continue;
    const c1 = GATE_TO_CENTER[ch[0]];
    const c2 = GATE_TO_CENTER[ch[1]];
    if (!c1 || !c2 || c1 === c2) continue;
    const [x1, y1] = getCenterMidpoint(c1);
    const [x2, y2] = getCenterMidpoint(c2);
    lines.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#8B6ECC" stroke-width="4" stroke-linecap="round" opacity="0.7"/>`);
  }
  return lines.join('\n');
}

function generateBodygraph(activatedGates = [], name = '') {
  const gates = Array.isArray(activatedGates) ? activatedGates.map(Number) : [];
  const defined = getDefinedCenters(gates);

  const centersSvg = Object.keys(CENTERS)
    .map(n => drawCenter(n, defined.has(n)))
    .join('\n');

  const channelsSvg = drawChannels(gates);

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 470" width="420" height="470" style="background:#F8F6FF;border-radius:12px;">
  <!-- Background -->
  <rect width="420" height="470" fill="#F8F6FF" rx="12"/>

  <!-- Title -->
  <text x="210" y="460" text-anchor="middle" fill="#4B3F8A" font-size="10" font-family="Arial,sans-serif" opacity="0.6">Бодиграф ${name ? '— ' + name : ''}</text>

  <!-- Channels (behind centers) -->
  ${channelsSvg}

  <!-- Centers -->
  ${centersSvg}

  <!-- Gate count -->
  <text x="10" y="465" fill="#9B90C0" font-size="8" font-family="Arial,sans-serif">Активних центрів: ${defined.size}/9</text>
</svg>`;
}

module.exports = { generateBodygraph, getDefinedCenters, CHANNELS, CENTER_GATES };
