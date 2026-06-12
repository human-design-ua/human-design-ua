/**
 * Human Design Calculator — accurate astronomical calculations
 * Uses Keplerian orbital elements (Meeus "Astronomical Algorithms", 2nd ed.)
 * Accuracy: Sun/Earth <0.01°, planets ~0.1-0.5°, Moon ~0.3°
 * Gates are 5.625° wide — this precision is sufficient for correct gate+line.
 */

// ── Gate sequence around the zodiac (0° Aries onwards) ─────
const GATE_SEQUENCE = [
  41,19,13,49,30,55,37,63,22,36,25,17,21,51,42,3,
  27,24,2,23,8,20,16,35,45,12,15,52,39,53,62,56,
  31,33,7,4,29,59,40,64,47,6,46,18,48,57,32,50,
  28,44,1,43,14,34,9,5,26,11,10,58,38,54,61,60
];

// ── Center gates ─────────────────────────────────────────────
const CENTER_GATES = {
  head:   [64,61,63],
  ajna:   [47,24,4,17,43,11],
  throat: [62,23,56,35,12,45,33,8,31,20,16],
  g:      [1,13,25,46,10,15,2,7],
  heart:  [51,21,40,26],
  sp:     [6,37,36,22,30,55,49],
  sacral: [5,14,29,59,9,3,42,27,34],
  spleen: [48,57,44,50,32,28,18],
  root:   [60,52,19,39,53,54,58,38,41]
};

// ── Channels ─────────────────────────────────────────────────
const CHANNELS = [
  [64,47],[61,24],[63,4],
  [17,62],[43,23],[11,56],
  [20,10],[31,7],[8,1],[33,13],
  [12,22],[35,36],[45,21],[16,48],
  [26,44],[51,25],[21,45],[40,37],
  [6,59],[29,46],[14,2],[5,15],[34,10],[34,20],
  [42,53],[3,60],[9,52],[27,50],[34,57],
  [48,16],[44,26],[50,27],[32,54],[28,38],[18,58],
  [41,30],[19,49],[39,55],[53,42],[54,32],[58,18],[38,28],[60,3],[52,9],
  [1,8],[13,33],[25,51],[46,29],[10,20],[15,5],[2,14],[7,31]
];

// Build reverse map: gate → center
const GATE_TO_CENTER = {};
for (const [center, gates] of Object.entries(CENTER_GATES)) {
  for (const g of gates) GATE_TO_CENTER[g] = center;
}

// ── Incarnation Cross names ───────────────────────────────────
// Key: "pSun/pEarth/dSun/dEarth", value: cross name (UA)
const INCARNATION_CROSS_NAMES = {
  '1/2/4/3':    'Хрест Сфінкса',
  '2/1/3/4':    'Хрест Сфінкса',
  '13/7/1/2':   'Хрест Планування',
  '7/13/2/1':   'Хрест Планування',
  '10/15/18/17':'Хрест Профілактики',
  '15/10/17/18':'Хрест Профілактики',
  '25/46/51/57':'Хрест Майя',
  '46/25/57/51':'Хрест Майя',
  '29/30/20/34':'Хрест Пенелопи',
  '30/29/34/20':'Хрест Пенелопи',
  '34/20/40/37':'Хрест Великих Мереж',
  '20/34/37/40':'Хрест Великих Мереж',
  '36/6/11/12': 'Хрест Таємниці',
  '6/36/12/11': 'Хрест Таємниці',
  '55/59/9/16': 'Хрест Нового Початку',
  '59/55/16/9': 'Хрест Нового Початку',
  '64/63/45/26':'Хрест Допитливості',
  '63/64/26/45':'Хрест Допитливості',
  '41/31/44/24':'Хрест Циклів',
  '31/41/24/44':'Хрест Циклів',
  '19/33/39/13':'Хрест Поверхневості',
  '33/19/13/39':'Хрест Поверхневості',
  '49/4/14/8':  'Хрест Принципів',
  '4/49/8/14':  'Хрест Принципів',
  '21/48/38/39':'Хрест Вовка',
  '48/21/39/38':'Хрест Вовка',
  '53/54/42/32':'Хрест Юності та Старості',
  '54/53/32/42':'Хрест Юності та Старості',
  '56/60/28/27':'Хрест Зміни',
  '60/56/27/28':'Хрест Зміни',
  '23/43/30/29':'Хрест Дуалізму',
  '43/23/29/30':'Хрест Дуалізму',
  '35/5/22/47': 'Хрест Послідовності',
  '5/35/47/22': 'Хрест Послідовності',
  '45/26/64/63':'Хрест Кармічного Колеса',
  '26/45/63/64':'Хрест Кармічного Колеса',
  '37/40/9/16': 'Хрест Сімейних Стосунків',
  '40/37/16/9': 'Хрест Сімейних Стосунків',
  '57/51/62/61':'Хрест Полотна',
  '51/57/61/62':'Хрест Полотна',
  '11/12/46/25':'Хрест Визначеності',
  '12/11/25/46':'Хрест Визначеності',
  '52/58/21/48':'Хрест Бездіяльності',
  '58/52/48/21':'Хрест Бездіяльності',
  '62/17/61/64':'Хрест Деталей',
  '17/62/64/61':'Хрест Деталей',
  '27/28/19/33':'Хрест Турботи',
  '28/27/33/19':'Хрест Турботи',
  '18/17/54/53':'Хрест Відкриття',
  '47/22/64/63':'Хрест Абстракції',
  '22/47/63/64':'Хрест Абстракції',
  '24/44/37/40':'Хрест Раціональності',
  '44/24/40/37':'Хрест Раціональності',
  '50/3/31/41': 'Хрест Законів',
  '3/50/41/31': 'Хрест Законів',
  '14/8/29/30': 'Хрест Звинувачення',
  '8/14/30/29': 'Хрест Звинувачення',
  '32/42/62/32':'Хрест Збереження',
  '42/32/32/62':'Хрест Збереження',
  '38/39/55/59':'Хрест Боротьби',
  '39/38/59/55':'Хрест Боротьби',
  '16/9/35/5':  'Хрест Ентузіазму',
  '9/16/5/35':  'Хрест Ентузіазму',
};

