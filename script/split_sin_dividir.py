# -*- coding: utf-8 -*-
"""Divide fuentes/<asignatura>/<year>/sin_dividir_<year>.pdf (2020-2024,
Oleada 2) en ordinaria/extraordinaria, reutilizando el mismo detector
generico ya probado en fetch_oleada2_2010_2019.py: paginas etiquetadas
por la palabra CRITERIOS o por "ordinaria"/"extraordinaria"/XUÑO/SETEMBRO
literal en el propio texto."""
import glob
import os
import re

import fitz

FUENTES = "fuentes"
SUBJECTS = ["castelan", "galego", "historiaespana", "historiafilosofia", "ingles",
            "debuxotecnico", "tecnoloxia"]
SUBJECT_CODE = {"castelan": "01", "galego": "02", "historiaespana": "03",
                "historiafilosofia": "08", "ingles": "11",
                "debuxotecnico": "22", "tecnoloxia": "26"}


# Requiere la palabra "Convocatoria" pegada a "(extra)ordinaria": en
# asignaturas de ensayo (Historia...) "extraordinaria/ordinaria" también
# aparece como palabra normal dentro del propio texto del examen (p.ej.
# "intervencións extraordinarias do Rei"), así que un match suelto sin el
# prefijo da falsos positivos que no pasan en las asignaturas de ciencias.
GENERIC_CONV_RE = re.compile(r"CONVOCATORIA\s+(EXTRA)?ORDINARIA", re.IGNORECASE)
XUNO_RE = re.compile(r"XU\w?O\s+\d{4}|CONVOCATORIA\s+DE\s+XU\wO\b", re.IGNORECASE)
SETEMBRO_RE = re.compile(r"SETEMBRO\s+\d{4}|XULLO\s+\d{4}|CONVOCATORIA\s+DE\s+SET|CONVOCATORIA\s+DE\s+XULLO", re.IGNORECASE)
CRIT_RE = re.compile(r"CRITERIOS", re.IGNORECASE)


def label(text):
    if CRIT_RE.search(text):
        return "criterios"
    m = GENERIC_CONV_RE.search(text)
    if m:
        return "extraordinaria" if m.group(1) else "ordinaria"
    if XUNO_RE.search(text):
        return "ordinaria"
    if SETEMBRO_RE.search(text):
        return "extraordinaria"
    return None


def find_blocks(doc):
    n = len(doc)
    texts = [doc[i].get_text() for i in range(n)]
    labels = [label(t) for t in texts]
    starts = [i for i in range(n) if labels[i] is not None]
    return [(i, labels[i]) for i in starts], n


def merge_superblocks(blocks, n):
    if not blocks:
        return []
    super_blocks = []
    cur_label = blocks[0][1]
    cur_start = blocks[0][0]
    for (idx, lab) in blocks[1:]:
        if lab != cur_label:
            super_blocks.append((cur_start, idx, cur_label))
            cur_label = lab
            cur_start = idx
    super_blocks.append((cur_start, n, cur_label))
    return super_blocks


report = []
problems = []

for subject in SUBJECTS:
    code = SUBJECT_CODE[subject]
    for path in sorted(glob.glob(f"{FUENTES}/{subject}/*/sin_dividir_*.pdf")):
        year = path.replace("\\", "/").split("/")[-2]
        doc = fitz.open(path)
        blocks, n = find_blocks(doc)
        supers = merge_superblocks(blocks, n)

        ord_supers = [s for s in supers if s[2] == "ordinaria"]
        extra_supers = [s for s in supers if s[2] == "extraordinaria"]

        # La portada ordinaria a veces no repite la palabra "ordinaria"
        # (solo dice el año), así que nunca se etiqueta. Si no hay ningún
        # superbloque "ordinaria", todo lo anterior al primer superbloque
        # de CUALQUIER tipo (ordinaria/extraordinaria/criterios) es el
        # examen ordinaria real - no asumir que el primer superbloque
        # etiquetado es "extraordinaria", podría ser "criterios".
        if not ord_supers and supers and supers[0][0] > 0:
            ord_supers = [(0, supers[0][0], "ordinaria")]

        if len(ord_supers) != 1 or len(extra_supers) != 1:
            problems.append((subject, year, f"superbloques: {supers}"))
            doc.close()
            continue

        ord_start, ord_end, _ = ord_supers[0]
        extra_start, extra_end, _ = extra_supers[0]
        ord_block = list(range(ord_start, ord_end))
        extra_block = list(range(extra_start, extra_end))

        if abs(len(ord_block) - len(extra_block)) > 2:
            problems.append((subject, year, f"tamanos dispares: ord={ord_block} extra={extra_block}"))
            doc.close()
            continue

        ord_dir = os.path.join(FUENTES, subject, year, "ordinaria")
        extra_dir = os.path.join(FUENTES, subject, year, "extraordinaria")
        os.makedirs(ord_dir, exist_ok=True)
        os.makedirs(extra_dir, exist_ok=True)
        ord_out = os.path.join(ord_dir, f"{code}_{subject}_ordinaria_{year}.pdf")
        extra_out = os.path.join(extra_dir, f"{code}_{subject}_extraordinaria_{year}.pdf")

        out1 = fitz.open()
        for i in ord_block:
            out1.insert_pdf(doc, from_page=i, to_page=i)
        out1.save(ord_out)
        out1.close()

        out2 = fitz.open()
        for i in extra_block:
            out2.insert_pdf(doc, from_page=i, to_page=i)
        out2.save(extra_out)
        out2.close()
        doc.close()

        os.remove(path)  # ya no hace falta el combinado
        report.append((subject, year, len(ord_block), len(extra_block)))
        print(f"{subject:18s} {year}  ord={len(ord_block)}p  extra={len(extra_block)}p  superblocks={len(supers)}")

print(f"\nTotal resueltos: {len(report)}")
print(f"\n=== PROBLEMAS ===")
for subject, year, msg in problems:
    print(f"  {subject} {year}: {msg}")
