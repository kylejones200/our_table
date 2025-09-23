#!/usr/bin/env python3
"""
Normalize Hugo recipe markdown files:
- Title -> Title Case
- Capitalize first letter of each step
- Ensure description exists (auto-generate if missing)
- Ensure yield, prep_time, cook_time, total_time exist (estimate when missing)
- Insert recipe image shortcode into content if missing
"""
import re
from pathlib import Path

RECIPES_DIR = Path('content/recipes')

MINOR_WORDS = {
    'a','an','and','as','at','but','by','for','in','nor','of','on','or','per','the','to','vs','via','with'
}

def smart_title_case(s: str) -> str:
    words = re.split(r'(\s+)', s.strip())
    out = []
    for i, w in enumerate(words):
        if i % 2 == 1:  # whitespace splitter preserves separators
            out.append(w)
            continue
        base = w.strip('"\'')
        lower = base.lower()
        if i == 0 or i == len(words)-1 or lower not in MINOR_WORDS:
            out.append(base[:1].upper() + base[1:])
        else:
            out.append(lower)
    return ''.join(out)

DURATION_RE = re.compile(r'(\d+)\s*(hour|hours|hr|hrs|minute|minutes|min|mins)', re.IGNORECASE)

def parse_minutes(text: str) -> int:
    total = 0
    for n, unit in DURATION_RE.findall(text):
        n = int(n)
        unit = unit.lower()
        if unit.startswith('hour') or unit.startswith('hr'):
            total += n * 60
        else:
            total += n
    return total

def sentence_case(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    return s[0].upper() + s[1:]

def extract_front_matter_sections(front: str):
    # Find positions of top-level keys (no leading spaces)
    lines = front.split('\n')
    key_indices = []
    for idx, line in enumerate(lines):
        if line and not line.startswith(' ') and ':' in line:
            key_indices.append(idx)
    return lines, key_indices

def get_list_block(lines, start_idx):
    items = []
    i = start_idx + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith('  - '):
            items.append((i, line))
            i += 1
            continue
        # Stop when next top-level or lesser indent
        if line and not line.startswith(' '):
            break
        if line.startswith(' '):
            i += 1
            continue
        break
    return items

def ensure_field(front_lines, key, value):
    # If key present, leave; else insert before the first blank line after title if possible, otherwise append at end
    for i, line in enumerate(front_lines):
        if re.match(rf'^{re.escape(key)}\s*:', line):
            # If empty value, replace
            if re.match(rf'^{re.escape(key)}\s*:\s*$', line):
                front_lines[i] = f"{key}: {value}"
            return front_lines
    # Insert near top after title/date/type if present
    insert_at = min(len(front_lines), 10)
    for i, line in enumerate(front_lines[:10]):
        if line.strip() == '' or line.startswith('description:'):
            insert_at = i
            break
    front_lines.insert(insert_at, f"{key}: {value}")
    return front_lines

def normalize_file(path: Path) -> bool:
    raw = path.read_text(encoding='utf-8')
    parts = raw.split('---', 2)
    if len(parts) < 3:
        return False
    head, front, body = parts[0], parts[1], parts[2]

    # Title Case
    m = re.search(r'(^|\n)title:\s*"([^"]*)"', front)
    if m:
        original_title = m.group(2)
        titled = smart_title_case(original_title)
        if titled != original_title:
            front = front.replace(f'title: "{original_title}"', f'title: "{titled}"')
    else:
        # If not quoted format, try unquoted
        m2 = re.search(r'(^|\n)title:\s*([^\n]+)', front)
        if m2:
            val = m2.group(2).strip()
            titled = smart_title_case(val.strip('"\''))
            front = re.sub(r'(^|\n)title:\s*[^\n]+', f"\1title: \"{titled}\"", front)

    # Capitalize steps
    lines = front.split('\n')
    for idx, line in enumerate(lines):
        if line.strip().startswith('steps:'):
            items = get_list_block(lines, idx)
            for i, item_line in items:
                # formats like:   - "text" or   - 'text'
                mitem = re.match(r"(\s*-\s*)(['\"]?)(.*)\2\s*$", item_line)
                if mitem:
                    prefix, quote, text = mitem.group(1), mitem.group(2), mitem.group(3)
                    # Keep quotes if they existed
                    new_text = sentence_case(text)
                    q = quote if quote else '"'
                    lines[i] = f"{prefix}{q}{new_text}{q}"
            break
    front = '\n'.join(lines)

    # Ensure description
    desc_match = re.search(r'(^|\n)description:\s*"([^"]*)"', front)
    if not desc_match or desc_match.group(2).strip() == '':
        # Try to build from title + up to two ingredients
        ing_lines = []
        lns = front.split('\n')
        for j, l in enumerate(lns):
            if l.strip().startswith('ingredients:'):
                items = get_list_block(lns, j)
                for _, il in items[:3]:
                    t = re.sub(r'^\s*-\s*', '', il).strip().strip('"\'')
                    # remove quantities
                    t = re.sub(r'\b\d+[\/\d]*\b', '', t)
                    t = re.sub(r'\([^)]*\)', '', t)
                    t = re.sub(r'[^A-Za-z ]+', ' ', t)
                    t = re.sub(r'\s+', ' ', t).strip()
                    if t:
                        ing_lines.append(t)
                break
        title_now = re.search(r'(^|\n)title:\s*"([^"]*)"', front)
        title_txt = title_now.group(2) if title_now else 'Recipe'
        if ing_lines:
            desc = f"{title_txt} made with {', '.join(ing_lines[:2])}."
        else:
            desc = f"A delicious {title_txt} recipe for any occasion."
        if desc_match:
            front = front.replace(desc_match.group(0), f"description: \"{desc}\"")
        else:
            front = f"{front}\ndescription: \"{desc}\""

    # Ensure times and yield
    text_for_times = front + "\n" + body
    minutes = parse_minutes(text_for_times)
    default_prep = 10
    cook_time = minutes if minutes > 0 else 20
    total_time = cook_time + default_prep

    # Detect existing fields
    has_prep = re.search(r'(^|\n)prep_time:\s*', front) is not None
    has_cook = re.search(r'(^|\n)cook_time:\s*', front) is not None
    has_total = re.search(r'(^|\n)total_time:\s*', front) is not None
    has_yield = re.search(r'(^|\n)yield:\s*', front) is not None

    flines = front.split('\n')
    if not has_prep:
        flines = ensure_field(flines, 'prep_time', f'"{default_prep} minutes"')
    if not has_cook:
        flines = ensure_field(flines, 'cook_time', f'"{cook_time} minutes"')
    if not has_total:
        flines = ensure_field(flines, 'total_time', f'"{total_time} minutes"')
    if not has_yield:
        flines = ensure_field(flines, 'yield', '"4 servings"')
    front = '\n'.join(flines)

    # Insert shortcode at top of content body if missing
    if '{{< recipe-image >}}' not in body:
        body = "\n{{< recipe-image >}}\n\n" + body.lstrip()

    new_content = f"---\n{front.strip()}\n---{body}"
    path.write_text(new_content, encoding='utf-8')
    return True


def main():
    changed = 0
    total = 0
    for md in sorted(RECIPES_DIR.glob('*.md')):
        total += 1
        try:
            if normalize_file(md):
                changed += 1
        except Exception as e:
            print(f"Failed {md.name}: {e}")
    print(f"Updated {changed}/{total} recipe files.")

if __name__ == '__main__':
    main()
