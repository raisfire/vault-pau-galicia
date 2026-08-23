import re
import glob
import os

MATH_ITALIC_RANGE = "\U0001D400-\U0001D7FF"
RUN_RE = re.compile(f"([{MATH_ITALIC_RANGE}])\\1+")
ETHIOPIC_RE = re.compile("[ሀ-፿]")
DOUBLED_LETTER_RE = re.compile(r"\b([A-Za-z])\1\b")

files = sorted(glob.glob("vault/*/*/*/*.md"))
groupA, groupB = [], []
for path in files:
    text = open(path, encoding="utf-8").read()
    if "revision_manual: true" not in text:
        continue
    norm = path.replace("\\", "/")
    if "numero de esta pregunta no estaba" in text or norm == "vault/bioloxia/2020/ordinaria/pregunta-2.md":
        continue
    has_long_run = any(len(m.group(0)) >= 3 for m in RUN_RE.finditer(text))
    has_ethiopic = bool(ETHIOPIC_RE.search(text))
    has_ascii_dup = len(DOUBLED_LETTER_RE.findall(text)) >= 3
    fuente = re.search(r'fuente:\s*"([^"]+)"', text).group(1)
    num = int(re.search(r"numero_pregunta:\s*(\d+)", text).group(1))
    entry = (path, fuente, num)
    if has_long_run or has_ethiopic or has_ascii_dup:
        groupA.append(entry)
    else:
        groupB.append(entry)

by_fuente = {}
for path, fuente, num in groupA + groupB:
    by_fuente.setdefault(fuente, []).append((num, path, "A" if (path, fuente, num) in groupA else "B"))

print(f"Group A: {len(groupA)}  Group B: {len(groupB)}  Unique source PDFs: {len(by_fuente)}")
for fuente, entries in sorted(by_fuente.items()):
    nums = sorted(set(n for n, _, _ in entries))
    print(f"{fuente}  -> preguntas {nums}")