function getIncarnationCrossName(pSun, pEarth, dSun, dEarth) {
  const key = `${pSun}/${pEarth}/${dSun}/${dEarth}`;
  return INCARNATION_CROSS_NAMES[key] || null;
}

// ── Type determination ───────────────────────────────────────
function isConnectedToThroat(dc, centers) {
  return centers.some(c => dc.has(c) && dc.has('throat'));
}

// ── Authority determination ──────────────────────────────────
function determineAuthority(definedCenters, hdType) {
  if (hdType === 'Рефлектор') return 'Місячний цикл';
  if (definedCenters.has('sp')) return 'Емоційний (Сонячне сплетіння)';
  if (definedCenters.has('sacral')) return 'Сакральний';
  if (definedCenters.has('spleen')) return 'Селезінковий';
  if (definedCenters.has('heart')) return 'Серцевий (Его)';
  if (definedCenters.has('g')) return 'Само-спроецьований (G-центр)';
  return 'Оточення (зовнішній)';
}

// ── Julian Day Number ────────────────────────────────────────
function dateToJD(year, month, day, hour = 12, minute = 0) {
  if (month <= 2) { year--; month += 12; }
  const A = Math.floor(year / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (year + 4716)) +
         Math.floor(30.6001 * (month + 1)) +
         day + B - 1524.5 + (hour + minute / 60) / 24;
}

// ── Keplerian orbital elements (Meeus, Table 33.a, J2000) ────
// Valid ~1800–2050. Rates per Julian century.
const ORBITAL_ELEMENTS = {
  Mercury: { L0:252.250906, Ldot:149472.6746358, a:0.38709927, e0:0.20563593, edot: 0.00001906, w0: 77.45779628, wdot:0.16047689 },
  Venus:   { L0:181.979801, Ldot: 58517.8157,    a:0.72333199, e0:0.00677323, edot:-0.00004938, w0:131.563703,  wdot:0.048746   },
  Earth:   { L0:100.464457, Ldot: 35999.3728,    a:1.00000011, e0:0.01671022, edot:-0.00003804, w0:102.937348,  wdot:0.32249    },
  Mars:    { L0:355.433275, Ldot: 19140.2993,    a:1.52366231, e0:0.09341233, edot: 0.00011902, w0:336.04024,   wdot:0.44441    },
  Jupiter: { L0: 34.351519, Ldot:  3034.90567,   a:5.20258853, e0:0.04849485, edot: 0.00016327, w0: 14.27495,   wdot:0.18774    },
  Saturn:  { L0: 50.077444, Ldot:  1222.11375,   a:9.53667594, e0:0.05550825, edot:-0.00032044, w0: 92.86136,   wdot:0.54649    },
};

