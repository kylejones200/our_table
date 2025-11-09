#!/usr/bin/env python3
"""
For recipes whose front matter has an empty ingredients list, extract bullet-list
ingredients from the body (content after front matter) where some recipes placed
section headers like "CRUST:", "FILLING:", or lines like "TOMATO-MEAT SAUCE ---"
followed by bullet items.

Actions per file:
- Detect empty ingredients in front matter (ingredients: [] or no items)
- Parse body to find bullet list blocks (lines starting with optional spaces then '- ')
- Filter out decorative/separator bullets like '--- RICOTTA ... ---'
- Move bullet items into front matter ingredients (as quoted strings)
- Remove the extracted bullet blocks (and any immediate header lines above them) from body
- Leave other content (steps, shortcodes) intact
"""
import re
from pathlib import Path

RECIPES_DIR = Path('content/recipes')

BULLET_RE = re.compile(r'^\s*-\s(.+)$')
HEADER_ABOVE_RE = re.compile(r'^\s*([A-Z0-9 ,\-&/]+:|.*---"?\s*)$')
SEPARATOR_ITEM_RE = re.compile(r'^-+\s*[A-Za-z ,\-&/]+\s*-+$')


def split_front_matter(text: str):
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None, None, None
    return parts[0], parts[1], parts[2]


def ingredients_items_in_front(front: str):
    # Return tuple (has_key, count, start_idx, end_idx, lines)
    lines = front.split('\n')
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith('ingredients:') and not ln.startswith(' '):
            start = i
            break
    if start is None:
        return False, 0, None, None, lines
    cnt = 0
    j = start + 1
    while j < len(lines):
        ln = lines[j]
        if ln and not ln.startswith(' '):
            break
        if re.match(r'^\s*-\s', ln):
            cnt += 1
        j += 1
    return True, cnt, start, j, lines


def extract_bullet_blocks(body: str):
    lines = body.split('\n')
    i = 0
    extracted = []  # list of (block_start, block_end, items)
    remove_lines = set()

    while i < len(lines):
        m = BULLET_RE.match(lines[i])
        if not m:
            i += 1
            continue
        # Found start of bullet block
        bstart = i
        items = []
        while i < len(lines):
            m2 = BULLET_RE.match(lines[i])
            if not m2:
                break
            raw = m2.group(1).strip()
            # Normalize remove surrounding quotes
            txt = raw.strip().strip('"\'')
            # Filter separator items like '--- SECTION ---'
            if not SEPARATOR_ITEM_RE.match(txt) and '---' not in txt:
                items.append(txt)
            remove_lines.add(i)
            i += 1
        bend = i  # exclusive
        # Optionally remove header line immediately above block
        if bstart - 1 >= 0:
            prev = lines[bstart - 1]
            if prev.strip() and not prev.strip().startswith('{{<') and HEADER_ABOVE_RE.match(prev.strip()):
                remove_lines.add(bstart - 1)
        if items:
            extracted.append((bstart, bend, items))
        # continue loop from current i
    # Build cleaned body with removed lines excluded
    cleaned_lines = [ln for idx, ln in enumerate(lines) if idx not in remove_lines]
    return extracted, '\n'.join(cleaned_lines)


def process_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    pre, front, body = split_front_matter(text)
    if front is None:
        return False
    has_ing, count, start, end, flines = ingredients_items_in_front(front)
    if not has_ing:
        return False
    if count > 0:
        return False  # already populated

    # Extract from body
    blocks, cleaned_body = extract_bullet_blocks(body)
    items = []
    for _, _, its in blocks:
        items.extend(its)

    if not items:
        return False

    # Rebuild ingredients block
    new_flines = flines[:start]
    new_flines.append('ingredients:')
    for it in items:
        new_flines.append(f'  - "{it}"')
    new_flines.extend(flines[end:])

    # Write back
    front_joined = "\n".join(new_flines)
    new_text = f"---\n{front_joined}---{cleaned_body}"
    path.write_text(new_text, encoding='utf-8')
    return True


def main():
    changed = 0
    total = 0
    for md in sorted(RECIPES_DIR.glob('*.md')):
        total += 1
        try:
            if process_file(md):
                changed += 1
        except Exception as e:
            print(f"Error processing {md.name}: {e}")
    print(f"Populated ingredients from body in {changed}/{total} files.")

if __name__ == '__main__':
    main()
