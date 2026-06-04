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
import math
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
BG       = (8,   5,   3)    # dark warm black
ORANGE   = (210, 95,  10)   # burnt orange
AMBER    = (195, 140, 15)   # golden amber
ORANGE_L = (230, 115, 20)   # bright orange
CREAM    = (245, 235, 210)  # cream text
W_WHITE  = (255, 248, 230)  # warm white headings
MUTED    = (175, 150, 115)  # muted text
DIM      = (115, 95,  70)   # dim captions

# ─── Translations ─────────────────────────────────────────────────────────────
T = {
    "ua": {
        # Cover
        "title_main":       "ДИЗАЙН ЛЮДИНИ",
        "subtitle":         "Персональна розшифровка бодіграфу",
        "badge_basic":      "БАЗОВА РОЗШИФРОВКА · 20 СТОРІНОК",
        "badge_full":       "ПОВНА РОЗШИФРОВКА · 50 СТОРІНОК",
        "label_date":       "Дата народження:",
        "label_time":       "Час народження:",
        "label_place":      "Місце народження:",
        "label_generated":  "Дата формування:",
        # Welcome page
        "welcome_title":    "Вітаємо,",
        "welcome_p1": (
            "Ви придбали персональну розшифровку Дизайну Людини — одну з найточніших "
            "систем самопізнання, що існують сьогодні."
        ),
        "welcome_p2": (
            "Ці знання вже допомогли понад 1 000 наших клієнтів, які довірились нам. "
            "Кожна розшифровка унікальна — так само, як унікальний кожен з них."
        ),
        "welcome_p3_tpl": (
            "Ця розшифровка створена спеціально для вас на основі точних астрологічних "
            "даних вашого народження: {{birth_date}} о {{birth_time}} у {{birth_place}}."
        ),
        "welcome_p4": (
            "Відкрийте нові сторінки цього документу з відкритим серцем — і ви дізнаєтесь "
            "про себе те, що відчували завжди, але не мали слів щоб описати."
        ),
        # Section titles
        "s01_num":  "01", "s01_title": "Що таке Дизайн Людини",
        "s02_num":  "02", "s02_title": "Твій Тип",
        "s02b_title": "Стратегія",
        "s03_num":  "03", "s03_title": "Авторитет прийняття рішень",
        "s03b_title": "Авторитет у щоденному житті",
        "s04_num":  "04", "s04_title": "Твій Профіль",
        "s04b_title": "Профіль у стосунках та роботі",
        "s05_num":  "05", "s05_title": "Твій Бодіграф — ключові центри",
        "s06_num":  "06", "s06_title": "Визначені центри — деталі",
        "s06b_title": "Другий визначений центр",
        "s06c_title": "Третій визначений центр",
        "s07_num":  "07", "s07_title": "Відкриті центри — де ти вбираєш енергію",
        "s08_num":  "08", "s08_title": "Сигнатура та Не-Я тема",
        "s09_num":  "09", "s09_title": "Твоя Тема Життя",
        "s10_num":  "10", "s10_title": "Практичні рекомендації",
        "s10b_title": "Ще 5 рекомендацій",
        "s11_num":  "11", "s11_title": "Твої наступні 30 днів",
        # Labels
        "your_type":      "Твій тип:",
        "your_strategy":  "Стратегія:",
        "your_authority": "Авторитет:",
        "your_profile":   "Твій профіль:",
        "your_signature": "Сигнатура:",
        "your_not_self":  "Не-Я тема:",
        "page_label":     "стор.",
        "contact_label":  "Зв'язок та підтримка:",
        "contact_email":  "humandesign.finance@gmail.com",
        "copyright":      "© 2026 Human Design UA · Всі права захищені",
        "brand":          "Human Design UA",
        "unique":         "Ти — унікальна.",
        "closing_msg": (
            "Цей документ — твій перший крок до глибшого розуміння себе. "
            "Кожен день, коли ти живеш у відповідності до свого Дизайну, "
            "ти стаєш більш собою. Довіряй своєму тілу, слухай свій авторитет, "
            "і пам'ятай: ти вже маєш всередині все, що потрібно."
        ),
        # Section content
        "hd_what_p1": (
            "Дизайн Людини — це синтез давніх та сучасних знань: астрології, Каббали, "
            "Іцзіну та квантової фізики. Система дає точну карту твоєї енергетичної "
            "структури, яка визначає, як ти взаємодієш зі світом і приймаєш рішення."
        ),
        "hd_what_p2": (
            "Твоя карта Дизайну Людини була зафіксована в момент твого народження "
            "і є такою ж унікальною, як відбиток пальця. Вона показує, де твоя "
            "енергія стала і надійна, а де ти вбираєш і підсилюєш енергії оточуючих."
        ),
        "hd_what_p3_tpl": (
            "{{name}}, твоя розшифровка побудована на основі точних даних: "
            "{{birth_date}} о {{birth_time}} у {{birth_place}}. "
            "Саме ця мить визначила унікальний малюнок твого бодіграфу."
        ),
        "type_box_desc": (
            "Твій тип — це фундамент усього твого Дизайну. "
            "Він визначає, яка в тебе аура, як ти взаємодієш з іншими людьми "
            "та яка стратегія є правильною саме для тебе.\n\n"
            "[ТУТ CLAUDE API ДОДАСТЬ ДЕТАЛЬНИЙ ОПИС ТВОГО ТИПУ — його ауру, "
            "природні сильні сторони, як він проявляється в роботі та стосунках, "
            "і яке місце цей тип займає серед людства.]"
        ),
        "strategy_box_desc": (
            "Стратегія — це твій практичний компас у повсякденному житті. "
            "Коли ти дотримуєшся своєї стратегії, рішення приходять легше, "
            "стосунки складаються природно, а енергія витрачається правильно.\n\n"
            "[ТУТ CLAUDE API ДЕТАЛЬНО ОПИШЕ ТВОЮ КОНКРЕТНУ СТРАТЕГІЮ — "
            "як вона працює на практиці, типові ситуації застосування, "
            "що відбувається коли ти її порушуєш, і конкретні приклади з реального "
            "життя для твого типу та сфери інтересів.]"
        ),
        "authority_p1": (
            "Твій авторитет — це внутрішній голос, якому варто довіряти більше за "
            "розум і чужі думки. Саме через цей канал тіло і свідомість повідомляють "
            "тобі правильне рішення у потрібний момент.\n\n"
            "[ТУТ CLAUDE API ДЕТАЛЬНО ПОЯСНИТЬ ТВІЙ АВТОРИТЕТ — як він фізично "
            "проявляється в тілі, в які моменти він активується, як навчитися "
            "його розпізнавати і як відрізнити голос авторитету від страху чи "
            "соціальних очікувань.]"
        ),
        "authority_p2": (
            "Більшість людей приймають рішення через розум — аналізуючи, "
            "порівнюючи, прислухаючись до чужих порад. Але розум у Дизайні Людини "
            "не є авторитетом для рішень — він лише спостерігач.\n\n"
            "[ТУТ CLAUDE API НАВЕДЕ 3 ПРАКТИЧНІ ПОРАДИ — конкретні кроки для "
            "практики твого авторитету в щоденному житті, типові помилки та як "
            "їх уникати, і вправи для розвитку довіри до свого внутрішнього сигналу.]"
        ),
        "profile_p1": (
            "Твій профіль — це архетип твоєї душі, закодований у двох числах. "
            "Він визначає роль, яку ти граєш у житті, і тип стосунків, що будуть "
            "найбільш значущими та трансформативними для тебе.\n\n"
            "[ТУТ CLAUDE API ДЕТАЛЬНО ОПИШЕ ТВІЙ ПРОФІЛЬ — значення кожної лінії, "
            "як вони взаємодіють між собою, яка роль призначена тобі у цьому житті, "
            "і як профіль впливає на твій шлях навчання та розвитку.]"
        ),
        "profile_p2": (
            "[ТУТ CLAUDE API РОЗКРИЄ ПРОФІЛЬ У КОНТЕКСТІ СТОСУНКІВ ТА РОБОТИ — "
            "з ким тобі природно легко будувати зв'язки, яка робота відповідає "
            "твоєму архетипу, які виклики характерні для твого профілю і як "
            "перетворити їх на переваги.\n\n"
            "Також тут будуть конкретні поради для твого профілю: що підтримує "
            "твій розквіт, чого варто уникати, і які практики допоможуть тобі "
            "жити своєю роллю автентично.]"
        ),
        "centers_overview_p1": (
            "Бодіграф містить 9 енергетичних центрів — трансформаторів, подібних до чакр. "
            "Кожен центр управляє певними функціями тіла, розуму та душі."
        ),
        "centers_overview_p2": (
            "Визначені центри (закрашені) — джерела постійної та надійної енергії. "
            "Ти завжди маєш доступ до їхніх якостей і можеш покладатися на них. "
            "Невизначені центри (відкриті) — місця мудрості та навчання через інших. "
            "Вони вбирають і підсилюють енергії оточуючих."
        ),
        "centers_list_label": "Стан твоїх центрів:",
        "centers_table": [
            ("Центр Голови",       "Натхнення, тиск на роздуми"),
            ("Центр Розуму (Аджна)","Аналіз, концептуалізація"),
            ("Горловий Центр",     "Комунікація, маніфестація"),
            ("Центр Я / G-Центр",  "Ідентичність, напрямок, кохання"),
            ("Центр Серця / Воля", "Воля, самооцінка, матеріальне"),
            ("Сонячне Сплетіння",  "Емоції, почуття, хвилі"),
            ("Сакральний Центр",   "ЖиТТєва сила, сексуальність, праця"),
            ("Селезінковий Центр", "Інтуїція, здоров'я, виживання"),
            ("Центр Кореня",       "Адреналін, тиск, трансформація"),
        ],
        "center1_p1": (
            "[НАЗВА ЦЕНТРУ 1] — один з твоїх визначених центрів. "
            "Це означає, що ця енергія є постійною і надійною частиною твоєї натури.\n\n"
            "[ТУТ CLAUDE API ДЕТАЛЬНО ОПИШЕ ЦЕЙ ЦЕНТР — що він контролює в твоєму "
            "житті, як його визначеність проявляється в характері та поведінці, "
            "які сильні сторони він тобі дає і як максимально використовувати його "
            "потенціал.]"
        ),
        "center2_p1": (
            "[НАЗВА ЦЕНТРУ 2] — другий ключовий визначений центр твого бодіграфу.\n\n"
            "[ТУТ CLAUDE API ОПИШЕ ДРУГИЙ ЦЕНТР — його вплив на твоє повсякденне "
            "функціонування, взаємодію з іншими центрами, і конкретні прояви "
            "в житті. Як цей центр допомагає або ускладнює досягнення твоїх цілей.]"
        ),
        "center3_p1": (
            "[НАЗВА ЦЕНТРУ 3] — третій визначений центр, що формує твою унікальну "
            "енергетичну підпис.\n\n"
            "[ТУТ CLAUDE API ОПИШЕ ТРЕТІЙ ЦЕНТР — його роль у твоїй системі, "
            "як він взаємодіє з іншими визначеними центрами, і що це означає "
            "практично для твого способу бути у світі.]"
        ),
        "open_centers_p1": (
            "Відкриті (невизначені) центри — це не слабкість. Це місця, де ти "
            "найбільш гнучка, де ти вбираєш мудрість від інших і де знаходиться "
            "твій потенціал для глибокого навчання."
        ),
        "open_centers_p2": (
            "[ТУТ CLAUDE API ОПИШЕ ТВОЇ ВІДКРИТІ ЦЕНТРИ — які з 9 центрів є "
            "невизначеними, як їхня відкритість впливає на твої відносини та "
            "рішення, де ти найбільш схильна до зовнішнього тиску або кондиціювання, "
            "і як свідомо працювати з відкритими центрами замість того, щоб "
            "страждати від їх непостійності.]"
        ),
        "open_centers_watch": (
            "[ТУТ CLAUDE API НАВЕДЕ КОНКРЕТНІ СИТУАЦІЇ — коли відкриті центри "
            "можуть 'грати' тебе, як розпізнати що ти зараз під впливом чужої "
            "енергії, і прості практики для збереження автентичності.]"
        ),
        "signature_p1": (
            "Сигнатура — це емоційний стан, який ти відчуваєш, коли живеш у "
            "відповідності до свого Дизайну. Це твій внутрішній компас правильності "
            "напрямку.\n\n"
            "[ТУТ CLAUDE API ОПИШЕ ТВОЮ КОНКРЕТНУ СИГНАТУРУ — як вона фізично "
            "відчувається, в яких ситуаціях вона найяскравіша, і як навчитися "
            "культивувати цей стан.]"
        ),
        "not_self_p1": (
            "Не-Я тема — це сигнал тривоги. Це почуття, яке виникає, коли ти "
            "живеш всупереч своєму Дизайну, намагаєшся бути кимось іншим або "
            "ігноруєш свій авторитет.\n\n"
            "[ТУТ CLAUDE API ОПИШЕ ТВОЮ НЕ-Я ТЕМУ — конкретні ситуації коли вона "
            "виникає, як вона проявляється в тілі та поведінці, і що робити "
            "коли ти помічаєш цей стан.]"
        ),
        "life_theme_career": (
            "[ТУТ CLAUDE API НАПИШЕ ПЕРСОНАЛІЗОВАНИЙ АНАЛІЗ ДЛЯ КАР'ЄРИ]\n\n"
            "Твій Дизайн має унікальні вказівки щодо кар'єрного шляху. Поєднання "
            "твого типу, авторитету та профілю створює специфічний рецепт успіху — "
            "не той, що нав'язує суспільство, а той що відповідає твоїй справжній природі.\n\n"
            "Ключові теми для тебе: тип роботи що резонує, стиль взаємодії з "
            "колегами та керівниками, ознаки правильного vs неправильного місця роботи, "
            "і як використовувати свій авторитет при прийнятті кар'єрних рішень."
        ),
        "life_theme_relationships": (
            "[ТУТ CLAUDE API НАПИШЕ ПЕРСОНАЛІЗОВАНИЙ АНАЛІЗ ДЛЯ СТОСУНКІВ]\n\n"
            "Твоя аура та центри визначають унікальну динаміку у стосунках. "
            "Розуміння свого Дизайну допомагає будувати більш автентичні зв'язки "
            "і уникати повторюваних патернів, що виснажують.\n\n"
            "Ключові теми: яких партнерів ти природно притягуєш, де виникають "
            "конфлікти та як їх вирішувати через Дизайн, як твій авторитет "
            "допомагає у виборі стосунків."
        ),
        "life_theme_energy": (
            "[ТУТ CLAUDE API НАПИШЕ ПЕРСОНАЛІЗОВАНИЙ АНАЛІЗ ДЛЯ ЕНЕРГІЇ]\n\n"
            "Енергетична система у кожного типу різна. Те, що виснажує одних, "
            "живить інших. Розуміння свого енергетичного дизайну — ключ до "
            "стабільного здоров'я та продуктивності.\n\n"
            "Ключові теми: природний енергетичний ритм твого типу, що наповнює "
            "і що забирає енергію, оптимальний розпорядок дня, і чому порівняння "
            "себе з іншими типами шкідливе."
        ),
        "life_theme_self": (
            "[ТУТ CLAUDE API НАПИШЕ ПЕРСОНАЛІЗОВАНИЙ АНАЛІЗ ДЛЯ САМОПІЗНАННЯ]\n\n"
            "Дизайн Людини — найглибша карта самопізнання. Вона відповідає на питання "
            "не 'що мені робити', а 'хто я насправді' — і саме звідси починаються "
            "справжні зміни.\n\n"
            "Ключові теми: твоя справжня природа vs. кондиціювання, де ти "
            "найбільш автентична, що заважає жити своїм Дизайном, і покроковий "
            "шлях до декондиціювання."
        ),
        "recs_intro_career":        "Рекомендації для твого кар'єрного шляху:",
        "recs_intro_relationships": "Рекомендації для твоїх стосунків:",
        "recs_intro_energy":        "Рекомендації для твоєї енергії:",
        "recs_intro_self":          "Рекомендації для самопізнання:",
        "recs_career_1": [
            "Приймай важливі кар'єрні рішення лише через свій авторитет — не поспішай під тиском",
            "Відстежуй, коли твоя енергія природно зростає — це сигнал правильного напрямку",
            "Вчися казати 'ні' проєктам та пропозиціям, які не резонують з твоїм відчуттям",
            "Будуй репутацію через автентичність, а не через те, ким хочуть тебе бачити",
            "Щотижня виділяй час на відновлення — це підвищить продуктивність більше ніж понаднормова робота",
        ],
        "recs_career_2": [
            "[ТУТ CLAUDE API] Персоналізована рекомендація для твого типу у кар'єрі",
            "[ТУТ CLAUDE API] Як використовувати свій авторитет при переговорах та рішеннях",
            "[ТУТ CLAUDE API] Конкретна порада щодо твого виклику 'decisions' у роботі",
            "Веди щоденник кар'єрних рішень — відстежуй, які прийняті через авторитет, і порівнюй результати",
            "Знайди ментора або спільноту, що підтримує твою автентичність, а не нав'язує чужі шляхи",
        ],
        "recs_relationships_1": [
            "Дозволяй стосункам розвиватися у своєму темпі — не форсуй і не стримуй природний плин",
            "Твоя аура природно притягує певний тип людей — довіряй цьому процесу, не намагайся його контролювати",
            "Практикуй вразливість там, де відчуваєш безпеку та справжній резонанс",
            "Вчися розпізнавати, коли ти береш на себе чужі емоції через відкриті центри",
            "Регулярно проводь час на самоті — це не егоїзм, це необхідність для твого типу",
        ],
        "recs_relationships_2": [
            "[ТУТ CLAUDE API] Конкретна порада для стосунків відповідно до твого профілю",
            "[ТУТ CLAUDE API] Як авторитет допомагає у виборі партнера та побудові близькості",
            "[ТУТ CLAUDE API] Типові виклики твого типу у стосунках і як з ними працювати",
            "Говори партнеру про свій Дизайн — розуміння знімає багато непорозумінь та образ",
            "Встановлюй межі з любов'ю, спираючись на свій Не-Я сигнал як індикатор",
        ],
        "recs_energy_1": [
            "Поважай свої природні енергетичні цикли — не порівнюй себе з іншими типами та їхньою витривалістю",
            "Впроваджуй ранковий ритуал, що відповідає твоєму типу та авторитету, а не загальним рекомендаціям",
            "Відстежуй, які ситуації та люди забирають твою енергію — встанови чіткі межі",
            "Харчування та якісний сон — фундамент для правильної роботи твого Дизайну",
            "Фізична активність що відповідає твоєму типу відновлює краще за пасивний відпочинок",
        ],
        "recs_energy_2": [
            "[ТУТ CLAUDE API] Конкретні рекомендації щодо режиму дня для твого типу",
            "[ТУТ CLAUDE API] Як відкриті центри впливають на твою енергію і як з цим працювати",
            "[ТУТ CLAUDE API] Практики відновлення що підходять саме для твого Дизайну",
            "Веди журнал енергії: вранці та ввечері оцінюй рівень за шкалою 1-10, шукай патерни",
            "Експериментуй зі своєю стратегією протягом 30 днів — помічай зміни в енергетичному стані",
        ],
        "recs_self_1": [
            "Щоденна практика спостереження за собою без осуду — основа декондиціювання та самопізнання",
            "Веди щоденник рішень, прийнятих через авторитет, та відстежуй результати без очікувань",
            "Вивчи свій профіль глибше — він відповідає на питання 'чому я така' і 'чому мені легко це'",
            "Практикуй паузу перед відповіддю на важливі запити — дай своєму авторитету час проявитися",
            "Оточуй себе людьми, які приймають тебе справжньою, а не тою, якою ти 'мала б' бути",
        ],
        "recs_self_2": [
            "[ТУТ CLAUDE API] Головна рекомендація для твого шляху самопізнання",
            "[ТУТ CLAUDE API] Як розрізняти справжнє 'я' і кондиціювання у конкретних ситуаціях",
            "[ТУТ CLAUDE API] Практика специфічна для твого авторитету та профілю",
            "Щомісяця робіть огляд: де ти жила своїм Дизайном, а де відступала — без осуду, з цікавістю",
            "Знайди спільноту або практику Дизайну Людини — живе занурення прискорює трансформацію",
        ],
        "plan_week1_career":   "Тиждень 1: Спостерігай за своїм авторитетом у кар'єрних ситуаціях. Веди записи коли ти чуєш внутрішній сигнал і що відбувається після.",
        "plan_week2_career":   "Тиждень 2: Визнач 3 кар'єрні рішення що чекають. Застосуй стратегію і авторитет до кожного — не поспішай.",
        "plan_week3_career":   "Тиждень 3: Налаштуй робочий ритм відповідно до свого типу. Якщо генератор — слухай сакральний відгук. Якщо проектор — чекай запрошення.",
        "plan_week4_career":   "Тиждень 4: Підсумок місяця. Що змінилося? Де ти відчула найбільший резонанс? Що хочеш поглибити далі?",
        "plan_week1_relationships": "Тиждень 1: Спостерігай за своєю аурою у стосунках. Кому ти природно відкрита? З ким відчуваєш напругу без причини?",
        "plan_week2_relationships": "Тиждень 2: Практикуй паузу перед відповіддю на важливі запити від близьких. Дай авторитету час.",
        "plan_week3_relationships": "Тиждень 3: Проведи час на самоті щоб 'відмити' чужі енергії. Запиши що ти справді відчуваєш без впливу інших.",
        "plan_week4_relationships": "Тиждень 4: Поговори з кимось близьким про свій Дизайн. Поділися одним відкриттям про себе.",
        "plan_week1_energy":   "Тиждень 1: Веди журнал енергії. Ранок і вечір — оцінка 1-10. Шукай патерни що дає і що забирає силу.",
        "plan_week2_energy":   "Тиждень 2: Введи один новий ритуал відновлення що відповідає твоєму типу. Практикуй щодня 15-20 хвилин.",
        "plan_week3_energy":   "Тиждень 3: Визнач 3 'енергетичних вампіри' у своєму житті. Встанови одну нову межу з кожним.",
        "plan_week4_energy":   "Тиждень 4: Порівняй перший і останній день місяця. Як змінився рівень енергії? Що спрацювало найкраще?",
        "plan_week1_self":     "Тиждень 1: Щодня 10 хвилин тихого спостереження за собою. Без телефону, без завдань — просто бути.",
        "plan_week2_self":     "Тиждень 2: Прочитай про свій тип та профіль детально. Запиши 5 речей що резонують і 5 що дивують.",
        "plan_week3_self":     "Тиждень 3: Практикуй авторитет у трьох дрібних щоденних рішеннях. Відстежуй відчуття та результати.",
        "plan_week4_self":     "Тиждень 4: Напиши листа собі — що ти дізналась за місяць? Яка ти справжня? Що хочеш продовжувати?",
        "week_labels": ["Тиждень 1", "Тиждень 2", "Тиждень 3", "Тиждень 4"],
    },
    "ru": {
        "title_main":       "ДИЗАЙН ЧЕЛОВЕКА",
        "subtitle":         "Персональная расшифровка бодиграфа",
        "badge_basic":      "БАЗОВАЯ РАСШИФРОВКА · 20 СТРАНИЦ",
        "badge_full":       "ПОЛНАЯ РАСШИФРОВКА · 50 СТРАНИЦ",
        "label_date":       "Дата рождения:",
        "label_time":       "Время рождения:",
        "label_place":      "Место рождения:",
        "label_generated":  "Дата создания:",
        "welcome_title":    "Добро пожаловать,",
        "welcome_p1": "Вы приобрели персональную расшифровку Дизайна Человека — одну из самых точных систем самопознания, существующих сегодня.",
        "welcome_p2": "Эти знания уже помогли более 1 000 наших клиентов. Каждая расшифровка уникальна — так же, как уникален каждый из них.",
        "welcome_p3_tpl": "Эта расшифровка создана специально для вас на основе точных астрологических данных: {{birth_date}} в {{birth_time}} в {{birth_place}}.",
        "welcome_p4": "Откройте страницы этого документа с открытым сердцем — и вы узнаете о себе то, что всегда чувствовали, но не могли выразить словами.",
        "s01_num": "01", "s01_title": "Что такое Дизайн Человека",
        "s02_num": "02", "s02_title": "Твой Тип",
        "s02b_title": "Стратегия",
        "s03_num": "03", "s03_title": "Авторитет принятия решений",
        "s03b_title": "Авторитет в повседневной жизни",
        "s04_num": "04", "s04_title": "Твой Профиль",
        "s04b_title": "Профиль в отношениях и работе",
        "s05_num": "05", "s05_title": "Твой Бодиграф — ключевые центры",
        "s06_num": "06", "s06_title": "Определённые центры — детали",
        "s06b_title": "Второй определённый центр",
        "s06c_title": "Третий определённый центр",
        "s07_num": "07", "s07_title": "Открытые центры — где ты впитываешь энергию",
        "s08_num": "08", "s08_title": "Сигнатура и Не-Я тема",
        "s09_num": "09", "s09_title": "Твоя Тема Жизни",
        "s10_num": "10", "s10_title": "Практические рекомендации",
        "s10b_title": "Ещё 5 рекомендаций",
        "s11_num": "11", "s11_title": "Твои следующие 30 дней",
        "your_type":      "Твой тип:",
        "your_strategy":  "Стратегия:",
        "your_authority": "Авторитет:",
        "your_profile":   "Твой профиль:",
        "your_signature": "Сигнатура:",
        "your_not_self":  "Не-Я тема:",
        "page_label":     "стр.",
        "contact_label":  "Связь и поддержка:",
        "contact_email":  "humandesign.finance@gmail.com",
        "copyright":      "© 2026 Human Design UA · Все права защищены",
        "brand":          "Human Design UA",
        "unique":         "Ты — уникальна.",
        "closing_msg": (
            "Этот документ — твой первый шаг к глубокому пониманию себя. "
            "Каждый день, когда ты живёшь в соответствии со своим Дизайном, "
            "ты становишься больше собой. Доверяй своему телу, слушай свой авторитет."
        ),
        "hd_what_p1": "Дизайн Человека — это синтез древних и современных знаний: астрологии, Каббалы, Ицзина и квантовой физики. Система даёт точную карту твоей энергетической структуры.",
        "hd_what_p2": "Твоя карта была зафиксирована в момент рождения и уникальна, как отпечаток пальца. Она показывает, где твоя энергия стабильна, а где ты впитываешь энергии окружающих.",
        "hd_what_p3_tpl": "{{name}}, твоя расшифровка построена на точных данных: {{birth_date}} в {{birth_time}} в {{birth_place}}.",
        "type_box_desc": "Твой тип — фундамент всего Дизайна. [ТУТ CLAUDE API ДЕТАЛЬНО ОПИШЕ ТИП]",
        "strategy_box_desc": "Стратегия — практический компас в жизни. [ТУТ CLAUDE API ОПИШЕ СТРАТЕГІЮ]",
        "authority_p1": "Твой авторитет — внутренний голос, которому стоит доверять. [ТУТ CLAUDE API]",
        "authority_p2": "Большинство людей принимают решения через ум. Но ум — не авторитет. [ТУТ CLAUDE API 3 СОВЕТА]",
        "profile_p1": "Твой профиль — архетип души. [ТУТ CLAUDE API ДЕТАЛЬНО]",
        "profile_p2": "[ТУТ CLAUDE API — ПРОФИЛЬ В ОТНОШЕНИЯХ И РАБОТЕ]",
        "centers_overview_p1": "Бодиграф содержит 9 энергетических центров. Каждый управляет определёнными функциями тела, разума и духа.",
        "centers_overview_p2": "Определённые центры — источники стабильной энергии. Неопределённые — места мудрости через взаимодействие с другими.",
        "centers_list_label": "Состояние твоих центров:",
        "centers_table": [
            ("Центр Головы",        "Вдохновение, давление на размышления"),
            ("Центр Разума (Аджна)", "Анализ, концептуализация"),
            ("Горловой Центр",      "Коммуникация, манифестация"),
            ("Центр Я / G-Центр",   "Идентичность, направление, любовь"),
            ("Центр Сердца / Воля", "Воля, самооценка, материальное"),
            ("Солнечное Сплетение", "Эмоции, чувства, волны"),
            ("Сакральный Центр",    "Жизненная сила, сексуальность, труд"),
            ("Селезёночный Центр",  "Интуиция, здоровье, выживание"),
            ("Центр Корня",         "Адреналин, давление, трансформация"),
        ],
        "center1_p1": "[ЦЕНТР 1] — определённый центр. [ТУТ CLAUDE API ДЕТАЛЬНО]",
        "center2_p1": "[ЦЕНТР 2] — второй ключевой центр. [ТУТ CLAUDE API]",
        "center3_p1": "[ЦЕНТР 3] — третий центр. [ТУТ CLAUDE API]",
        "open_centers_p1": "Открытые центры — не слабость. Это места гибкости и мудрости через других.",
        "open_centers_p2": "[ТУТ CLAUDE API — ТВОИ ОТКРЫТЫЕ ЦЕНТРЫ И ИХ ВЛИЯНИЕ]",
        "open_centers_watch": "[ТУТ CLAUDE API — КОНКРЕТНЫЕ СИТУАЦИИ И ПРАКТИКИ]",
        "signature_p1": "Сигнатура — эмоциональное состояние при жизни в Дизайне. [ТУТ CLAUDE API]",
        "not_self_p1": "Не-Я тема — сигнал тревоги. Возникает когда ты живёшь вопреки Дизайну. [ТУТ CLAUDE API]",
        "life_theme_career": "[ТУТ CLAUDE API — ПЕРСОНАЛИЗИРОВАННЫЙ АНАЛИЗ ДЛЯ КАРЬЕРЫ]",
        "life_theme_relationships": "[ТУТ CLAUDE API — ПЕРСОНАЛИЗИРОВАННЫЙ АНАЛИЗ ДЛЯ ОТНОШЕНИЙ]",
        "life_theme_energy": "[ТУТ CLAUDE API — ПЕРСОНАЛИЗИРОВАННЫЙ АНАЛИЗ ДЛЯ ЭНЕРГИИ]",
        "life_theme_self": "[ТУТ CLAUDE API — ПЕРСОНАЛИЗИРОВАННЫЙ АНАЛИЗ ДЛЯ САМОПОЗНАНИЯ]",
        "recs_intro_career": "Рекомендации для твоего карьерного пути:",
        "recs_intro_relationships": "Рекомендации для твоих отношений:",
        "recs_intro_energy": "Рекомендации для твоей энергии:",
        "recs_intro_self": "Рекомендации для самопознания:",
        "recs_career_1": ["[КЛОД REC 1]","[КЛОД REC 2]","[КЛОД REC 3]","[КЛОД REC 4]","[КЛОД REC 5]"],
        "recs_career_2": ["[КЛОД REC 6]","[КЛОД REC 7]","[КЛОД REC 8]","[КЛОД REC 9]","[КЛОД REC 10]"],
        "recs_relationships_1": ["[КЛОД REC 1]","[КЛОД REC 2]","[КЛОД REC 3]","[КЛОД REC 4]","[КЛОД REC 5]"],
        "recs_relationships_2": ["[КЛОД REC 6]","[КЛОД REC 7]","[КЛОД REC 8]","[КЛОД REC 9]","[КЛОД REC 10]"],
        "recs_energy_1": ["[КЛОД REC 1]","[КЛОД REC 2]","[КЛОД REC 3]","[КЛОД REC 4]","[КЛОД REC 5]"],
        "recs_energy_2": ["[КЛОД REC 6]","[КЛОД REC 7]","[КЛОД REC 8]","[КЛОД REC 9]","[КЛОД REC 10]"],
        "recs_self_1": ["[КЛОД REC 1]","[КЛОД REC 2]","[КЛОД REC 3]","[КЛОД REC 4]","[КЛОД REC 5]"],
        "recs_self_2": ["[КЛОД REC 6]","[КЛОД REC 7]","[КЛОД REC 8]","[КЛОД REC 9]","[КЛОД REC 10]"],
        "plan_week1_career": "Неделя 1: Наблюдай за авторитетом в карьерных ситуациях.",
        "plan_week2_career": "Неделя 2: Определи 3 решения. Применяй стратегию.",
        "plan_week3_career": "Неделя 3: Настрой рабочий ритм под свой тип.",
        "plan_week4_career": "Неделя 4: Подведи итоги. Что изменилось?",
        "plan_week1_relationships": "Неделя 1: Наблюдай за аурой в отношениях.",
        "plan_week2_relationships": "Неделя 2: Практикуй паузу перед ответом.",
        "plan_week3_relationships": "Неделя 3: Время наедине для очищения.",
        "plan_week4_relationships": "Неделя 4: Поделись открытием с близким.",
        "plan_week1_energy": "Неделя 1: Веди журнал энергии утром и вечером.",
        "plan_week2_energy": "Неделя 2: Введи один ритуал восстановления.",
        "plan_week3_energy": "Неделя 3: Определи энергетических вампиров.",
        "plan_week4_energy": "Неделя 4: Сравни начало и конец месяца.",
        "plan_week1_self": "Неделя 1: 10 минут тихого наблюдения за собой ежедневно.",
        "plan_week2_self": "Неделя 2: Изучи свой тип и профиль детально.",
        "plan_week3_self": "Неделя 3: Практикуй авторитет в трёх решениях.",
        "plan_week4_self": "Неделя 4: Напиши письмо себе о месяце.",
        "week_labels": ["Неделя 1", "Неделя 2", "Неделя 3", "Неделя 4"],
    },
    "en": {
        "title_main":       "HUMAN DESIGN",
        "subtitle":         "Personal Bodygraph Reading",
        "badge_basic":      "BASIC READING · 20 PAGES",
        "badge_full":       "FULL READING · 50 PAGES",
        "label_date":       "Date of birth:",
        "label_time":       "Time of birth:",
        "label_place":      "Place of birth:",
        "label_generated":  "Generated on:",
        "welcome_title":    "Welcome,",
        "welcome_p1": "You have purchased a personal Human Design reading — one of the most accurate self-knowledge systems available today.",
        "welcome_p2": "This knowledge has already helped over 1,000 of our clients. Every reading is unique — just like every person.",
        "welcome_p3_tpl": "This reading was created specifically for you based on your precise birth data: {{birth_date}} at {{birth_time}} in {{birth_place}}.",
        "welcome_p4": "Open these pages with an open heart — and you'll discover about yourself what you always felt but never had words to describe.",
        "s01_num": "01", "s01_title": "What is Human Design",
        "s02_num": "02", "s02_title": "Your Type",
        "s02b_title": "Your Strategy",
        "s03_num": "03", "s03_title": "Decision-Making Authority",
        "s03b_title": "Authority in Daily Life",
        "s04_num": "04", "s04_title": "Your Profile",
        "s04b_title": "Profile in Relationships & Work",
        "s05_num": "05", "s05_title": "Your Bodygraph — Key Centers",
        "s06_num": "06", "s06_title": "Defined Centers — Details",
        "s06b_title": "Second Defined Center",
        "s06c_title": "Third Defined Center",
        "s07_num": "07", "s07_title": "Open Centers — Where You Absorb Energy",
        "s08_num": "08", "s08_title": "Signature & Not-Self Theme",
        "s09_num": "09", "s09_title": "Your Life Theme",
        "s10_num": "10", "s10_title": "Practical Recommendations",
        "s10b_title": "5 More Recommendations",
        "s11_num": "11", "s11_title": "Your Next 30 Days",
        "your_type":      "Your type:",
        "your_strategy":  "Strategy:",
        "your_authority": "Authority:",
        "your_profile":   "Your profile:",
        "your_signature": "Signature:",
        "your_not_self":  "Not-Self theme:",
        "page_label":     "p.",
        "contact_label":  "Support & contact:",
        "contact_email":  "humandesign.finance@gmail.com",
        "copyright":      "© 2026 Human Design UA · All rights reserved",
        "brand":          "Human Design UA",
        "unique":         "You are unique.",
        "closing_msg": (
            "This document is your first step toward deeper self-understanding. "
            "Every day you live in alignment with your Design, you become more yourself. "
            "Trust your body, listen to your authority."
        ),
        "hd_what_p1": "Human Design is a synthesis of ancient and modern knowledge: astrology, Kabbalah, the I Ching, and quantum physics. It provides an accurate map of your energetic structure.",
        "hd_what_p2": "Your Human Design chart was fixed at the moment of your birth and is as unique as a fingerprint. It shows where your energy is consistent and where you absorb others' energies.",
        "hd_what_p3_tpl": "{{name}}, your reading is built on precise data: {{birth_date}} at {{birth_time}} in {{birth_place}}.",
        "type_box_desc": "Your type is the foundation of your Design. [CLAUDE API WILL DESCRIBE YOUR TYPE IN DETAIL]",
        "strategy_box_desc": "Strategy is your practical compass in daily life. [CLAUDE API WILL DESCRIBE YOUR STRATEGY]",
        "authority_p1": "Your authority is the inner voice to trust above the mind. [CLAUDE API WILL EXPLAIN IN DETAIL]",
        "authority_p2": "Most people decide through the mind. But the mind is not an authority for decisions. [CLAUDE API — 3 PRACTICAL TIPS]",
        "profile_p1": "Your profile is the archetype of your soul. [CLAUDE API WILL DESCRIBE IN DETAIL]",
        "profile_p2": "[CLAUDE API — PROFILE IN RELATIONSHIPS AND WORK]",
        "centers_overview_p1": "The bodygraph contains 9 energy centers. Each governs specific functions of body, mind, and spirit.",
        "centers_overview_p2": "Defined centers are sources of consistent energy. Undefined centers are places of wisdom through interaction with others.",
        "centers_list_label": "Your centers status:",
        "centers_table": [
            ("Head Center",        "Inspiration, pressure to think"),
            ("Ajna Center",        "Analysis, conceptualization"),
            ("Throat Center",      "Communication, manifestation"),
            ("G / Self Center",    "Identity, direction, love"),
            ("Heart / Ego Center", "Will, self-worth, material"),
            ("Solar Plexus",       "Emotions, feelings, waves"),
            ("Sacral Center",      "Life force, sexuality, work"),
            ("Spleen Center",      "Intuition, health, survival"),
            ("Root Center",        "Adrenaline, pressure, transformation"),
        ],
        "center1_p1": "[CENTER 1] is a defined center. [CLAUDE API WILL DESCRIBE IN DETAIL]",
        "center2_p1": "[CENTER 2] is the second key center. [CLAUDE API]",
        "center3_p1": "[CENTER 3] is the third center. [CLAUDE API]",
        "open_centers_p1": "Open centers are not weakness. They are places of flexibility and wisdom through others.",
        "open_centers_p2": "[CLAUDE API — YOUR OPEN CENTERS AND THEIR INFLUENCE]",
        "open_centers_watch": "[CLAUDE API — SPECIFIC SITUATIONS AND PRACTICES]",
        "signature_p1": "The Signature is the emotional state when living in Design. [CLAUDE API WILL DESCRIBE YOURS]",
        "not_self_p1": "The Not-Self theme is an alarm signal. It appears when living against your Design. [CLAUDE API]",
        "life_theme_career": "[CLAUDE API — PERSONALIZED ANALYSIS FOR CAREER]",
        "life_theme_relationships": "[CLAUDE API — PERSONALIZED ANALYSIS FOR RELATIONSHIPS]",
        "life_theme_energy": "[CLAUDE API — PERSONALIZED ANALYSIS FOR ENERGY]",
        "life_theme_self": "[CLAUDE API — PERSONALIZED ANALYSIS FOR SELF-KNOWLEDGE]",
        "recs_intro_career": "Recommendations for your career path:",
        "recs_intro_relationships": "Recommendations for your relationships:",
        "recs_intro_energy": "Recommendations for your energy:",
        "recs_intro_self": "Recommendations for self-knowledge:",
        "recs_career_1": ["[CLAUDE REC 1]","[CLAUDE REC 2]","[CLAUDE REC 3]","[CLAUDE REC 4]","[CLAUDE REC 5]"],
        "recs_career_2": ["[CLAUDE REC 6]","[CLAUDE REC 7]","[CLAUDE REC 8]","[CLAUDE REC 9]","[CLAUDE REC 10]"],
        "recs_relationships_1": ["[CLAUDE REC 1]","[CLAUDE REC 2]","[CLAUDE REC 3]","[CLAUDE REC 4]","[CLAUDE REC 5]"],
        "recs_relationships_2": ["[CLAUDE REC 6]","[CLAUDE REC 7]","[CLAUDE REC 8]","[CLAUDE REC 9]","[CLAUDE REC 10]"],
        "recs_energy_1": ["[CLAUDE REC 1]","[CLAUDE REC 2]","[CLAUDE REC 3]","[CLAUDE REC 4]","[CLAUDE REC 5]"],
        "recs_energy_2": ["[CLAUDE REC 6]","[CLAUDE REC 7]","[CLAUDE REC 8]","[CLAUDE REC 9]","[CLAUDE REC 10]"],
        "recs_self_1": ["[CLAUDE REC 1]","[CLAUDE REC 2]","[CLAUDE REC 3]","[CLAUDE REC 4]","[CLAUDE REC 5]"],
        "recs_self_2": ["[CLAUDE REC 6]","[CLAUDE REC 7]","[CLAUDE REC 8]","[CLAUDE REC 9]","[CLAUDE REC 10]"],
        "plan_week1_career": "Week 1: Observe your authority in career situations.",
        "plan_week2_career": "Week 2: Identify 3 pending decisions. Apply strategy.",
        "plan_week3_career": "Week 3: Align work rhythm with your type.",
        "plan_week4_career": "Week 4: Monthly review. What changed?",
        "plan_week1_relationships": "Week 1: Observe your aura in relationships.",
        "plan_week2_relationships": "Week 2: Practice pausing before important responses.",
        "plan_week3_relationships": "Week 3: Solo time to clear others' energies.",
        "plan_week4_relationships": "Week 4: Share one discovery with someone close.",
        "plan_week1_energy": "Week 1: Keep an energy journal morning and evening.",
        "plan_week2_energy": "Week 2: Introduce one restoration ritual.",
        "plan_week3_energy": "Week 3: Identify energy drains. Set one new boundary each.",
        "plan_week4_energy": "Week 4: Compare day 1 vs day 30. What worked?",
        "plan_week1_self": "Week 1: 10 minutes of quiet self-observation daily.",
        "plan_week2_self": "Week 2: Study your type and profile in depth.",
        "plan_week3_self": "Week 3: Practice authority in three daily decisions.",
        "plan_week4_self": "Week 4: Write a letter to yourself about the month.",
        "week_labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
    },
}


