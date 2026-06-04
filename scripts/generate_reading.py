#!/usr/bin/env python3
"""
Human Design UA — PDF Reading Generator
Generates personalized bodygraph reading PDFs for basic and full plans.
Usage:
  python3 scripts/generate_reading.py --order HD-001 --name "Олена" \
    --birth-date "1990-05-15" --birth-time "14:30" --birth-place "Київ" \
    --life-area career --challenge decisions --plan basic --locale ua
"""

import argparse
import os
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from datetime import date
from fpdf import FPDF

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR  = os.path.join(BASE_DIR, "scripts", "fonts")
OUTPUT_DIR = os.path.join(BASE_DIR, "tmp", "readings")

# ─── Colors ───────────────────────────────────────────────────────────────────
BG         = (13,  11,  30)      # deep dark purple-black
BG_CARD    = (22,  18,  48)      # slightly lighter card bg
BG_SECTION = (28,  24,  58)      # section box
GOLD       = (212, 168,  48)     # gold accent
GOLD_DIM   = (160, 120,  30)     # dimmer gold
PURPLE     = (155, 110, 224)     # purple accent
WHITE      = (240, 236, 232)     # warm white text
MUTED      = (160, 150, 180)     # muted secondary text
PURPLE_MID = (100,  72, 160)     # mid purple for decorative elements

