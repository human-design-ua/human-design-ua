#!/usr/bin/env python3
"""
Human Design bodygraph calculator using real astronomical data (pyswisseph).

Usage:
  python3 scripts/hd_calculator.py --date 2002-02-20 --time 16:18 --place "Україна"
"""

import argparse
import sys
import logging

log = logging.getLogger(__name__)

# ─── Gate sequence around the zodiac (starting from ~0° Aries) ───────────────
# Each gate = 360/64 = 5.625°
GATE_SEQUENCE = [
    41, 19, 13, 49, 30, 55, 37, 63,
    22, 36, 25, 17, 21, 51, 42,  3,
    27, 24,  2, 23,  8, 20, 16, 35,
    45, 12, 15, 52, 39, 53, 62, 56,
    31, 33,  7,  4, 29, 59, 40, 64,
    47,  6, 46, 18, 48, 57, 32, 50,
    28, 44,  1, 43, 14, 34,  9,  5,
    26, 11, 10, 58, 38, 54, 61, 60,
]

# ─── Center gates ──────────────────────────────────────────────────────────────
CENTER_GATES = {
    'head':   [64, 61, 63],
    'ajna':   [47, 24, 4, 17, 43, 11],
    'throat': [62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16],
    'g':      [1, 13, 25, 46, 10, 15, 2, 7],
    'heart':  [51, 21, 40, 26],
    'sp':     [6, 37, 36, 22, 30, 55, 49],
    'sacral': [5, 14, 29, 59, 9, 3, 42, 27, 34],
    'spleen': [48, 57, 44, 50, 32, 28, 18],
    'root':   [60, 52, 19, 39, 53, 54, 58, 38, 41],
}

# Build reverse mapping: gate → center
GATE_TO_CENTER = {}
for center, gates in CENTER_GATES.items():
    for g in gates:
        GATE_TO_CENTER[g] = center

# ─── Channels (pairs of gates connecting two centers) ─────────────────────────
CHANNELS = [
    # Head-Ajna
    (64, 47), (61, 24), (63, 4),
    # Ajna-Throat
    (17, 62), (43, 23), (11, 56),
    # Throat-G
    (20, 10), (31, 7), (8, 1), (33, 13),
    # Throat-SP (Solar Plexus)
    (12, 22), (35, 36),
    # Throat-Heart
    (45, 21),
    # Throat-Sacral
    (16, 48),  # actually Throat-Spleen
    # Heart-Spleen
    (26, 44),
    # Heart-G
    (51, 25),
    # Heart-Throat
    (21, 45),
    # Heart-SP
    (40, 37),
    # SP-Sacral
    (6, 59),
    # SP connections
    (22, 12), (30, 41), (55, 39), (36, 35), (49, 19),
    # Sacral-G
    (29, 46), (14, 2), (5, 15), (34, 10), (34, 20),
    # Sacral-SP
    (59, 6),
    # Sacral-Root
    (42, 53), (3, 60), (9, 52), (27, 50),
    # Sacral-Spleen
    (34, 57),
    # Spleen connections
    (48, 16), (57, 34), (44, 26), (50, 27), (32, 54), (28, 38), (18, 58),
    # Root connections
    (41, 30), (19, 49), (39, 55), (53, 42), (54, 32), (58, 18), (38, 28),
    (60, 3), (52, 9),
    # G center
    (1, 8), (13, 33), (25, 51), (46, 29), (10, 20), (15, 5), (2, 14), (7, 31),
]

# ─── Strategies ───────────────────────────────────────────────────────────────
STRATEGIES = {
    'Генератор':               'Чекати на відгук (Wait to Respond)',
    'Маніфестуючий Генератор': 'Інформувати і чекати на відгук',
    'Маніфестор':              'Інформувати перед дією (Inform)',
    'Проектор':                'Чекати на запрошення (Wait for Invitation)',
    'Рефлектор':               'Чекати місячний цикл (Wait a Lunar Cycle)',
}

