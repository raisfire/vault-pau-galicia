# -*- coding: utf-8 -*-
"""
Fase 1b: trocea los PDFs de fuentes/ en preguntas sueltas dentro de vault/.

ALCANCE: solo 2020-2026 (Matemáticas II, Bioloxía, Física, Química).
2010-2019 usa una estructura completamente distinta ("OPCIÓN A/B" con
cuestións numeradas + terminoloxía + test, sin "PREGUNTA N" ni tema por
pregunta) que no encaja con la ficha de troceo dada - se deja sin tocar,
documentado en el resumen final para decidir una ficha propia más adelante.
Bioloxía 2019 (escaneado) y los huecos de 2019 extraordinaria tampoco se tocan.

Formatos de pregunta encontrados dentro del rango 2020-2026:
  - "PREGUNTA N. TEMA" (Bioloxía, Física, Química 2020-2024; las 4
    asignaturas 2025-2026) - Física/Química 2020-2024 en realidad NO traen
    tema real en la cabecera (solo una instrucción genérica tipo "Resolva
    este problema:"), así que tema queda vacío ahí en vez de inventarlo.
  - "N. Tema:" sin la palabra PREGUNTA (Matemáticas II 2020-2023).
  - "PREGUNTA N. TEMA. (X puntos)" con puntuación explícita por pregunta
    (2025-2026, las 4 asignaturas).

La puntuación por pregunta, cuando no viene explícita en su propio
encabezado, se toma de la regla general del párrafo introductorio (p.ej.
"cada pregunta vale 2 puntos (1 punto por apartado)"), aplicada por igual
a las 8 (o 4) preguntas.
"""
import csv
import os
import re
import unicodedata
import fitz  # pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(ROOT, "fuentes")
VAULT = os.path.join(ROOT, "vault")

SUBJECT_CODE = {"matematicas_ii": "20", "bioloxia": "21", "fisica": "23", "quimica": "24"}
YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]
CONVOCATORIAS = ["ordinaria", "extraordinaria"]

INTRO_GAL_RE = re.compile(r"exame\s+consta\s+de", re.IGNORECASE)
INTRO_CAST_RE = re.compile(r"examen\s+consta\s+de", re.IGNORECASE)

# "PREGUNTA 3. TEMA. (2,5 puntos)" / "PREGUNTA 3. TEMA" / "PREGUNTA 3."
# / "PREGUNTA 3 [2 puntos (1 punto por apartado)]." (no period after the number)
PREGUNTA_RE = re.compile(r"PREGUNTA\s+(\d+)\b", re.IGNORECASE)
# Same word but with the number glyph missing in extraction (a real, seen bug in
# the source PDF, e.g. bioloxia 2020: "PREGUNTA. La BASE MOLECULAR..." where
# "PREGUNTA 2." lost its "2"). Never guess silently - the caller infers the
# number from sequence and flags the question for manual review.
# The uppercase-next-letter check must stay case-SENSITIVE even though the
# rest of the pattern is not (otherwise IGNORECASE makes [A-Z] match lowercase
# too, and this fires on ordinary text like "Cada pregunta vale 2 puntos").
PREGUNTA_NONUM_RE = re.compile(r"PREGUNTA\.?\s+(?=(?-i:[A-ZÁÉÍÓÚÑÜ]))", re.IGNORECASE)
# "3. Xeometría:" or "3. Álxebra" (colon not always present) at the start of a
# question line (Matemáticas 2020-2023). Must be short (a topic, not a sentence)
# and start with a capital letter, to avoid matching "1. Despeje X de..." bodies.
BARE_NUM_TEMA_RE = re.compile(r"(?:^|\n)[ \t]*(\d+)\.[ \t]*([A-ZÁÉÍÓÚÑÜ][^\n:]{2,59})(?::|\n)", re.MULTILINE)

# Accepts both "(2 puntos)" and "[2 puntos (1 punto por apartado)]" forms.
POINTS_PARENS_RE = re.compile(r"[(\[](\d+(?:[.,]\d+)?)\s*puntos?", re.IGNORECASE)
INTRO_POINTS_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*puntos?(?:\s*\(([^)]*apartado[^)]*)\))?", re.IGNORECASE
)
APARTADO_RE = re.compile(r"(?:^|\n)\s*(\d+\.\d+\.?|[a-hA-H]\))\s+", re.MULTILINE)

INSTRUCTION_WORDS = re.compile(
    r"^(Responda|Resolva|Desenvolva|Conteste|Responde|Resuelve|Desarrolle|Contesta)\b",
    re.IGNORECASE,
)

# Heuristic for the "duplicated character" garbling the user warned about:
# a run of 2+ identical letters standing alone as if it were one variable
# name (e.g. "AA x BB", "kk"), OUTSIDE of normal Galician/Spanish words.
DOUBLED_LETTER_RE = re.compile(r"\b([A-Za-z])\1\b")
MATH_ITALIC_RE = re.compile(r"[\U0001D400-\U0001D7FF]")