# ─── PDF Class ────────────────────────────────────────────────────────────────
class HumanDesignPDF(FPDF):
    def __init__(self, locale, plan, name):
        super().__init__()
        self.locale      = locale
        self.plan        = plan
        self.client_name = name
        self.t           = T[locale]
        self._page_count = 0
        self.set_margins(0, 0, 0)
        self.set_auto_page_break(False)

    def _add_fonts(self):
        self.add_font("DejaVu",     "", os.path.join(FONTS_DIR, "DejaVuSans.ttf"))
        self.add_font("DejaVuBold", "", os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf"))

    # ── Page management ───────────────────────────────────────────────────────
    def add_page(self, *args, **kwargs):
        super().add_page(*args, **kwargs)
        self._page_count += 1
        # Full dark background on every page
        self.set_fill_color(*BG)
        self.rect(0, 0, 210, 297, "F")

    # ── Shorthand geometry ────────────────────────────────────────────────────
    def _lm(self): return 20      # left margin
    def _w(self):  return 170     # content width
    def _pw(self): return 210     # page width

    # ── Decorative primitives ─────────────────────────────────────────────────
    def _amber_line(self, y, x=20, w=170, thickness=0.4):
        self.set_draw_color(*AMBER)
        self.set_line_width(thickness)
        self.line(x, y, x + w, y)

    def _orange_accent_bar(self, h=297):
        """Left edge orange accent bar (full page height)."""
        self.set_fill_color(*ORANGE)
        self.rect(0, 0, 5, h, "F")

    def _cover_glow(self):
        """Warm orange gradient glow effect via overlapping rects."""
        layers = [
            (0,   0,  210, 120, (35, 18,  5)),
            (0,   0,  210,  90, (48, 24,  6)),
            (0,   0,  160,  70, (58, 30,  7)),
            (0,   0,  120,  55, (68, 36,  8)),
            (0,   0,   90,  40, (75, 40,  9)),
            (0,   0,   65,  28, (80, 42, 10)),
        ]
        for x, y, rw, rh, col in layers:
            self.set_fill_color(*col)
            self.rect(x, y, rw, rh, "F")

    def _draw_star_symbol(self, cx, cy, size=8):
        """Draw ✦ as 4-pointed cross using lines."""
        self.set_draw_color(*ORANGE_L)
        self.set_line_width(1.2)
        self.line(cx, cy - size, cx, cy + size)
        self.line(cx - size, cy, cx + size, cy)
        diag = size * 0.45
        self.set_line_width(0.6)
        self.line(cx - diag, cy - diag, cx + diag, cy + diag)
        self.line(cx - diag, cy + diag, cx + diag, cy - diag)
        # Center dot
        self.set_fill_color(*ORANGE_L)
        self.ellipse(cx - 1, cy - 1, 2, 2, "F")

    def _section_header(self, num, title, with_bar=True):
        """Section header: left orange bar + big number + title + amber underline."""
        if with_bar:
            self._orange_accent_bar()
        y0 = self.get_y()
        # Large section number
        self.set_xy(8, y0)
        self.set_font("DejaVuBold", "", 36)
        self.set_text_color(*ORANGE)
        self.cell(22, 18, num, ln=0)
        # Section title
        self.set_xy(32, y0 + 2)
        self.set_font("DejaVuBold", "", 17)
        self.set_text_color(*W_WHITE)
        self.cell(self._w() - 12, 14, title, ln=1)
        # Amber underline
        self._amber_line(self.get_y(), x=8, w=194, thickness=0.6)
        self.ln(7)

    def _body(self, text, size=10, color=None, indent=0, align="J"):
        if color is None:
            color = CREAM
        self.set_font("DejaVu", "", size)
        self.set_text_color(*color)
        self.set_x(self._lm() + indent)
        self.multi_cell(self._w() - indent, 6, text, align=align, new_x="LMARGIN", new_y="NEXT")
        self.set_x(self._lm())
        self.ln(2)

    def _highlight_box(self, label, value, bg=None):
        """Amber-bordered highlight box with label + large value."""
        if bg is None:
            bg = (18, 12, 6)
        box_y = self.get_y()
        bh = 22
        self.set_fill_color(*bg)
        self.rect(self._lm(), box_y, self._w(), bh, "F")
        # Left amber bar
        self.set_fill_color(*AMBER)
        self.rect(self._lm(), box_y, 4, bh, "F")
        # Amber border
        self.set_draw_color(*AMBER)
        self.set_line_width(0.4)
        self.rect(self._lm(), box_y, self._w(), bh)
        # Label
        self.set_xy(self._lm() + 8, box_y + 2)
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(60, 5, label)
        # Value
        self.set_xy(self._lm() + 8, box_y + 8)
        self.set_font("DejaVuBold", "", 13)
        self.set_text_color(*ORANGE_L)
        self.cell(self._w() - 12, 10, value)
        self.set_y(box_y + bh + 4)

    def _big_value_box(self, label, value):
        """Large centered value box with amber border."""
        box_y = self.get_y()
        bh = 30
        self.set_fill_color(18, 12, 6)
        self.rect(self._lm(), box_y, self._w(), bh, "F")
        self.set_draw_color(*AMBER)
        self.set_line_width(0.7)
        self.rect(self._lm(), box_y, self._w(), bh)
        # Top amber bar
        self.set_fill_color(*AMBER)
        self.rect(self._lm(), box_y, self._w(), 4, "F")
        self.set_xy(self._lm(), box_y + 6)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*DIM)
        self.cell(self._w(), 5, label, align="C")
        self.set_xy(self._lm(), box_y + 13)
        self.set_font("DejaVuBold", "", 20)
        self.set_text_color(*ORANGE_L)
        self.cell(self._w(), 14, value, align="C")
        self.set_y(box_y + bh + 5)

    def _bullet(self, text, num=None):
        """Bullet point or numbered item."""
        y0 = self.get_y()
        self.set_x(self._lm())
        if num is not None:
            self.set_font("DejaVuBold", "", 9)
            self.set_text_color(*ORANGE)
            self.cell(8, 6, f"{num}.", ln=0)
            self.set_x(self._lm() + 8)
        else:
            self.set_font("DejaVuBold", "", 12)
            self.set_text_color(*AMBER)
            self.cell(7, 6, "✦", ln=0)
            self.set_x(self._lm() + 7)
        self.set_font("DejaVu", "", 9.5)
        self.set_text_color(*CREAM)
        self.multi_cell(self._w() - (8 if num else 7), 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def _week_box(self, label, content):
        """Week box for 30-day plan."""
        box_y = self.get_y()
        bh = 32
        if box_y + bh > 278:
            return
        self.set_fill_color(15, 10, 5)
        self.rect(self._lm(), box_y, self._w(), bh, "F")
        self.set_fill_color(*ORANGE)
        self.rect(self._lm(), box_y, self._w(), 6, "F")
        self.set_xy(self._lm(), box_y + 0.5)
        self.set_font("DejaVuBold", "", 8)
        self.set_text_color(*BG)
        self.cell(self._w(), 5, label, align="C")
        self.set_xy(self._lm(), box_y + 9)
        self.set_font("DejaVu", "", 8.5)
        self.set_text_color(*CREAM)
        self.multi_cell(self._w() - 4, 5.5, content, new_x="LMARGIN", new_y="NEXT")
        self.set_y(box_y + bh + 4)

    def _page_header(self, name):
        """Small header: top-right dim text."""
        self.set_xy(0, 6)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*DIM)
        self.cell(self._pw() - 8, 5, f"ДИЗАЙН ЛЮДИНИ  ·  {name}", align="R")

    def _page_number(self):
        """Bottom center page number."""
        self.set_xy(0, 285)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*MUTED)
        self.cell(self._pw(), 6, f"— {self._page_count} —", align="C")

    def _interp(self, text, name="", birth_date="", birth_time="", birth_place=""):
        return (text
                .replace("{{name}}", name)
                .replace("{{birth_date}}", birth_date)
                .replace("{{birth_time}}", birth_time)
                .replace("{{birth_place}}", birth_place))

    # ════════════════════════════════════════════════════════════════════════
    # PAGE BUILDERS
    # ════════════════════════════════════════════════════════════════════════

    # ── Page 1: COVER ────────────────────────────────────────────────────────
    def build_cover(self, name, birth_date, birth_time, birth_place, plan):
        self.add_page()
        t = self.t

        # Warm glow effect
        self._cover_glow()

        # Large ✦ at top center
        self._draw_star_symbol(105, 28, size=10)

        # Amber separator line near top
        self._amber_line(46, x=25, w=160, thickness=0.5)
        self._amber_line(48, x=40, w=130, thickness=0.2)

        # "ДИЗАЙН ЛЮДИНИ"
        self.set_y(54)
        self.set_font("DejaVuBold", "", 26)
        self.set_text_color(*AMBER)
        self.cell(self._pw(), 13, t["title_main"], align="C", new_x="LMARGIN", new_y="NEXT")

        # Person's name — very large
        self.set_font("DejaVuBold", "", 36)
        self.set_text_color(*W_WHITE)
        self.cell(self._pw(), 20, name, align="C", new_x="LMARGIN", new_y="NEXT")

        # Subtitle
        self.set_font("DejaVu", "", 11)
        self.set_text_color(*MUTED)
        self.cell(self._pw(), 8, t["subtitle"], align="C", new_x="LMARGIN", new_y="NEXT")

        # Gold separator
        self._amber_line(110, x=30, w=150, thickness=0.6)
        self._amber_line(112, x=50, w=110, thickness=0.2)

        # Birth data block
        self.set_y(120)
        items = [
            (t["label_date"],  birth_date),
            (t["label_time"],  birth_time),
            (t["label_place"], birth_place),
        ]
        for lbl, val in items:
            self.set_x(0)
            self.set_font("DejaVu", "", 9)
            self.set_text_color(*MUTED)
            self.cell(self._pw() / 2, 8, lbl, align="R")
            self.set_font("DejaVuBold", "", 9)
            self.set_text_color(*CREAM)
            self.cell(5, 8, "")
            self.cell(self._pw() / 2 - 5, 8, val, align="L", new_x="LMARGIN", new_y="NEXT")

        # Generated date
        self.set_x(0)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(*MUTED)
        self.cell(self._pw() / 2, 8, t["label_generated"], align="R")
        self.set_font("DejaVuBold", "", 9)
        self.set_text_color(*DIM)
        self.cell(5, 8, "")
        self.cell(self._pw() / 2 - 5, 8, date.today().strftime("%d.%m.%Y"), align="L",
                  new_x="LMARGIN", new_y="NEXT")

        # Badge
        badge = t["badge_full"] if plan == "full" else t["badge_basic"]
        badge_w, badge_h = 120, 14
        badge_x = (self._pw() - badge_w) / 2
        badge_y = 183
        self.set_fill_color(*ORANGE)
        self.rect(badge_x, badge_y, badge_w, badge_h, "F")
        self.set_xy(badge_x, badge_y + 1)
        self.set_font("DejaVuBold", "", 9.5)
        self.set_text_color(*BG)
        self.cell(badge_w, badge_h - 2, badge, align="C")

        # Bottom separator
        self._amber_line(205, x=20, w=170, thickness=0.5)

        # Bottom decorative stars
        for sx, sy, sz in [(50, 225, 6), (160, 235, 5), (105, 255, 4), (75, 270, 3.5), (138, 268, 4)]:
            self._draw_star_symbol(sx, sy, size=sz)

        self._page_number()

    # ── Page 2: WELCOME ──────────────────────────────────────────────────────
    def build_welcome(self, name, birth_date, birth_time, birth_place):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)

        self.set_y(22)
        # "Вітаємо, NAME!"
        self.set_x(self._lm())
        self.set_font("DejaVuBold", "", 22)
        self.set_text_color(*ORANGE_L)
        self.cell(self._w(), 13, f"{t['welcome_title']} {name}!", new_x="LMARGIN", new_y="NEXT")

        self._amber_line(self.get_y(), x=self._lm(), w=self._w(), thickness=0.5)
        self.ln(8)

        for para_key in ["welcome_p1", "welcome_p2", "welcome_p4"]:
            self._body(t[para_key], size=11)
            self.ln(3)

        # Personalized paragraph
        p3 = self._interp(t["welcome_p3_tpl"], name, birth_date, birth_time, birth_place)
        self._body(p3, size=11, color=AMBER)
        self.ln(3)

        self._page_number()

    # ── Page 3: WHAT IS HD ───────────────────────────────────────────────────
    def build_what_is_hd(self, name, birth_date, birth_time, birth_place):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s01_num"], t["s01_title"], with_bar=False)
        self._body(t["hd_what_p1"], size=10)
        self._body(t["hd_what_p2"], size=10)
        self.ln(3)
        self._amber_line(self.get_y(), x=self._lm(), w=80, thickness=0.3)
        self.ln(6)
        p3 = self._interp(t["hd_what_p3_tpl"], name, birth_date, birth_time, birth_place)
        self._body(p3, size=10, color=AMBER)
        self._page_number()

    # ── Page 4: YOUR TYPE (part 1) ───────────────────────────────────────────
    def build_type_p1(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s02_num"], t["s02_title"], with_bar=False)
        self._big_value_box(t["your_type"], "[ТИП]")
        self._body(t["type_box_desc"], size=10)
        self._page_number()

    # ── Page 5: YOUR TYPE (part 2) — Strategy ───────────────────────────────
    def build_type_p2(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s02_num"], t["s02b_title"], with_bar=False)
        self._big_value_box(t["your_strategy"], "[СТРАТЕГІЯ]")
        self._body(t["strategy_box_desc"], size=10)
        self._page_number()

    # ── Page 6: AUTHORITY (part 1) ───────────────────────────────────────────
    def build_authority_p1(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s03_num"], t["s03_title"], with_bar=False)
        self._big_value_box(t["your_authority"], "[АВТОРИТЕТ]")
        self._body(t["authority_p1"], size=10)
        self._page_number()

    # ── Page 7: AUTHORITY (part 2) ───────────────────────────────────────────
    def build_authority_p2(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s03_num"], t["s03b_title"], with_bar=False)
        self._body(t["authority_p2"], size=10)
        self._page_number()

    # ── Page 8: PROFILE (part 1) ─────────────────────────────────────────────
    def build_profile_p1(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s04_num"], t["s04_title"], with_bar=False)
        self._big_value_box(t["your_profile"], "[ПРОФІЛЬ]")
        self._body(t["profile_p1"], size=10)
        self._page_number()

    # ── Page 9: PROFILE (part 2) ─────────────────────────────────────────────
    def build_profile_p2(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s04_num"], t["s04b_title"], with_bar=False)
        self._body(t["profile_p2"], size=10)
        self._page_number()

    # ── Page 10: CENTERS OVERVIEW ────────────────────────────────────────────
    def build_centers_overview(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s05_num"], t["s05_title"], with_bar=False)
        self._body(t["centers_overview_p1"], size=10)
        self._body(t["centers_overview_p2"], size=10)
        self.ln(3)

        # Centers table
        self.set_x(self._lm())
        self.set_font("DejaVuBold", "", 8)
        self.set_text_color(*AMBER)
        self.cell(self._w(), 6, t["centers_list_label"], new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        for i, (cname, cdesc) in enumerate(t["centers_table"]):
            row_y = self.get_y()
            bg = (14, 10, 5) if i % 2 == 0 else (10, 7, 3)
            self.set_fill_color(*bg)
            self.rect(self._lm(), row_y, self._w(), 8, "F")
            # Left colored dot
            self.set_fill_color(*ORANGE)
            self.ellipse(self._lm() + 1, row_y + 2.5, 3, 3, "F")
            self.set_xy(self._lm() + 7, row_y + 1)
            self.set_font("DejaVuBold", "", 8.5)
            self.set_text_color(*W_WHITE)
            self.cell(55, 6, cname)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(*MUTED)
            self.cell(self._w() - 62, 6, cdesc, new_x="LMARGIN", new_y="NEXT")

        self._page_number()

    # ── Pages 11-13: CENTERS detail ──────────────────────────────────────────
    def _build_center_page(self, name, sec_num, sec_title, content_key):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(sec_num, sec_title, with_bar=False)
        self._body(t[content_key], size=10)
        self._page_number()

    def build_center1(self, name):
        self._build_center_page(name, self.t["s06_num"], self.t["s06_title"], "center1_p1")

    def build_center2(self, name):
        self._build_center_page(name, self.t["s06_num"], self.t["s06b_title"], "center2_p1")

    def build_center3(self, name):
        self._build_center_page(name, self.t["s06_num"], self.t["s06c_title"], "center3_p1")

    # ── Page 14: OPEN CENTERS ────────────────────────────────────────────────
    def build_open_centers(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s07_num"], t["s07_title"], with_bar=False)
        self._body(t["open_centers_p1"], size=10)
        self.ln(2)
        self._body(t["open_centers_p2"], size=10)
        self.ln(2)
        self._amber_line(self.get_y(), x=self._lm(), w=self._w(), thickness=0.3)
        self.ln(5)
        self._body(t["open_centers_watch"], size=10, color=MUTED)
        self._page_number()

    # ── Page 15: SIGNATURE & NOT-SELF ────────────────────────────────────────
    def build_signature(self, name):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s08_num"], t["s08_title"], with_bar=False)
        self._highlight_box(t["your_signature"], "[СИГНАТУРА]")
        self._body(t["signature_p1"], size=10)
        self.ln(4)
        self._amber_line(self.get_y(), x=self._lm(), w=self._w(), thickness=0.4)
        self.ln(6)
        self._highlight_box(t["your_not_self"], "[НЕ-Я ТЕМА]")
        self._body(t["not_self_p1"], size=10)
        self._page_number()

    # ── Page 16: LIFE THEME ──────────────────────────────────────────────────
    def build_life_theme(self, name, life_area):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s09_num"], t["s09_title"], with_bar=False)
        key = f"life_theme_{life_area}"
        if key not in t:
            key = "life_theme_self"
        self._body(t[key], size=10)
        self._page_number()

    # ── Page 17: RECOMMENDATIONS (part 1) ───────────────────────────────────
    def build_recs_p1(self, name, life_area):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s10_num"], t["s10_title"], with_bar=False)
        intro_key = f"recs_intro_{life_area}"
        if intro_key not in t:
            intro_key = "recs_intro_self"
        self.set_x(self._lm())
        self.set_font("DejaVuBold", "", 10)
        self.set_text_color(*ORANGE_L)
        self.cell(self._w(), 7, t[intro_key], new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        recs_key = f"recs_{life_area}_1"
        if recs_key not in t:
            recs_key = "recs_self_1"
        for rec in t[recs_key]:
            self._bullet(rec)
        self._page_number()

    # ── Page 18: RECOMMENDATIONS (part 2) ───────────────────────────────────
    def build_recs_p2(self, name, life_area):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s10_num"], t["s10b_title"], with_bar=False)
        recs_key = f"recs_{life_area}_2"
        if recs_key not in t:
            recs_key = "recs_self_2"
        for rec in t[recs_key]:
            self._bullet(rec)
        self._page_number()

    # ── Page 19: NEXT 30 DAYS ────────────────────────────────────────────────
    def build_30days(self, name, life_area):
        self.add_page()
        t = self.t
        self._orange_accent_bar()
        self._page_header(name)
        self.set_y(18)
        self._section_header(t["s11_num"], t["s11_title"], with_bar=False)

        week_keys = [
            f"plan_week1_{life_area}",
            f"plan_week2_{life_area}",
            f"plan_week3_{life_area}",
            f"plan_week4_{life_area}",
        ]
        fallback_area = "self"
        labels = t["week_labels"]
        for i, wk in enumerate(week_keys):
            content = t.get(wk, t.get(f"plan_week{i+1}_{fallback_area}", ""))
            self._week_box(labels[i], content)

        self._page_number()

    # ── Page 20: CLOSING ─────────────────────────────────────────────────────
    def build_closing(self, name):
        self.add_page()
        t = self.t

        # Warm glow on closing page
        self._cover_glow()

        # Large ✦
        self._draw_star_symbol(105, 40, size=12)

        # "Ти — унікальна."
        self.set_y(65)
        self.set_font("DejaVuBold", "", 28)
        self.set_text_color(*CREAM)
        self.cell(self._pw(), 15, t["unique"], align="C", new_x="LMARGIN", new_y="NEXT")

        # Amber line
        self._amber_line(84, x=35, w=140, thickness=0.6)
        self.ln(12)

        # Closing message
        self.set_x(self._lm())
        self.set_font("DejaVu", "", 11)
        self.set_text_color(*CREAM)
        self.multi_cell(self._w(), 7.5, t["closing_msg"], align="C",
                        new_x="LMARGIN", new_y="NEXT")

        # Brand name
        self.set_y(190)
        self.set_font("DejaVuBold", "", 16)
        self.set_text_color(*AMBER)
        self.cell(self._pw(), 10, t["brand"], align="C", new_x="LMARGIN", new_y="NEXT")

        # Contact
        self.ln(4)
        self._amber_line(self.get_y(), x=50, w=110, thickness=0.3)
        self.ln(6)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(*MUTED)
        self.cell(self._pw(), 7, t["contact_label"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVuBold", "", 10)
        self.set_text_color(*ORANGE_L)
        self.cell(self._pw(), 7, t["contact_email"], align="C", new_x="LMARGIN", new_y="NEXT")

        # Copyright
        self.set_y(265)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*DIM)
        self.cell(self._pw(), 7, t["copyright"], align="C", new_x="LMARGIN", new_y="NEXT")

        # Bottom decorative stars
        for sx, sy, sz in [(40, 245, 5), (170, 250, 4.5), (105, 280, 3)]:
            self._draw_star_symbol(sx, sy, size=sz)

        self._page_number()


# ─── Main generator ───────────────────────────────────────────────────────────
def generate_reading(order, name, birth_date, birth_time, birth_place,
                     life_area, challenge, plan, locale):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"reading_{order}_{plan}.pdf")

    pdf = HumanDesignPDF(locale=locale, plan=plan, name=name)
    pdf._add_fonts()

    # ── BASIC PLAN: exactly 20 pages ─────────────────────────────────────────
    pdf.build_cover(name, birth_date, birth_time, birth_place, plan)   # 1
    pdf.build_welcome(name, birth_date, birth_time, birth_place)        # 2
    pdf.build_what_is_hd(name, birth_date, birth_time, birth_place)     # 3
    pdf.build_type_p1(name)                                             # 4
    pdf.build_type_p2(name)                                             # 5
    pdf.build_authority_p1(name)                                        # 6
    pdf.build_authority_p2(name)                                        # 7
    pdf.build_profile_p1(name)                                          # 8
    pdf.build_profile_p2(name)                                          # 9
    pdf.build_centers_overview(name)                                    # 10
    pdf.build_center1(name)                                             # 11
    pdf.build_center2(name)                                             # 12
    pdf.build_center3(name)                                             # 13
    pdf.build_open_centers(name)                                        # 14
    pdf.build_signature(name)                                           # 15
    pdf.build_life_theme(name, life_area)                               # 16
    pdf.build_recs_p1(name, life_area)                                  # 17
    pdf.build_recs_p2(name, life_area)                                  # 18
    pdf.build_30days(name, life_area)                                   # 19
    pdf.build_closing(name)                                             # 20

    # ── FULL PLAN: 30 additional pages (pages 21-50) ─────────────────────────
    if plan == "full":
        t = pdf.t

        def add_text_page(sec_num, sec_title, lines):
            pdf.add_page()
            pdf._orange_accent_bar()
            pdf._page_header(name)
            pdf.set_y(18)
            pdf._section_header(sec_num, sec_title, with_bar=False)
            for line in lines:
                pdf._body(line, size=10)
            pdf._page_number()

        # Pages 21-29: All 9 centers in detail
        all_centers = [
            ("Центр Голови",        "Голова — центр натхнення та тиску на думки."),
            ("Центр Розуму / Аджна","Аджна — центр аналізу та концептуалізації."),
            ("Горловий Центр",      "Горло — центр комунікації та маніфестації."),
            ("G-Центр / Центр Я",   "G-Центр — ідентичність, напрямок, любов."),
            ("Центр Серця / Воля",  "Серце — воля, самооцінка, матеріальне."),
            ("Сонячне Сплетіння",   "Сонячне Сплетіння — емоції, почуття, хвилі."),
            ("Сакральний Центр",    "Сакральний — життєва сила і сексуальність."),
            ("Селезінка",           "Селезінка — інтуїція, здоров'я, виживання."),
            ("Центр Кореня",        "Корінь — адреналін, тиск, трансформація."),
        ]
        for cname, cdesc in all_centers:
            add_text_page("●", cname, [
                cdesc,
                f"[ТУТ CLAUDE API ДЕТАЛЬНО ОПИШЕ ЦЕНТР '{cname}' — "
                f"стан визначеності/невизначеності для {name}, "
                f"конкретні прояви, сильні сторони та рекомендації.]"
            ])

        # Pages 30-34: Gates and channels (5 pages)
        for i in range(1, 6):
            add_text_page("◆", f"Гейти та Канали — частина {i}", [
                "[ТУТ CLAUDE API ОПИШЕ АКТИВНІ ГЕЙТИ ТА КАНАЛИ]\n",
                "Гейти — це 64 архетипи Іцзіну, що формують твою унікальну конфігурацію. "
                "Активні гейти визначають теми, з якими ти постійно стикаєшся у житті.",
                f"[ЧАСТИНА {i}/5 — персоналізований аналіз активних гейтів для {name}]"
            ])

        # Pages 35-37: Incarnation Cross (3 pages)
        for i in range(1, 4):
            add_text_page("✦", f"Інкарнаційний Хрест — частина {i}", [
                "[ТУТ CLAUDE API ОПИШЕ ТВІЙ ІНКАРНАЦІЙНИЙ ХРЕСТ]\n",
                "Інкарнаційний Хрест — тема твого життя та місія. "
                "Це не те, що треба виконати силою волі, а те, що природно розкривається.",
                f"[ЧАСТИНА {i}/3 — детальний аналіз хреста для {name}]"
            ])

        # Pages 38-42: Relationship analysis (5 pages)
        for i in range(1, 6):
            add_text_page("♥", f"Аналіз стосунків — частина {i}", [
                "[ТУТ CLAUDE API ОПИШЕ ДИНАМІКУ СТОСУНКІВ]\n",
                "Твоя аура та центри визначають унікальну динаміку у стосунках. "
                "Розуміння механіки центрів допомагає будувати глибші зв'язки.",
                f"[ЧАСТИНА {i}/5 — аналіз стосунків для {name}]"
            ])

        # Pages 43-44: Definition type (2 pages)
        for i in range(1, 3):
            add_text_page("◉", f"Тип визначення — частина {i}", [
                "[ТУТ CLAUDE API ОПИШЕ ТИП ВИЗНАЧЕННЯ]\n",
                "Тип визначення показує, наскільки самодостатньою є твоя енергетична система.",
                f"[ЧАСТИНА {i}/2 — аналіз типу визначення для {name}]"
            ])

        # Pages 45-47: Deconditioning (3 pages)
        for i in range(1, 4):
            add_text_page("★", f"Декондиціювання — частина {i}", [
                "[ТУТ CLAUDE API ОПИШЕ ПРАКТИКИ ДЕКОНДИЦІЮВАННЯ]\n",
                "Декондиціювання — процес звільнення від чужих патернів і повернення до себе. "
                "Займає роки, але кожен крок приносить полегшення.",
                f"[ЧАСТИНА {i}/3 — практики декондиціювання для {name}]"
            ])

        # Pages 48-50: 90-day plan (3 pages)
        month_names = ["Місяць 1 — Усвідомлення", "Місяць 2 — Практика", "Місяць 3 — Інтеграція"]
        for i, mname in enumerate(month_names, 1):
            add_text_page("📅" if False else "▶", mname, [
                f"[ТУТ CLAUDE API СКЛАДЕ ПЛАН {i}-ГО МІСЯЦЯ ДЛЯ {name}]\n",
                "Тиждень 1-2: [персоналізовані завдання]\n"
                "Тиждень 3-4: [персоналізовані завдання]"
            ])

    pdf.output(output_path)
    total = pdf._page_count
    print(f"Generated: {output_path}")
    print(f"Total pages: {total}")
    return output_path


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate Human Design reading PDF")
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
    parser.add_argument("--locale",      default="ua",  choices=["ua", "ru", "en"])
    args = parser.parse_args()

    generate_reading(
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


if __name__ == "__main__":
    main()
