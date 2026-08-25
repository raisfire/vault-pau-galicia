# -*- coding: utf-8 -*-
"""Extrae los enunciados de Historia de España 2010-2018 SOLO para
estadisticas (no crea archivos vault/). 2015 y 2019 faltan en las
fuentes (huecos conocidos).

Formato: por convocatoria, un unico PDF con paginas para "OPCIÓN A" y
"OPCIÓN B" (a veces solo una de las dos esta presente en la fuente).
2010-2017: composicion/ensayo unico por opcion (bloque ORIENTACIÓNS +
documentos). 2018 en adelante: subpreguntas numeradas (1. define
terminos, 2. explica cuestion...). En ambos casos tratamos cada OPCIÓN
completa como una unidad a clasificar (puede tocar varios temas)."""
import glob
import json
import re

import fitz

OPCION_RE = re.compile(r"OPCI[ÓO]N\s+([A-Za-z0-9]+)", re.IGNORECASE)


def split_options(text):
    matches = list(OPCION_RE.finditer(text))
    if not matches:
        return [("UNICA", text)]
    out = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        chunk = re.sub(r"\s+", " ", chunk)
        out.append((m.group(1), chunk))
    return out


def process_file(path, year, conv):
    doc = fitz.open(path)
    text = "\n".join(doc[i].get_text() for i in range(len(doc)))
    if len(text.strip()) < 100:
        return {"path": path, "year": year, "conv": conv,
                "status": "vacio_o_escaneado", "opciones": []}

    opciones = [(label, chunk) for label, chunk in split_options(text) if len(chunk) > 50]
    status = "ok" if opciones else "sin_opciones_detectadas"
    return {"path": path, "year": year, "conv": conv,
            "status": status, "opciones": opciones}


def main():
    results = []
    for year in [str(y) for y in range(2010, 2019)]:
        for path in sorted(glob.glob(f"fuentes/historiaespana/{year}/*/*.pdf")):
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

    total_op = sum(len(r["opciones"]) for r in ok)
    print(f"\nTotal opciones extraidas: {total_op}")
    for r in ok:
        if len(r["opciones"]) != 2:
            print(f"  aviso: {r['path']} tiene {len(r['opciones'])} opciones (esperado 2)")

    with open("script/extracted_historiaespana_2010_2019.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
