# -*- coding: utf-8 -*-
"""
Fase 1b (limpieza): colapsa pares de caracteres EXACTAMENTE duplicados
dentro del bloque Unicode "Mathematical Alphanumeric Symbols" (U+1D400-
U+1D7FF) - el bloque usado para variables en cursiva/negrita (𝐴, 𝑋, 𝐵...)
que la extracción de PyMuPDF duplicó por error en varias preguntas.

IMPORTANTE - lección aprendida tras un primer intento fallido: solo se
colapsan RACHAS DE EXACTAMENTE 2 caracteres idénticos consecutivos. Una
racha de 3 o más (ej. "𝐴𝐴𝐴𝐴", cuatro veces el mismo codepoint) NO se toca,
porque se comprobó visualmente contra el PDF (Matemáticas II 2020
extraordinaria, pregunta 1) que ese caso concreto en realidad eran DOS
LETRAS DISTINTAS ("AB") mal identificadas como el mismo carácter repetido
- no una letra duplicada. Colapsar una racha larga habría borrado la "B"
de la ecuación sin que nada lo delatara en el texto. Las rachas de exactamente
2 sí se verificaron visualmente en 3 casos distintos (B, A, X) y coinciden
con el original en los 3 - ese patrón sí es duplicación simple y segura.

Una pregunta queda RESUELTA (revision_manual: false, limpieza:
"colapso_automatico") solo si:
  (a) tenía al menos un par (racha de exactamente 2) que colapsar, y
  (b) tras colapsar, no quedan indicios de otros problemas:
      - rachas de 3+ del mismo carácter (posible pérdida de información,
        no es duplicación simple)
      - glifos de flecha mal identificados (bloque Etíope)
      - el patrón de letras ASCII sueltas dobladas (otra causa distinta)
"""
import glob
import re

MATH_ITALIC_RANGE = "\U0001D400-\U0001D7FF"
RUN_RE = re.compile(f"([{MATH_ITALIC_RANGE}])\\1+")  # any run of 2+ identical math-italic chars
PAIR_ONLY_RE = re.compile(f"([{MATH_ITALIC_RANGE}])\\1(?!\\1)")  # exactly 2 (not 3+)
MATH_ITALIC_RE = re.compile(f"[{MATH_ITALIC_RANGE}]")
ETHIOPIC_RE = re.compile("[ሀ-፿]")
DOUBLED_LETTER_RE = re.compile(r"\b([A-Za-z])\1\b")


def collapse_pairs_only(text):
    """Collapse only exact-length-2 runs; leave runs of 3+ untouched."""
    out = []
    i = 0
    n = len(text)
    changed = False
    had_long_run = False
    while i < n:
        ch = text[i]
        if MATH_ITALIC_RE.match(ch):
            j = i
            while j < n and text[j] == ch:
                j += 1
            run_len = j - i
            if run_len == 2:
                out.append(ch)
                changed = True
            elif run_len >= 3:
                out.append(text[i:j])
                had_long_run = True
            else:
                out.append(ch)
            i = j
        else:
            out.append(ch)
            i += 1
    return "".join(out), changed, had_long_run


files = sorted(glob.glob("vault/*/*/*/*.md"))
flagged = [f for f in files if 'revision_manual: true' in open(f, encoding="utf-8").read()]

resolved = []
unresolved_long_run = []
unresolved_arrow = []
unresolved_ascii_dup = []
unresolved_single_math = []
unresolved_other = []

for path in flagged:
    with open(path, encoding="utf-8") as f:
        original = f.read()

    new_text, had_pair, had_long_run = collapse_pairs_only(original)
    has_ethiopic = bool(ETHIOPIC_RE.search(new_text))
    ascii_dup_hits = len(DOUBLED_LETTER_RE.findall(new_text))
    has_ascii_dup_pattern = ascii_dup_hits >= 3
    has_single_math_italic = bool(MATH_ITALIC_RE.search(new_text)) and not had_long_run

    if had_pair and not had_long_run and not has_ethiopic and not has_ascii_dup_pattern:
        new_text = new_text.replace("revision_manual: true", 'revision_manual: false\nlimpieza: "colapso_automatico"')
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        resolved.append(path)
    else:
        if had_long_run:
            unresolved_long_run.append(path)
        elif has_ethiopic:
            unresolved_arrow.append(path)
        elif has_ascii_dup_pattern:
            unresolved_ascii_dup.append(path)
        elif not had_pair and has_single_math_italic:
            unresolved_single_math.append(path)
        else:
            unresolved_other.append(path)

print(f"Total marcadas revision_manual: true: {len(flagged)}")
print(f"Resueltas por colapso automático (solo pares exactos de 2): {len(resolved)}")
print()
print(f"Sin resolver - racha de 3+ caracteres idénticos (posible pérdida de información, ej. 2 letras distintas mal leídas como la misma): {len(unresolved_long_run)}")
for p in unresolved_long_run:
    print(f"  {p}")
print()
print(f"Sin resolver - glifo de flecha/otro (bloque Etíope): {len(unresolved_arrow)}")
for p in unresolved_arrow:
    print(f"  {p}")
print()
print(f"Sin resolver - patrón de letras ASCII dobladas (no es este bloque Unicode): {len(unresolved_ascii_dup)}")
for p in unresolved_ascii_dup:
    print(f"  {p}")
print()
print(f"Sin resolver - solo tenía un símbolo matemático SUELTO (no duplicado, nada que colapsar): {len(unresolved_single_math)}")
for p in unresolved_single_math:
    print(f"  {p}")
print()
print(f"Sin resolver - otra causa no identificada: {len(unresolved_other)}")
for p in unresolved_other:
    print(f"  {p}")

total_unresolved = (len(unresolved_long_run) + len(unresolved_arrow) + len(unresolved_ascii_dup)
                     + len(unresolved_single_math) + len(unresolved_other))
print()
print(f"Total sin resolver: {total_unresolved}  (suma con resueltas: {len(resolved) + total_unresolved} / {len(flagged)})")