# ─── Planets to calculate ─────────────────────────────────────────────────────
# (swisseph constant, label)
PLANETS = [
    (0,  'Sun'),
    (1,  'Moon'),
    (2,  'Mercury'),
    (3,  'Venus'),
    (4,  'Mars'),
    (5,  'Jupiter'),
    (6,  'Saturn'),
    (7,  'Uranus'),
    (8,  'Neptune'),
    (9,  'Pluto'),
    (11, 'TrueNode'),  # True North Node
]


def longitude_to_gate(lon: float) -> tuple:
    """Convert ecliptic longitude (0-360) to (gate, line)."""
    lon = lon % 360.0
    idx = int(lon / 5.625) % 64
    gate = GATE_SEQUENCE[idx]
    line = int((lon % 5.625) / (5.625 / 6)) + 1
    line = min(line, 6)
    return gate, line


def _parse_datetime_utc(birth_date: str, birth_time: str, birth_place: str):
    """
    Parse birth date/time and return UTC datetime.
    Uses geopy+timezonefinder if available for timezone lookup,
    otherwise assumes UTC.
    """
    from datetime import datetime, timezone, timedelta

    dt_str = f"{birth_date} {birth_time}"
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

    # Try to get timezone from place name
    tz_offset_hours = _get_tz_offset(birth_place, birth_date)

    # Subtract UTC offset to get UTC time
    dt_utc = dt - timedelta(hours=tz_offset_hours)
    return dt_utc


def _get_tz_offset(place: str, date_str: str) -> float:
    """
    Try to determine UTC offset for a place.
    Returns offset in hours (e.g. +2 for Ukraine summer time).
    Falls back to common defaults.
    """
    # Try timezonefinder + geopy
    try:
        from geopy.geocoders import Nominatim
        from timezonefinder import TimezoneFinder
        import pytz
        from datetime import datetime

        geolocator = Nominatim(user_agent="hd_calculator")
        location = geolocator.geocode(place, timeout=5)
        if location:
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
            if tz_name:
                tz = pytz.timezone(tz_name)
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                # Use noon to determine offset (avoids DST edge at midnight)
                dt_noon = dt.replace(hour=12)
                offset = tz.utcoffset(dt_noon)
                hours = offset.total_seconds() / 3600
                log.info(f"Timezone for '{place}': {tz_name} (UTC{hours:+.1f})")
                return hours
    except Exception as e:
        log.debug(f"Timezone lookup failed: {e}")

    # Fallback heuristics
    place_lower = place.lower()
    ukraine_keywords = ['україна', 'ukraine', 'київ', 'kyiv', 'харків', 'одеса',
                        'дніпро', 'lviv', 'львів']
    moscow_keywords = ['москва', 'moscow', 'россия', 'russia', 'санкт', 'питер']

    for kw in ukraine_keywords:
        if kw in place_lower:
            # Ukraine is UTC+2 (EET) or UTC+3 (EEST summer)
            # For simplicity use UTC+2 (standard time)
            log.info(f"Using default Ukraine offset UTC+2 for '{place}'")
            return 2.0

    for kw in moscow_keywords:
        if kw in place_lower:
            log.info(f"Using default Moscow offset UTC+3 for '{place}'")
            return 3.0

    log.info(f"Unknown place '{place}', assuming UTC+0")
    return 0.0


def _datetime_to_jd(dt_utc) -> float:
    """Convert UTC datetime to Julian Day Number."""
    try:
        import swisseph as swe
        return swe.julday(
            dt_utc.year, dt_utc.month, dt_utc.day,
            dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
        )
    except ImportError:
        raise RuntimeError("pyswisseph not installed. Run: pip install pyswisseph")


def _calc_planets(jd: float) -> dict:
    """Calculate planetary positions (ecliptic longitude) for a Julian Day."""
    import swisseph as swe

    result = {}
    for planet_id, planet_name in PLANETS:
        try:
            # SEFLG_SWIEPH | SEFLG_SPEED = 256 | 2048 → we just need position
            xx, ret = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH)
            lon = xx[0]  # ecliptic longitude
            result[planet_name] = lon
        except Exception as e:
            log.warning(f"Could not calculate {planet_name}: {e}")

    return result


