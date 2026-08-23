"""
Ajuste puntual: clasifica los 8 PDFs de 2015 que quedaron en sin_clasificar/.

Hallazgo tras inspeccionar cada PDF pagina a pagina:
  - Los 4 archivos "_xun" son 100% XUÑO (ordinaria), en gallego+castellano, sin
    criterios. Se usan tal cual como el archivo de ordinaria de 2015.
  - Los 4 archivos sin sufijo son un PDF combinado (igual que 2020-2024): traen
    paginas de examen XUÑO (ordinaria) Y paginas de examen SETEMBRO
    (extraordinaria) + criterios de cada convocatoria, todo junto. La
    extraordinaria de 2015 SOLO existe dentro de estos archivos combinados.
    Se extraen sus paginas SETEMBRO (con "forward-fill": una pagina sin
    marcador hereda el marcador de la ultima pagina marcada, porque los
    criterios continuan varias paginas sin repetir la cabecera) para producir
    el archivo de extraordinaria. La parte XUÑO de estos combinados se
    descarta por ser redundante con el archivo "_xun" (mejor version: bilingue
    y sin paginas de criterios mezcladas).
"""
import os
import re
import shutil
import fitz  # pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(ROOT, "fuentes")

GENERIC_CONV_RE = re.compile(r"(extra)?ordinaria", re.IGNORECASE)
XUNO_RE = re.compile(r"XU\w?O\s+\d{4}|CONVOCATORIA\s+DE\s+XU", re.IGNORECASE)
SETEMBRO_RE = re.compile(r"SETEMBRO\s+\d{4}|CONVOCATORIA\s+DE\s+SET", re.IGNORECASE)

SUBJECTS = {
    "matematicas_ii": "20",
    "bioloxia": "21",
    "fisica": "23",
    "quimica": "24",
}
YEAR = "2015"


def page_label(text):
    m = GENERIC_CONV_RE.search(text)
    if m:
        return "extraordinaria" if m.group(1) else "ordinaria"
    if XUNO_RE.search(text):
        return "ordinaria"
    if SETEMBRO_RE.search(text):
        return "extraordinaria"
    return None


def forward_fill_labels(doc):
    labels = []
    current = None
    for i in range(len(doc)):
        lab = page_label(doc[i].get_text())
        if lab is not None:
            current = lab
        labels.append(current)
    return labels


def extract_pages(src_doc, page_indices, out_path):
    out = fitz.open()
    for i in page_indices:
        out.insert_pdf(src_doc, from_page=i, to_page=i)
    out.save(out_path)


def is_probably_scanned(pdf_path, sample_pages=3):
    doc = fitz.open(pdf_path)
    n = min(sample_pages, len(doc))
    if n == 0:
        return "desconocido"
    total_chars = sum(len(doc[i].get_text().strip()) for i in range(n))
    return "si" if (total_chars / n) < 40 else "no"


report = []  # (subject, action, detail)

for subject, code in SUBJECTS.items():
    subj_dir = os.path.join(FUENTES, subject, YEAR)
    unclass_dir = os.path.join(subj_dir, "sin_clasificar")
    ord_dir = os.path.join(subj_dir, "ordinaria")
    extra_dir = os.path.join(subj_dir, "extraordinaria")
    os.makedirs(ord_dir, exist_ok=True)
    os.makedirs(extra_dir, exist_ok=True)

    files = os.listdir(unclass_dir)
    xun_files = [f for f in files if f.lower().endswith("_xun.pdf")]
    bundle_file = next(f for f in files if not f.lower().endswith("_xun.pdf"))
    bundle_path = os.path.join(unclass_dir, bundle_file)
    ord_out = os.path.join(ord_dir, f"{code}_{subject}_ordinaria_{YEAR}.pdf")

    # --- 1. ordinaria: move the _xun file wholesale (100% XUÑO throughout) ---
    if xun_files:
        xun_path = os.path.join(unclass_dir, xun_files[0])
        doc_xun = fitz.open(xun_path)
        labels_xun = forward_fill_labels(doc_xun)
        assert all(l == "ordinaria" for l in labels_xun), f"{xun_path} no es 100% ordinaria: {labels_xun}"
        doc_xun.close()
        shutil.copy(xun_path, ord_out)
        os.remove(xun_path)
        scan_ord = is_probably_scanned(ord_out)
        report.append((subject, "ordinaria", ord_out, scan_ord, f"movido tal cual desde {xun_files[0]} (100% XUÑO)"))
    else:
        scan_ord = is_probably_scanned(ord_out)
        report.append((subject, "ordinaria", ord_out, scan_ord, "ya movido en un intento anterior"))

    # --- 2. extraordinaria: extract SETEMBRO pages from the combined file ---
    doc_bundle = fitz.open(bundle_path)
    labels_bundle = forward_fill_labels(doc_bundle)
    extra_pages = [i for i, l in enumerate(labels_bundle) if l == "extraordinaria"]
    ord_pages_in_bundle = [i for i, l in enumerate(labels_bundle) if l == "ordinaria"]
    none_pages = [i for i, l in enumerate(labels_bundle) if l is None]

    extra_out = os.path.join(extra_dir, f"{code}_{subject}_extraordinaria_{YEAR}.pdf")
    extract_pages(doc_bundle, extra_pages, extra_out)
    scan_extra = is_probably_scanned(extra_out)
    report.append((
        subject, "extraordinaria", extra_out, scan_extra,
        f"extraído de {bundle_file} (páginas SETEMBRO: {extra_pages} de {len(doc_bundle)}; "
        f"páginas XUÑO del mismo combinado descartadas: {ord_pages_in_bundle}; "
        f"sin marcador propio, heredado por continuidad: {none_pages})"
    ))
    doc_bundle.close()

    os.remove(bundle_path)
    if not os.listdir(unclass_dir):
        os.rmdir(unclass_dir)

print("=== Resultado ===")
for subject, conv, path, scan, detail in report:
    print(f"{subject:16s} {conv:15s} escaneado={scan}  {os.path.relpath(path, ROOT)}")
    print(f"    {detail}")
