# -*- coding: utf-8 -*-
"""Debuxo Técnico es un examen ~100% gráfico (ver build_debuxotecnico_catalog.py),
así que no se trocea en preguntas navegables. Pero el ENUNCIADO de cada
PREGUNTA sí es texto limpio (aunque la figura que acompaña no se pueda
representar), así que se puede extraer para construir una estadística de
frecuencia por bloque, sin necesidad de leer ni representar los propios
dibujos.

v2: corrige un bug de la v1 (ventana fija de 120 caracteres que a veces
se solapaba con el enunciado de la SIGUIENTE pregunta y clasificaba mal)
acotando cada pregunta hasta la siguiente "PREGUNTA N" real. Además,
muchas preguntas no nombran el bloque explícitamente ("Resolva este
exercicio de X") sino que van directas al enunciado del dibujo - para
esas, la clasificación por palabra clave no basta y se delega en IA
(ver classify_debuxotecnico_ai.py), igual que el resto de asignaturas.

Cubre 2010-2026 usando lo ya descargado en fuentes/debuxotecnico/."""
import glob
import json
import re

import fitz

PREGUNTA_RE = re.compile(r"PREGUNTA\s+(\d)\b", re.IGNORECASE)

TEMAS_DEBUXOTECNICO = [
    "FUNDAMENTOS GEOMÉTRICOS",
    "SISTEMA DIÉDRICO",
    "SISTEMA DIÉDRICO / SISTEMA AXONOMÉTRICO",
    "NORMALIZACIÓN Y DOCUMENTACIÓN GRÁFICA DE PROYECTOS",
]

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
    """Fast path determinista: solo cuando el enunciado nombra el bloque
    explícitamente. Busca solo en los primeros ~150 caracteres para no
    engancharse con el nombre de bloque de la SIGUIENTE pregunta."""
    head = snippet[:150]
    for tema, pattern in _RULES:
        if pattern.search(head):
            return tema
    return None


def extract_preguntas(text):
    """Devuelve {numero_pregunta: texto} acotando cada pregunta hasta la
    siguiente aparición de "PREGUNTA N" con un número DISTINTO (o fin de
    documento) - evita el solape con la pregunta siguiente. Un mismo número
    puede repetirse pegado dentro del propio bloque (p. ej. el título
    bilingüe galego/castellano vuelve a decir "PREGUNTA 1."), así que no
    basta con mirar el siguiente match cualquiera: hay que saltar los que
    tengan el mismo número que el actual. Toma solo la PRIMERA aparición de
    cada número como punto de partida."""
    matches = list(PREGUNTA_RE.finditer(text))
    out = {}
    for i, m in enumerate(matches):
        num = m.group(1)
        if num in out:
            continue
        end = len(text)
        for m2 in matches[i + 1:]:
            if m2.group(1) != num:
                end = m2.start()
                break
        out[num] = text[m.start():end].replace("\n", " ").strip()
    return out


def process_file(path, year, conv):
    """Devuelve una lista con un registro por cada PREGUNTA detectada (no
    uno por examen), para que build_stats.py cuente bien el total de
    preguntas y los porcentajes por tema. "tema" queda None cuando hace
    falta IA (classify_debuxotecnico_ai.py lo resuelve después)."""
    doc = fitz.open(path)
    text = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    preguntas = extract_preguntas(text)
    out = []
    for num, texto in preguntas.items():
        tema = classify_header(texto)
        out.append({
            "subject": "debuxotecnico", "year": year, "conv": conv,
            "numero": num, "texto": texto[:600],
            "temas": [tema] if tema else [],
        })
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
    print(f"Total preguntas detectadas: {len(records)}")
    print(f"Clasificadas por palabra clave: {len(records) - total_sin}")
    print(f"Pendientes de IA (sin frase de bloque explícita): {total_sin}")

    with open("script/stats_debuxotecnico_raw.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
