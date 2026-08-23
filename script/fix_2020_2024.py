"""
Corrige fuentes/<asignatura>/<year 2020-2024>/{ordinaria,extraordinaria}/*.pdf

Algoritmo final (v3): cada "bloque" dentro del PDF combinado (examen
ordinaria, examen extraordinaria, modelo/simulacro, criterios...) empieza
con una página que repite la frase fija "O exame consta de 8 preguntas..."
/ "El examen consta de 8 preguntas...". Esa frase es la frontera de bloque
fiable (aparece una vez por idioma al principio de cada bloque, incluido en
los "modelos" que no son ninguna convocatoria real).

Pasos:
  1. Localizar todas las páginas "inicio de bloque" (la frase anterior).
  2. Etiquetar cada una: 'ordinaria' / 'extraordinaria' / None (sin mención
     de convocatoria -> modelo, se descarta).
  3. Fusionar inicios de bloque consecutivos con la MISMA etiqueta (el
     gallego y el castellano del mismo examen comparten etiqueta) en un
     solo superbloque, que abarca desde su primer inicio hasta el inicio
     del siguiente superbloque (de cualquier etiqueta).
  4. El superbloque etiquetado 'ordinaria' es el examen ordinaria; el
     etiquetado 'extraordinaria', el examen extraordinaria. Todo lo demás
     (modelos sin etiqueta, criterios de corrección) se descarta.
  5. Si no aparece exactamente un superbloque de cada tipo, no se adivina:
     se marca para revisión manual.
"""
import csv
import os
import re
import requests
import urllib3
import fitz  # pymupdf

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(ROOT, "fuentes")
SCRATCH = r"C:\Users\raisa\AppData\Local\Temp\claude\C--Users-raisa-Destructor-de-PAU\f3cb49d5-73a6-4f43-89ff-6ecbabc3ef64\scratchpad"

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ABAU-catalog-script/1.0)"})

GENERIC_CONV_RE = re.compile(r"(extra)?ordinaria", re.IGNORECASE)
INTRO_RE = re.compile(r"exame\s+consta\s+de|examen\s+consta\s+de", re.IGNORECASE)
CRIT_RE = re.compile(r"CRITERIOS", re.IGNORECASE)

SUBJECTS = {"matematicas_ii": "20", "bioloxia": "21", "fisica": "23", "quimica": "24"}
SUBJECT_LABELS = {"matematicas_ii": "Matemáticas II", "bioloxia": "Bioloxía", "fisica": "Física", "quimica": "Química"}
YEARS = ["2020", "2021", "2022", "2023", "2024"]


def label(text):
    # A page that mentions CRITERIOS is the start of an answer-key block, never a
    # real exam block, even if it also restates "Convocatoria ordinaria/extraordinaria".
    if CRIT_RE.search(text):
        return "criterios"
    m = GENERIC_CONV_RE.search(text)
    if m:
        return "extraordinaria" if m.group(1) else "ordinaria"
    return None


def get_bundle_url(subject_label, year):
    with open(os.path.join(ROOT, "manifest.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["asignatura"] == subject_label and row["año"] == year:
                return row["url_examen"]
    return None


def find_blocks(doc):
    """Return list of (start_page, label) for each block-boundary page, in order.
    A boundary is either the fixed intro sentence (starts every exam/modelo block,
    in both languages) or the word CRITERIOS (starts an answer-key block, which
    does NOT repeat the intro sentence) - without both, a criteria block would
    never end its preceding exam superblock and swallow it whole."""
    n = len(doc)
    texts = [doc[i].get_text() for i in range(n)]
    starts = [i for i in range(n) if INTRO_RE.search(texts[i]) or CRIT_RE.search(texts[i])]
    return [(i, label(texts[i])) for i in starts], n


def merge_superblocks(blocks, n):
    """Merge consecutive block-starts sharing the same label into superblocks
    (start, end, label). end is exclusive (next superblock's start, or n)."""
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

for subject, code in SUBJECTS.items():
    subject_label = SUBJECT_LABELS[subject]
    for year in YEARS:
        url = get_bundle_url(subject_label, year)
        bundle_path = os.path.join(SCRATCH, f"refetch_{subject}_{year}.pdf")
        r = SESSION.get(url, timeout=60)
        r.raise_for_status()
        with open(bundle_path, "wb") as f:
            f.write(r.content)

        doc = fitz.open(bundle_path)
        blocks, n = find_blocks(doc)
        supers = merge_superblocks(blocks, n)

        ord_supers = [s for s in supers if s[2] == "ordinaria"]
        extra_supers = [s for s in supers if s[2] == "extraordinaria"]

        # Some years never label the real exam pages at all (just say "2021", not
        # "Convocatoria ordinaria") - in that case the exam is implicitly the very
        # first (unlabeled) superblock, positioned right at the start of the doc.
        if not ord_supers and supers and supers[0][2] is None and supers[0][0] == 0:
            ord_supers = [supers[0]]

        # A label can legitimately reappear later (detailed worked solutions restate
        # "Convocatoria X" in their own header too) - the real exam is always the
        # FIRST occurrence, so later repeats of the same label are ignored.
        if len(ord_supers) < 1 or len(extra_supers) < 1:
            problems.append((subject, year, f"superbloques inesperados: {supers}"))
            doc.close()
            os.remove(bundle_path)
            continue

        ord_start, ord_end, _ = ord_supers[0]
        extra_start, extra_end, _ = extra_supers[0]
        ord_block = list(range(ord_start, ord_end))
        extra_block = list(range(extra_start, extra_end))

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
        os.remove(bundle_path)

        report.append((subject, year, len(ord_block), len(extra_block)))
        print(f"{subject_label:16s} {year}  ord={len(ord_block)}p [{ord_start}:{ord_end}]  extra={len(extra_block)}p [{extra_start}:{extra_end}]  (total superblocks={len(supers)})")

print("\n=== PROBLEMAS (no resueltos automáticamente) ===")
for subject, year, msg in problems:
    print(f"{subject} {year}: {msg}")

print(f"\nTotal resueltos: {len(report)} / 20   Problemas: {len(problems)}")
