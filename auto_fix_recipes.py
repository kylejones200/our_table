from pathlib import Path
import re

SRC = Path('Christmas Sweet Recipes.dedup.txt')
DST = Path('Christmas Sweet Recipes.dedup.fixed.txt')

# Regex helpers
TITLE_RE = re.compile(r'^\s*title\s*:\s*', re.IGNORECASE)
ING_RE = re.compile(r'^\s*ingredients\s*:?', re.IGNORECASE)
DIR_RE = re.compile(r'^\s*direction[s]?\s*:?', re.IGNORECASE)
SERVES_RE = re.compile(r'^\s*serves\s*:?', re.IGNORECASE)
SEPARATOR_RE = re.compile(r'^\s*---\s*$')

# Quantity or bullet detection for ingredients
QUANTITY_RE = re.compile(
    r"^\s*(?:\*|\d|\d+/\d+|\d+\s*[/‐-]\s*\d+|\d+\.\d+|one|two|three|four|five|six|seven|eight|nine|ten|half|quarter|pinch|dash|handful)\b",
    re.IGNORECASE,
)
MEASURE_RE = re.compile(r"\b(cups?|tsp\.?|tbsp\.?|tablespoons?|teaspoons?|oz\.?|ounce[s]?|lb[s]?|pounds?|grams?|g|kg|milliliters?|ml|liters?|l)\b", re.IGNORECASE)

# Common sub-section labels that should end with ':' inside ingredients
SUBSECTIONS = {
    'filling','topping','icing','glaze','sauce','beans','cake','salad','crust','dough','dressing',
    'vinaigrette','marinade','rub','garnish','streusel','mousse','custard','meringue','cookies','sprinkles'
}

# Verbs indicating directions start
DIRECTION_VERBS = {
    'preheat','heat','cook','stir','mix','combine','whisk','bake','simmer','boil','add','reduce','transfer',
    'serve','pour','place','bring','season','fold','beat','brown','arrange','cover','uncover','remove',
    'let','cut','chop','slice','dice','in a','meanwhile','return','drizzle','toast','saute','sauté','marinate',
    'garnish','press','roll','knead','rise','cool','rest','sear','broil','fry','line','grease','sprinkle'
}

def looks_like_direction(line: str) -> bool:
    s = line.strip()
    if not s or SEPARATOR_RE.match(s) or TITLE_RE.match(s) or ING_RE.match(s) or DIR_RE.match(s):
        return False
    low = s.lower()
    # starts with a known verb phrase
    return any(low.startswith(v) for v in DIRECTION_VERBS)


def normalize_section_header(line: str) -> str:
    if ING_RE.match(line):
        return 'ingredients\n'
    if DIR_RE.match(line):
        return 'directions\n'
    if SERVES_RE.match(line):
        # normalize to 'Serves: N'
        val = line.split(':',1)[1].strip() if ':' in line else line.split(None,1)[1].strip() if len(line.split())>1 else ''
        return f'Serves: {val}\n' if val else 'Serves:\n'
    return line


def should_bullet_ingredient(line: str) -> bool:
    s = line.rstrip('\n')
    if not s.strip():
        return False
    if s.lstrip().startswith(('*','-')):
        return False
    if s.strip().endswith(':'):
        return False
    if QUANTITY_RE.match(s):
        return False
    if MEASURE_RE.search(s):
        return False
    # short seasoning/notes lines become bullets
    return True


def add_colon_if_subsection(line: str) -> str:
    s = line.strip()
    if not s:
        return line
    # Already has colon
    if s.endswith(':'):
        return line
    # If matches known subsection words exactly (case-insensitive), add colon
    if s.lower() in SUBSECTIONS:
        return s + ':\n'
    # Handle patterns like 'Beans' or 'Glaze' with trailing spaces
    words = s.lower().split()
    if len(words) <= 3 and words[0] in SUBSECTIONS:
        return s + ':\n'
    return line


def main():
    text = SRC.read_text(encoding='utf-8', errors='ignore').splitlines(True)
    out = []

    in_recipe = False
    in_ingredients = False
    in_directions = False

    prev_line = ''

    for i, line in enumerate(text):
        raw = line
        s = raw.strip('\n')

        # Ensure separator before title
        if TITLE_RE.match(s):
            if not out or not SEPARATOR_RE.match(out[-1].strip()):
                out.append('---\n')
            in_recipe = True
            in_ingredients = False
            in_directions = False
            out.append(normalize_section_header(raw))
            prev_line = raw
            continue

        # Normalize headers regardless of case and optional colon
        if ING_RE.match(s) or DIR_RE.match(s) or SERVES_RE.match(s):
            norm = normalize_section_header(raw)
            key = norm.strip().lower()
            if key == 'ingredients':
                in_ingredients = True
                in_directions = False
            elif key == 'directions':
                in_directions = True
                in_ingredients = False
            out.append(norm)
            prev_line = norm
            continue

        # If inside ingredients, convert obvious subsection labels to end with ':'
        if in_ingredients:
            maybe = add_colon_if_subsection(raw)
            if maybe != raw:
                out.append(maybe)
                prev_line = maybe
                continue
            # Bullet stray ingredient lines that lack quantity/measure
            if should_bullet_ingredient(raw):
                # Avoid bulletting long narrative sentences (probable directions)
                # Heuristic: keep short lines or lines containing 'salt', 'pepper', 'to taste'
                t = raw.strip()
                if len(t) <= 60 or any(w in t.lower() for w in ['salt','pepper','to taste','margarine','margarine','flour','sugar','butter','oil']):
                    out.append('* ' + t + '\n')
                    prev_line = out[-1]
                    continue

        # If not in directions but we likely hit steps after ingredients, auto-insert 'directions'
        if not in_directions and in_recipe and looks_like_direction(raw):
            out.append('directions\n')
            in_directions = True
            in_ingredients = False
            out.append(raw)
            prev_line = raw
            continue

        # Pass through by default
        out.append(raw)
        prev_line = raw

        # Track recipe state resets at separators
        if SEPARATOR_RE.match(s):
            in_recipe = True
            in_ingredients = False
            in_directions = False

    DST.write_text(''.join(out), encoding='utf-8')
    print(f'Wrote fixed file to {DST}')

if __name__ == '__main__':
    main()