# ─── Translations ─────────────────────────────────────────────────────────────
T = {
    "ua": {
        # Cover
        "title_main":       "ДИЗАЙН ЛЮДИНИ",
        "subtitle":         "Персональна розшифровка бодіграфу",
        "badge_basic":      "БАЗОВА РОЗШИФРОВКА",
        "badge_full":       "ПОВНА РОЗШИФРОВКА",
        "label_date":       "Дата народження:",
        "label_time":       "Час народження:",
        "label_place":      "Місце народження:",
        "label_generated":  "Дата формування:",
        # Section titles
        "s01_num":  "01",
        "s01_title":"Що таке Дизайн Людини",
        "s02_num":  "02",
        "s02_title":"Твій Тип та Стратегія",
        "s03_num":  "03",
        "s03_title":"Авторитет прийняття рішень",
        "s04_num":  "04",
        "s04_title":"Твій Профіль — роль у житті",
        "s05_num":  "05",
        "s05_title_basic": "Ключові центри бодіграфу",
        "s05_title_full":  "Всі центри бодіграфу",
        "s06_num":  "06",
        "s06_title":"Практичні рекомендації",
        # Full-only sections
        "s07_num":  "07",
        "s07_title":"Інкарнаційний Хрест",
        "s08_num":  "08",
        "s08_title":"Аналіз стосунків та партнерства",
        "s09_num":  "09",
        "s09_title":"Тип визначення бодіграфу",
        "s10_num":  "10",
        "s10_title":"Практики декондиціювання",
        "s11_num":  "11",
        "s11_title":"Особистий план на 90 днів",
        # Labels in sections
        "your_type":        "Твій тип:",
        "your_strategy":    "Стратегія:",
        "your_authority":   "Авторитет:",
        "your_profile":     "Твій профіль:",
        "your_cross":       "Твій хрест:",
        "your_definition":  "Тип визначення:",
        "month_1":          "Місяць 1 — Усвідомлення",
        "month_2":          "Місяць 2 — Практика",
        "month_3":          "Місяць 3 — Інтеграція",
        "recommendations":  "Рекомендації для тебе:",
        "closing_title":    "Твій унікальний шлях починається тут",
        "closing_sub":      "Ця розшифровка — лише початок твоєї подорожі до себе.",
        "page_label":       "стор.",
        "contact_label":    "Зв'язок та підтримка:",
        "contact_email":    "support@humandesign.ua",
        # Placeholder texts — will be replaced by Claude API
        "intro_p1": (
            "[ТУТ БУДЕ ПЕРСОНАЛІЗОВАНИЙ ВСТУП ВІД CLAUDE API]\n"
            "Дизайн Людини — це синтез давніх та сучасних знань: астрології, Каббали, "
            "Ічінгу та квантової фізики. Система дає точну карту твоєї енергетичної структури, "
            "яка визначає, як ти взаємодієш зі світом і приймаєш рішення."
        ),
        "intro_p2": (
            "Твоя карта Дизайну Людини була зафіксована в момент твого народження "
            "і є такою ж унікальною, як відбиток пальця. Вона показує, де твоя енергія "
            "стала і надійна, а де ти вбираєш і підсилюєш енергії оточуючих."
        ),
        "intro_personalized": (
            "{{name}}, твоя розшифровка побудована на основі точних даних: "
            "{{birth_date}} о {{birth_time}} у {{birth_place}}. "
            "Саме ця мить визначила унікальний малюнок твого бодіграфу."
        ),
        "type_desc": (
            "Твій тип — [ТИП] — це фундамент усього твого Дизайну. "
            "Він визначає, яка в тебе аура, як ти взаємодієш з іншими людьми "
            "та яка стратегія є правильною саме для тебе. "
            "[ТУТ CLAUDE API ДОДАСТЬ ОПИС КОНКРЕТНОГО ТИПУ]"
        ),
        "strategy_desc": (
            "Стратегія [ТИП] — це твій практичний компас у повсякденному житті. "
            "Коли ти дотримуєшся своєї стратегії, рішення приходять легше, "
            "стосунки складаються природно, а енергія витрачається правильно. "
            "[ТУТ CLAUDE API ОПИШЕ КОНКРЕТНУ СТРАТЕГІЮ]"
        ),
        "authority_desc": (
            "Твій авторитет — [АВТОРИТЕТ] — це внутрішній голос, якому варто довіряти "
            "більше за розум і чужі думки. Саме через цей канал тіло і свідомість "
            "повідомляють тобі правильне рішення у потрібний момент. "
            "[ТУТ CLAUDE API ДЕТАЛЬНО ОПИШЕ КОНКРЕТНИЙ АВТОРИТЕТ]"
        ),
        "profile_desc": (
            "Твій профіль — [ПРОФІЛЬ] — визначає роль, яку ти граєш у житті, "
            "і тип стосунків, що будуть найбільш значущими. "
            "Це архетип твоєї душі, закодований у числах. "
            "[ТУТ CLAUDE API ОПИШЕ КОНКРЕТНИЙ ПРОФІЛЬ]"
        ),
        "centers_intro": (
            "Центри бодіграфу — це енергетичні трансформатори, подібні до чакр. "
            "Визначені центри (закрашені) — джерела постійної та надійної енергії. "
            "Невизначені центри (порожні) — місця мудрості та навчання через інших."
        ),
        "centers_basic": [
            ("[ЦЕНТР 1]", "[ТУТ БУДЕ ОПИС КЛЮЧОВОГО ЦЕНТРУ 1 ВІД CLAUDE API] — цей центр відповідає за... та впливає на..."),
            ("[ЦЕНТР 2]", "[ТУТ БУДЕ ОПИС КЛЮЧОВОГО ЦЕНТРУ 2 ВІД CLAUDE API] — взаємодія цього центру з..."),
            ("[ЦЕНТР 3]", "[ТУТ БУДЕ ОПИС КЛЮЧОВОГО ЦЕНТРУ 3 ВІД CLAUDE API] — визначення або невизначення цього центру означає..."),
        ],
        "centers_full": [
            ("Центр Голови",      "[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Центр Розуму",      "[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Горловий Центр",    "[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Центр Я / Серце",   "[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Сонячне Сплетіння", "[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Сакральний Центр",  "[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Центр Кореня",      "[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Селезінковий Центр","[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
            ("Центр Серця / Воля","[ВИЗНАЧЕНИЙ/НЕВИЗНАЧЕНИЙ] — [ТУТ CLAUDE API ОПИШЕ ЦЕЙ ЦЕНТР ДЛЯ {{name}}]"),
        ],
        "recs_career": [
            "Приймай важливі кар'єрні рішення лише через свій [АВТОРИТЕТ] — не поспішай",
            "Відстежуй, коли твоя енергія природно зростає — це сигнал правильного напрямку",
            "Вчися казати 'ні' проєктам, які не резонують з твоїм внутрішнім відчуттям",
            "Будуй репутацію через автентичність, а не через те, ким хочуть тебе бачити",
            "Щотижня виділяй час на відновлення енергії — це підвищить продуктивність",
            "[ТУТ CLAUDE API ДОДАСТЬ ПЕРСОНАЛІЗОВАНУ РЕКОМЕНДАЦІЮ ПО КАР'ЄРІ]",
        ],
        "recs_relationships": [
            "Дозволяй стосункам розвиватися у своєму темпі — не форсуй і не стримуй",
            "Твоя аура [ТИП] природно притягує певний тип людей — довіряй цьому процесу",
            "Практикуй вразливість там, де відчуваєш безпеку та резонанс",
            "Вчися розпізнавати, коли ти береш на себе чужі емоції через невизначені центри",
            "Регулярно 'проветрюй' свою ауру — проводь час на самоті для відновлення",
            "[ТУТ CLAUDE API ДОДАСТЬ ПЕРСОНАЛІЗОВАНУ РЕКОМЕНДАЦІЮ ПО СТОСУНКАХ]",
        ],
        "recs_energy": [
            "Поважай свої природні енергетичні цикли — не порівнюй себе з іншими типами",
            "Впроваджуй ранковий ритуал, що відповідає твоєму типу та авторитету",
            "Відстежуй, які ситуації та люди забирають твою енергію — встанови межі",
            "Харчування та сон — фундамент для правильної роботи твого Дизайну",
            "Фізична активність, що відповідає твоєму типу, відновлює краще за відпочинок",
            "[ТУТ CLAUDE API ДОДАСТЬ ПЕРСОНАЛІЗОВАНУ РЕКОМЕНДАЦІЮ ПО ЕНЕРГІЇ]",
        ],
        "recs_self": [
            "Щоденна практика спостереження за собою без осуду — основа декондиціювання",
            "Веди щоденник рішень, прийнятих через [АВТОРИТЕТ], та відстежуй результати",
            "Вивчи свій Профіль глибше — він відповідає на питання 'чому я такий/така'",
            "Практикуй паузу перед відповіддю — дай своєму авторитету час проявитися",
            "Оточуй себе людьми, які приймають тебе справжнього/справжню",
            "[ТУТ CLAUDE API ДОДАСТЬ ПЕРСОНАЛІЗОВАНУ РЕКОМЕНДАЦІЮ ПО САМОПІЗНАННЮ]",
        ],
        "closing_basic": (
            "{{name}}, ця розшифровка — твій перший крок до глибшого розуміння себе. "
            "Кожен день, коли ти живеш у відповідності до свого Дизайну, "
            "ти стаєш більш собою — і саме це є найбільшим подарунком для тебе і світу."
        ),
        # Full-only
        "cross_desc": (
            "Твій Інкарнаційний Хрест — [НАЗВА ХРЕСТА] — це тема твого життя, "
            "твоя місія і внесок у світ. Це не те, що ти маєш виконати силою волі, "
            "а те, що природно розкривається, коли ти живеш у відповідності до свого Дизайну. "
            "[ТУТ CLAUDE API ДЕТАЛЬНО ОПИШЕ КОНКРЕТНИЙ ХРЕСТ]"
        ),
        "relations_desc": (
            "Твоя аура [ТИП] у стосунках створює особливу динаміку. "
            "Розуміння механіки своїх центрів у взаємодії з іншими допомагає "
            "будувати глибші та більш автентичні зв'язки. "
            "[ТУТ CLAUDE API ОПИШЕ ТВОЮ УНІКАЛЬНУ ДИНАМІКУ У СТОСУНКАХ]"
        ),
        "best_partners": "[ТУТ CLAUDE API ОПИШЕ ТИПИ ПАРТНЕРІВ, ЩО НАЙКРАЩЕ ПІДХОДЯТЬ {{name}}]",
        "definition_desc": (
            "Твій тип визначення — [ТИП ВИЗНАЧЕННЯ] — визначає, наскільки самодостатньою "
            "є твоя енергетична система та як ти взаємодієш з оточенням. "
            "[ТУТ CLAUDE API ДЕТАЛЬНО ПОЯСНИТЬ ТВІЙ ТИП ВИЗНАЧЕННЯ]"
        ),
        "deconditioning": [
            "[ПРАКТИКА 1]: [ТУТ CLAUDE API ОПИШЕ ПРАКТИКУ ДЕКОНДИЦІЮВАННЯ ДЛЯ ТВОГО ТИПУ]",
            "[ПРАКТИКА 2]: Щоденна медитація або тиша протягом 20-30 хвилин для розрізнення власного голосу",
            "[ПРАКТИКА 3]: Журнал спостережень — записуй рішення та їхні наслідки без оцінки",
            "[ПРАКТИКА 4]: [ТУТ CLAUDE API ОПИШЕ ТІЛЕСНУ ПРАКТИКУ ДЛЯ ТВОГО АВТОРИТЕТУ]",
            "[ПРАКТИКА 5]: Практика меж — вчися відповідати 'ні' на те, що не резонує",
            "[ПРАКТИКА 6]: Аудит оточення — визнач, хто підсилює тебе, а хто виснажує",
            "[ПРАКТИКА 7]: [ТУТ CLAUDE API ДОДАСТЬ ПРАКТИКУ, СПЕЦИФІЧНУ ДЛЯ ТВОГО ПРОФІЛЮ]",
        ],
        "plan_month1": (
            "[ТУТ CLAUDE API СКЛАДЕ ПЛАН ПЕРШОГО МІСЯЦЯ ДЛЯ {{name}}]\n"
            "Тиждень 1-2: Спостереження та усвідомлення своїх патернів без змін\n"
            "Тиждень 3-4: Введення стратегії [ТИП] у повсякденні рішення"
        ),
        "plan_month2": (
            "[ТУТ CLAUDE API СКЛАДЕ ПЛАН ДРУГОГО МІСЯЦЯ ДЛЯ {{name}}]\n"
            "Тиждень 1-2: Поглиблення практики авторитету [АВТОРИТЕТ]\n"
            "Тиждень 3-4: Робота з ключовими центрами та декондиціювання"
        ),
        "plan_month3": (
            "[ТУТ CLAUDE API СКЛАДЕ ПЛАН ТРЕТЬОГО МІСЯЦЯ ДЛЯ {{name}}]\n"
            "Тиждень 1-2: Інтеграція знань у кар'єрі та стосунках\n"
            "Тиждень 3-4: Підсумок та складання власної практики на наступні місяці"
        ),
        "closing_full": (
            "{{name}}, повна розшифровка відкриває всю глибину твого унікального Дизайну. "
            "Пам'ятай: декондиціювання — це процес, що займає роки. "
            "Будь терплячою до себе, спостерігай, експериментуй і довіряй своєму тілу. "
            "Ти вже маєш всередині все, що потрібно — Дизайн допомагає це відкрити."
        ),
    },
    "ru": {
        "title_main":       "ДИЗАЙН ЧЕЛОВЕКА",
        "subtitle":         "Персональная расшифровка бодиграфа",
        "badge_basic":      "БАЗОВАЯ РАСШИФРОВКА",
        "badge_full":       "ПОЛНАЯ РАСШИФРОВКА",
        "label_date":       "Дата рождения:",
        "label_time":       "Время рождения:",
        "label_place":      "Место рождения:",
        "label_generated":  "Дата создания:",
        "s01_num":  "01", "s01_title":"Что такое Дизайн Человека",
        "s02_num":  "02", "s02_title":"Твой Тип и Стратегия",
        "s03_num":  "03", "s03_title":"Авторитет принятия решений",
        "s04_num":  "04", "s04_title":"Твой Профиль — роль в жизни",
        "s05_num":  "05",
        "s05_title_basic": "Ключевые центры бодиграфа",
        "s05_title_full":  "Все центры бодиграфа",
        "s06_num":  "06", "s06_title":"Практические рекомендации",
        "s07_num":  "07", "s07_title":"Инкарнационный Крест",
        "s08_num":  "08", "s08_title":"Анализ отношений и партнёрства",
        "s09_num":  "09", "s09_title":"Тип определения бодиграфа",
        "s10_num":  "10", "s10_title":"Практики декондиционирования",
        "s11_num":  "11", "s11_title":"Личный план на 90 дней",
        "your_type":       "Твой тип:",
        "your_strategy":   "Стратегия:",
        "your_authority":  "Авторитет:",
        "your_profile":    "Твой профиль:",
        "your_cross":      "Твой крест:",
        "your_definition": "Тип определения:",
        "month_1":  "Месяц 1 — Осознание",
        "month_2":  "Месяц 2 — Практика",
        "month_3":  "Месяц 3 — Интеграция",
        "recommendations": "Рекомендации для тебя:",
        "closing_title":   "Твой уникальный путь начинается здесь",
        "closing_sub":     "Эта расшифровка — лишь начало твоего путешествия к себе.",
        "page_label":      "стр.",
        "contact_label":   "Связь и поддержка:",
        "contact_email":   "support@humandesign.ua",
        "intro_p1": (
            "[ЗДЕСЬ БУДЕТ ПЕРСОНАЛИЗИРОВАННОЕ ВСТУПЛЕНИЕ ОТ CLAUDE API]\n"
            "Дизайн Человека — это синтез древних и современных знаний: астрологии, Каббалы, "
            "Ицзина и квантовой физики. Система даёт точную карту твоей энергетической структуры."
        ),
        "intro_p2": (
            "Твоя карта Дизайна Человека была зафиксирована в момент твоего рождения "
            "и уникальна, как отпечаток пальца. Она показывает, где твоя энергия стабильна, "
            "а где ты впитываешь и усиливаешь энергии окружающих."
        ),
        "intro_personalized": (
            "{{name}}, твоя расшифровка построена на основе точных данных: "
            "{{birth_date}} в {{birth_time}} в {{birth_place}}."
        ),
        "type_desc": "[ТУТ CLAUDE API ОПИШЕ ТИП] — [ТИП] визначає фундаментальний спосіб взаємодії з реальністю.",
        "strategy_desc": "Стратегія для [ТИП]: [ТУТ CLAUDE API ОПИШЕ СТРАТЕГІЮ ДЕТАЛЬНО]",
        "authority_desc": "[АВТОРИТЕТ] — твій внутрішній компас. [ТУТ CLAUDE API ДЕТАЛЬНО ПОЯСНИТЬ]",
        "profile_desc": "Профіль [ПРОФІЛЬ]: [ТУТ CLAUDE API ОПИШЕ РОЛЬ ТА АРХЕТИП]",
        "centers_intro": (
            "Центры бодиграфа — это энергетические трансформаторы. "
            "Определённые центры (закрашенные) — источники стабильной энергии. "
            "Неопределённые центры — места мудрости через взаимодействие."
        ),
        "centers_basic": [
            ("[ЦЕНТР 1]", "[ЗДЕСЬ CLAUDE API ОПИШЕТ КЛЮЧЕВОЙ ЦЕНТР 1]"),
            ("[ЦЕНТР 2]", "[ЗДЕСЬ CLAUDE API ОПИШЕТ КЛЮЧЕВОЙ ЦЕНТР 2]"),
            ("[ЦЕНТР 3]", "[ЗДЕСЬ CLAUDE API ОПИШЕТ КЛЮЧЕВОЙ ЦЕНТР 3]"),
        ],
        "centers_full": [
            ("Центр Головы",      "[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Центр Разума",      "[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Горловой Центр",    "[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Центр Я / Сердце",  "[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Солнечное Сплетение","[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Сакральный Центр",  "[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Центр Корня",       "[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Селезёночный Центр","[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
            ("Центр Сердца / Воля","[ОПРЕДЕЛЁН/НЕ ОПРЕДЕЛЁН] — [CLAUDE API]"),
        ],
        "recs_career":        ["[КЛОД API РЕКОМЕНДАЦИЯ 1 ПО КАРЬЕРЕ]", "[КЛОД API РЕКОМЕНДАЦИЯ 2]", "[КЛОД API РЕКОМЕНДАЦИЯ 3]", "[КЛОД API РЕКОМЕНДАЦИЯ 4]", "[КЛОД API РЕКОМЕНДАЦИЯ 5]"],
        "recs_relationships": ["[КЛОД API РЕКОМЕНДАЦИЯ 1 ПО ОТНОШЕНИЯМ]", "[КЛОД API РЕКОМЕНДАЦИЯ 2]", "[КЛОД API РЕКОМЕНДАЦИЯ 3]", "[КЛОД API РЕКОМЕНДАЦИЯ 4]", "[КЛОД API РЕКОМЕНДАЦИЯ 5]"],
        "recs_energy":        ["[КЛОД API РЕКОМЕНДАЦИЯ 1 ПО ЭНЕРГИИ]", "[КЛОД API РЕКОМЕНДАЦИЯ 2]", "[КЛОД API РЕКОМЕНДАЦИЯ 3]", "[КЛОД API РЕКОМЕНДАЦИЯ 4]", "[КЛОД API РЕКОМЕНДАЦИЯ 5]"],
        "recs_self":          ["[КЛОД API РЕКОМЕНДАЦИЯ 1 ПО САМОПОЗНАНИЮ]", "[КЛОД API РЕКОМЕНДАЦИЯ 2]", "[КЛОД API РЕКОМЕНДАЦИЯ 3]", "[КЛОД API РЕКОМЕНДАЦИЯ 4]", "[КЛОД API РЕКОМЕНДАЦИЯ 5]"],
        "closing_basic":  "{{name}}, эта расшифровка — твой первый шаг к глубокому пониманию себя. [CLAUDE API ЗАВЕРШЕННЯ]",
        "cross_desc":      "[КЛОД API ОПИШЕТ КРЕСТ [НАЗВА ХРЕСТА]]",
        "relations_desc":  "[КЛОД API ОПИШЕТ ДИНАМИКУ ОТНОШЕНИЙ ДЛЯ {{name}}]",
        "best_partners":   "[КЛОД API ОПИШЕТ ЛУЧШИХ ПАРТНЁРОВ ДЛЯ {{name}}]",
        "definition_desc": "[КЛОД API ОПИШЕТ ТИП ОПРЕДЕЛЕНИЯ [ТИП ВИЗНАЧЕННЯ]]",
        "deconditioning":  ["[ПРАКТИКА 1]", "[ПРАКТИКА 2]", "[ПРАКТИКА 3]", "[ПРАКТИКА 4]", "[ПРАКТИКА 5]", "[ПРАКТИКА 6]", "[ПРАКТИКА 7]"],
        "plan_month1":     "[КЛОД API МЕСЯЦ 1 ДЛЯ {{name}}]",
        "plan_month2":     "[КЛОД API МЕСЯЦ 2 ДЛЯ {{name}}]",
        "plan_month3":     "[КЛОД API МЕСЯЦ 3 ДЛЯ {{name}}]",
        "closing_full":    "{{name}}, полная расшифровка открывает всю глубину твоего уникального Дизайна. [CLAUDE API ЗАВЕРШЕННЯ]",
    },
    "en": {
        "title_main":       "HUMAN DESIGN",
        "subtitle":         "Personal Bodygraph Reading",
        "badge_basic":      "BASIC READING",
        "badge_full":       "FULL READING",
        "label_date":       "Date of birth:",
        "label_time":       "Time of birth:",
        "label_place":      "Place of birth:",
        "label_generated":  "Generated on:",
        "s01_num":  "01", "s01_title":"What is Human Design",
        "s02_num":  "02", "s02_title":"Your Type & Strategy",
        "s03_num":  "03", "s03_title":"Decision-Making Authority",
        "s04_num":  "04", "s04_title":"Your Profile — Life Role",
        "s05_num":  "05",
        "s05_title_basic": "Key Bodygraph Centers",
        "s05_title_full":  "All Bodygraph Centers",
        "s06_num":  "06", "s06_title":"Practical Recommendations",
        "s07_num":  "07", "s07_title":"Incarnation Cross",
        "s08_num":  "08", "s08_title":"Relationship & Partnership Analysis",
        "s09_num":  "09", "s09_title":"Definition Type",
        "s10_num":  "10", "s10_title":"Deconditioning Practices",
        "s11_num":  "11", "s11_title":"Personal 90-Day Plan",
        "your_type":       "Your type:",
        "your_strategy":   "Strategy:",
        "your_authority":  "Authority:",
        "your_profile":    "Your profile:",
        "your_cross":      "Your cross:",
        "your_definition": "Definition type:",
        "month_1":  "Month 1 — Awareness",
        "month_2":  "Month 2 — Practice",
        "month_3":  "Month 3 — Integration",
        "recommendations": "Recommendations for you:",
        "closing_title":   "Your unique journey starts here",
        "closing_sub":     "This reading is just the beginning of your journey inward.",
        "page_label":      "p.",
        "contact_label":   "Support & contact:",
        "contact_email":   "support@humandesign.ua",
        "intro_p1": (
            "[PERSONALIZED INTRO FROM CLAUDE API WILL GO HERE]\n"
            "Human Design is a synthesis of ancient and modern knowledge: astrology, Kabbalah, "
            "the I Ching, and quantum physics. The system provides an accurate map of your energetic "
            "structure, revealing how you interact with the world and make decisions."
        ),
        "intro_p2": (
            "Your Human Design chart was fixed at the moment of your birth "
            "and is as unique as a fingerprint. It shows where your energy is consistent "
            "and reliable, and where you absorb and amplify the energies of others."
        ),
        "intro_personalized": (
            "{{name}}, your reading is built on precise data: "
            "{{birth_date}} at {{birth_time}} in {{birth_place}}. "
            "That exact moment determined the unique pattern of your bodygraph."
        ),
        "type_desc": "[TYPE] is the foundation of your entire Design. [CLAUDE API WILL DESCRIBE YOUR SPECIFIC TYPE IN DETAIL]",
        "strategy_desc": "The strategy for [TYPE]: [CLAUDE API WILL DESCRIBE YOUR SPECIFIC STRATEGY]",
        "authority_desc": "[AUTHORITY] — your inner compass. [CLAUDE API WILL EXPLAIN IN DETAIL]",
        "profile_desc": "Profile [PROFILE]: [CLAUDE API WILL DESCRIBE YOUR ROLE AND ARCHETYPE]",
        "centers_intro": (
            "Bodygraph centers are energetic transformers, similar to chakras. "
            "Defined centers (coloured) are sources of consistent, reliable energy. "
            "Undefined centers (open) are places of wisdom and learning through others."
        ),
        "centers_basic": [
            ("[CENTER 1]", "[CLAUDE API WILL DESCRIBE KEY CENTER 1 FOR YOU]"),
            ("[CENTER 2]", "[CLAUDE API WILL DESCRIBE KEY CENTER 2 FOR YOU]"),
            ("[CENTER 3]", "[CLAUDE API WILL DESCRIBE KEY CENTER 3 FOR YOU]"),
        ],
        "centers_full": [
            ("Head Center",     "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("Ajna Center",     "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("Throat Center",   "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("G / Self Center", "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("Solar Plexus",    "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("Sacral Center",   "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("Root Center",     "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("Spleen Center",   "[DEFINED/UNDEFINED] — [CLAUDE API]"),
            ("Heart / Ego Center","[DEFINED/UNDEFINED] — [CLAUDE API]"),
        ],
        "recs_career":        ["[CLAUDE API CAREER REC 1]", "[CLAUDE API REC 2]", "[CLAUDE API REC 3]", "[CLAUDE API REC 4]", "[CLAUDE API REC 5]"],
        "recs_relationships": ["[CLAUDE API RELATIONSHIP REC 1]", "[CLAUDE API REC 2]", "[CLAUDE API REC 3]", "[CLAUDE API REC 4]", "[CLAUDE API REC 5]"],
        "recs_energy":        ["[CLAUDE API ENERGY REC 1]", "[CLAUDE API REC 2]", "[CLAUDE API REC 3]", "[CLAUDE API REC 4]", "[CLAUDE API REC 5]"],
        "recs_self":          ["[CLAUDE API SELF-KNOWLEDGE REC 1]", "[CLAUDE API REC 2]", "[CLAUDE API REC 3]", "[CLAUDE API REC 4]", "[CLAUDE API REC 5]"],
        "closing_basic":  "{{name}}, this reading is your first step toward deeper self-understanding. [CLAUDE API CLOSING]",
        "cross_desc":      "[CLAUDE API WILL DESCRIBE THE CROSS [CROSS NAME]]",
        "relations_desc":  "[CLAUDE API WILL DESCRIBE RELATIONSHIP DYNAMICS FOR {{name}}]",
        "best_partners":   "[CLAUDE API WILL DESCRIBE BEST PARTNER TYPES FOR {{name}}]",
        "definition_desc": "[CLAUDE API WILL DESCRIBE [DEFINITION TYPE] IN DETAIL]",
        "deconditioning":  ["[PRACTICE 1]", "[PRACTICE 2]", "[PRACTICE 3]", "[PRACTICE 4]", "[PRACTICE 5]", "[PRACTICE 6]", "[PRACTICE 7]"],
        "plan_month1":     "[CLAUDE API MONTH 1 PLAN FOR {{name}}]",
        "plan_month2":     "[CLAUDE API MONTH 2 PLAN FOR {{name}}]",
        "plan_month3":     "[CLAUDE API MONTH 3 PLAN FOR {{name}}]",
        "closing_full":    "{{name}}, this full reading opens the full depth of your unique Design. [CLAUDE API CLOSING]",
    },
}


# ─── PDF Class ────────────────────────────────────────────────────────────────
class HumanDesignPDF(FPDF):
    def __init__(self, locale, plan, name):
        super().__init__()
        self.locale = locale
        self.plan   = plan
        self.client_name = name
        self.t = T[locale]
        self._page_count = 0
        self.set_margins(0, 0, 0)
        self.set_auto_page_break(False)

    def _add_fonts(self):
        self.add_font("DejaVu",     "", os.path.join(FONTS_DIR, "DejaVuSans.ttf"))
        self.add_font("DejaVuBold", "", os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf"))

    def add_page(self, *args, **kwargs):
        super().add_page(*args, **kwargs)
        self._page_count += 1
        # Full-page dark background
        self.set_fill_color(*BG)
        self.rect(0, 0, 210, 297, "F")

    def _x(self): return 20
    def _w(self): return 170
    def _page_w(self): return 210

    # ── Decorative helpers ────────────────────────────────────────────────────
    def _gold_line(self, y, x=20, w=170, thickness=0.4):
        self.set_draw_color(*GOLD)
        self.set_line_width(thickness)
        self.line(x, y, x + w, y)

    def _gold_deco_lines(self, y):
        """Triple decorative lines."""
        self.set_draw_color(*GOLD)
        self.set_line_width(0.6)
        self.line(20, y, 95, y)
        self.set_line_width(0.2)
        self.line(20, y + 2, 85, y + 2)
        self.set_line_width(0.6)
        self.line(115, y, 190, y)
        self.set_line_width(0.2)
        self.line(125, y + 2, 190, y + 2)

    def _draw_star(self, cx, cy, r_outer=8, r_inner=3.5, points=8):
        """Draw an 8-pointed star."""
        import math
        self.set_fill_color(*GOLD)
        # We'll draw as a series of triangles using FPDF's polygon approximation
        vertices = []
        for i in range(points * 2):
            angle = math.pi / points * i - math.pi / 2
            r = r_outer if i % 2 == 0 else r_inner
            vertices.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        # Draw filled polygon
        path = " ".join(f"{v[0]:.2f} {v[1]:.2f}" for v in vertices)
        # Use FPDF drawing primitives via lines
        self.set_fill_color(*GOLD)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.1)
        # Build polygon string for fpdf2
        pts = [(cx + (r_outer if i % 2 == 0 else r_inner) *
                __import__('math').cos(__import__('math').pi / points * i - __import__('math').pi / 2),
                cy + (r_outer if i % 2 == 0 else r_inner) *
                __import__('math').sin(__import__('math').pi / points * i - __import__('math').pi / 2))
               for i in range(points * 2)]
        # Draw using polyline (fpdf2 supports polygon via polyline)
        with self.local_context():
            self.set_fill_color(*GOLD)
            # Use fpdf2 drawing support
            from fpdf.drawing import Move, Line, Close
        # Fallback: draw as filled circle + star arms
        self.set_fill_color(*GOLD)
        self.ellipse(cx - r_inner, cy - r_inner, r_inner * 2, r_inner * 2, "F")
        import math
        for i in range(points):
            angle = math.pi / points * 2 * i - math.pi / 2
            x1 = cx + r_inner * math.cos(angle)
            y1 = cy + r_inner * math.sin(angle)
            x2 = cx + r_outer * math.cos(angle)
            y2 = cy + r_outer * math.sin(angle)
            self.set_line_width(2.5)
            self.set_draw_color(*GOLD)
            self.line(x1, y1, x2, y2)

    def _section_header(self, num_key, title_key, y=None):
        """Draw a section header with large gold number + title."""
        if y:
            self.set_y(y)
        # Gold section number
        self.set_x(self._x())
        self.set_font("DejaVuBold", "", 40)
        self.set_text_color(*GOLD_DIM)
        self.cell(25, 20, self.t[num_key], ln=0)
        # Section title
        self.set_font("DejaVuBold", "", 18)
        self.set_text_color(*WHITE)
        self.set_x(self._x() + 27)
        title = self.t[title_key] if isinstance(title_key, str) else title_key
        self.cell(self._w() - 27, 20, title, ln=1)
        # Gold underline
        self._gold_line(self.get_y(), x=20, w=170, thickness=0.5)
        self.ln(6)

    def _section_header_str(self, num, title):
        """Draw section header with direct string values."""
        self.set_x(self._x())
        self.set_font("DejaVuBold", "", 40)
        self.set_text_color(*GOLD_DIM)
        self.cell(25, 20, num, ln=0)
        self.set_font("DejaVuBold", "", 18)
        self.set_text_color(*WHITE)
        self.set_x(self._x() + 27)
        self.cell(self._w() - 27, 20, title, ln=1)
        self._gold_line(self.get_y(), x=20, w=170, thickness=0.5)
        self.ln(6)

    def _body_text(self, text, size=10, color=None, indent=0):
        """Render multi-line body text."""
        if color is None:
            color = WHITE
        self.set_font("DejaVu", "", size)
        self.set_text_color(*color)
        self.set_x(self._x() + indent)
        self.multi_cell(self._w() - indent, 6, text, ln=1)
        self.ln(2)

    def _highlight_box(self, label, value, y=None):
        """Draw a highlighted info box."""
        if y:
            self.set_y(y)
        box_y = self.get_y()
        # Background card
        self.set_fill_color(*BG_CARD)
        self.rect(self._x(), box_y, self._w(), 18, "F")
        # Left purple bar
        self.set_fill_color(*PURPLE_MID)
        self.rect(self._x(), box_y, 3, 18, "F")
        # Label
        self.set_xy(self._x() + 6, box_y + 2)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*MUTED)
        self.cell(50, 5, label, ln=0)
        # Value
        self.set_xy(self._x() + 6, box_y + 8)
        self.set_font("DejaVuBold", "", 13)
        self.set_text_color(*GOLD)
        self.cell(self._w() - 10, 8, value, ln=1)
        self.ln(3)

    def _large_type_box(self, label, value):
        """Big centered type/strategy box."""
        box_y = self.get_y()
        self.set_fill_color(*BG_SECTION)
        self.rect(self._x(), box_y, self._w(), 28, "F")
        # Gold border
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.rect(self._x(), box_y, self._w(), 28)
        # Label
        self.set_xy(self._x(), box_y + 3)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*MUTED)
        self.cell(self._w(), 5, label, align="C", ln=1)
        # Value
        self.set_x(self._x())
        self.set_font("DejaVuBold", "", 22)
        self.set_text_color(*GOLD)
        self.cell(self._w(), 16, value, align="C", ln=1)
        self.ln(5)

    def _bullet_point(self, text, color=None):
        if color is None:
            color = WHITE
        self.set_x(self._x())
        self.set_font("DejaVuBold", "", 11)
        self.set_text_color(*GOLD)
        self.cell(6, 6, "•", ln=0)
        self.set_font("DejaVu", "", 9.5)
        self.set_text_color(*color)
        self.set_x(self._x() + 6)
        self.multi_cell(self._w() - 6, 6, text, ln=1)
        self.ln(1)

    def _month_box(self, month_label, content):
        """90-day plan month box."""
        box_y = self.get_y()
        h = 38
        self.set_fill_color(18, 15, 42)
        self.rect(self._x(), box_y, self._w(), h, "F")
        # Top colored bar
        self.set_fill_color(*PURPLE_MID)
        self.rect(self._x(), box_y, self._w(), 7, "F")
        self.set_xy(self._x(), box_y + 1)
        self.set_font("DejaVuBold", "", 9)
        self.set_text_color(*WHITE)
        self.cell(self._w(), 5, month_label, align="C", ln=1)
        self.set_xy(self._x(), box_y + 10)
        self.set_font("DejaVu", "", 8.5)
        self.set_text_color(*MUTED)
        self.multi_cell(self._w() - 4, 5.5, content, ln=1)
        self.set_y(box_y + h + 4)

    def _footer_page_number(self):
        """Draw page number in gold at bottom."""
        self.set_xy(0, 285)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*GOLD_DIM)
        self.cell(210, 8, f"— {self._page_count} —", align="C", ln=1)

    def _interpolate(self, text, name, birth_date="", birth_time="", birth_place=""):
        return (text
                .replace("{{name}}", name)
                .replace("{{birth_date}}", birth_date)
                .replace("{{birth_time}}", birth_time)
                .replace("{{birth_place}}", birth_place))

    # ── Page builders ──────────────────────────────────────────────────────────
    def build_cover(self, name, birth_date, birth_time, birth_place, plan):
        self.add_page()
        t = self.t
        w = self._page_w()

        # Subtle purple gradient overlay (top area)
        self.set_fill_color(30, 20, 65)
        self.rect(0, 0, 210, 80, "F")
        self.set_fill_color(*BG)
        self.rect(0, 80, 210, 217, "F")

        # ── Star symbol ───────────────────────────────────────────────────────
        self._draw_star(105, 30, r_outer=10, r_inner=4, points=8)

        # ── Decorative top lines ──────────────────────────────────────────────
        self._gold_line(50, x=20, w=170, thickness=0.3)
        self._gold_line(52, x=30, w=150, thickness=0.15)

        # ── Main title ────────────────────────────────────────────────────────
        self.set_y(58)
        self.set_font("DejaVuBold", "", 28)
        self.set_text_color(*GOLD)
        self.cell(w, 14, t["title_main"], align="C", ln=1)

        # ── Decorative dashes ─────────────────────────────────────────────────
        self._gold_deco_lines(76)

        # ── Client name ───────────────────────────────────────────────────────
        self.set_y(84)
        self.set_font("DejaVuBold", "", 34)
        self.set_text_color(*WHITE)
        self.cell(w, 18, name, align="C", ln=1)

        # ── Subtitle ──────────────────────────────────────────────────────────
        self.set_font("DejaVu", "", 11)
        self.set_text_color(*MUTED)
        self.cell(w, 8, t["subtitle"], align="C", ln=1)

        # ── Mid decorative line ───────────────────────────────────────────────
        self._gold_line(115, x=40, w=130, thickness=0.3)
        self._gold_line(117, x=60, w=90, thickness=0.15)

        # ── Birth info ────────────────────────────────────────────────────────
        self.set_y(124)
        info_items = [
            (t["label_date"],  birth_date),
            (t["label_time"],  birth_time),
            (t["label_place"], birth_place),
        ]
        for lbl, val in info_items:
            self.set_x(0)
            self.set_font("DejaVu", "", 9)
            self.set_text_color(*MUTED)
            self.cell(w / 2, 8, lbl, align="R", ln=0)
            self.set_font("DejaVuBold", "", 9)
            self.set_text_color(*WHITE)
            self.cell(4, 8, " ", ln=0)
            self.cell(w / 2 - 4, 8, val, align="L", ln=1)

        # Generated date
        self.set_x(0)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(*MUTED)
        self.cell(w / 2, 8, t["label_generated"], align="R", ln=0)
        self.set_font("DejaVuBold", "", 9)
        self.set_text_color(*GOLD_DIM)
        self.cell(4, 8, " ", ln=0)
        self.cell(w / 2 - 4, 8, str(date.today().strftime("%d.%m.%Y")), align="L", ln=1)

        # ── Plan badge ────────────────────────────────────────────────────────
        badge_text = t["badge_full"] if plan == "full" else t["badge_basic"]
        badge_y = 185
        badge_w, badge_h = 90, 14
        badge_x = (w - badge_w) / 2
        self.set_fill_color(*GOLD)
        self.rect(badge_x, badge_y, badge_w, badge_h, "F")
        self.set_xy(badge_x, badge_y + 1)
        self.set_font("DejaVuBold", "", 11)
        self.set_text_color(*BG)
        self.cell(badge_w, badge_h - 2, badge_text, align="C", ln=1)

        # ── Bottom decorative border ──────────────────────────────────────────
        self._gold_line(207, x=20, w=170, thickness=0.5)
        self._gold_line(209, x=30, w=150, thickness=0.2)
        self._gold_line(211, x=40, w=130, thickness=0.1)

        # ── Bottom star cluster ───────────────────────────────────────────────
        for sx, sy, sz in [(45, 230, 3), (165, 240, 2.5), (105, 255, 2), (75, 270, 1.8), (135, 265, 2)]:
            self._draw_star(sx, sy, r_outer=sz, r_inner=sz * 0.4, points=4)

        self._footer_page_number()

    def build_intro_page(self, name, birth_date, birth_time, birth_place):
        self.add_page()
        t = self.t
        self._section_header("s01_num", "s01_title")
        self._body_text(t["intro_p1"], size=10)
        self.ln(2)
        self._body_text(t["intro_p2"], size=10)
        self.ln(4)
        self._gold_line(self.get_y(), x=20, w=60, thickness=0.3)
        self.ln(6)
        personalized = self._interpolate(
            t["intro_personalized"], name, birth_date, birth_time, birth_place
        )
        self._body_text(personalized, size=10, color=PURPLE)
        self._footer_page_number()

    def build_type_strategy_page(self):
        self.add_page()
        t = self.t
        self._section_header("s02_num", "s02_title")
        self._large_type_box(t["your_type"], "[ТИП]")
        self._body_text(t["type_desc"], size=10)
        self.ln(4)
        self._highlight_box(t["your_strategy"], "[СТРАТЕГІЯ / STRATEGY]")
        self.ln(2)
        self._body_text(t["strategy_desc"], size=10)
        self._footer_page_number()

    def build_authority_page(self):
        self.add_page()
        t = self.t
        self._section_header("s03_num", "s03_title")
        self._large_type_box(t["your_authority"], "[АВТОРИТЕТ / AUTHORITY]")
        self._body_text(t["authority_desc"], size=10)
        self._footer_page_number()

    def build_profile_page(self):
        self.add_page()
        t = self.t
        self._section_header("s04_num", "s04_title")
        self._large_type_box(t["your_profile"], "[ПРОФІЛЬ / PROFILE]")
        self._body_text(t["profile_desc"], size=10)
        self._footer_page_number()

    def build_centers_page(self, plan):
        self.add_page()
        t = self.t
        title_key = "s05_title_full" if plan == "full" else "s05_title_basic"
        self._section_header_str(t["s05_num"], t[title_key])
        self._body_text(t["centers_intro"], size=9.5, color=MUTED)
        self.ln(3)
        centers = t["centers_full"] if plan == "full" else t["centers_basic"]
        for center_name, center_desc in centers:
            # Center name row
            box_y = self.get_y()
            self.set_fill_color(*BG_CARD)
            self.rect(self._x(), box_y, self._w(), 8, "F")
            self.set_fill_color(*PURPLE_MID)
            self.rect(self._x(), box_y, 3, 8, "F")
            self.set_xy(self._x() + 6, box_y + 1)
            self.set_font("DejaVuBold", "", 10)
            self.set_text_color(*GOLD)
            self.cell(self._w() - 6, 6, center_name, ln=1)
            # Center description
            self.set_x(self._x() + 3)
            self.set_font("DejaVu", "", 8.5)
            self.set_text_color(*MUTED)
            self.multi_cell(self._w() - 3, 5, center_desc, ln=1)
            self.ln(2)
            if self.get_y() > 270:
                break
        self._footer_page_number()

    def build_recommendations_page(self, life_area, name, plan):
        self.add_page()
        t = self.t
        self._section_header("s06_num", "s06_title")
        rec_key = f"recs_{life_area}" if f"recs_{life_area}" in t else "recs_self"
        recs = t[rec_key]
        self._body_text(t["recommendations"], size=10, color=GOLD)
        self.ln(2)
        for rec in recs:
            self._bullet_point(rec)
        if plan == "basic":
            self.ln(6)
            self._gold_deco_lines(self.get_y())
            self.ln(10)
            closing = self._interpolate(t["closing_basic"], name)
            self._body_text(closing, size=10, color=PURPLE)
        self._footer_page_number()

    # ── FULL plan extra pages ─────────────────────────────────────────────────
    def build_cross_page(self):
        self.add_page()
        t = self.t
        self._section_header("s07_num", "s07_title")
        self._large_type_box(t["your_cross"], "[ІНКАРНАЦІЙНИЙ ХРЕСТ / INCARNATION CROSS]")
        self._body_text(t["cross_desc"], size=10)
        self._footer_page_number()

    def build_relationships_page(self, name):
        self.add_page()
        t = self.t
        self._section_header("s08_num", "s08_title")
        desc = self._interpolate(t["relations_desc"], name)
        self._body_text(desc, size=10)
        self.ln(4)
        self._highlight_box("Best partners / Найкращі партнери:", t["best_partners"])
        self._footer_page_number()

    def build_definition_page(self):
        self.add_page()
        t = self.t
        self._section_header("s09_num", "s09_title")
        self._large_type_box(t["your_definition"], "[ТИП ВИЗНАЧЕННЯ / DEFINITION TYPE]")
        self._body_text(t["definition_desc"], size=10)
        self._footer_page_number()

    def build_deconditioning_page(self):
        self.add_page()
        t = self.t
        self._section_header("s10_num", "s10_title")
        practices = t["deconditioning"]
        for i, practice in enumerate(practices, 1):
            # Number circle
            cx = self._x() + 4
            cy = self.get_y() + 4
            self.set_fill_color(*PURPLE_MID)
            self.ellipse(cx - 4, cy - 4, 8, 8, "F")
            self.set_xy(cx - 4, cy - 5)
            self.set_font("DejaVuBold", "", 8)
            self.set_text_color(*WHITE)
            self.cell(8, 8, str(i), align="C", ln=0)
            # Practice text
            self.set_x(self._x() + 11)
            self.set_font("DejaVu", "", 9.5)
            self.set_text_color(*WHITE)
            self.multi_cell(self._w() - 11, 6, practice, ln=1)
            self.ln(2)
        self._footer_page_number()

    def build_90day_plan_page(self, name, life_area):
        self.add_page()
        t = self.t
        self._section_header("s11_num", "s11_title")
        month_data = [
            (t["month_1"], self._interpolate(t["plan_month1"], name)),
            (t["month_2"], self._interpolate(t["plan_month2"], name)),
            (t["month_3"], self._interpolate(t["plan_month3"], name)),
        ]
        for label, content in month_data:
            self._month_box(label, content)
        self._footer_page_number()

    def build_closing_page(self, name, plan):
        self.add_page()
        t = self.t
        # Decorative top area
        self.set_fill_color(25, 18, 55)
        self.rect(0, 0, 210, 70, "F")
        self._draw_star(105, 35, r_outer=12, r_inner=5, points=8)
        self._gold_line(60, x=20, w=170, thickness=0.4)
        # Title
        self.set_y(70)
        self.set_font("DejaVuBold", "", 20)
        self.set_text_color(*GOLD)
        self.cell(210, 12, t["closing_title"], align="C", ln=1)
        self.set_font("DejaVu", "", 10)
        self.set_text_color(*MUTED)
        self.cell(210, 8, t["closing_sub"], align="C", ln=1)
        self.ln(8)
        self._gold_deco_lines(self.get_y())
        self.ln(12)
        # Closing text
        closing_key = "closing_full" if plan == "full" else "closing_basic"
        closing = self._interpolate(t[closing_key], name)
        self.set_x(self._x())
        self.set_font("DejaVu", "", 10.5)
        self.set_text_color(*WHITE)
        self.multi_cell(self._w(), 7, closing, align="C", ln=1)
        # Contact info
        self.set_y(230)
        self._gold_line(230, x=60, w=90, thickness=0.3)
        self.set_y(236)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*MUTED)
        self.cell(210, 6, t["contact_label"], align="C", ln=1)
        self.set_font("DejaVuBold", "", 9)
        self.set_text_color(*GOLD)
        self.cell(210, 6, t["contact_email"], align="C", ln=1)
        # Bottom stars
        for sx, sy, sz in [(40, 270, 2.5), (170, 268, 2), (105, 280, 1.5)]:
            self._draw_star(sx, sy, r_outer=sz, r_inner=sz * 0.4, points=4)
        self._footer_page_number()


# ─── Main generator function ──────────────────────────────────────────────────
def generate_reading(order, name, birth_date, birth_time, birth_place,
                     life_area, challenge, plan, locale):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"reading_{order}_{plan}.pdf")

    pdf = HumanDesignPDF(locale=locale, plan=plan, name=name)
    pdf._add_fonts()

    # Page 1 — Cover
    pdf.build_cover(name, birth_date, birth_time, birth_place, plan)

    # Page 2 — Intro
    pdf.build_intro_page(name, birth_date, birth_time, birth_place)

    # Page 3 — Type & Strategy
    pdf.build_type_strategy_page()

    # Page 4 — Authority
    pdf.build_authority_page()

    # Page 5 — Profile
    pdf.build_profile_page()

    # Page 6 — Centers
    pdf.build_centers_page(plan)

    # Page 7 — Recommendations
    pdf.build_recommendations_page(life_area, name, plan)

    if plan == "full":
        # Page 8 — Incarnation Cross
        pdf.build_cross_page()

        # Page 9 — Relationships
        pdf.build_relationships_page(name)

        # Page 10 — Definition Type
        pdf.build_definition_page()

        # Page 11 — Deconditioning Practices
        pdf.build_deconditioning_page()

        # Page 12 — 90-Day Plan
        pdf.build_90day_plan_page(name, life_area)

        # Page 13 — Closing (full)
        pdf.build_closing_page(name, plan)

    pdf.output(output_path)
    return output_path


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate Human Design reading PDF"
    )
    parser.add_argument("--order",       required=True,  help="Order ID, e.g. HD-001")
    parser.add_argument("--name",        required=True,  help="Client name")
    parser.add_argument("--birth-date",  required=True,  help="Birth date YYYY-MM-DD")
    parser.add_argument("--birth-time",  required=True,  help="Birth time HH:MM")
    parser.add_argument("--birth-place", required=True,  help="Birth place")
    parser.add_argument("--life-area",   required=True,
                        choices=["career", "relationships", "energy", "self"])
    parser.add_argument("--challenge",   required=True,
                        choices=["decisions", "fatigue", "purpose", "people"])
    parser.add_argument("--plan",        required=True,  choices=["basic", "full"])
    parser.add_argument("--locale",      default="ua",   choices=["ua", "ru", "en"])
    args = parser.parse_args()

    output = generate_reading(
        order       = args.order,
        name        = args.name,
        birth_date  = args.birth_date,
        birth_time  = args.birth_time,
        birth_place = args.birth_place,
        life_area   = args.life_area,
        challenge   = args.challenge,
        plan        = args.plan,
        locale      = args.locale,
    )
    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