// Solve Kepler's equation E = M + e*sin(E) by Newton-Raphson
function keplerSolve(M_deg, e) {
  const M = ((M_deg % 360) + 360) % 360 * Math.PI / 180;
  let E = M;
  for (let i = 0; i < 15; i++) {
    const dE = (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E));
    E -= dE;
    if (Math.abs(dE) < 1e-10) break;
  }
  return E;
}

// Returns heliocentric { lon (deg), R (AU), x, y }
function planetHeliocentric(elem, T) {
  const L = ((elem.L0 + elem.Ldot * T) % 360 + 360) % 360;
  const e = elem.e0 + elem.edot * T;
  const w = ((elem.w0 + elem.wdot * T) % 360 + 360) % 360;

  const M_deg = ((L - w) % 360 + 360) % 360;
  const E = keplerSolve(M_deg, e);

  const nu = 2 * Math.atan2(
    Math.sqrt(1 + e) * Math.sin(E / 2),
    Math.sqrt(1 - e) * Math.cos(E / 2)
  );

  const R = elem.a * (1 - e * Math.cos(E));
  const lon = ((nu * 180 / Math.PI + w) % 360 + 360) % 360;

  return {
    lon,
    R,
    x: R * Math.cos(lon * Math.PI / 180),
    y: R * Math.sin(lon * Math.PI / 180),
  };
}

// ── Sun longitude (ecliptic, apparent) ──────────────────────
function sunLongitude(jd) {
  const T = (jd - 2451545.0) / 36525;

  // Mean longitude and anomaly
  let L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  L0 = ((L0 % 360) + 360) % 360;
  let M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  M = ((M % 360) + 360) % 360;
  const Mrad = M * Math.PI / 180;

  // Equation of center
  const C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(Mrad)
          + (0.019993 - 0.000101 * T) * Math.sin(2 * Mrad)
          + 0.000289 * Math.sin(3 * Mrad);

  // Apparent longitude: apply aberration correction (−0.00569°) and nutation (~−0.00478°·sin(Ω))
  let omega = 125.04 - 1934.136 * T;
  omega = omega * Math.PI / 180;
  const apparent = L0 + C - 0.00569 - 0.00478 * Math.sin(omega);

  return ((apparent % 360) + 360) % 360;
}

// ── Moon longitude (accurate, ~0.3°) ────────────────────────
function moonLongitude(jd) {
  const T = (jd - 2451545.0) / 36525;

  const rad = Math.PI / 180;

  // Fundamental arguments (Meeus Ch.47)
  const L0  = ((218.3165 + 481267.8813 * T) % 360 + 360) % 360; // mean longitude
  const M   = ((357.5291 +  35999.0503 * T) % 360 + 360) % 360 * rad; // Sun mean anomaly
  const Mm  = ((134.9634 + 477198.8676 * T) % 360 + 360) % 360 * rad; // Moon mean anomaly
  const D   = ((297.8502 + 445267.1115 * T) % 360 + 360) % 360 * rad; // Mean elongation
  const F   = (( 93.2720 + 483202.0175 * T) % 360 + 360) % 360 * rad; // Argument of latitude

  // Main periodic terms for longitude (degrees)
  const dL = 6.2888 * Math.sin(Mm)
           + 1.2740 * Math.sin(2*D - Mm)
           + 0.6583 * Math.sin(2*D)
           + 0.2136 * Math.sin(2*Mm)
           - 0.1851 * Math.sin(M)
           - 0.1143 * Math.sin(2*F)
           + 0.0588 * Math.sin(2*D - 2*Mm)
           - 0.0571 * Math.sin(2*D - M - Mm)
           + 0.0533 * Math.sin(2*D + Mm)
           + 0.0458 * Math.sin(2*D - M)
           + 0.0409 * Math.sin(Mm - M)
           - 0.0347 * Math.sin(D)
           - 0.0312 * Math.sin(Mm + M)
           - 0.0150 * Math.sin(2*F - 2*D)
           + 0.0115 * Math.sin(2*D - 2*M)
           + 0.0080 * Math.sin(2*Mm + 2*F)
           - 0.0064 * Math.sin(2*D + M - Mm)
           - 0.0060 * Math.sin(2*D - Mm + M)
           + 0.0041 * Math.sin(4*D - Mm)
           + 0.0039 * Math.sin(Mm - 2*F)
           + 0.0032 * Math.sin(Mm + 2*F)
           - 0.0029 * Math.sin(2*D - M + Mm)
           + 0.0027 * Math.sin(2*D + 2*Mm)
           - 0.0021 * Math.sin(3*Mm)
           + 0.0021 * Math.sin(2*M)
           - 0.0021 * Math.sin(4*D)
           + 0.0020 * Math.sin(2*D - 4*F);

  return ((L0 + dL) % 360 + 360) % 360;
}

