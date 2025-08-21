import re
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path

INPUT = Path('Christmas Sweet Recipes.docx.txt')
OUTPUT = Path('Christmas Sweet Recipes.dedup.txt')
REPORT = Path('Christmas Sweet Recipes.dedup.report.txt')

title_re = re.compile(r'^(?i:title)\s*:?', re.ASCII)


def _ascii_simplify(s: str) -> str:
    # Unicode normalize, then replace common typography to ASCII
    s = unicodedata.normalize('NFKD', s)
    # Translate curly quotes and dashes
    trans = {
        ord('’'): "'",
        ord('‘'): "'",
        ord('“'): '"',
        ord('”'): '"',
        ord('–'): '-',  # en dash
        ord('—'): '-',  # em dash
        ord('‐'): '-',  # hyphen
        ord('−'): '-',  # minus sign
        ord('·'): ' ',
        ord('\u00A0'): ' ',  # non-breaking space
    }
    s = s.translate(trans)
    return s


def normalize_title(line: str) -> str:
    # strip leading 'title' label and normalize whitespace and case
    t = title_re.sub('', line, count=1)
    t = _ascii_simplify(t)
    t = t.strip()
    t = re.sub(r'\s+', ' ', t)
    # normalize some punctuation spacing like " - " to "-"
    t = re.sub(r'\s*-[\s-]*', '-', t)
    # collapse multiple ampersand spaces
    t = re.sub(r'\s*&\s*', ' & ', t)
    return t.lower()


def is_title(line: str) -> bool:
    return bool(title_re.match(line))


def block_size(lines: list[str]) -> int:
    # Use character count excluding leading/trailing blank lines to prefer fullest block
    # but include title line as well
    # Trim leading/trailing empty lines for fair comparison
    i, j = 0, len(lines) - 1
    while i <= j and not lines[i].strip():
        i += 1
    while j >= i and not lines[j].strip():
        j -= 1
    if i > j:
        return 0
    return sum(len(l) for l in lines[i:j+1])


def parse_blocks(text: list[str]):
    preface = []
    blocks = []  # list of (start_index, title_line, block_lines)

    i = 0
    n = len(text)
    # Collect preface until first title
    while i < n and not is_title(text[i]):
        preface.append(text[i])
        i += 1

    while i < n:
        if not is_title(text[i]):
            # If stray content between titles, attach to previous block if any, else preface
            if blocks:
                blocks[-1][2].append(text[i])
            else:
                preface.append(text[i])
            i += 1
            continue
        # Start of a block
        start = i
        title_line = text[i].rstrip('\n')
        cur = [text[i]]  # include title line
        i += 1
        while i < n and not is_title(text[i]):
            cur.append(text[i])
            i += 1
        blocks.append([start, title_line, cur])

    return preface, blocks


def main():
    raw = INPUT.read_text(encoding='utf-8', errors='ignore').splitlines(True)
    preface, blocks = parse_blocks(raw)

    # Track the best block for each normalized title; preserve first-seen order of titles
    order = []
    best_block_by_title: dict[str, list[str]] = {}
    best_size_by_title: dict[str, int] = {}
    all_blocks_by_title: defaultdict[str, list[list[str]]] = defaultdict(list)

    for _, title_line, block_lines in blocks:
        key = normalize_title(title_line)
        if key not in best_block_by_title:
            order.append(key)
        all_blocks_by_title[key].append(block_lines)
        size = block_size(block_lines)
        if key not in best_block_by_title or size > best_size_by_title[key]:
            best_block_by_title[key] = block_lines
            best_size_by_title[key] = size

    # Build output
    out_lines = []
    out_lines.extend(preface)
    if out_lines and out_lines[-1].strip():
        out_lines.append('\n')

    for key in order:
        blk = best_block_by_title[key]
        # Ensure single blank line separation
        if out_lines and out_lines[-1].strip():
            out_lines.append('\n')
        out_lines.extend(blk)
        if blk and blk[-1] and not blk[-1].endswith('\n'):
            out_lines.append('\n')

    OUTPUT.write_text(''.join(out_lines), encoding='utf-8')

    # Report
    counts = {k: len(v) for k, v in all_blocks_by_title.items()}
    total_titles = sum(counts.values())
    unique_titles = len(counts)
    duplicates = {k: c for k, c in counts.items() if c > 1}

    lines = []
    lines.append(f'Input file: {INPUT}\n')
    lines.append(f'Output file: {OUTPUT}\n')
    lines.append(f'Unique titles: {unique_titles}\n')
    lines.append(f'Total title blocks: {total_titles}\n')
    lines.append(f'Duplicated titles: {len(duplicates)}\n')
    lines.append('\nTop duplicates (count: title)\n')
    for k, c in sorted(duplicates.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f'{c}: {k}\n')

    REPORT.write_text(''.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
