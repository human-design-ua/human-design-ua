#!/usr/bin/env python3
"""
Human Design UA — Claude API Reading Generator
Calls Claude API to generate personalized HD reading content.

Usage (standalone test):
  python3 scripts/claude_reading.py --order HD-AI-TEST --name "Наталія" \
    --birth-date "2002-02-20" --birth-time "16:18" --birth-place "Україна" \
    --life-area career --challenge decisions --plan basic --locale ua
"""

import argparse
import json
import logging
import os
import re
import sys

# ─── Load .env ────────────────────────────────────────────────────────────────
def _load_env():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    # Always override — env var from file takes priority
                    os.environ[k] = v

_load_env()

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [claude_reading] %(message)s")
log = logging.getLogger(__name__)

# ─── Prompt files ─────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

def _read_prompt(filename: str) -> str:
    path = os.path.join(PROMPTS_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

# ─── Fallback content (returned when API unavailable) ────────────────────────
FALLBACK_BASIC = {
    "hd_type":             "[ТИП]",
    "strategy":            "[СТРАТЕГІЯ]",
    "authority":           "[АВТОРИТЕТ]",
    "profile":             "[ПРОФІЛЬ]",
    "definition":          "[ВИЗНАЧЕННЯ]",
    "incarnation_cross":   "[ХРЕСТ]",
    "intro_text":          "[Персональний вступ буде згенеровано Claude API]",
    "type_description":    "[Опис типу буде згенеровано Claude API]",
    "strategy_description":"[Опис стратегії буде згенеровано Claude API]",
    "authority_description":"[Опис авторитету буде згенеровано Claude API]",
    "authority_how_to":    "[Практичні поради авторитету — Claude API]",
    "profile_description": "[Опис профілю буде згенеровано Claude API]",
    "profile_role":        "[Роль профілю — Claude API]",
    "centers_overview":    "[Огляд центрів — Claude API]",
    "center1_name":        "[Центр 1]",
    "center1_description": "[Опис центру 1 — Claude API]",
    "center2_name":        "[Центр 2]",
    "center2_description": "[Опис центру 2 — Claude API]",
    "center3_name":        "[Центр 3]",
    "center3_description": "[Опис центру 3 — Claude API]",
    "center4_name":        "[Центр 4]",
    "center4_description": "[Опис центру 4 — Claude API]",
    "open_centers_description":"[Відкриті центри — Claude API]",
    "signature":           "[Сигнатура — Claude API]",
    "not_self":            "[Не-Я тема — Claude API]",
    "life_theme":          "[Тема життя — Claude API]",
    "recommendations":     [
        "[Рекомендація 1 — Claude API]",
        "[Рекомендація 2 — Claude API]",
        "[Рекомендація 3 — Claude API]",
        "[Рекомендація 4 — Claude API]",
        "[Рекомендація 5 — Claude API]",
        "[Рекомендація 6 — Claude API]",
        "[Рекомендація 7 — Claude API]",
        "[Рекомендація 8 — Claude API]",
        "[Рекомендація 9 — Claude API]",
        "[Рекомендація 10 — Claude API]",
    ],
    "week1": "[Тиждень 1 план — Claude API]",
    "week2": "[Тиждень 2 план — Claude API]",
    "week3": "[Тиждень 3 план — Claude API]",
    "week4": "[Тиждень 4 план — Claude API]",
    "closing_message": "[Персональне завершення — Claude API]",
}

FALLBACK_FULL = {
    **FALLBACK_BASIC,
    "all_9_centers": {
        "head":        "[Центр Голови — Claude API]",
        "ajna":        "[Аджна — Claude API]",
        "throat":      "[Горло — Claude API]",
        "g_center":    "[G-Центр — Claude API]",
        "heart":       "[Серце — Claude API]",
        "solar_plexus":"[Сонячне Сплетіння — Claude API]",
        "sacral":      "[Сакральний — Claude API]",
        "spleen":      "[Селезінка — Claude API]",
        "root":        "[Корінь — Claude API]",
    },
    "channels":                "[Канали — Claude API]",
    "cross_description":       "[Хрест деталі — Claude API]",
    "relationship_analysis":   "[Аналіз стосунків — Claude API]",
    "deconditioning_practices":[
        "[Практика 1]","[Практика 2]","[Практика 3]","[Практика 4]",
        "[Практика 5]","[Практика 6]","[Практика 7]",
    ],
    "plan_month1": "[Місяць 1 план — Claude API]",
    "plan_month2": "[Місяць 2 план — Claude API]",
    "plan_month3": "[Місяць 3 план — Claude API]",
}

# ─── Prompt builders ──────────────────────────────────────────────────────────

def _build_prompt(order_data: dict, plan: str) -> str:
    """Load prompt template from file and fill in order data."""
    locale = order_data.get("locale", "ua")

    if plan == "full":
        tpl_file = f"reading_full_{locale}.md"
        fallback_file = "reading_full_ua.md"
    else:
        tpl_file = f"reading_basic_{locale}.md"
        fallback_file = "reading_basic_ua.md"

    prompt = _read_prompt(tpl_file) or _read_prompt(fallback_file)

    if not prompt:
        # Inline minimal fallback prompt
        prompt = _inline_prompt(order_data, plan)
        return prompt

    # Replace placeholders
    replacements = {
        "{{NAME}}":        order_data.get("name", ""),
        "{{BIRTH_DATE}}":  order_data.get("birth_date", ""),
        "{{BIRTH_TIME}}":  order_data.get("birth_time", ""),
        "{{BIRTH_PLACE}}": order_data.get("birth_place", ""),
        "{{LIFE_AREA}}":   order_data.get("life_area", "career"),
        "{{CHALLENGE}}":   order_data.get("challenge", "decisions"),
        "{{PLAN}}":        plan,
    }
    for key, val in replacements.items():
        prompt = prompt.replace(key, str(val))

    return prompt


def _inline_prompt(order_data: dict, plan: str) -> str:
    """Minimal inline prompt when no prompt file found."""
    name        = order_data.get("name", "")
    birth_date  = order_data.get("birth_date", "")
    birth_time  = order_data.get("birth_time", "")
    birth_place = order_data.get("birth_place", "")
    life_area   = order_data.get("life_area", "career")
    challenge   = order_data.get("challenge", "decisions")
    locale      = order_data.get("locale", "ua")

    lang_map = {"ua": "Ukrainian", "ru": "Russian", "en": "English"}
    lang = lang_map.get(locale, "Ukrainian")

    full_fields = ""
    if plan == "full":
        full_fields = """
  "all_9_centers": {
    "head": "...", "ajna": "...", "throat": "...", "g_center": "...",
    "heart": "...", "solar_plexus": "...", "sacral": "...", "spleen": "...", "root": "..."
  },
  "channels": "2-3 main channels description",
  "cross_description": "Incarnation cross detailed (4-5 sentences)",
  "relationship_analysis": "Compatibility analysis based on type/profile (4-5 sentences)",
  "deconditioning_practices": ["practice1","practice2","practice3","practice4","practice5","practice6","practice7"],
  "plan_month1": "Month 1 awareness plan (3-4 sentences)",
  "plan_month2": "Month 2 practice plan (3-4 sentences)",
  "plan_month3": "Month 3 integration plan (3-4 sentences)","""

    return f"""You are an expert Human Design analyst. Generate a personalized Human Design reading in {lang}.

Person: {name}
Born: {birth_date} at {birth_time} in {birth_place}
Life focus: {life_area}
Challenge: {challenge}

Based on the birth data, determine the approximate Human Design type, authority, and profile,
then generate a complete personalized reading.

Respond ONLY with a valid JSON object (no markdown, no explanation):
{{
  "hd_type": "Generator|Manifesting Generator|Projector|Manifestor|Reflector",
  "strategy": "Strategy in {lang}",
  "authority": "Authority in {lang}",
  "profile": "X/Y",
  "definition": "Single|Split|Triple Split|Quadruple Split",
  "incarnation_cross": "Cross name",
  "intro_text": "2-3 sentences personalized intro for {name}",
  "type_description": "3-4 sentences about their specific type",
  "strategy_description": "3-4 sentences about their strategy in practice",
  "authority_description": "3-4 sentences about their authority",
  "authority_how_to": "3-4 sentences practical advice for using authority daily",
  "profile_description": "3-4 sentences about their profile",
  "profile_role": "3-4 sentences about their role in life",
  "centers_overview": "2-3 sentences about their centers configuration",
  "center1_name": "Name of first defined center",
  "center1_description": "3-4 sentences about this defined center",
  "center2_name": "Name of second defined center",
  "center2_description": "3-4 sentences",
  "center3_name": "Name of third defined center",
  "center3_description": "3-4 sentences",
  "center4_name": "Name of fourth defined center (or repeat center1 if fewer)",
  "center4_description": "3-4 sentences",
  "open_centers_description": "3-4 sentences about open/undefined centers",
  "signature": "2 sentences — emotional feeling when living in alignment",
  "not_self": "2 sentences — emotional signal when out of alignment",
  "life_theme": "4-5 sentences personalized to their {life_area} focus",
  "recommendations": ["rec1","rec2","rec3","rec4","rec5","rec6","rec7","rec8","rec9","rec10"],
  "week1": "Week 1 action plan (2-3 sentences)",
  "week2": "Week 2 action plan (2-3 sentences)",
  "week3": "Week 3 action plan (2-3 sentences)",
  "week4": "Week 4 action plan (2-3 sentences)",
  "closing_message": "3-4 sentences personal closing for {name}"{full_fields}
}}"""


# ─── JSON extraction ──────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Parse JSON from Claude response, handles markdown code blocks."""
    text = text.strip()

    # Strip leading ```json or ``` fence
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    # Strip trailing ``` fence
    if text.endswith('```'):
        text = re.sub(r'\n?```$', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first complete { ... } block
    m = re.search(r'\{[\s\S]+\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from Claude response")


# ─── Main API call ────────────────────────────────────────────────────────────

def get_reading_content(order_data: dict) -> dict:
    """
    Call Claude API and return a dict with all section texts.
    Falls back to template placeholders if the API call fails.
    """
    plan   = order_data.get("plan", "basic")
    name   = order_data.get("name", "")
    locale = order_data.get("locale", "ua")

    # ── Calculate real HD params first ────────────────────────────────────────
    hd_params = {}
    try:
        import hd_calculator
        hd_params = hd_calculator.calculate_hd(
            order_data.get('birth_date', ''),
            order_data.get('birth_time', ''),
            order_data.get('birth_place', ''),
        )
        log.info(f"HD calculated: {hd_params['hd_type']} / {hd_params['authority']} / {hd_params['profile']}")
    except Exception as e:
        log.warning(f"HD calculation failed: {e} — Claude will estimate")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-ant-api03-..."):
        log.warning("ANTHROPIC_API_KEY not set — using fallback content")
        fb = FALLBACK_FULL.copy() if plan == "full" else FALLBACK_BASIC.copy()
        if hd_params:
            fb['hd_type']   = hd_params['hd_type']
            fb['strategy']  = hd_params['strategy']
            fb['authority'] = hd_params['authority']
            fb['profile']   = hd_params['profile']
            fb['definition']= hd_params.get('definition', fb.get('definition', ''))
            fb['_source']   = 'calculated'
        return fb

    try:
        import anthropic
    except ImportError:
        log.error("anthropic package not installed (pip install anthropic) — using fallback")
        return FALLBACK_FULL.copy() if plan == "full" else FALLBACK_BASIC.copy()

    prompt = _build_prompt(order_data, plan)

    # ── Inject calculated HD params into prompt ────────────────────────────────
    if hd_params:
        defined_str = ', '.join(hd_params.get('defined_centers', [])) or 'none'
        calc_note = f"""
РОЗРАХОВАНІ АСТРОЛОГІЧНІ ПАРАМЕТРИ (використовуй ТІЛЬКИ ці значення):
- Тип: {hd_params['hd_type']}
- Стратегія: {hd_params['strategy']}
- Авторитет: {hd_params['authority']}
- Профіль: {hd_params['profile']}
- Визначення: {hd_params.get('definition', '')}
- Активні центри: {defined_str}

НЕ вигадуй ці значення — вони розраховані точно по планетарних позиціях.

"""
        prompt = calc_note + prompt
    # Haiku max context — need 8192 for complete JSON
    max_tokens = 8192

    log.info(f"Calling Claude API for {name} ({plan} plan, locale={locale})...")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Use haiku — cheapest model, ~$0.004 per reading vs $0.24 for opus
        # Prompt caching reduces cost by 90% on repeated system prompts
        system_prompt = (
            "Ти — експерт з Дизайну Людини з 15 роками практики. "
            "Ти точно розраховуєш параметри бодіграфу та генеруєш глибокі, "
            "персональні розшифровки. Відповідай ТІЛЬКИ валідним JSON без пояснень."
        )

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}  # кешуємо system prompt
                }
            ],
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        # Extract text from response
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text = block.text
                break

        if not response_text:
            raise ValueError("Empty response from Claude API")

        data = _extract_json(response_text)
        log.info(f"Claude API success — hd_type={data.get('hd_type', '?')}, "
                 f"authority={data.get('authority', '?')}, profile={data.get('profile', '?')}")

        # Ensure recommendations is a list of 10
        recs = data.get("recommendations", [])
        if isinstance(recs, list):
            while len(recs) < 10:
                recs.append(f"[Рекомендація {len(recs)+1}]")
            data["recommendations"] = recs[:10]

        # ── Override with calculated HD params (authoritative) ─────────────────
        if hd_params:
            data['hd_type']    = hd_params['hd_type']
            data['strategy']   = hd_params['strategy']
            data['authority']  = hd_params['authority']
            data['profile']    = hd_params['profile']
            data['definition'] = hd_params.get('definition', data.get('definition', ''))
            data['_source']    = 'calculated'
            log.info(f"HD params overridden with calculated values: "
                     f"{hd_params['hd_type']} / {hd_params['authority']} / {hd_params['profile']}")

        return data

    except Exception as e:
        log.error(f"Claude API failed: {e} — using fallback content")
        fb = FALLBACK_FULL.copy() if plan == "full" else FALLBACK_BASIC.copy()
        if hd_params:
            fb['hd_type']   = hd_params['hd_type']
            fb['strategy']  = hd_params['strategy']
            fb['authority'] = hd_params['authority']
            fb['profile']   = hd_params['profile']
            fb['definition']= hd_params.get('definition', fb.get('definition', ''))
            fb['_source']   = 'calculated'
        return fb


