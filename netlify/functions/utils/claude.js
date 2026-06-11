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

async function generateReading(order) {
  const prompt = buildPrompt(order);

  console.log(`Calling Claude API for ${order.email}, plan=${order.plan}`);

  const message = await client.messages.create({
    model: 'claude-sonnet-4-5',
    max_tokens: order.plan === 'full' ? 8000 : 5000,
    system: 'Ти — експерт з Дизайну Людини. Відповідай ТІЛЬКИ валідним JSON без markdown, без пояснень.',
    messages: [{ role: 'user', content: prompt }],
  });

  const raw = message.content[0].text.trim();
  console.log('Claude raw response (first 200 chars):', raw.slice(0, 200));

  // Strip markdown code fences if present
  const cleaned = raw
    .replace(/^```json\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/```\s*$/i, '')
    .trim();

  let parsed;
  try {
    parsed = JSON.parse(cleaned);
  } catch(e) {
    console.error('JSON parse failed:', e.message);
    console.error('Cleaned text (first 500):', cleaned.slice(0, 500));
    throw new Error('Claude вернул невалидный JSON: ' + e.message);
  }

  if (!parsed || typeof parsed !== 'object') {
    throw new Error('Claude вернул не объект: ' + typeof parsed);
  }

  console.log('Reading generated successfully, hd_type:', parsed.hd_type);
  return parsed;
}

module.exports = { generateReading };