def _get_activated_gates(planet_positions: dict) -> list:
    """Convert planet positions to list of (gate, line, planet) tuples."""
    activations = []
    for planet_name, lon in planet_positions.items():
        gate, line = longitude_to_gate(lon)
        activations.append((gate, line, planet_name))
    return activations


def _find_defined_centers(all_gates: set) -> list:
    """
    A center is defined if it contains a gate that is part of a COMPLETE channel
    where BOTH gates are activated.
    """
    defined = set()
    for g1, g2 in CHANNELS:
        if g1 in all_gates and g2 in all_gates:
            c1 = GATE_TO_CENTER.get(g1)
            c2 = GATE_TO_CENTER.get(g2)
            if c1:
                defined.add(c1)
            if c2:
                defined.add(c2)
    return sorted(defined)


def _find_active_channels(all_gates: set) -> list:
    """Return list of channel tuples where both gates are activated."""
    active = []
    seen = set()
    for g1, g2 in CHANNELS:
        key = (min(g1, g2), max(g1, g2))
        if key not in seen and g1 in all_gates and g2 in all_gates:
            active.append((g1, g2))
            seen.add(key)
    return active


def determine_type(defined_centers: list) -> str:
    if not defined_centers:
        return 'Рефлектор'

    defined_set = set(defined_centers)
    sacral_defined = 'sacral' in defined_set
    throat_defined = 'throat' in defined_set
    motor_centers = {'heart', 'sp', 'sacral', 'root'}
    motors_defined = motor_centers & defined_set

    if sacral_defined:
        if throat_defined:
            return 'Маніфестуючий Генератор'
        return 'Генератор'

    # No sacral
    if throat_defined and (motors_defined - {'sacral'}):
        return 'Маніфестор'

    return 'Проектор'


def determine_authority(defined_centers: list, hd_type: str) -> str:
    if hd_type == 'Рефлектор':
        return 'Місячний (Lunar)'
    defined_set = set(defined_centers)
    if 'sp' in defined_set:
        return 'Емоційний (Solar Plexus)'
    if 'sacral' in defined_set:
        return 'Сакральний'
    if 'spleen' in defined_set:
        return 'Селезінковий (Spleen)'
    if 'heart' in defined_set:
        return 'Его (Heart/Will)'
    if 'g' in defined_set:
        return 'Я (G-Center / Self)'
    if 'ajna' in defined_set or 'head' in defined_set:
        return 'Ментальний (Mental Projector)'
    return 'Місячний (Lunar)'


def _determine_definition(defined_centers: list, active_channels: list) -> str:
    """Determine definition type based on connected center groups."""
    if not defined_centers:
        return 'No Definition'

    # Build adjacency among defined centers via active channels
    center_set = set(defined_centers)
    adjacency = {c: set() for c in center_set}

    for g1, g2 in active_channels:
        c1 = GATE_TO_CENTER.get(g1)
        c2 = GATE_TO_CENTER.get(g2)
        if c1 and c2 and c1 != c2 and c1 in center_set and c2 in center_set:
            adjacency[c1].add(c2)
            adjacency[c2].add(c1)

    # Count connected components (splits)
    visited = set()
    groups = 0

    def dfs(node):
        visited.add(node)
        for neighbor in adjacency[node]:
            if neighbor not in visited:
                dfs(neighbor)

    for c in center_set:
        if c not in visited:
            dfs(c)
            groups += 1

    if groups == 1:
        return 'Single Definition'
    elif groups == 2:
        return 'Split Definition'
    elif groups == 3:
        return 'Triple Split'
    else:
        return 'Quadruple Split'