# ─── CLI (standalone test) ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Test Claude reading generation")
    parser.add_argument("--order",       required=True)
    parser.add_argument("--name",        required=True)
    parser.add_argument("--birth-date",  required=True)
    parser.add_argument("--birth-time",  required=True)
    parser.add_argument("--birth-place", required=True)
    parser.add_argument("--life-area",   required=True,
                        choices=["career", "relationships", "energy", "self"])
    parser.add_argument("--challenge",   required=True,
                        choices=["decisions", "fatigue", "purpose", "people"])
    parser.add_argument("--plan",        required=True, choices=["basic", "full"])
    parser.add_argument("--locale",      default="ua", choices=["ua", "ru", "en"])
    args = parser.parse_args()

    order_data = {
        "order_id":    args.order,
        "name":        args.name,
        "birth_date":  args.birth_date,
        "birth_time":  args.birth_time,
        "birth_place": args.birth_place,
        "life_area":   args.life_area,
        "challenge":   args.challenge,
        "plan":        args.plan,
        "locale":      args.locale,
    }

    print(f"\n{'='*60}")
    print(f"Testing Claude reading generation")
    print(f"  Name:  {args.name}")
    print(f"  Born:  {args.birth_date} {args.birth_time} @ {args.birth_place}")
    print(f"  Plan:  {args.plan}  |  Locale: {args.locale}")
    print(f"{'='*60}\n")

    content = get_reading_content(order_data)

    print(f"HD Type:    {content.get('hd_type', '—')}")
    print(f"Strategy:   {content.get('strategy', '—')}")
    print(f"Authority:  {content.get('authority', '—')}")
    print(f"Profile:    {content.get('profile', '—')}")
    print(f"Cross:      {content.get('incarnation_cross', '—')}")
    print()
    print(f"Intro:      {content.get('intro_text', '—')[:120]}...")
    print()
    print(f"Center 1:   {content.get('center1_name', '—')}")
    print(f"Center 2:   {content.get('center2_name', '—')}")
    print()

    recs = content.get("recommendations", [])
    print(f"Recommendations ({len(recs)}):")
    for i, r in enumerate(recs[:3], 1):
        print(f"  {i}. {r[:80]}")
    print()

    # Now generate the PDF
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from generate_reading import generate_reading_with_ai

    print("Generating PDF with AI content...")
    pdf_path = generate_reading_with_ai(order_data)
    print(f"\n✅ PDF generated: {pdf_path}")
    print(f"   Open with: open '{pdf_path}'")


if __name__ == "__main__":
    main()