YEAR_LEY = lambda y: "LOE" if int(y) <= 2016 else ("LOMCE" if int(y) <= 2024 else "LOMLOE")


def find_castellano_start(doc):
    """First page whose text matches the Spanish ('examen consta de'), not
    Galician ('exame consta de'), intro sentence. Falls back to the second
    half of the document if not found (every sample so far: gal first, then
    an identical-length cast block)."""
    n = len(doc)
    for i in range(n):
        if INTRO_CAST_RE.search(doc[i].get_text()):
            return i
    return n // 2


def _dedup_first_per_number(pairs):
    """Some sources restate 'PREGUNTA N' a second time inside leftover
    criteria/solutions text glued to the exam (a fuentes/ splitting
    limitation, not something this script should silently hide) - keep only
    the FIRST occurrence of each question number, which is always the real
    enunciado, never the later restatement."""
    seen = set()
    out = []
    for num, block in pairs:
        if num in seen:
            continue
        seen.add(num)
        out.append((num, block))
    return out


def split_questions(text):
    """Return list of (number:int, block:str, inferred_number:bool) using
    whichever question-boundary pattern this text actually uses."""
    numbered = [(m.start(), m.end(), int(m.group(1))) for m in PREGUNTA_RE.finditer(text)]
    unnumbered = [(m.start(), m.end(), None) for m in PREGUNTA_NONUM_RE.finditer(text)
                  if not any(ns <= m.start() < ne for ns, ne, _ in numbered)]
    all_starts = sorted(numbered + unnumbered, key=lambda t: t[0])
    if all_starts:
        out = []
        last_num = 0
        for idx, (s, e, num) in enumerate(all_starts):
            end = all_starts[idx + 1][0] if idx + 1 < len(all_starts) else len(text)
            inferred = num is None
            if inferred:
                num = last_num + 1
            block = text[e:end]
            out.append((num, block, inferred))
            last_num = num
        deduped = _dedup_first_per_number([(n, b) for n, b, _ in out])
        inferred_nums = {n for n, _, inf in out if inf}
        return [(n, b, n in inferred_nums) for n, b in deduped], "PREGUNTA"

    matches = list(BARE_NUM_TEMA_RE.finditer(text))
    if matches:
        out = []
        for idx, m in enumerate(matches):
            start = m.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            num = int(m.group(1))
            block = text[start:end]
            out.append((num, block))
        deduped = _dedup_first_per_number(out)
        return [(n, b, False) for n, b in deduped], "BARE_NUM"

    return [], None


def extract_tema_and_rest(block, style):
    """Pull the topic header (if any) off the front of a question block."""
    block = block.strip()
    if style == "BARE_NUM":
        m = re.match(r"\d+\.\s*([^\n:]{3,60}):\s*(.*)", block, re.DOTALL)
        if m:
            return m.group(1).strip(), m.group(2).strip()
        return "", block

    # style == "PREGUNTA": the topic (if any) is the FIRST sentence of the
    # header line, stopping before any points-marker. Two things a naive
    # "first period" cut gets wrong, both seen in real data:
    #   - "Interacción electromagnética. Responda indicando..." (2024 Física)
    #     has a *second* sentence (an instruction) before the points marker -
    #     only the first sentence is the real tema.
    #   - "1.1. Nombre los siguientes..." (2020 Química) has NO tema at all;
    #     its sub-item numbering "1.1." must not be mistaken for one.
    first_line, _, rest = block.partition("\n")
    pts_match = POINTS_PARENS_RE.search(first_line)
    search_zone = first_line[: pts_match.start()] if pts_match else first_line
    tail_after_zone = first_line[pts_match.end():] if pts_match else ""

    header, cut_at, pos = "", None, 0
    while True:
        dot = search_zone.find(".", pos)
        if dot == -1:
            break
        piece = search_zone[:dot].strip()
        if re.fullmatch(r"\d+(\.\d+)*", piece):
            pos = dot + 1  # that period belongs to "N." / "N.N." numbering - keep looking
            continue
        if 3 <= len(piece) < 90 and re.search(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]", piece):
            header, cut_at = piece, dot
        break

    if not header or INSTRUCTION_WORDS.match(header):
        return "", block  # no real topic in the source - don't invent one

    remainder = search_zone[cut_at + 1:] + tail_after_zone + "\n" + rest
    header = header.strip(" .:")
    return header, remainder.strip()


def general_points_rule(intro_text):
    """Parse the flat per-question scoring rule stated once in the intro
    paragraph, e.g. '8 preguntas de 2 puntos' or 'puntuadas cada unha con
    2,5 puntos' or 'Cada pregunta vale 2 puntos (1 punto por apartado)'."""
    m = INTRO_POINTS_RE.search(intro_text)
    if not m:
        return None, None
    total = m.group(1).replace(",", ".")
    per_apartado_note = m.group(2)
    return total, per_apartado_note


