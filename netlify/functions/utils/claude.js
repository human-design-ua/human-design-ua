// Claude API — generate HD reading as structured JSON
const Anthropic = require('@anthropic-ai/sdk');
const fs = require('fs');
const path = require('path');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const LIFE_AREA_UA = {
  career:        'Кар\'єра та гроші',
  relationships: 'Стосунки та любов',
  self:          'Самопізнання',
  energy:        'Здоров\'я та енергія',
  purpose:       'Призначення та місія',
};

const CHALLENGE_UA = {
  decisions: 'Складно приймати рішення',
  fatigue:   'Постійна втома',
  purpose:   'Не розумію свого призначення',
  people:    'Конфлікти з людьми',
  self:      'Не приймаю себе',
};

function loadPrompt(plan) {
  const file = plan === 'full' ? 'reading_full_ua.md' : 'reading_basic_ua.md';
  // Try multiple paths — works both locally and on Netlify
  const candidates = [
    path.join(__dirname, '..', '..', '..', 'prompts', file),
    path.join(process.cwd(), 'prompts', file),
    path.join('/var/task', 'prompts', file),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return fs.readFileSync(p, 'utf8');
  }
  // Fallback — inline basic prompt if file not found
  console.warn('Prompt file not found, using inline fallback');
  return getFallbackPrompt(plan);
}

function getFallbackPrompt(plan) {
  return `Ти — експерт з Дизайну Людини з 15-річним досвідом.

## Дані клієнта
- Ім'я: {{NAME}}
- Дата народження: {{BIRTH_DATE}}
- Час народження: {{BIRTH_TIME}}
- Місце народження: {{BIRTH_PLACE}}
- Сфера уваги: {{LIFE_AREA}}
- Виклик: {{CHALLENGE}}

Згенеруй персоналізовану розшифровку Дизайну Людини УКРАЇНСЬКОЮ МОВОЮ.
Визнач Тип, Авторитет і Профіль на основі дати народження.
Зверни увагу на {{LIFE_AREA}} та {{CHALLENGE}}.

Відповідай ТІЛЬКИ валідним JSON:
{
  "hd_type": "Генератор",
  "strategy": "Чекати на відгук",
  "authority": "Сакральний",
  "profile": "2/4",
  "definition": "Простий",
  "incarnation_cross": "Хрест Планування",
  "intro_text": "Персоналізований вступ для {{NAME}}...",
  "type_description": "Опис типу...",
  "type_benefit": "Перевага типу...",
  "strategy_description": "Опис стратегії...",
  "strategy_benefit": "Перевага стратегії...",
  "authority_description": "Опис авторитету...",
  "authority_how_to": "Як застосовувати...",
  "authority_benefit": "Перевага авторитету...",
  "profile_description": "Опис профілю...",
  "profile_role": "Роль у житті...",
  "profile_benefit": "Перевага профілю...",
  "centers_overview": "Огляд центрів...",
  "centers_life_areas": "Центри та сфери...",
  "center1_name": "Сакральний центр",
  "center1_description": "Опис центру...",
  "center2_name": "Центр серця",
  "center2_description": "Опис центру...",
  "center3_name": "Центр самості",
  "center3_description": "Опис центру...",
  "center4_name": "Центр горла",
  "center4_description": "Опис центру...",
  "open_centers_description": "Відкриті центри...",
  "signature": "Задоволення та спокій...",
  "not_self": "Фрустрація та гнів...",
  "life_theme": "Тема для {{LIFE_AREA}} та {{CHALLENGE}}...",
  "recommendations": [
    "Рекомендація 1",
    "Рекомендація 2",
    "Рекомендація 3",
    "Рекомендація 4",
    "Рекомендація 5"
  ]
}`;
}

function buildPrompt(order) {
  const { name, birth_date, birth_time, birth_place, life_area, challenge, plan } = order;
  const template = loadPrompt(plan);

  return template
    .replace(/\{\{NAME\}\}/g,        name || 'Клієнт')
    .replace(/\{\{BIRTH_DATE\}\}/g,  birth_date || '')
    .replace(/\{\{BIRTH_TIME\}\}/g,  birth_time || 'невідомий')
    .replace(/\{\{BIRTH_PLACE\}\}/g, birth_place || '')
    .replace(/\{\{LIFE_AREA\}\}/g,   LIFE_AREA_UA[life_area] || life_area || '')
    .replace(/\{\{CHALLENGE\}\}/g,   CHALLENGE_UA[challenge] || challenge || '');
}