def calculate_hd(birth_date: str, birth_time: str, birth_place: str) -> dict:
    """
    Calculate Human Design parameters from birth data.

    Args:
        birth_date:  'YYYY-MM-DD'
        birth_time:  'HH:MM'
        birth_place: city/country name string

    Returns dict with:
        hd_type, strategy, authority, profile, definition,
        incarnation_cross, personality_gates, design_gates,
        all_gates, defined_centers, channels_active
    """
    # 1. Parse birth datetime to UTC
    dt_utc = _parse_datetime_utc(birth_date, birth_time, birth_place)
    log.info(f"Birth UTC: {dt_utc}")

    # 2. Julian Day for birth moment
    jd_birth = _datetime_to_jd(dt_utc)
    log.info(f"JD birth: {jd_birth:.6f}")

    # 3. Design moment: 88.736 days before birth
    jd_design = jd_birth - 88.736
    log.info(f"JD design: {jd_design:.6f}")

    # 4. Calculate planet positions
    personality_positions = _calc_planets(jd_birth)
    design_positions = _calc_planets(jd_design)

    # 5. Convert to gates
    personality_activations = _get_activated_gates(personality_positions)
    design_activations = _get_activated_gates(design_positions)

    # 6. Combine all activated gates
    personality_gates = [(g, l, p) for g, l, p in personality_activations]
    design_gates = [(g, l, p) for g, l, p in design_activations]
    all_gates = set(g for g, l, p in personality_activations) | set(g for g, l, p in design_activations)

    # 7. Find defined centers
    defined_centers = _find_defined_centers(all_gates)

    # 8. Find active channels
    active_channels = _find_active_channels(all_gates)

    # 9. Determine type, authority
    hd_type = determine_type(defined_centers)
    authority = determine_authority(defined_centers, hd_type)

    # 10. Profile = personality sun line / design sun line
    p_sun = next(((g, l) for g, l, p in personality_activations if p == 'Sun'), (0, 0))
    d_sun = next(((g, l) for g, l, p in design_activations if p == 'Sun'), (0, 0))
    profile = f"{p_sun[1]}/{d_sun[1]}"

    # 11. Definition type
    definition = _determine_definition(defined_centers, active_channels)

    # 12. Strategy
    strategy = STRATEGIES.get(hd_type, '')

    return {
        'hd_type':          hd_type,
        'strategy':         strategy,
        'authority':        authority,
        'profile':          profile,
        'definition':       definition,
        'incarnation_cross': f"Cross of {p_sun[0]}/{d_sun[0]}",  # placeholder
        'personality_gates': [(g, l, planet) for g, l, planet in personality_gates],
        'design_gates':      [(g, l, planet) for g, l, planet in design_gates],
        'all_gates':         sorted(all_gates),
        'defined_centers':   defined_centers,
        'channels_active':   active_channels,
        'personality_sun':   p_sun,
        'design_sun':        d_sun,
        '_jd_birth':         jd_birth,
        '_jd_design':        jd_design,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [hd_calc] %(message)s")

    parser = argparse.ArgumentParser(description="Human Design calculator")
    parser.add_argument("--date",  required=True, help="Birth date YYYY-MM-DD")
    parser.add_argument("--time",  required=True, help="Birth time HH:MM")
    parser.add_argument("--place", required=True, help="Birth place (city/country)")
    args = parser.parse_args()

    result = calculate_hd(args.date, args.time, args.place)

    print(f"\n{'='*60}")
    print(f"  Human Design Calculation")
    print(f"  Born: {args.date} {args.time} @ {args.place}")
    print(f"{'='*60}")
    print(f"  Type:       {result['hd_type']}")
    print(f"  Strategy:   {result['strategy']}")
    print(f"  Authority:  {result['authority']}")
    print(f"  Profile:    {result['profile']}")
    print(f"  Definition: {result['definition']}")
    print(f"  Cross:      {result['incarnation_cross']}")
    print()
    print(f"  Defined centers: {', '.join(result['defined_centers']) or 'none'}")
    print(f"  Active channels ({len(result['channels_active'])}):")
    for ch in result['channels_active']:
        print(f"    {ch[0]}-{ch[1]}")
    print()
    print(f"  Personality gates (Conscious):")
    for g, l, p in result['personality_gates']:
        print(f"    {p:10s}  Gate {g:2d}.{l}")
    print()
    print(f"  Design gates (Unconscious):")
    for g, l, p in result['design_gates']:
        print(f"    {p:10s}  Gate {g:2d}.{l}")
    print()


if __name__ == "__main__":
    main()