def looks_garbled(text):
    if MATH_ITALIC_RE.search(text):
        return True
    hits = DOUBLED_LETTER_RE.findall(text)
    # A couple of stray hits are normal noise (OCR ligatures, etc.); several
    # in one question is the real signature of the bug the user described.
    return len(hits) >= 3


def yaml_escape(s):
    if s is None:
        return '""'
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def make_vault_entry(asignatura_label, year, conv, num, tema, puntuacion, apartados,
                      ley, fuente_rel, revision_manual, body):
    q_id = f"{asignatura_label}-{year}-{conv}-{num}"
    lines = ["---"]
    lines.append(f"id: {q_id}")
    lines.append(f"asignatura: {yaml_escape(asignatura_label)}")
    lines.append(f"año: {year}")
    lines.append(f"convocatoria: {conv}")
    lines.append(f"numero_pregunta: {num}")
    lines.append(f"tema: {yaml_escape(tema)}")
    lines.append(f"puntuacion: {yaml_escape(puntuacion)}")
    if apartados:
        lines.append("apartados:")
        for a in apartados:
            lines.append(f"  - {yaml_escape(a)}")
    else:
        lines.append("apartados: []")
    lines.append(f"ley_educativa: {ley}")
    lines.append(f"fuente: {yaml_escape(fuente_rel)}")
    if revision_manual:
        lines.append("revision_manual: true")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines) + "\n"


SUBJECT_LABEL_ES = {
    "matematicas_ii": "Matemáticas II",
    "bioloxia": "Biología",
    "fisica": "Física",
    "quimica": "Química",
}

report_rows = []


def process_file(subject, year, conv):
    code = SUBJECT_CODE[subject]
    path = os.path.join(FUENTES, subject, year, conv, f"{code}_{subject}_{conv}_{year}.pdf")
    if not os.path.isfile(path):
        return "no_encontrado", 0, 0

    doc = fitz.open(path)
    cast_start = find_castellano_start(doc)
    if cast_start >= len(doc):
        return "sin_castellano", 0, 0
    cast_text = "\n".join(doc[i].get_text() for i in range(cast_start, len(doc)))
    intro_text = doc[cast_start].get_text()

    questions, style = split_questions(cast_text)
    if not questions:
        return "sin_preguntas_detectadas", 0, 0

    total_rule, apartado_note = general_points_rule(intro_text)
    ley = YEAR_LEY(year)
    out_dir = os.path.join(VAULT, subject, year, conv)
    os.makedirs(out_dir, exist_ok=True)
    fuente_rel = os.path.relpath(path, ROOT).replace("\\", "/")

    written = 0
    flagged = 0
    for num, block, inferred in questions:
        tema, body = extract_tema_and_rest(block, style)
        own_points = POINTS_PARENS_RE.search(block[:120])
        if own_points:
            puntuacion = f"{own_points.group(1).replace(',', '.')} puntos"
        elif total_rule:
            puntuacion = f"{total_rule} puntos" + (f" ({apartado_note})" if apartado_note else "")
        else:
            puntuacion = ""

        apartados = []
        for am in APARTADO_RE.finditer(body):
            label = am.group(1)
            start = am.end()
            nxt = APARTADO_RE.search(body, start)
            end = nxt.start() if nxt else len(body)
            snippet = " ".join(body[start:end].split())
            if snippet:
                apartados.append(f"{label} {snippet[:200]}")

        revision_manual = looks_garbled(block)
        if inferred:
            revision_manual = True
            body = (
                f"[NOTA: el número de esta pregunta no estaba en el PDF original "
                f"(\"PREGUNTA {num}.\" apareció como \"PREGUNTA.\", sin el dígito); "
                f"se infirió por su posición en la secuencia 1-8, verificar.]\n\n" + body
            )

        entry = make_vault_entry(
            SUBJECT_LABEL_ES[subject], year, conv, num, tema, puntuacion, apartados,
            ley, fuente_rel, revision_manual, body,
        )
        out_path = os.path.join(out_dir, f"pregunta-{num}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(entry)
        written += 1
        if revision_manual:
            flagged += 1

    return "ok", written, flagged


if __name__ == "__main__":
    for subject in SUBJECT_CODE:
        for year in YEARS:
            for conv in CONVOCATORIAS:
                status, written, flagged = process_file(subject, year, conv)
                report_rows.append((subject, year, conv, status, written, flagged))
                print(f"{subject:16s} {year} {conv:15s} -> {status:26s} preguntas={written} revision_manual={flagged}")

    ok = sum(1 for r in report_rows if r[3] == "ok")
    total_q = sum(r[4] for r in report_rows)
    total_flagged = sum(r[5] for r in report_rows)
    problems = [r for r in report_rows if r[3] != "ok"]

    print(f"\nExámenes procesados con éxito: {ok} / {len(report_rows)}")
    print(f"Preguntas escritas en vault/: {total_q}")
    print(f"Preguntas marcadas revision_manual: {total_flagged}")
    print("\n=== Exámenes NO procesados ===")
    for subject, year, conv, status, _, _ in problems:
        print(f"  {subject} {year} {conv}: {status}")
