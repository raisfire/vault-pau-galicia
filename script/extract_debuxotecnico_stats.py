# -*- coding: utf-8 -*-
"""Debuxo Técnico es un examen ~100% gráfico (ver build_debuxotecnico_catalog.py),
así que no se trocea en preguntas navegables. Pero el ENCABEZADO de cada
PREGUNTA sí es texto limpio y nombra el bloque de contido ("PREGUNTA 3.
XEOMETRÍA PROXECTIVA: SISTEMA DIÉDRICO (2,25 puntos)"), así que se puede
extraer solo eso para construir una estadística de frecuencia por bloque,
sin necesidad de leer ni representar los propios dibujos.

Cubre 2010-2026 usando lo ya descargado en fuentes/debuxotecnico/ (2020-2026)
más los ZIPs históricos si están disponibles. Clasificación 100%
determinista por palabras clave (sin IA, sin coste) - los bloques son
pocos y muy estables en su redacción."""
import glob
import json
import re

import fitz

PREGUNTA_RE = re.compile(r"PREGUNTA\s+(\d)", re.IGNORECASE)

_RULES = [
    ("SISTEMA DIÉDRICO / SISTEMA AXONOMÉTRICO", re.compile(
        r"S\.?\s*DI[ÉE]DRICO\s*/\s*S\.?\s*AXONOM[ÉE]TRICO|"
        r"S\.?\s*AXONOM[ÉE]TRICO\s*/\s*S\.?\s*DI[ÉE]DRICO|"
        r"SISTEMA\s+DI[ÉE]DRICO\s*/\s*SISTEMA\s+AXONOM[ÉE]TRICO|"
        r"SISTEMA\s+AXONOM[ÉE]TRICO\s*/\s*SISTEMA\s*\.?\s*DI[ÉE]DRICO",
        re.IGNORECASE)),
    ("NORMALIZACIÓN Y DOCUMENTACIÓN GRÁFICA DE PROYECTOS", re.compile(
        r"NORMALIZACI[ÓO]N", re.IGNORECASE)),
    ("SISTEMA DIÉDRICO", re.compile(r"SISTEMA\s+DI[ÉE]DRICO", re.IGNORECASE)),
    ("FUNDAMENTOS GEOMÉTRICOS", re.compile(
        r"FUNDAMENTOS\s+[XG]EOM[ÉE]TRICOS|[XG]EOMETR[ÍI]A\s+PLANA",
        re.IGNORECASE)),
]


def classify_header(snippet):
    for tema, pattern in _RULES:
        if pattern.search(snippet):
            return tema
    return None


def extract_headers(text):
    """Devuelve {numero_pregunta: snippet} tomando solo la PRIMERA
    aparición de cada numero (evita contar dos veces el bloque bilingüe)."""
    out = {}
    for m in PREGUNTA_RE.finditer(text):
        num = m.group(1)
        if num in out:
            continue
        snippet = text[m.start():m.start() + 120].replace("\n", " ")
        out[num] = snippet
    return out


def process_file(path, year, conv):
    """Devuelve una lista con un registro por cada PREGUNTA detectada (no
    uno por examen), para que build_stats.py cuente bien el total de
    preguntas y los porcentajes por tema."""
    doc = fitz.open(path)
    text = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    headers = extract_headers(text)
    out = []
    for num, snippet in headers.items():
        tema = classify_header(snippet)
        out.append({"subject": "debuxotecnico", "year": year, "conv": conv,
                     "temas": [tema] if tema else []})
    return out


def main():
    records = []
    n_examenes = 0

    for path in sorted(glob.glob("fuentes/debuxotecnico/*/sin_dividir_*.pdf")):
        year = re.search(r"sin_dividir_(\d{4})\.pdf", path).group(1)
        records.extend(process_file(path, year, "combinada"))
        n_examenes += 1

    for path in sorted(glob.glob("fuentes/debuxotecnico/*/*/*.pdf")):
        parts = path.replace("\\", "/").split("/")
        year, conv = parts[2], parts[3]
        records.extend(process_file(path, year, conv))
        n_examenes += 1

    total_sin = sum(1 for r in records if not r["temas"])
    print(f"Total exámenes: {n_examenes}")
    print(f"Total preguntas (encabezados) detectadas: {len(records)}")
    print(f"Clasificadas: {len(records) - total_sin}")
    print(f"Sin clasificar (encabezado sin tema legible): {total_sin}")

    with open("script/stats_debuxotecnico.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
