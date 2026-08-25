# -*- coding: utf-8 -*-
"""Extrae preguntas de los examenes 2010-2019 SOLO para estadisticas
(no crea archivos vault/). Maneja 3 formatos:
- 2010-2018: una sola pagina, un solo idioma (galego), "OPCION A/B" o
  "OPCION 1/2", preguntas numeradas "1." "2." etc.
- 2019: bilingue (castellano + galego duplicado), a veces con paginas
  adicionales de modelo; usamos solo el primer bloque de idioma. Usa
  numeracion "C.1" "C.2" (cuestions) y "P.1" "P.2" (problemas) ademas
  de la simple "1." "2.".
"""
import glob
import json
import re

import fitz

OPCION_RE = re.compile(r"OPCI[ÓO]N\s+([A-Za-z0-9]+)", re.IGNORECASE)

# cada asignatura tiene su propia convencion de numeracion estable
# 2010-2018 (fisica usa "C./P." en todos los anios, no solo 2019).
Q_START_PATTERNS = {
    "matematicas_ii": r"(?:^|\n)\s*(?P<plain>\d{1,2})\.[\-\s]",
    "quimica": r"(?:^|\n)\s*(?P<plain>\d{1,2})\.[\-\s]",
    "fisica": r"(?:^|\n)\s*(?P<cp>[CP])\.?\s*(?P<cpnum>\d{1,2})[\.\-]*\s",
    "bioloxia": r"(?:^|\n)\s*(?P<plain>\d{1,2})\s(?=[A-ZÁÉÍÓÚÑ])",
}


def get_first_language_block(doc):
    """Concatena paginas; si detecta contenido bilingue duplicado
    (mismo encabezado de asignatura repetido), se queda solo con el
    primer bloque."""
    pages = [doc[i].get_text() for i in range(len(doc))]
    full = "\n".join(pages)

    # heuristica: si la pagina 1 repite casi el mismo arranque que la
    # pagina 0 (mismo "Código: NN" y misma materia en mayusculas), es
    # contenido duplicado en otro idioma -> quedarse solo con pagina 0.
    if len(pages) >= 2:
        head0 = pages[0][:120]
        head1 = pages[1][:120]
        codigo0 = re.search(r"C[oó]digo:\s*(\d+)", head0)
        codigo1 = re.search(r"C[oó]digo:\s*(\d+)", head1)
        if codigo0 and codigo1 and codigo0.group(1) == codigo1.group(1):
            return pages[0]

    return full


def split_options(text):
    """Devuelve lista de (etiqueta_opcion, texto_opcion)."""
    matches = list(OPCION_RE.finditer(text))
    if not matches:
        return [("UNICA", text)]
    out = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1), text[start:end]))
    return out


def split_questions(opcion_text, subject):
    q_re = re.compile(Q_START_PATTERNS[subject])
    matches = list(q_re.finditer(opcion_text))
    out = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(opcion_text)
        gd = m.groupdict()
        label = gd.get("plain") or f"{gd.get('cp')}{gd.get('cpnum')}"
        chunk = opcion_text[start:end].strip()
        chunk = re.sub(r"\s+", " ", chunk)
        if len(chunk) > 20:  # descarta ruido/matches vacios
            out.append((label, chunk))
    return out


def process_file(path, subject, year, conv):
    doc = fitz.open(path)
    text = get_first_language_block(doc)
    if len(text.strip()) < 100:
        return {"path": path, "subject": subject, "year": year, "conv": conv,
                "status": "vacio_o_escaneado", "questions": []}

    options = split_options(text)
    questions = []
    for opt_label, opt_text in options:
        qs = split_questions(opt_text, subject)
        for q_label, q_text in qs:
            questions.append({"opcion": opt_label, "num": q_label, "texto": q_text})

    status = "ok" if questions else "sin_preguntas_detectadas"
    return {"path": path, "subject": subject, "year": year, "conv": conv,
            "status": status, "questions": questions}


def main():
    results = []
    for subject in ["matematicas_ii", "bioloxia", "fisica", "quimica"]:
        for year in [str(y) for y in range(2010, 2020)]:
            for path in sorted(glob.glob(f"fuentes/{subject}/{year}/*/*.pdf")):
                conv = path.replace("\\", "/").split("/")[3]
                r = process_file(path, subject, year, conv)
                results.append(r)

    ok = [r for r in results if r["status"] == "ok"]
    bad = [r for r in results if r["status"] != "ok"]

    print(f"Total ficheros: {len(results)}")
    print(f"OK: {len(ok)}")
    print(f"Con problemas: {len(bad)}")
    for r in bad:
        print(f"  [{r['status']}] {r['path']}")

    total_q = sum(len(r["questions"]) for r in ok)
    print(f"\nTotal preguntas/cuestions extraidas: {total_q}")

    # resumen por asignatura
    from collections import Counter
    per_subject = Counter()
    for r in ok:
        per_subject[r["subject"]] += len(r["questions"])
    for s, n in per_subject.items():
        print(f"  {s}: {n}")

    with open("script/extracted_2010_2019.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
