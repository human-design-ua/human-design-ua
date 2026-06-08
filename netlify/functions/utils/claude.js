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
  const filePath = path.join(__dirname, '..', '..', '..', 'prompts', file);
  return fs.readFileSync(filePath, 'utf8');
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

  const message = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: order.plan === 'full' ? 8000 : 5000,
    system: 'Ти — експерт з Дизайну Людини. Відповідай ТІЛЬКИ валідним JSON без markdown, без пояснень.',
    messages: [{ role: 'user', content: prompt }],
  });

  const raw = message.content[0].text.trim();

  // Strip markdown code fences if present
  const cleaned = raw.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```\s*$/i, '').trim();

  return JSON.parse(cleaned);
}

module.exports = { generateReading };
