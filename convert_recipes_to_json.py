import json
import os
import re
from typing import List, Dict, Optional
import unicodedata

SRC_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "Christmas Sweet Recipes.dedup.fixed.txt"),
    os.path.join(os.path.dirname(__file__), "Christmas Sweet Recipes.dedup.txt"),
]
SRC_PATH = next((p for p in SRC_CANDIDATES if os.path.exists(p)), SRC_CANDIDATES[-1])
OUT_PATH = os.path.join(os.path.dirname(__file__), "recipes.json")

# Util regex
FRACTIONS = "¼½¾⅓⅔⅛⅜⅝⅞"
QTY_RE = re.compile(rf"^(?:\*\s*)?(\d+(?:[\s/]+\d+\/\d+)?|\d*\.\d+|[{FRACTIONS}]|\d+\s*[{FRACTIONS}])\b|^(?:\*\s*)?(pinch|dash|few|handful)\b", re.I)
STEP_NUM_RE = re.compile(r"^\s*\d+\s*[\).:]\s*")
SECTION_RE = re.compile(r":\s*$")
TIME_LINE_RE = re.compile(r"\b(Prep|Cook|Total)\s*:\s*", re.I)
TIME_LINE_VARIANT_RE = re.compile(r"\b(Prep|Cook|Total)\s*(?:time)?\s*:\s*", re.I)
SERVES_RE = re.compile(r"\b(Serves|Serving|SERVINGS)\b", re.I)
SOURCE_HINT_RE = re.compile(r"\b(adapted from|via|recipe (?:from|courtesy)|photo by)\b", re.I)
# Only match explicit source lines at the start of the line
SOURCE_LINE_RE = re.compile(r"^\s*(adapted from|from|via|recipe by|recipe from|courtesy of)\b[:\s]+(.+)$", re.I)
CATEGORY_KV_RE = re.compile(r"^\s*(category|categories)\s*:\s*(.+)$", re.I)
SEPARATOR_RE = re.compile(r"^(_+|[-–—]{3,})\s*$")
IMAGE_DIM_RE = re.compile(r"\b\d{2,4}\s*[x×]\s*\d{2,4}\b")
IMAGE_EXT_RE = re.compile(r"\.(?:jpg|jpeg|png|gif|bmp|webp)\b", re.I)
CAPTION_HINT_RE = re.compile(r"\b(12\s*Days\s*of\s*Cookies|image|photo|gallery)\b", re.I)
SERVES_LINE_RE = re.compile(r"^\s*(Serves|Serving|SERVINGS)\b[:\s]*(.*)$", re.I)
READY_IN_LINE_RE = re.compile(r"^\s*Ready\s*in\b[:\s]*(.*)$", re.I)
MAKES_LINE_RE = re.compile(r"^\s*\(?Makes?\b([^)]*)\)?$", re.I)
VARIATION_RE = re.compile(r"^\s*Variation\s*:\s*(.*)$", re.I)
MAKING_MINUTES_RE = re.compile(r"^\s*Making\s+the\s+Minutes\s+Count\s*:\s*(.*)$", re.I)
TITLE_KV_RE = re.compile(r"^\s*(title|tile)\s*:\s*(.+)$", re.I)
SOURCE_KV_RE = re.compile(r"^\s*(source|from)\s*:\s*(.+)$", re.I)
EVENT_KV_RE = re.compile(r"^\s*(event)\s*:\s*(.+)$", re.I)
SUBTITLE_KV_RE = re.compile(r"^\s*(subtitle)\s*:\s*(.+)$", re.I)
SOURCE_NAME_HINTS = {
    s.lower(): s for s in [
        "Cook’s Country", "Cooks Country", "Amanda Jones", "Brashears Family", "Sugar Solutions",
        "Taste of Home’s", "Taste of Home", "Stop and Smell the Rosemary", "Briana Warner",
        "The Best New Recipes", "Brashears", "Brian Johnson"
    ]
}

# Heuristic helpers

def strip_accents(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))

