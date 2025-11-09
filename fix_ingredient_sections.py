#!/usr/bin/env python3
"""
Merge inline section headers (e.g., CRUST:, FILLING:, TOPPING:, GLAZE:, ICING:, etc.)
that appear as top-level front matter keys with list items into the ingredients list.

- Detects top-level keys whose blocks are list items ("  - ...") and whose key is
  not part of the canonical recipe keys. Those are treated as ingredient sections.
- Moves their bullet items under a single ingredients: list, preserving existing
  ingredients items if present.
- Removes the section keys from front matter.
- Leaves content body unchanged.
"""
import re
from pathlib import Path

RECIPES_DIR = Path('content/recipes')

CANONICAL_KEYS = {
    'title','date','type','description','yield','categories','source',
    'prep_time','cook_time','total_time','ingredients','steps','notes',
    'allergens','nutrition','image','image_credit','image_emoji'
}

TOP_LEVEL_KEY_RE = re.compile(r'^(?P<key>[A-Za-z0-9_ \-]+):\s*(.*)$')


def split_front_matter(text: str):
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None, None, None
    return parts[0], parts[1], parts[2]


def parse_blocks(front: str):
    lines = front.split('\n')
    blocks = []  # list of (key, start_idx, end_idx)
    i = 0
    while i < len(lines):
        line = lines[i]
        m = TOP_LEVEL_KEY_RE.match(line)
        if m and not line.startswith(' '):
            key = m.group('key').strip()
            start = i
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt and not nxt.startswith(' '):
                    if TOP_LEVEL_KEY_RE.match(nxt):
                        break
                i += 1
            blocks.append((key, start, i))
        else:
            i += 1
    return lines, blocks


def get_list_items(block_lines):
    # Return list of bullet lines for a block (lines with any indentation + dash)
    items = []
    for ln in block_lines[1:]:  # skip the key line
        if re.match(r"\s+-\s", ln):
            items.append(ln)
    return items


def merge_sections(front: str) -> str:
    lines, blocks = parse_blocks(front)
    if not blocks:
        return front

    # Locate ingredients block and collect existing items
    ing_idx = None
    existing_items = []
    for idx, (key, start, end) in enumerate(blocks):
        if key.strip().lower() == 'ingredients':
            ing_idx = idx
            existing_items = get_list_items(lines[start:end])
            break

    # Identify candidate section blocks to merge
    merge_indices = []
    merged_items = []
    for idx, (key, start, end) in enumerate(blocks):
        kcanon = key.strip().lower()
        if kcanon in CANONICAL_KEYS:
            continue
        block_lines = lines[start:end]
        items = get_list_items(block_lines)
        # Only consider as a section if it has at least 1 bullet line and no scalar value on key line
        if items and TOP_LEVEL_KEY_RE.match(block_lines[0]) and block_lines[0].endswith(':'):
            merge_indices.append(idx)
            merged_items.extend(items)

    if not merge_indices and existing_items:
        # Nothing to do
        return front
    if not merge_indices and not existing_items:
        # No ingredients and no sections to merge
        return front

    # Build new lines without the merged section blocks
    keep_mask = [True] * len(lines)
    for idx in merge_indices:
        _, start, end = blocks[idx]
        for i in range(start, end):
            keep_mask[i] = False

    # Reconstruct ingredients block
    if ing_idx is None:
        # Create a new ingredients block near the end of front matter
        # Append at the end with a blank line before
        new_lines = [ln for i, ln in enumerate(lines) if keep_mask[i]]
        if new_lines and new_lines[-1] != '':
            new_lines.append('')
        new_lines.append('ingredients:')
        # Add all items merged
        for it in merged_items:
            new_lines.append(it)
        return '\n'.join(new_lines)
    else:
        # Replace existing ingredients block with combined items
        ikey, istart, iend = blocks[ing_idx]
        # Keep everything except the inner lines of the ingredients block; we'll rebuild it
        new_lines = lines[:istart]
        # Ingredients header
        new_lines.append('ingredients:')
        # Combined items: existing first, then merged
        combined = existing_items[:]
        combined.extend(merged_items)
        # Deduplicate while preserving order
        seen = set()
        for it in combined:
            val = it.strip()
            if val not in seen:
                new_lines.append(it)
                seen.add(val)
        # Append the remainder, skipping whatever was in the original ingredients block
        new_lines.extend(lines[iend:])
        # Remove any now-unused lines from removed blocks
        new_lines = [ln for i, ln in enumerate(new_lines)]
        return '\n'.join(new_lines)


def process_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    pre, front, body = split_front_matter(text)
    if front is None:
        return False
    new_front = merge_sections(front)
    if new_front != front:
        path.write_text(f"---\n{new_front}---{body}", encoding='utf-8')
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
    print(f"Merged ingredient sections in {changed}/{total} files.")

if __name__ == '__main__':
    main()
