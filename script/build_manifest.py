"""
Fase 1a - Descarga y cataloga los examenes de la CIUG (Matematicas II,
Bioloxia, Fisica, Quimica; 2010-2026; ordinaria + extraordinaria).

No trocea preguntas ni etiqueta temas. Solo descarga el PDF del examen,
lo organiza en fuentes/<asignatura>/<year>/<convocatoria>/ y escribe manifest.csv.

Fuentes reales usadas (leidas de las paginas indice, no adivinadas):
  - https://ciug.gal/pau/exames                 -> tabla 2020-2024 (1 PDF combinado por materia/ano)
  - https://ciug.gal/pau/exames-pau-2025        -> tabla 2025 (4 columnas: exame/criterios x ord/extra)
  - https://ciug.gal/exames-pau-2026            -> lista 2026 (idem, formato parrafo+lista)
  - https://ciug.gal/uploads/PDF/anos_anteriores/probas/2001_2012.zip  -> 2010-2012
  - https://ciug.gal/uploads/PDF/anos_anteriores/probas/2013_2019.zip -> 2013-2019
"""
import csv
import os
import re
import zipfile
import requests
import urllib3
import fitz  # pymupdf

from fetch_index import (
    SUBJECTS, BASE, SESSION,
    parse_table_2020_2024, parse_table_2025, parse_paragraph_2026,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(ROOT, "fuentes")
SCRATCH = r"C:\Users\raisa\AppData\Local\Temp\claude\C--Users-raisa-Destructor-de-PAU\f3cb49d5-73a6-4f43-89ff-6ecbabc3ef64\scratchpad"
ZIP_2001_2012 = os.path.join(SCRATCH, "2001_2012.zip")
ZIP_2013_2019 = os.path.join(SCRATCH, "2013_2019.zip")

SUBJECT_CODE_NAME = {
    "20": "Matemáticas II",
    "21": "Bioloxía",
    "23": "Física",
    "24": "Química",
}

MANIFEST_ROWS = []  # dict rows


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p


def add_row(asignatura, year, convocatoria, url_examen, ruta_local, url_criterios,
            estado, sospecha_escaneado, notas):
    MANIFEST_ROWS.append({
        "asignatura": asignatura,
        "año": year,
        "convocatoria": convocatoria,
        "url_examen": url_examen or "",
        "ruta_local": os.path.relpath(ruta_local, ROOT).replace("\\", "/") if ruta_local else "",
        "url_criterios": url_criterios or "",
        "estado": estado,
        "sospecha_escaneado": sospecha_escaneado,
        "notas": notas or "",
    })


def is_probably_scanned(pdf_path, sample_pages=3):
    """Heuristic: if extracted text per page is near-empty, the PDF is likely a scanned image."""
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return "desconocido"
    n = min(sample_pages, len(doc))
    if n == 0:
        return "desconocido"
    total_chars = sum(len(doc[i].get_text().strip()) for i in range(n))
    avg = total_chars / n
    return "si" if avg < 40 else "no"


def resolve(short_href):
    if not short_href:
        return None
    url = short_href if short_href.startswith("http") else BASE + short_href
    r = SESSION.head(url, allow_redirects=True, timeout=30)
    return r.url


def download(url, dest_path):
    r = SESSION.get(url, timeout=60, stream=True)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(1 << 16):
            f.write(chunk)
    return dest_path


# Catches "Convocatoria ordinaria", "2021 - ordinaria", "ORDINARIA", "extraordinaria", etc.
# in one shot: "extra" is an optional prefix of "ordinaria", so this never confuses the two
# (checked via the captured group, not two separate patterns).
GENERIC_CONV_RE = re.compile(r"(extra)?ordinaria", re.IGNORECASE)
# Older exams (pre-2013) label pages "XUÑO <year>" / "SETEMBRO <year>" instead of the word
# ordinaria/extraordinaria - xuño (June) = ordinaria, setembro (September) = extraordinaria.
XUNO_RE = re.compile(r"XU\w?O\s+\d{4}|CONVOCATORIA\s+DE\s+XU", re.IGNORECASE)
SETEMBRO_RE = re.compile(r"SETEMBRO\s+\d{4}|CONVOCATORIA\s+DE\s+SET", re.IGNORECASE)


def detect_page_labels(pdf_path):
    """Return {'ordinaria': [page_idx,...], 'extraordinaria':[...]} based on in-page text markers."""
    doc = fitz.open(pdf_path)
    labels = {"ordinaria": [], "extraordinaria": []}
    for i in range(len(doc)):
        t = doc[i].get_text()
        m = GENERIC_CONV_RE.search(t)
        if m:
            labels["extraordinaria" if m.group(1) else "ordinaria"].append(i)
        elif XUNO_RE.search(t):
            labels["ordinaria"].append(i)
        elif SETEMBRO_RE.search(t):
            labels["extraordinaria"].append(i)
    return labels, len(doc)


def split_pdf_by_convocatoria(src_path, out_ord_path, out_extra_path):
    """
    Detect contiguous page ranges labelled 'ordinaria' / 'extraordinaria' inside a bundled
    PDF and save each as its own file. Returns (has_ord, has_extra).
    Pages with no label (e.g. trailing 'modelo'/'criterios' sections) are dropped.
    """
    labels, n_pages = detect_page_labels(src_path)
    doc = fitz.open(src_path)

    def save_range(pages, out_path):
        if not pages:
            return False
        lo, hi = min(pages), max(pages)
        out = fitz.open()
        out.insert_pdf(doc, from_page=lo, to_page=hi)
        out.save(out_path)
        return True

    has_ord = save_range(labels["ordinaria"], out_ord_path)
    has_extra = save_range(labels["extraordinaria"], out_extra_path)
    return has_ord, has_extra


# ---------------------------------------------------------------------------
# 2020-2024 : one bundled PDF per subject/year -> split by convocatoria
# ---------------------------------------------------------------------------
def process_2020_2024():
    print("== 2020-2024 (bundled PDFs, splitting by convocatoria) ==")
    for code, year, href in parse_table_2020_2024():
        subject = SUBJECTS[code]
        subject_label = SUBJECT_CODE_NAME[code]
        ord_dir = ensure_dir(os.path.join(FUENTES, subject, year, "ordinaria"))
        extra_dir = ensure_dir(os.path.join(FUENTES, subject, year, "extraordinaria"))
        ord_path = os.path.join(ord_dir, f"{code}_{subject}_ordinaria_{year}.pdf")
        extra_path = os.path.join(extra_dir, f"{code}_{subject}_extraordinaria_{year}.pdf")

        if not href:
            add_row(subject_label, year, "ordinaria", None, None, None, "no_encontrado", "n/a",
                    "No hay enlace en la tabla /pau/exames para este año/materia.")
            add_row(subject_label, year, "extraordinaria", None, None, None, "no_encontrado", "n/a",
                    "No hay enlace en la tabla /pau/exames para este año/materia.")
            continue

        try:
            final_url = resolve(href)
            tmp_path = os.path.join(SCRATCH, f"bundle_{subject}_{year}.pdf")
            download(final_url, tmp_path)
            has_ord, has_extra = split_pdf_by_convocatoria(tmp_path, ord_path, extra_path)
            note = ("PDF original combinaba ordinaria+extraordinaria+modelo+criterios; "
                    "se separó por convocatoria detectando el texto 'Convocatoria ordinaria/extraordinaria' "
                    "en cada página. Páginas de modelo/criterios (sin ese marcador) se descartaron de "
                    "estos archivos de examen.")
            if has_ord:
                scan = is_probably_scanned(ord_path)
                add_row(subject_label, year, "ordinaria", final_url, ord_path, None,
                        "descargado", scan, note)
            else:
                add_row(subject_label, year, "ordinaria", final_url, None, None,
                        "revisar_manual", "n/a",
                        "No se detectó el marcador 'Convocatoria ordinaria' dentro del PDF; revisar a mano.")
            if has_extra:
                scan = is_probably_scanned(extra_path)
                add_row(subject_label, year, "extraordinaria", final_url, extra_path, None,
                        "descargado", scan, note)
            else:
                add_row(subject_label, year, "extraordinaria", final_url, None, None,
                        "revisar_manual", "n/a",
                        "No se detectó el marcador 'Convocatoria extraordinaria' dentro del PDF; "
                        "es posible que solo se conserve la convocatoria ordinaria para este año.")
            os.remove(tmp_path)
        except Exception as e:
            add_row(subject_label, year, "ordinaria", href, None, None, "error", "n/a", str(e))
            add_row(subject_label, year, "extraordinaria", href, None, None, "error", "n/a", str(e))
        print(f"  {subject_label} {year}: ord={os.path.exists(ord_path)} extra={os.path.exists(extra_path)}")


# ---------------------------------------------------------------------------
# 2025 / 2026 : clean per-convocatoria links
# ---------------------------------------------------------------------------
def process_clean_year(year, rows):
    print(f"== {year} (enlaces separados por convocatoria) ==")
    for code, exame_ord, crit_ord, exame_extra, crit_extra in rows:
        subject = SUBJECTS[code]
        subject_label = SUBJECT_CODE_NAME[code]
        for conv, exame_href, crit_href in (
            ("ordinaria", exame_ord, crit_ord),
            ("extraordinaria", exame_extra, crit_extra),
        ):
            out_dir = ensure_dir(os.path.join(FUENTES, subject, year, conv))
            if not exame_href:
                add_row(subject_label, year, conv, None, None, None, "no_encontrado", "n/a",
                        f"No hay enlace de examen {conv} publicado todavía para {year}.")
                continue
            try:
                final_exam_url = resolve(exame_href)
                final_crit_url = resolve(crit_href) if crit_href else None
                ext = ".pdf"
                fname = f"{code}_{subject}_{conv}_{year}{ext}"
                out_path = os.path.join(out_dir, fname)
                download(final_exam_url, out_path)
                scan = is_probably_scanned(out_path)
                add_row(subject_label, year, conv, final_exam_url, out_path, final_crit_url,
                        "descargado", scan, "")
            except Exception as e:
                add_row(subject_label, year, conv, exame_href, None, None, "error", "n/a", str(e))
        print(f"  {subject_label} {year}: ok")


# ---------------------------------------------------------------------------
# 2010-2019 : zip archives, inconsistent per-year naming
# ---------------------------------------------------------------------------
# (include_pattern, exclude_pattern) - matematicas_ii is called just "Matematicas" in
# pre-2013 filenames (no "II" suffix), so we match on the stem and explicitly exclude
# "Matematicas aplicadas" / "Mat_Apli" (a different subject, not in our scope).
SUBJECT_FILENAME_PATTERNS = {
    "matematicas_ii": (re.compile(r"matematic", re.IGNORECASE), re.compile(r"aplicad|apli", re.IGNORECASE)),
    "bioloxia": (re.compile(r"bioloxia", re.IGNORECASE), None),
    "fisica": (re.compile(r"fisica", re.IGNORECASE), None),
    "quimica": (re.compile(r"quimica", re.IGNORECASE), None),
}


def zip_members_for_year(zf, year, zip_root_prefix):
    prefix = f"{zip_root_prefix}/{year}/"
    return [n for n in zf.namelist() if n.startswith(prefix) and n.lower().endswith(".pdf")]


def process_zip_years(zip_path, zip_root_prefix, years):
    print(f"== {years[0]}-{years[-1]} (zip: {os.path.basename(zip_path)}) ==")
    with zipfile.ZipFile(zip_path) as zf:
        for year in years:
            members = zip_members_for_year(zf, year, zip_root_prefix)
            for subject, (include_pat, exclude_pat) in SUBJECT_FILENAME_PATTERNS.items():
                code = [c for c, s in SUBJECTS.items() if s == subject][0]
                subject_label = SUBJECT_CODE_NAME[code]
                matches = [
                    m for m in members
                    if include_pat.search(os.path.basename(m))
                    and not (exclude_pat and exclude_pat.search(os.path.basename(m)))
                ]

                if not matches:
                    add_row(subject_label, year, "ordinaria", None, None, None, "no_encontrado", "n/a",
                            f"No se encontró PDF de {subject} para {year} dentro de {os.path.basename(zip_path)}.")
                    add_row(subject_label, year, "extraordinaria", None, None, None, "no_encontrado", "n/a",
                            f"No se encontró PDF de {subject} para {year} dentro de {os.path.basename(zip_path)}.")
                    continue

                if len(matches) == 1:
                    # Single bundled file: try to split by convocatoria marker like 2020-2024.
                    member = matches[0]
                    tmp_path = os.path.join(SCRATCH, f"zipmember_{subject}_{year}.pdf")
                    with zf.open(member) as f, open(tmp_path, "wb") as out:
                        out.write(f.read())
                    ord_dir = ensure_dir(os.path.join(FUENTES, subject, year, "ordinaria"))
                    extra_dir = ensure_dir(os.path.join(FUENTES, subject, year, "extraordinaria"))
                    ord_path = os.path.join(ord_dir, f"{code}_{subject}_ordinaria_{year}.pdf")
                    extra_path = os.path.join(extra_dir, f"{code}_{subject}_extraordinaria_{year}.pdf")
                    has_ord, has_extra = split_pdf_by_convocatoria(tmp_path, ord_path, extra_path)
                    src_url = f"{BASE}/uploads/PDF/anos_anteriores/probas/{os.path.basename(zip_path)}#{member}"

                    if not has_ord and not has_extra:
                        # No convocatoria marker found at all - check if it's because the PDF
                        # is a scanned image (no selectable text), which is expected to get more
                        # common in older years. Don't discard the file: keep it whole for later OCR.
                        scan = is_probably_scanned(tmp_path)
                        if scan == "si":
                            import shutil
                            shutil.copy(tmp_path, ord_path)
                            add_row(subject_label, year, "ordinaria", src_url, ord_path, None,
                                    "revisar_manual", "si",
                                    f"Único PDF disponible ({member}) parece escaneado (sin texto seleccionable); "
                                    f"no se pudo separar por convocatoria automáticamente. Se guardó completo sin "
                                    f"recortar, pendiente de OCR.")
                            add_row(subject_label, year, "extraordinaria", src_url, None, None,
                                    "revisar_manual", "si",
                                    f"Mismo PDF escaneado que la fila ordinaria; no se puede saber si incluye "
                                    f"la extraordinaria sin OCR.")
                            os.remove(tmp_path)
                            continue

                    if has_ord:
                        scan = is_probably_scanned(ord_path)
                        add_row(subject_label, year, "ordinaria", src_url, ord_path, None, "descargado", scan,
                                f"Único PDF disponible para {year} en el zip ({member}); se separó la parte "
                                f"'ordinaria' detectando el marcador de convocatoria dentro del texto.")
                    else:
                        add_row(subject_label, year, "ordinaria", src_url, None, None, "revisar_manual", "n/a",
                                f"Único PDF disponible ({member}) pero no se detectó marcador de convocatoria; revisar a mano.")
                    if has_extra:
                        scan = is_probably_scanned(extra_path)
                        add_row(subject_label, year, "extraordinaria", src_url, extra_path, None, "descargado", scan,
                                f"Único PDF disponible para {year} en el zip ({member}); se separó la parte "
                                f"'extraordinaria' detectando el marcador de convocatoria dentro del texto.")
                    else:
                        add_row(subject_label, year, "extraordinaria", src_url, None, None, "no_encontrado", "n/a",
                                f"Único PDF disponible ({member}) no contiene convocatoria extraordinaria "
                                f"identificable; probablemente solo se conserva la ordinaria para este año.")
                    os.remove(tmp_path)

                else:
                    # Two (or more) files with ambiguous naming: do NOT guess. Dump as-is for manual review.
                    unclassified_dir = ensure_dir(os.path.join(FUENTES, subject, year, "sin_clasificar"))
                    saved_names = []
                    for member in matches:
                        base = os.path.basename(member)
                        out_path = os.path.join(unclassified_dir, base)
                        with zf.open(member) as f, open(out_path, "wb") as out:
                            out.write(f.read())
                        saved_names.append(base)
                    src_url = f"{BASE}/uploads/PDF/anos_anteriores/probas/{os.path.basename(zip_path)}"
                    note = (f"Se encontraron {len(matches)} PDFs para {subject}/{year} con nombres que no "
                            f"distinguen ordinaria/extraordinaria de forma fiable ({', '.join(saved_names)}). "
                            f"Guardados sin clasificar en fuentes/{subject}/{year}/sin_clasificar/ para revisión manual.")
                    for conv in ("ordinaria", "extraordinaria"):
                        add_row(subject_label, year, conv, src_url, unclassified_dir, None,
                                "revisar_manual", "desconocido", note)
            print(f"  {year}: procesado")


def write_manifest():
    path = os.path.join(ROOT, "manifest.csv")
    fieldnames = ["asignatura", "año", "convocatoria", "url_examen", "ruta_local",
                  "url_criterios", "estado", "sospecha_escaneado", "notas"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in MANIFEST_ROWS:
            w.writerow(row)
    print(f"\nmanifest.csv escrito con {len(MANIFEST_ROWS)} filas -> {path}")


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("all", "recent"):
        process_2020_2024()
        process_clean_year("2025", parse_table_2025())
        process_clean_year("2026", parse_paragraph_2026())

    if mode in ("all", "old"):
        process_zip_years(ZIP_2001_2012, "2001_2012", ["2010", "2011", "2012"])
        process_zip_years(ZIP_2013_2019, "2013_2019", ["2013", "2014", "2015", "2016", "2017", "2018", "2019"])

    write_manifest()