def parse_fraction(s: str) -> float:
    # handle unicode vulgar fractions and forms like "1 1/2"
    frac_map = {
        '¼': 0.25, '½': 0.5, '¾': 0.75, '⅓': 1/3, '⅔': 2/3, '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875,
    }
    s = s.strip()
    if s in frac_map:
        return frac_map[s]
    m = re.match(r"^(\d+)\s+(\d+)/(\d+)$", s)
    if m:
        return float(m.group(1)) + (int(m.group(2)) / int(m.group(3)))
    m2 = re.match(r"^(\d+)/(\d+)$", s)
    if m2:
        return int(m2.group(1)) / int(m2.group(2))
    try:
        return float(s)
    except ValueError:
        return 0.0

def parse_duration_to_minutes(s: str) -> Optional[int]:
    if not s:
        return None
    txt = strip_accents(s.lower())
    # replace unicode fractions with ascii approximations spaces for parsing
    txt = txt.replace('–', '-').replace('—', '-').replace('hr.', 'hr').replace('hrs', 'hr')
    total = 0.0
    # patterns like "1 hr 30 min", "2 hours", "45 min"
    for part in re.findall(r"(\d+[\s\d/]*\s*(?:hour|hr|h|minute|min|m))", txt):
        num = re.match(r"(\d+[\s\d/]*)", part)
        unit = re.search(r"(hour|hr|h|minute|min|m)$", part)
        if not num or not unit:
            continue
        minutes = 0.0
        val = parse_fraction(num.group(1))
        u = unit.group(1)
        if u in ('hour', 'hr', 'h'):
            minutes = val * 60.0
        else:
            minutes = val * 1.0
        total += minutes
    if total > 0:
        return int(round(total))
    # fallback: single number might imply minutes
    m = re.search(r"(\d+)", txt)
    if m:
        return int(m.group(1))
    return None

def extract_servings_range(s: str) -> Optional[Dict[str, int]]:
    if not s:
        return None
    txt = strip_accents(s.lower()).replace('serves', '').replace('servings', '').strip()
    # patterns: 6-8, 6 – 8, 6 to 8
    m = re.search(r"(\d+)\s*(?:-|to|–)\s*(\d+)", txt)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return {'min': min(a, b), 'max': max(a, b)}
    m2 = re.search(r"\b(\d+)\b", txt)
    if m2:
        v = int(m2.group(1))
        return {'min': v, 'max': v}
    return None

CANON_CATEGORY_MAP = {
    'entree': 'entree', 'entrée': 'entree', 'main': 'entree', 'main dish': 'entree',
    'side dish': 'side', 'side': 'side',
    'appetizer': 'appetizer', 'starter': 'appetizer',
    'dessert': 'dessert', 'cookies': 'cookies', 'cake': 'cake', 'pie': 'pie', 'pastry': 'pastry',
    'soup': 'soup', 'dinner soup': 'soup',
    'salad': 'salad',
    'seafood': 'seafood', 'pasta': 'pasta', 'breakfast': 'breakfast', 'vegetarian': 'vegetarian',
}

def canonicalize_category(token: str) -> str:
    base = clean(strip_accents(token)).lower()
    return CANON_CATEGORY_MAP.get(base, base)

SECTION_WORDS = {
    'topping', 'icing', 'filling', 'glaze', 'frosting', 'dough', 'crust', 'sauce'
}

def is_title(line: str) -> bool:
    """Loose check if a line could be a title on its own (without context)."""
    if not line:
        return False
    if SEPARATOR_RE.match(line):
        return False
    low = line.lower()
    if any(h in low for h in ["ingredients", "directions", "serves:", "prep:", "cook:", "total:"]):
        return False
    if len(line) > 90:  # long sentence => likely not title
        return False
    if line.strip().endswith(":"):
        return False
    sline = line.strip()
    # Avoid treating sentences that end with a period as titles
    if sline.endswith('.'):
        return False
    # Avoid lines containing periods or obvious sentence punctuation
    if ('.' in sline) or (',' in sline) or (';' in sline):
        return False
    # Titles generally start with uppercase
    if re.match(r"^[a-z]", sline):
        return False
    # Avoid bare section headers (e.g., TOPPING) from becoming titles
    if re.match(r"^[A-Z ]{3,}$", sline) and sline.strip().lower() in SECTION_WORDS:
        return False
    # Avoid lines that clearly look like quantities or steps
    if QTY_RE.match(line) or STEP_NUM_RE.match(line):
        return False
    # Avoid treating imperative cooking lines as titles
    if is_direction(line):
        return False
    # Avoid source-like lines as titles
    if SOURCE_LINE_RE.match(line):
        return False
    if line.strip().lower() in SOURCE_NAME_HINTS:
        return False
    # Avoid common trivial words used alone
    trivial = [
        "salt and pepper", "notes", "variation", "serves", "servings", "makes", "garnish",
        "ingredients", "directions", "prep", "cook", "total"
    ]
    if line.strip().lower() in trivial:
        return False
    return True


