# -*- coding: utf-8 -*-
"""Debuxo Técnico II es un examen casi 100% gráfico (cada pregunta pide
dibujar una pieza/perspectiva/intersección a partir de figuras): no tiene
sentido trocearlo en preguntas de texto ni clasificarlo por tema. En vez
de eso, este script compila un catálogo simple de los PDF completos por
año/convocatoria para mostrarlos como lista de enlaces en el visor.

2020-2022 no se pudieron dividir de forma fiable por convocatoria (el
texto extraído del PDF sale desordenado por el layout de diagramas), así
que esos años se listan como un único PDF combinado."""
import glob
import json
import re


def main():
    entries = []
    for path in sorted(glob.glob("fuentes/debuxotecnico/*/sin_dividir_*.pdf")):
        year = int(re.search(r"sin_dividir_(\d{4})\.pdf", path).group(1))
        entries.append({"año": year, "convocatoria": "combinada", "fuente": path.replace("\\", "/")})

    for path in sorted(glob.glob("fuentes/debuxotecnico/*/*/*.pdf")):
        parts = path.replace("\\", "/").split("/")
        year, conv = int(parts[2]), parts[3]
        entries.append({"año": year, "convocatoria": conv, "fuente": path.replace("\\", "/")})

    entries.sort(key=lambda e: (e["año"], e["convocatoria"]))

    data = {
        "asignatura": "Debuxo Técnico",
        "nota": "Examen mayoritariamente gráfico: se muestra como catálogo de PDF completos, sin trocear en preguntas ni clasificar por tema.",
        "examenes": entries,
    }

    with open("web/data/debuxotecnico.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"Catálogo: {len(entries)} exámenes")
    for e in entries:
        print(f"  {e['año']} {e['convocatoria']}: {e['fuente']}")


if __name__ == "__main__":
    main()
