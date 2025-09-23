#!/usr/bin/env python3
"""
Reorder and normalize front matter keys for all recipe markdown files.
- Enforces canonical order
- Normalizes common misspellings and synonyms (field->yield, category/categoties->categories,
  incredients->ingredients, nutirtion->nutrition, note->notes)
- Preserves values and list blocks as-is
- Keeps any extra keys not listed, appended after canonical keys in original relative order
"""
import re
from pathlib import Path
from collections import OrderedDict

RECIPES_DIR = Path('content/recipes')

# Canonical order of keys (front matter)
CANONICAL_ORDER = [
    'title',
    'date',
    'type',
    'description',
    'yield',
    'categories',
    'source',
    'prep_time',
    'cook_time',
    'total_time',
    'ingredients',
    'steps',
    'notes',
    'allergens',
    'nutrition',
    'image',
    'image_credit',
    'image_emoji',
]

# Map misspelled/synonym keys to canonical
NORMALIZE_KEY = {
    'field': 'yield',
    'servings': 'yield',  # sometimes appears
    'category': 'categories',
    'categories': 'categories',
    'categoties': 'categories',
    'categores': 'categories',
    'catergories': 'categories',
    'incredients': 'ingredients',
    'ingredient': 'ingredients',
    'ingredients': 'ingredients',
    'nutirtion': 'nutrition',
    'nutriton': 'nutrition',
    'note': 'notes',
    'notes': 'notes',
}

TOP_LEVEL_KEY_RE = re.compile(r'^(?P<key>[A-Za-z0-9_ \-]+):\s*(.*)$')


def split_front_matter(text: str):
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None, None, None
    return parts[0], parts[1], parts[2]


def parse_blocks(front: str):
    lines = front.split('\n')
    blocks = []  # list of (orig_key, start_idx, end_idx)
    i = 0
    while i < len(lines):
        line = lines[i]
        m = TOP_LEVEL_KEY_RE.match(line)
        if m and not line.startswith(' '):
            key = m.group('key').strip()
            start = i
            i += 1
            # capture following indented lines as part of this block
            while i < len(lines):
                nxt = lines[i]
                if nxt and not nxt.startswith(' '):
                    if TOP_LEVEL_KEY_RE.match(nxt):
                        break
                i += 1
            end = i  # exclusive
            blocks.append((key, start, end))
        else:
            i += 1
    return lines, blocks


def normalize_key_name(name: str) -> str:
    key_lower = name.strip().lower()
    return NORMALIZE_KEY.get(key_lower, key_lower)


def reorder_front(front: str) -> str:
    lines, blocks = parse_blocks(front)
    if not blocks:
        return front

    # Build mapping: canonical_key -> list of (orig_key, block_lines)
    key_blocks = OrderedDict()
    seen_order = []

    for key, start, end in blocks:
        canon = normalize_key_name(key)
        block_lines = lines[start:end]
        if canon not in key_blocks:
            key_blocks[canon] = []
        key_blocks[canon].append((key, block_lines))
        seen_order.append(canon)

    # Compose in canonical order first, then remaining extra keys in their first-seen order
    out_lines = []

    def append_block(block_lines):
        # Ensure a blank line separation only where appropriate
        if out_lines and (out_lines[-1] != ''):
            out_lines.append('')
        out_lines.extend(block_lines)

    # Emit canonical keys
    for canon in CANONICAL_ORDER:
        if canon in key_blocks:
            # If multiple blocks for same canonical key exist, emit them in appearance order
            for _, blines in key_blocks[canon]:
                # If we are renaming, replace the first line's key label to canonical
                if blines:
                    m = TOP_LEVEL_KEY_RE.match(blines[0])
                    if m:
                        # reconstruct the first line with canonical key
                        value = blines[0].split(':', 1)[1]
                        blines = [f"{canon}:{value}"] + blines[1:]
                append_block(blines)
            del key_blocks[canon]

    # Emit any remaining keys (not in canonical list) in original order of first appearance
    for canon, blocks_list in key_blocks.items():
        for _, blines in blocks_list:
            append_block(blines)

    # Preserve trailing newline semantics
    return '\n'.join(out_lines).strip('\n') + '\n'


def process_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    pre, front, body = split_front_matter(text)
    if front is None:
        return False
    new_front = reorder_front(front)
    if new_front != front:
        new_text = f"---\n{new_front}---{body}"
        path.write_text(new_text, encoding='utf-8')
        return True
    return False


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
    print(f"Reordered front matter in {changed}/{total} files.")

if __name__ == '__main__':
    main()