def is_ingredient(line: str) -> bool:
    if not line:
        return False
    if QTY_RE.match(line.strip()):
        return True
    # Bullet with *
    if line.strip().startswith("*") and len(line.strip()) > 2:
        return True
    # Lines like "Salt for rolling" etc. when inside ingredient mode
    return False


def is_direction(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if STEP_NUM_RE.match(s):
        return True
    # Heuristic: sentence starting with a verb-like word and contains a period
    if re.match(r"^(?:(?:Slowly|Gradually|Carefully|Gently|Lightly|Briefly|Quickly|Evenly)\s+)?(Preheat|Heat|Bake|Mix|Beat|Whisk|Whip|Add|Stir|Pour|Fold|Remove|Let|Chill|Cook|Bring|Combine|Transfer|Spread|Scoop|Drop|Roll|Place|Use|Melt|Grease|Line|Cut|Garnish|Serve|Dip|Coat|Cover|Refrigerate|Simmer|Season|Sprinkle|Return|Arrange|Cool|Pipe|Repeat|Boil|Drain|Rinse|Toast|Knead|Shape|Form|Broil|Grill|Marinate|Peel|Chop|Slice|Dice|Crush|Grate|Zest|Reduce|Deglaze|Dissolve|Blend|Set|Spray|Sift|Spoon|Drizzle)\b", s, re.I):
        return True
    return False


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def norm(s: str) -> str:
    # Normalize unicode punctuation for matching
    return clean(s).replace("\u2019", "'").replace("\u2018", "'").lower()


def parse_time_and_serves(line: str, cur: Dict):
    # Example: "Serves:  Prep: 27min Cook: 38min Total: 2hr 15min"
    if TIME_LINE_RE.search(line) or TIME_LINE_VARIANT_RE.search(line) or SERVES_RE.search(line) or READY_IN_LINE_RE.search(line):
        if 'times' not in cur:
            cur['times'] = {}
        # Extract serves
        m_serv = re.search(r"\bServes\s*:\s*([^\n]+?)\s*(?:Prep|Cook|Total|$)", line, re.I)
        if m_serv:
            cur['servings'] = clean(m_serv.group(1))
        # Extract times
        for key in ['Prep', 'Cook', 'Total']:
            # support both "Prep:" and "Prep time:"
            m = re.search(fr"{key}\s*(?:time)?\s*:\s*([^\n]+?)(?=\s*(?:Prep|Cook|Total|Serves|Ready\s*in|$))", line, re.I)
            if m:
                cur['times'][key.lower()] = clean(m.group(1))
        # Ready in
        m_ready = READY_IN_LINE_RE.match(line)
        if not m_ready:
            m_ready = re.search(r"Ready\s*in\s*:\s*([^\n]+)", line, re.I)
        if m_ready:
            cur['times']['ready_in'] = clean(m_ready.group(1))
        return True
    return False


def finalize_recipe(cur: Optional[Dict], out: List[Dict]):
    if not cur:
        return
    # Trim empty fields
    if not cur.get('ingredients'):
        cur.pop('ingredients', None)
    if not cur.get('directions'):
        cur.pop('directions', None)
    if not cur.get('notes'):
        cur.pop('notes', None)
    if not cur.get('times'):
        cur.pop('times', None)
    # Ensure categories field always exists as an array
    if 'categories' not in cur or cur['categories'] is None:
        cur['categories'] = []
    else:
        # Normalize categories: lowercase, trimmed, unique preserving order
        seen = set()
        normed = []
        for c in cur.get('categories', []) or []:
            lc = canonicalize_category(c)
            if lc and lc not in seen:
                seen.add(lc)
                normed.append(lc)
        cur['categories'] = normed
    # Normalize servings into min/max if possible
    if cur.get('servings'):
        rng = extract_servings_range(cur['servings'])
        if rng:
            cur['servings_min'] = rng['min']
            cur['servings_max'] = rng['max']
    # Normalize ingredient sections
    if 'ingredients' in cur:
        # Merge unnamed sections into one list
        merged: List[Dict] = []
        for sec in cur['ingredients']:
            if not sec.get('section'):
                sec['section'] = None
            merged.append({'section': sec['section'], 'items': [clean(x) for x in sec.get('items', []) if clean(x)]})
        cur['ingredients'] = merged
    # Clean notes and extract source lines
    if 'notes' in cur and cur['notes']:
        filtered = []
        for n in cur['notes']:
            if IMAGE_DIM_RE.search(n) or IMAGE_EXT_RE.search(n) or CAPTION_HINT_RE.search(n):
                continue
            # Try to extract source from note
            msrc = SOURCE_LINE_RE.match(n)
            low = norm(n)
            if msrc:
                cur['source'] = clean(msrc.group(2))
                continue
            if low in SOURCE_NAME_HINTS:
                cur['source'] = SOURCE_NAME_HINTS[low]
                continue
            filtered.append(n)
        cur['notes'] = filtered
    # Mirror common times to top-level aliases for convenience
    if 'times' in cur:
        if 'prep' in cur['times']:
            cur['prep_time'] = cur['times']['prep']
            pm = parse_duration_to_minutes(cur['times']['prep'])
            if pm is not None:
                cur['prep_minutes'] = pm
        if 'cook' in cur['times']:
            cur['cook_time'] = cur['times']['cook']
            cm = parse_duration_to_minutes(cur['times']['cook'])
            if cm is not None:
                cur['cook_minutes'] = cm
        if 'total' in cur['times']:
            cur['total_time'] = cur['times']['total']
            tm = parse_duration_to_minutes(cur['times']['total'])
            if tm is not None:
                cur['total_minutes'] = tm
        if 'ready_in' in cur['times']:
            cur['ready_in'] = cur['times']['ready_in']
            rm = parse_duration_to_minutes(cur['times']['ready_in'])
            if rm is not None:
                cur['ready_in_minutes'] = rm
    out.append(cur)


def main():
    with open(SRC_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [ln.rstrip('\n').strip('\ufeff') for ln in f]

    recipes: List[Dict] = []
    cur: Optional[Dict] = None
    mode: Optional[str] = None  # 'notes' | 'ingredients' | 'directions'
    current_ing_section: Optional[Dict] = None

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        # Skip empty separators
        if not line:
            i += 1
            continue
        if SEPARATOR_RE.match(line):
            # separator denotes end of a recipe block
            finalize_recipe(cur, recipes)
            cur = None
            mode = None
            current_ing_section = None
            i += 1
            continue

        # Explicit key-value title/source lines
        m_title_kv = TITLE_KV_RE.match(line)
        if m_title_kv:
            new_title = clean(m_title_kv.group(2))
            # If we were in a recipe with any content, close it and start fresh
            if cur and (cur.get('title') or cur.get('ingredients') or cur.get('directions') or cur.get('notes')):
                finalize_recipe(cur, recipes)
                cur = None
                mode = None
                current_ing_section = None
            # Start new recipe with this explicit title
            cur = {'title': new_title, 'notes': [], 'ingredients': [], 'directions': []}
            mode = 'notes'
            i += 1
            continue

        m_source_kv = SOURCE_KV_RE.match(line)
        if m_source_kv and cur is not None:
            cur['source'] = clean(m_source_kv.group(2))
            i += 1
            continue

        # Explicit event line
        m_event_kv = EVENT_KV_RE.match(line)
        if m_event_kv and cur is not None:
            cur['event'] = clean(m_event_kv.group(2))
            i += 1
            continue

        # Explicit subtitle line
        m_subtitle_kv = SUBTITLE_KV_RE.match(line)
        if m_subtitle_kv and cur is not None:
            cur['subtitle'] = clean(m_subtitle_kv.group(2))
            i += 1
            continue

        # Explicit categories line
        m_cats_kv = CATEGORY_KV_RE.match(line)
        if m_cats_kv and cur is not None:
            raw_val = clean(m_cats_kv.group(2))
            cats: List[str] = []
            val = raw_val.strip()
            # Handle bracketed list forms like [salad, soup]
            if val.startswith('[') and val.endswith(']'):
                inner = val[1:-1].strip()
                if inner:
                    parts = [p.strip().strip("'\"") for p in inner.split(',')]
                    cats = [clean(c).lower() for c in parts if clean(c)]
            else:
                # Comma-separated or single value
                parts = [p.strip().strip("'\"") for p in val.split(',')]
                cats = [clean(c).lower() for c in parts if clean(c)]
            if cats:
                existing = cur.get('categories', []) or []
                # Merge unique while preserving order (case-insensitive already lowercased)
                for c in cats:
                    if c not in existing:
                        existing.append(c)
                cur['categories'] = existing
            i += 1
            continue

        # Global skip or attach: image captions or gallery/caption-like lines
        if IMAGE_DIM_RE.search(line) or IMAGE_EXT_RE.search(line) or CAPTION_HINT_RE.search(line):
            # Prefer to drop; if inside a recipe, keep as a note for traceability
            if cur is not None:
                cur.setdefault('notes', []).append(clean(line))
            i += 1
            continue

        # Source lines like "Recipe by Amanda Jones" or "from Cook's Country"
        if cur is not None:
            msrc = SOURCE_LINE_RE.match(line)
            if msrc:
                cur['source'] = clean(msrc.group(2))
                i += 1
                continue
            # Standalone name hints as source
            low = line.strip().lower()
            if low in SOURCE_NAME_HINTS and len(line) <= 80:
                cur['source'] = SOURCE_NAME_HINTS[low]
                i += 1
                continue

        # Variation lines -> store in dedicated variations array
        m_var = VARIATION_RE.match(line)
        if m_var:
            if cur is not None:
                cur.setdefault('variations', []).append(clean(m_var.group(1)))
            i += 1
            continue

        # "Making the Minutes Count" explanatory line -> keep in dedicated field
        m_mtmc = MAKING_MINUTES_RE.match(line)
        if m_mtmc and cur is not None:
            cur['making_the_minutes_count'] = clean(m_mtmc.group(1))
            i += 1
            continue

        # Standalone Serves/Serving lines
        m_servline = SERVES_LINE_RE.match(line)
        if m_servline and cur is not None:
            cur['servings'] = clean(m_servline.group(2)) if m_servline.group(2) else cur.get('servings')
            i += 1
            continue

        # Standalone Ready in line
        m_readyline = READY_IN_LINE_RE.match(line)
        if m_readyline and cur is not None:
            cur.setdefault('times', {})['ready_in'] = clean(m_readyline.group(1))
            i += 1
            continue

        # Standalone Makes lines -> normalize into servings/yield
        m_makes = MAKES_LINE_RE.match(line)
        if m_makes and cur is not None:
            val = clean(m_makes.group(1))
            if val:
                cur['servings'] = (cur.get('servings') + f"; Makes {val}") if cur.get('servings') else f"Makes {val}"
            i += 1
            continue

        # Handle bare section headers (without trailing colon) within a recipe
        if cur is not None and re.match(r"^[A-Z ]{3,}$", line) and line.strip().lower() in SECTION_WORDS:
            sec_name = line.strip().title()
            if 'ingredients' not in cur or cur['ingredients'] is None:
                cur['ingredients'] = []
            current_ing_section = {'section': sec_name, 'items': []}
            cur['ingredients'].append(current_ing_section)
            mode = 'ingredients'
            i += 1
            continue

        # Detect new title with lookahead to reduce false positives
        if is_title(line):
            # Look ahead a few lines for evidence of a recipe start (ingredients/sections/times)
            look_ok = False
            for j in range(1, 6):
                if i + j >= len(lines):
                    break
                nxt = lines[i + j].strip()
                if not nxt:
                    continue
                if SECTION_RE.search(nxt) and not nxt.lower().startswith('directions'):
                    look_ok = True
                    break
                if is_ingredient(nxt):
                    look_ok = True
                    break
                if TIME_LINE_RE.search(nxt) or SERVES_RE.search(nxt) or SOURCE_HINT_RE.search(nxt):
                    look_ok = True
                    break
                # If next line clearly looks like a direction, that also signals a valid start
                if is_direction(nxt):
                    look_ok = True
                    break
            if look_ok and (cur is None or (not cur.get('ingredients') and not cur.get('directions'))):
                # Either start a new recipe, or replace a false-start title with a better one
                if cur is None:
                    cur = {'title': clean(line), 'notes': [], 'ingredients': [], 'directions': []}
                else:
                    cur['title'] = clean(line)
                mode = 'notes'
                i += 1
                continue
            elif look_ok and cur and (cur.get('ingredients') or cur.get('directions')):
                # We were in a finished recipe, so close it and start a new one
                finalize_recipe(cur, recipes)
                cur = {'title': clean(line), 'notes': [], 'ingredients': [], 'directions': []}
                mode = 'notes'
                i += 1
                continue

        # If we don't yet have a recipe, skip until we find one
        if cur is None:
            i += 1
            continue

        # Time/Serves lines
        if parse_time_and_serves(line, cur):
            i += 1
            continue

        # Detect section headers (e.g., "Cookies:", "Caramel:") in ingredients mode or generally
        if SECTION_RE.search(line) and not line.lower().startswith('directions'):
            sec_name = clean(line[:-1])
            if cur is not None:
                if 'ingredients' not in cur or cur['ingredients'] is None:
                    cur['ingredients'] = []
                current_ing_section = {'section': sec_name, 'items': []}
                cur['ingredients'].append(current_ing_section)
                mode = 'ingredients'
            i += 1
            continue

        # Switch explicitly to ingredients/directions mode via headers
        if re.match(r"^\s*ingredients\b[:\s]*$", line, re.I):
            # Start or switch to ingredients mode
            if cur is not None:
                mode = 'ingredients'
                if current_ing_section is None:
                    current_ing_section = {'section': None, 'items': []}
                    cur.setdefault('ingredients', []).append(current_ing_section)
            i += 1
            continue

        if re.match(r"^\s*(directions?|method|instructions?)\b[:\s]*$", line, re.I):
            mode = 'directions'
            i += 1
            continue

        # Ingredient line
        if is_ingredient(line):
            if mode != 'ingredients':
                mode = 'ingredients'
                if current_ing_section is None:
                    current_ing_section = {'section': None, 'items': []}
                    cur['ingredients'].append(current_ing_section)
            current_ing_section['items'].append(clean(line.lstrip('* ').strip()))
            i += 1
            continue

        # Direction line
        if is_direction(line):
            mode = 'directions'
            # strip leading numbers
            cleaned = STEP_NUM_RE.sub('', line).strip()
            cur['directions'].append(clean(cleaned))
            i += 1
            continue

        # If none matched, treat as note unless we are mid-directions
        if mode in (None, 'notes'):
            # Strip common note prefixes
            note_line = line
            m_note_prefix = re.match(r"^\s*(note|notes)\s*:\s*(.*)$", note_line, re.I)
            if m_note_prefix:
                note_line = m_note_prefix.group(2)
            cur.setdefault('notes', []).append(clean(note_line))
        elif mode == 'directions':
            # Continuation of previous step sentence
            if cur['directions']:
                prev = cur['directions'][-1] + ' ' + clean(line)
                cur['directions'][-1] = prev
            else:
                cur['directions'].append(clean(line))
        else:
            # In ingredients but line didn't parse as quantified; treat as ingredient-ish line
            if mode == 'ingredients':
                if current_ing_section is None:
                    current_ing_section = {'section': None, 'items': []}
                    cur['ingredients'].append(current_ing_section)
                current_ing_section['items'].append(clean(line))
            else:
                cur.setdefault('notes', []).append(clean(line))
        i += 1

    # finalize last
    finalize_recipe(cur, recipes)

    # Drop empty recipes (no title or no content)
    recipes = [r for r in recipes if r.get('title')]

    with open(OUT_PATH, 'w', encoding='utf-8') as out:
        json.dump(recipes, out, indent=2, ensure_ascii=False)

    print(f"Wrote {len(recipes)} recipes to {OUT_PATH}")


if __name__ == '__main__':
    main()
