# -*- coding: utf-8 -*-
import re

MATH_RUN_RE = re.compile(r"([\U0001D400-\U0001D7FF])\1+")
PUA_RE = re.compile("[-]")
ETHIOPIC_RE = re.compile("[ሀ-፿]")
TAMIL_RE = re.compile("[஀-௿]")
BENGALI_TELUGU_RE = re.compile("[ঀ-௿ఀ-౿]")

ALL_69 = """vault/fisica/2024/extraordinaria/pregunta-6.md
vault/fisica/2024/ordinaria/pregunta-1.md
vault/fisica/2024/ordinaria/pregunta-6.md
vault/matematicas_ii/2020/extraordinaria/pregunta-1.md
vault/matematicas_ii/2020/extraordinaria/pregunta-2.md
vault/matematicas_ii/2020/extraordinaria/pregunta-3.md
vault/matematicas_ii/2020/extraordinaria/pregunta-4.md
vault/matematicas_ii/2020/extraordinaria/pregunta-6.md
vault/matematicas_ii/2020/ordinaria/pregunta-1.md
vault/matematicas_ii/2020/ordinaria/pregunta-2.md
vault/matematicas_ii/2020/ordinaria/pregunta-4.md
vault/matematicas_ii/2021/extraordinaria/pregunta-2.md
vault/matematicas_ii/2021/extraordinaria/pregunta-8.md
vault/matematicas_ii/2021/ordinaria/pregunta-1.md
vault/matematicas_ii/2021/ordinaria/pregunta-2.md
vault/matematicas_ii/2021/ordinaria/pregunta-6.md
vault/matematicas_ii/2021/ordinaria/pregunta-8.md
vault/matematicas_ii/2022/extraordinaria/pregunta-1.md
vault/matematicas_ii/2022/extraordinaria/pregunta-2.md
vault/matematicas_ii/2022/extraordinaria/pregunta-3.md
vault/matematicas_ii/2022/extraordinaria/pregunta-6.md
vault/matematicas_ii/2022/ordinaria/pregunta-1.md
vault/matematicas_ii/2022/ordinaria/pregunta-2.md
vault/matematicas_ii/2024/extraordinaria/pregunta-1.md
vault/matematicas_ii/2024/extraordinaria/pregunta-2.md
vault/matematicas_ii/2024/extraordinaria/pregunta-3.md
vault/matematicas_ii/2024/ordinaria/pregunta-1.md
vault/matematicas_ii/2024/ordinaria/pregunta-2.md
vault/matematicas_ii/2026/extraordinaria/pregunta-2.md
vault/matematicas_ii/2026/extraordinaria/pregunta-3.md
vault/quimica/2022/extraordinaria/pregunta-3.md
vault/quimica/2022/extraordinaria/pregunta-5.md
vault/quimica/2024/extraordinaria/pregunta-8.md
vault/quimica/2026/extraordinaria/pregunta-1.md
vault/fisica/2020/extraordinaria/pregunta-1.md
vault/fisica/2020/ordinaria/pregunta-2.md
vault/fisica/2022/ordinaria/pregunta-2.md
vault/fisica/2022/ordinaria/pregunta-3.md
vault/fisica/2023/extraordinaria/pregunta-1.md
vault/fisica/2023/extraordinaria/pregunta-3.md
vault/fisica/2023/extraordinaria/pregunta-6.md
vault/fisica/2026/extraordinaria/pregunta-1.md
vault/fisica/2026/extraordinaria/pregunta-2.md
vault/fisica/2026/ordinaria/pregunta-2.md
vault/matematicas_ii/2023/extraordinaria/pregunta-1.md
vault/matematicas_ii/2023/extraordinaria/pregunta-2.md
vault/matematicas_ii/2023/extraordinaria/pregunta-3.md
vault/matematicas_ii/2023/extraordinaria/pregunta-4.md
vault/matematicas_ii/2023/extraordinaria/pregunta-5.md
vault/matematicas_ii/2023/extraordinaria/pregunta-6.md
vault/matematicas_ii/2023/extraordinaria/pregunta-7.md
vault/matematicas_ii/2023/ordinaria/pregunta-1.md
vault/matematicas_ii/2023/ordinaria/pregunta-2.md
vault/matematicas_ii/2023/ordinaria/pregunta-3.md
vault/matematicas_ii/2023/ordinaria/pregunta-4.md
vault/matematicas_ii/2023/ordinaria/pregunta-5.md
vault/matematicas_ii/2023/ordinaria/pregunta-6.md
vault/matematicas_ii/2023/ordinaria/pregunta-7.md
vault/matematicas_ii/2025/extraordinaria/pregunta-2.md
vault/matematicas_ii/2025/extraordinaria/pregunta-3.md
vault/matematicas_ii/2025/extraordinaria/pregunta-4.md
vault/matematicas_ii/2026/extraordinaria/pregunta-4.md
vault/matematicas_ii/2026/ordinaria/pregunta-1.md
vault/matematicas_ii/2026/ordinaria/pregunta-2.md
vault/matematicas_ii/2026/ordinaria/pregunta-3.md
vault/matematicas_ii/2026/ordinaria/pregunta-4.md
vault/matematicas_ii/2025/ordinaria/pregunta-2.md
vault/matematicas_ii/2025/ordinaria/pregunta-3.md""".splitlines()

print(f"Total files in list: {len(ALL_69)}")

problems = []
still_true = []
for path in ALL_69:
    with open(path, encoding="utf-8") as f:
        t = f.read()
    if "revision_manual: true" in t:
        still_true.append(path)
    long_runs = [m.group(0) for m in MATH_RUN_RE.finditer(t) if len(m.group(0)) >= 3]
    pua = PUA_RE.findall(t)
    eth = ETHIOPIC_RE.findall(t)
    tam = TAMIL_RE.findall(t)
    bt = BENGALI_TELUGU_RE.findall(t)
    if long_runs or pua or eth or tam or bt:
        problems.append((path, long_runs, set(hex(ord(c)) for c in pua), set(hex(ord(c)) for c in tam+bt)))

print(f"\nTodavía revision_manual: true ({len(still_true)}):")
for p in still_true:
    print(" ", p)

print(f"\nProblemas restantes detectados ({len(problems)}):")
for path, runs, pua, other in problems:
    print(f"  {path}: runs={runs} pua={pua} other_script={other}")
