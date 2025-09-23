#!/usr/bin/env python3
"""
Ensure that 'description:' in recipe front matter starts on a new line.
This fixes cases like:
  type: "recipe"description: "..."
becoming
  type: "recipe"
  description: "..."
"""
import re
from pathlib import Path

RECIPES_DIR = Path('content/recipes')

# Pattern: description: that is not at start of a line (no preceding newline)
NOT_LINE_START_DESC = re.compile(r'(?<!\n)(description:\s*")', re.IGNORECASE)

# Also fix when description exists without quotes
NOT_LINE_START_DESC_NOQUOTE = re.compile(r'(?<!\n)(description:\s*[^\n])', re.IGNORECASE)

def fix_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    parts = text.split('---', 2)
    if len(parts) < 3:
        return False
    pre, front, body = parts[0], parts[1], parts[2]

    new_front = NOT_LINE_START_DESC.sub(r"\n\1", front)
    # Apply second pass carefully to avoid double newlines for quoted handled above
    if new_front == front:
        new_front2 = NOT_LINE_START_DESC_NOQUOTE.sub(lambda m: '\n' + m.group(1), front)
    else:
        new_front2 = new_front

    if new_front2 != front:
        new_text = f"---{new_front2}---{body}"
        path.write_text(new_text, encoding='utf-8')
        return True
    return False


def main():
    changed = 0
    total = 0
    for md in sorted(RECIPES_DIR.glob('*.md')):
        total += 1
        try:
            if fix_file(md):
                changed += 1
        except Exception as e:
            print(f"Error fixing {md.name}: {e}")
    print(f"Description newline fixes applied to {changed}/{total} files.")

if __name__ == '__main__':
    main()
