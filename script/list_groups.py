import glob
import re

MATH_ITALIC_RANGE = "\U0001D400-\U0001D7FF"
RUN_RE = re.compile(f"([{MATH_ITALIC_RANGE}])\\1+")
MATH_ITALIC_RE = re.compile(f"[{MATH_ITALIC_RANGE}]")
ETHIOPIC_RE = re.compile("[ሀ-፿]")
DOUBLED_LETTER_RE = re.compile(r"\b([A-Za-z])\1\b")

files = sorted(glob.glob("vault/*/*/*/*.md"))
groupA, groupB, other = [], [], []
for path in files:
    text = open(path, encoding="utf-8").read()
    if "revision_manual: true" not in text:
        continue
    norm = path.replace("\\", "/")
    if "numero de esta pregunta no estaba" in text or norm == "vault/bioloxia/2020/ordinaria/pregunta-2.md":
        other.append(path)
        continue
    has_long_run = any(len(m.group(0)) >= 3 for m in RUN_RE.finditer(text))
    has_ethiopic = bool(ETHIOPIC_RE.search(text))
    has_ascii_dup = len(DOUBLED_LETTER_RE.findall(text)) >= 3
    if has_long_run or has_ethiopic or has_ascii_dup:
        groupA.append(path)
    else:
        groupB.append(path)

print("GROUP A:", len(groupA))
for p in groupA:
    print(" ", p)
print()
print("GROUP B:", len(groupB))
for p in groupB:
    print(" ", p)
print()
print("OTHER (skip):", len(other))
for p in other:
    print(" ", p)
