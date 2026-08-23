import re
import glob

RUN_RE = re.compile(r"([\U0001D400-\U0001D7FF])\1+")

files = sorted(glob.glob("vault/matematicas_ii/*/*/*.md")) + \
        sorted(glob.glob("vault/fisica/*/*/*.md")) + \
        sorted(glob.glob("vault/quimica/*/*/*.md"))

for f in files:
    t = open(f, encoding="utf-8").read()
    if "revision_manual: true" not in t:
        continue
    runs = [m.group(0) for m in RUN_RE.finditer(t) if len(m.group(0)) >= 3]
    if runs:
        # dedupe preserving order
        seen = []
        for r in runs:
            if r not in seen:
                seen.append(r)
        print(f, seen)