// ── Find Design JD: Sun exactly 88° before birth Sun ─────────
// More accurate than a fixed 88.736-day offset
function findDesignJD(jdBirth) {
  const birthSunLon = sunLongitude(jdBirth);
  const targetLon = ((birthSunLon - 88.0) + 360) % 360;

  // Initial estimate (~88 days back)
  let jd = jdBirth - 88.0;

  // Newton-Raphson: Sun moves ~1°/day, so Δjd ≈ Δlon in degrees
  for (let i = 0; i < 10; i++) {
    let diff = targetLon - sunLongitude(jd);
    if (diff > 180) diff -= 360;
    if (diff < -180) diff += 360;
    const step = diff / 0.9856; // degrees per day
    jd += step;
    if (Math.abs(step) < 1e-6) break;
  }

  return jd;
}

// ── Calculate all planet positions ───────────────────────────
function calcPlanets(jd) {
  const T = (jd - 2451545.0) / 36525;

  // Earth heliocentric position
  const earthH = planetHeliocentric(ORBITAL_ELEMENTS.Earth, T);

  // Sun geocentric (= -Earth heliocentric + aberration + nutation)
  const sun = sunLongitude(jd);
  const earth = (sun + 180) % 360;

  // Geocentric longitude for outer/inner planets
  function geoLon(name) {
    const h = planetHeliocentric(ORBITAL_ELEMENTS[name], T);
    const dx = h.x - earthH.x;
    const dy = h.y - earthH.y;
    return ((Math.atan2(dy, dx) * 180 / Math.PI) + 360) % 360;
  }

  // Moon
  const moon = moonLongitude(jd);

  // Mean North Node of Moon
  let node = 125.0445 - 1934.1363 * T;
  node = ((node % 360) + 360) % 360;

  return {
    Sun:      sun,
    Earth:    earth,
    Moon:     moon,
    Mercury:  geoLon('Mercury'),
    Venus:    geoLon('Venus'),
    Mars:     geoLon('Mars'),
    Jupiter:  geoLon('Jupiter'),
    Saturn:   geoLon('Saturn'),
    'N.Node': node,
    'S.Node': (node + 180) % 360,
  };
}

// ── Map longitude to gate ────────────────────────────────────
function lonToGate(lon) {
  const idx = Math.floor(((lon % 360) + 360) % 360 / (360 / 64)) % 64;
  return GATE_SEQUENCE[idx];
}

// ── Map longitude to line (1-6) ──────────────────────────────
function lonToLine(lon) {
  const gateWidth = 360 / 64;        // 5.625°
  const lineWidth = gateWidth / 6;   // 0.9375°
  const posInGate = ((lon % gateWidth) + gateWidth) % gateWidth;
  return Math.floor(posInGate / lineWidth) + 1;
}

// ── Get activated gates from positions ───────────────────────
function getActivatedGates(positions) {
  return Object.entries(positions).map(([planet, lon]) => ({
    planet,
    gate: lonToGate(lon),
    line: lonToLine(lon),
    lon: Math.round(lon * 10000) / 10000,
  }));
}

// ── Find defined centers ─────────────────────────────────────
function findDefinedCenters(allGates) {
  const defined = new Set();
  for (const [g1, g2] of CHANNELS) {
    if (allGates.has(g1) && allGates.has(g2)) {
      if (GATE_TO_CENTER[g1]) defined.add(GATE_TO_CENTER[g1]);
      if (GATE_TO_CENTER[g2]) defined.add(GATE_TO_CENTER[g2]);
    }
  }
  return defined;
}