async function callClaude(prompt, maxTokens) {
  const message = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: maxTokens,
    system: 'Ти — експерт з Дизайну Людини. Відповідай ТІЛЬКИ валідним JSON без markdown, без пояснень. Не обривай JSON.',
    messages: [{ role: 'user', content: prompt }],
  });

  const raw = message.content[0].text.trim();
  console.log('Claude raw (first 300):', raw.slice(0, 300));

  const cleaned = raw
    .replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```\s*$/i, '').trim();

  try {
    return JSON.parse(cleaned);
  } catch(e) {
    console.error('JSON parse failed at pos:', e.message);
    // Try to fix truncated JSON by closing it
    const fixed = tryFixJson(cleaned);
    if (fixed) { console.log('JSON auto-fixed'); return fixed; }
    throw new Error('Invalid JSON: ' + e.message);
  }
}

function tryFixJson(str) {
  // Try to close unclosed JSON by finding last complete key-value pair
  try {
    // Find last complete field before truncation
    const lastComma = str.lastIndexOf('",');
    const lastBrace = str.lastIndexOf('"}');
    const cutAt = Math.max(lastComma, lastBrace);
    if (cutAt > 100) {
      const fixed = str.slice(0, cutAt + 1) + '}';
      return JSON.parse(fixed);
    }
  } catch(e) { /* ignore */ }
  return null;
}

async function generateReading(order) {
  const prompt = buildPrompt(order);
  console.log(`Calling Claude API for ${order.email}, plan=${order.plan}`);

  // Use 8192 (max) for both plans to avoid truncation
  const reading = await callClaude(prompt, 8192);

  if (!reading || !reading.hd_type) {
    throw new Error('Reading missing hd_type field');
  }

  // For full plan — generate extended part separately
  if (order.plan === 'full' && !reading.channels_description) {
    console.log('Generating extended part for full plan...');
    try {
      const extPrompt = buildExtendedPrompt(order, reading);
      const extended = await callClaude(extPrompt, 8192);
      Object.assign(reading, extended);
      console.log('Extended part merged');
    } catch(e) {
      console.warn('Extended part failed (non-fatal):', e.message);
    }
  }

  console.log('Reading generated! hd_type:', reading.hd_type);
  return reading;
}

function buildExtendedPrompt(order, basicReading) {
  const { name, birth_date, birth_time, birth_place, life_area, challenge } = order;
  return `Ти — експерт з Дизайну Людини. Клієнт: ${name || 'Клієнт'}, ${birth_date}, ${birth_time}, ${birth_place}.
Тип: ${basicReading.hd_type}, Профіль: ${basicReading.profile}, Авторитет: ${basicReading.authority}.
Сфера: ${LIFE_AREA_UA[life_area] || life_area}, Виклик: ${CHALLENGE_UA[challenge] || challenge}.

Згенеруй РОЗШИРЕНУ частину розшифровки (повний тариф) УКРАЇНСЬКОЮ МОВОЮ.
Відповідай ТІЛЬКИ валідним JSON:
{
  "channels_description": "5-6 речень про канали та ворота — які активовані, що означають для ${name}",
  "planets_description": "5-6 речень про планетарні активації — Сонце, Земля, Місяць, їх вплив",
  "incarnation_cross_description": "5-6 речень про інкарнаційний хрест ${basicReading.incarnation_cross} — тема життя, призначення",
  "conditioning_description": "5-6 речень про декондиціювання — що знімати, як прийти до себе",
  "relationships_description": "5-6 речень про стосунки — аура, притяжіння, сумісність для типу ${basicReading.hd_type}",
  "self_sufficiency": "4-5 речень про самодостатність ${name} — де черпати силу, ресурсність",
  "gift_meditation": "Персональна медитація-практика для ${name} (5-7 речень)",
  "gift_affirmations": ["Афірмація 1 для ${name}", "Афірмація 2", "Афірмація 3", "Афірмація 4", "Афірмація 5"]
}`;
}

module.exports = { generateReading };
