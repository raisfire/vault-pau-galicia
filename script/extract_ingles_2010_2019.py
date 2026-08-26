# -*- coding: utf-8 -*-
"""Extrae y clasifica (solo para estadisticas, no crea vault/) las
opciones de Inglés 2010-2019. Sin IA: el "tema" de Inglés es el tipo de
destreza (ver ingles_temas.py), detectable por palabras clave, igual que
en chop_ingles.py. 2015 falta en las fuentes (hueco conocido)."""
import glob
import json
import re
import sys

import fitz

sys.path.insert(0, "script")
from ingles_temas import classify_by_keywords

OPCION_RE = re.compile(r"OPCI[ÓO]N\s+([A-Za-z0-9]+)", re.IGNORECASE)


def split_options(text):
    matches = list(OPCION_RE.finditer(text))
    if not matches:
        return [("UNICA", text)]
    out = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1).upper(), text[start:end].strip()))
    return out


def process_file(path, year, conv):
    doc = fitz.open(path)
    text = "\n".join(doc[i].get_text() for i in range(len(doc)))
    text = text.replace("\xa0", " ")
    if len(text.strip()) < 100:
        return {"path": path, "year": year, "conv": conv,
                "status": "vacio_o_escaneado", "opciones": []}

    opciones = [(label, chunk) for label, chunk in split_options(text) if len(chunk) > 50]
    status = "ok" if opciones else "sin_opciones_detectadas"
    return {"path": path, "year": year, "conv": conv, "status": status, "opciones": opciones}


def main():
    results = []
    for year in [str(y) for y in range(2010, 2020)]:
        for path in sorted(glob.glob(f"fuentes/ingles/{year}/*/*.pdf")):
            conv = path.replace("\\", "/").split("/")[3]
            r = process_file(path, year, conv)
            results.append(r)

    ok = [r for r in results if r["status"] == "ok"]
    bad = [r for r in results if r["status"] != "ok"]

    print(f"Total ficheros: {len(results)}")
    print(f"OK: {len(ok)}")
    print(f"Con problemas: {len(bad)}")
    for r in bad:
        print(f"  [{r['status']}] {r['path']}")

    records = []
    sin_tema = 0
    for r in ok:
        for label, texto in r["opciones"]:
            temas = classify_by_keywords(" ".join(texto.split()))
            if not temas:
                sin_tema += 1
            records.append({"subject": "ingles", "year": r["year"], "conv": r["conv"], "temas": temas})

    print(f"\nTotal opciones: {len(records)}")
    print(f"Sin tema detectado: {sin_tema}")

    with open("script/stats_ingles_2010_2019.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