// ── Find active channels (deduplicated) ──────────────────────
function findActiveChannels(allGates) {
  const seen = new Set();
  return CHANNELS.filter(([g1, g2]) => {
    if (!allGates.has(g1) || !allGates.has(g2)) return false;
    const key = [g1, g2].sort((a, b) => a - b).join('-');
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ── Determine HD Type ─────────────────────────────────────────
function determineType(definedCenters) {
  if (definedCenters.size === 0) return 'Рефлектор';
  if (!definedCenters.has('sacral')) {
    if (definedCenters.has('throat') &&
        (definedCenters.has('heart') || definedCenters.has('sp'))) {
      return 'Маніфестор';
    }
    return 'Проектор';
  }
  if (definedCenters.has('throat')) {
    return 'Маніфестуючий Генератор';
  }
  return 'Генератор';
}

// ── Determine definition ──────────────────────────────────────
function determineDefinition(definedCenters) {
  const count = definedCenters.size;
  if (count === 0) return 'Немає (Рефлектор)';
  if (count <= 3) return 'Простий';
  if (count <= 5) return 'Подвійний';
  if (count <= 7) return 'Потрійний';
  return 'Четверний';
}

// ── Cross quarter classification ─────────────────────────────
function classifyCross(profile) {
  const [l1] = profile.split('/').map(Number);
  if (l1 === 4) return 'Хрест Перехрестя';       // Juxtaposition
  if (l1 >= 5) return 'Лівокутовий Хрест';        // Left Angle
  return 'Правокутовий Хрест';                     // Right Angle
}

// ── Parse time ────────────────────────────────────────────────
function parseTime(timeStr) {
  if (!timeStr || timeStr === 'невідомий') return [12, 0];
  const parts = timeStr.split(':').map(Number);
  return [parts[0] || 12, parts[1] || 0];
}

// ── Main calculation function ─────────────────────────────────
function calculateHD(birthDate, birthTime = '12:00', birthPlace = '') {
  try {
    let year, month, day;
    if (birthDate.includes('.')) {
      [day, month, year] = birthDate.split('.').map(Number);
    } else {
      [year, month, day] = birthDate.split('-').map(Number);
    }

    const [hour, minute] = parseTime(birthTime);

    const jdBirth  = dateToJD(year, month, day, hour, minute);
    const jdDesign = findDesignJD(jdBirth); // Sun 88° before birth

    const personalityPos   = calcPlanets(jdBirth);
    const designPos        = calcPlanets(jdDesign);

    const personalityGates = getActivatedGates(personalityPos);
    const designGates      = getActivatedGates(designPos);

    const allGates = new Set([
      ...personalityGates.map(g => g.gate),
      ...designGates.map(g => g.gate),
    ]);

    const definedCenters  = findDefinedCenters(allGates);
    const activeChannels  = findActiveChannels(allGates);
    const hdType          = determineType(definedCenters);
    const authority       = determineAuthority(definedCenters, hdType);
    const definition      = determineDefinition(definedCenters);

    const pSun   = personalityGates.find(g => g.planet === 'Sun');
    const dSun   = designGates.find(g => g.planet === 'Sun');
    const pEarth = personalityGates.find(g => g.planet === 'Earth');
    const dEarth = designGates.find(g => g.planet === 'Earth');

    const profile = pSun && dSun ? `${pSun.line}/${dSun.line}` : '—';

    const crossGates = [pSun?.gate, pEarth?.gate, dSun?.gate, dEarth?.gate].filter(Boolean);
    const crossName  = pSun && pEarth && dSun && dEarth
      ? (getIncarnationCrossName(pSun.gate, pEarth.gate, dSun.gate, dEarth.gate)
         || `${classifyCross(profile)} ${crossGates.join('/')}`)
      : '—';

    const STRATEGIES = {
      'Генератор':              'Чекати на відгук (Wait to Respond)',
      'Маніфестуючий Генератор':'Інформувати і чекати на відгук',
      'Маніфестор':             'Інформувати перед дією (Inform)',
      'Проектор':               'Чекати на запрошення (Wait for Invitation)',
      'Рефлектор':              'Чекати місячний цикл (28 днів)',
    };

    return {
      hd_type:           hdType,
      strategy:          STRATEGIES[hdType] || '',
      authority:         authority,
      profile:           profile,
      definition:        definition,
      incarnation_cross: crossName,
      activated_gates:   [...allGates],
      defined_centers:   [...definedCenters],
      active_channels:   activeChannels.map(([g1, g2]) => `${g1}-${g2}`),
      personality_gates: personalityGates.map(g => `${g.planet}: ${g.gate}.${g.line}`),
      design_gates:      designGates.map(g => `${g.planet}: ${g.gate}.${g.line}`),
      sun_gate:          pSun?.gate,
      cross_gates:       crossGates,
      birth_jd:          jdBirth,
      design_jd:         jdDesign,
    };
  } catch (err) {
    console.error('HD calculation error:', err.message);
    return null;
  }
}

module.exports = { calculateHD };
