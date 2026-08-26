# -*- coding: utf-8 -*-
"""Trocea vault/ingles/ para 2020-2026 (3 formatos de examen).

Inglés es un examen de idioma (no de contenidos), así que "tema" aquí es
el tipo de destreza practicada (comprensión lectora, gramática,
pronunciación, vocabulario, writing) - se detecta por palabras clave del
propio enunciado (ver ingles_temas.py), sin IA y sin coste.

- 2020-2022: 6 QUESTION numeradas, responde 4 de 6. Cada QUESTION es una
  sola destreza (1-2: reading; 3-4: grammar+pronunciation; 5-6: writing).
- 2023-2024: 3 QUESTION numeradas, responde 2 de 3. Cada QUESTION mezcla
  varias destrezas (reading+grammar+pronunciation, o +writing).
- 2025-2026: 4 QUESTION obligatorias (1-2 con elección de apartado interna
  vía subapartados, 3 sin apartados, 4 con elección de 1 de 2).

2010-2019 NO se trocea aquí (formato "OPCIÓN A/B" de un solo texto largo,
grano distinto) - pase de solo estadísticas aparte, ver
extract_ingles_2010_2019.py."""
import glob
import os
import re
import sys

import fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ingles_temas import classify_by_keywords

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]

QUESTION_RE = re.compile(r"(?:^|\n)\s*(?:\d+\.\s*)?QUESTION\s+(\d)\.?\s*", re.IGNORECASE)
QUESTION_RE_2025 = re.compile(r"(?:^|\n)\s*(\d)\.\s+(?:Answer|In this text)", re.IGNORECASE)
APARTADO_RE_TMPL = r"(?:^|\n)\s*({num}\.\d)\.(?!\d)\s*"


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def make_entry(num, tema_list, puntuacion, apartados, ley, fuente_rel, body):
    lines = ["---"]
    lines.append(f"id: Inglés-{{year}}-{{conv}}-{num}")
    lines.append('asignatura: "Inglés"')
    lines.append("año: {year}")
    lines.append("convocatoria: {conv}")
    lines.append(f"numero_pregunta: {num}")
    if tema_list:
        lines.append("tema:")
        for t in tema_list:
            lines.append(f"  - {yaml_escape(t)}")
    else:
        lines.append("tema: []")
    lines.append(f"tema_fuente: palabras_clave")
    lines.append(f"puntuacion: {yaml_escape(puntuacion)}")
    if apartados:
        lines.append("apartados:")
        for a in apartados:
            lines.append(f"  - {yaml_escape(a[:400])}")
    else:
        lines.append("apartados: []")
    lines.append(f"ley_educativa: {ley}")
    lines.append(f"fuente: {yaml_escape(fuente_rel)}")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines)


def split_questions(text, is_new_format):
    re_used = QUESTION_RE_2025 if is_new_format else QUESTION_RE
    matches = list(re_used.finditer(text))
    out = []
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((num, text[start:end].strip()))
    return out


def extract_apartados(num, body):
    marker_re = re.compile(APARTADO_RE_TMPL.format(num=num))
    matches = list(marker_re.finditer(body))
    if not matches:
        return []
    apartados = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end].strip()
        chunk = " ".join(chunk.split())
        apartados.append(chunk)
    return apartados


PUNTOS_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*points?\)", re.IGNORECASE)


def extract_puntuacion(body):
    m = PUNTOS_RE.search(body[:300])
    if m:
        return f"{m.group(1)} puntos"
    return "? puntos"


def process_file(path, year, conv):
    doc = fitz.open(path)
    text = "\n".join(doc[i].get_text() for i in range(len(doc)))
    text = text.replace(" ", " ")
    is_new_format = int(year) >= 2025
    questions = split_questions(text, is_new_format)
    ley = "LOMCE" if int(year) <= 2024 else "LOMLOE"

    out_dir = os.path.join("vault", "ingles", year, conv)
    os.makedirs(out_dir, exist_ok=True)

    fuente_rel = path.replace("\\", "/")

    results = []
    for num, body in questions:
        apartados = extract_apartados(num, body)
        puntuacion = extract_puntuacion(body)

        temas = classify_by_keywords(" ".join(body.split()))

        entry = make_entry(num, temas, puntuacion, apartados, ley, fuente_rel, body)
        entry = entry.replace("{year}", year).replace("{conv}", conv)

        out_path = os.path.join(out_dir, f"pregunta-{num}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(entry)
        results.append((out_path, temas))
    return results


def main():
    total = []
    problems = []
    sin_tema = []
    for year in YEARS:
        for conv in ["ordinaria", "extraordinaria"]:
            matches = glob.glob(f"fuentes/ingles/{year}/{conv}/*.pdf")
            if not matches:
                problems.append((year, conv, "sin fuente"))
                continue
            path = matches[0]
            results = process_file(path, year, conv)
            if not results:
                problems.append((year, conv, f"0 preguntas detectadas: {path}"))
            for out_path, temas in results:
                if not temas:
                    sin_tema.append(out_path)
            total.extend(results)
            print(f"{year} {conv}: {len(results)} preguntas")

    print(f"\nTotal archivos vault creados: {len(total)}")
    print(f"Preguntas sin tema detectado por palabras clave: {len(sin_tema)}")
    for p in sin_tema:
        print("  ", p)
    print(f"\n=== PROBLEMAS ===")
    for year, conv, msg in problems:
        print(f"  {year} {conv}: {msg}")


if __name__ == "__main__":
    main()
