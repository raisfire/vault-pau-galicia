"""
Rehace fuentes/<asignatura>/<year 2010-2019 excepto 2015>/{ordinaria,extraordinaria}
desde cero, extrayendo de nuevo el PDF de origen dentro de los ZIP de la CIUG.

Se descubrió que el primer arreglo (fix_2010_2019.py, que solo recortaba
"CRITERIOS" al final) no bastaba: en esta época más antigua, los criterios
de corrección no siempre dicen la palabra "CRITERIOS" - a veces solo
repiten "CONVOCATORIA DE XUÑO/SETEMBRO", la MISMA etiqueta que ya llevaba
el examen real. Eso causaba contaminación cruzada real (páginas de la
convocatoria contraria coladas en el archivo), el mismo tipo de bug que en
2020-2024, solo que con "XUÑO/SETEMBRO" en vez de "ordinaria/extraordinaria".

Algoritmo: igual que fix_2020_2024.py pero:
  - las etiquetas 'ordinaria'/'extraordinaria' incluyen tanto la palabra
    ordinaria/extraordinaria como XUÑO (ordinaria) / SETEMBRO
    (extraordinaria) - son equivalentes en esta época.
  - los límites de bloque no dependen de una frase fija de introducción
    (no siempre está); cualquier página etiquetada, o con la palabra
    CRITERIOS, cuenta como límite.
  - se toma la PRIMERA aparición de cada etiqueta como el examen real; las
    reapariciones posteriores (criterios, que a menudo repiten la misma
    etiqueta de convocatoria) se descartan.

Bioloxía 2019 (escaneado) y todo 2015 (ya resuelto a mano en la tarea
anterior) se saltan explícitamente.
"""
import os
import re
import zipfile
import fitz  # pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(ROOT, "fuentes")
SCRATCH = r"C:\Users\raisa\AppData\Local\Temp\claude\C--Users-raisa-Destructor-de-PAU\f3cb49d5-73a6-4f43-89ff-6ecbabc3ef64\scratchpad"
ZIP_2001_2012 = os.path.join(SCRATCH, "2001_2012.zip")
ZIP_2013_2019 = os.path.join(SCRATCH, "2013_2019.zip")

GENERIC_CONV_RE = re.compile(r"(extra)?ordinaria", re.IGNORECASE)
XUNO_RE = re.compile(r"XU\w?O\s+\d{4}|CONVOCATORIA\s+DE\s+XU\wO\b", re.IGNORECASE)
# 2019 (ABAU) renamed the extraordinaria sitting from "setembro" to "xullo" (July).
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


SUBJECT_FILENAME_PATTERNS = {
    "matematicas_ii": (re.compile(r"matematic", re.IGNORECASE), re.compile(r"aplicad|apli", re.IGNORECASE)),
    "bioloxia": (re.compile(r"bioloxia", re.IGNORECASE), None),
    "fisica": (re.compile(r"fisica", re.IGNORECASE), None),
    "quimica": (re.compile(r"quimica", re.IGNORECASE), None),
}
SUBJECT_CODE = {"matematicas_ii": "20", "bioloxia": "21", "fisica": "23", "quimica": "24"}

YEAR_TO_ZIP = {}
for y in ["2010", "2011", "2012"]:
    YEAR_TO_ZIP[y] = (ZIP_2001_2012, "2001_2012")
for y in ["2013", "2014", "2016", "2017", "2018", "2019"]:
    YEAR_TO_ZIP[y] = (ZIP_2013_2019, "2013_2019")

SKIP = {("bioloxia", "2019")}  # scanned, left untouched per user instruction

report = []
problems = []

open_zips = {}


def get_zip(path):
    if path not in open_zips:
        open_zips[path] = zipfile.ZipFile(path)
    return open_zips[path]


for subject, (include_pat, exclude_pat) in SUBJECT_FILENAME_PATTERNS.items():
    code = SUBJECT_CODE[subject]
    for year, (zip_path, zip_prefix) in YEAR_TO_ZIP.items():
        if (subject, year) in SKIP:
            continue
        zf = get_zip(zip_path)
        prefix = f"{zip_prefix}/{year}/"
        members = [n for n in zf.namelist() if n.startswith(prefix) and n.lower().endswith(".pdf")]
        matches = [
            m for m in members
            if include_pat.search(os.path.basename(m))
            and not (exclude_pat and exclude_pat.search(os.path.basename(m)))
        ]
        if len(matches) != 1:
            continue  # 0 matches = no_encontrado (unchanged); 2+ matches = 2015-style, not touched here

        member = matches[0]
        tmp_path = os.path.join(SCRATCH, f"zsrc_{subject}_{year}.pdf")
        with zf.open(member) as f, open(tmp_path, "wb") as out:
            out.write(f.read())

        doc = fitz.open(tmp_path)
        blocks, n = find_blocks(doc)
        supers = merge_superblocks(blocks, n)

        ord_supers = [s for s in supers if s[2] == "ordinaria"]
        extra_supers = [s for s in supers if s[2] == "extraordinaria"]

        if not ord_supers and supers and supers[0][2] is None and supers[0][0] == 0:
            ord_supers = [supers[0]]

        if len(ord_supers) < 1 or len(extra_supers) < 1:
            problems.append((subject, year, f"superbloques inesperados: {supers} (fuente: {member})"))
            doc.close()
            os.remove(tmp_path)
            continue

        ord_start, ord_end, _ = ord_supers[0]
        extra_start, extra_end, _ = extra_supers[0]
        ord_block = list(range(ord_start, ord_end))
        extra_block = list(range(extra_start, extra_end))

        # In this era, unlabeled criteria-continuation pages (no CRITERIOS word, no
        # XUÑO/SETEMBRO/XULLO) can silently run to EOF and get swallowed into whichever
        # superblock precedes them if nothing later re-labels the document. A real exam
        # block here is consistently short (1-2 pages); a lopsided result is a sign that
        # happened - flag instead of guessing where to cut.
        if len(ord_block) > 0 and len(extra_block) > len(ord_block) + 1:
            problems.append((subject, year, f"extra sospechosamente largo frente a ord: ord={ord_block} extra={extra_block} (fuente: {member}); probablemente incluye criterios sin etiqueta al final, revisar a mano"))
            doc.close()
            os.remove(tmp_path)
            continue
        if len(extra_block) > 0 and len(ord_block) > len(extra_block) + 1:
            problems.append((subject, year, f"ord sospechosamente largo frente a extra: ord={ord_block} extra={extra_block} (fuente: {member}); probablemente incluye criterios sin etiqueta al final, revisar a mano"))
            doc.close()
            os.remove(tmp_path)
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
        os.remove(tmp_path)

        report.append((subject, year, len(ord_block), len(extra_block)))
        print(f"{subject:16s} {year}  ord={len(ord_block)}p [{ord_start}:{ord_end}]  extra={len(extra_block)}p [{extra_start}:{extra_end}]  superblocks={len(supers)}  ({member})")

for z in open_zips.values():
    z.close()

print("\n=== PROBLEMAS (no resueltos automáticamente) ===")
for subject, year, msg in problems:
    print(f"{subject} {year}: {msg}")

print(f"\nTotal resueltos: {len(report)}   Problemas: {len(problems)}")
