import json
import re
from pathlib import Path

# Heuristics for tokens to preserve uppercase (simple list; extend as needed)
PRESERVE_UPPER = {
    "BBQ", "BLT", "DIY", "M&M", "M&Ms", "M&M's",
    "JELL-O", "JELLO", "MISO", "RAMEN", "OK", "OKRA", "NO",
}

# Words to keep lowercase even at start of interior segments (common connectors)
LOWER_CONNECTORS = {
    "and", "or", "the", "a", "an", "to", "of", "in", "on", "with", "for",
    "at", "by", "from", "as", "but", "nor"
}

def sentence_case(title: str) -> str:
    if not title:
        return title

    # Normalize whitespace
    t = re.sub(r"\s+", " ", title.strip())

    # If looks like ALL CAPS with punctuation, normalize to lower first
    if re.fullmatch(r"[^a-z]*", t):
        t = t.lower()

    # Split on spaces but preserve punctuation attached to words
    tokens = t.split(" ")

    out_tokens = []
    for i, tok in enumerate(tokens):
        core = tok
        prefix = re.match(r"^([^A-Za-z0-9']*)", core).group(0)
        suffix = re.search(r"([^A-Za-z0-9']*)$", core).group(0)
        mid = core[len(prefix):len(core)-len(suffix) if len(suffix) else None]

        # Preserve known uppercase tokens (match case-insensitively)
        if mid.upper() in PRESERVE_UPPER:
            new_mid = mid.upper()
        else:
            # If contains digits or mixed case already, keep as is
            if re.search(r"\d", mid) or (any(c.islower() for c in mid) and any(c.isupper() for c in mid)):
                new_mid = mid
            else:
                # default: lowercase
                new_mid = mid.lower()
                # capitalize first real token
                if i == 0:
                    new_mid = new_mid[:1].upper() + new_mid[1:]
                else:
                    # keep common connectors lowercase, else leave as lower
                    if new_mid in LOWER_CONNECTORS:
                        pass
                    else:
                        # For tokens that were originally Title/Upper case and are 2+ letters, leave lower (sentence case)
                        pass
        out_tokens.append(prefix + new_mid + suffix)

    # Join and fix spacing around punctuation
    s = " ".join(out_tokens)

    # Normalize quotes for foot/inch marks (avoid changing data, just a light touch)
    s = s.replace('”', '"').replace('“', '"').replace("’", "'")

    return s


def process_recipes_json(path: Path):
    data = json.loads(path.read_text())
    changed = False
    for obj in data:
        if isinstance(obj, dict) and "title" in obj and isinstance(obj["title"], str):
            new_title = sentence_case(obj["title"])
            if new_title != obj["title"]:
                obj["title"] = new_title
                changed = True
    if changed:
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        # Write pretty JSON back to original
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return changed


def process_txt_titles(path: Path):
    lines = path.read_text().splitlines()
    changed = False

    def repl(m: re.Match):
        nonlocal changed
        before = m.group(0)
        title_text = m.group(1)
        new = f"title: {sentence_case(title_text)}"
        if new != before:
            changed = True
        return new

    new_lines = []
    pattern = re.compile(r"^title:\s*(.+)$", re.IGNORECASE)
    for line in lines:
        new_line = pattern.sub(repl, line)
        new_lines.append(new_line)

    if changed:
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text("\n".join(lines))
        path.write_text("\n".join(new_lines) + "\n")
    return changed


def main():
    root = Path(__file__).resolve().parent
    paths = [
        root / "recipes.json",
        root / "Christmas Sweet Recipes.dedup.txt",
    ]

    any_changed = False
    for p in paths:
        if not p.exists():
            continue
        if p.suffix == ".json":
            c = process_recipes_json(p)
        else:
            c = process_txt_titles(p)
        any_changed = any_changed or c
    if not any_changed:
        print("No title changes needed.")
    else:
        print("Titles normalized to sentence case. Backups created with .bak extensions.")


if __name__ == "__main__":
    main()
