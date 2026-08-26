# -*- coding: utf-8 -*-
"""Trocea vault/castelan/ para 2020-2026 (2 formatos de examen).

- 2020-2024 (LOMCE): 8 PREGUNTA de 2 puntos, responde un máximo de 5,
  combinadas como quiera. Cada PREGUNTA es una unidad independiente
  (comentario, resumen+gramática, obra lida, historia da literatura...).
- 2025-2026 (LOMLOE): 4 PREGUNTA obligatorias (comentario de texto sin
  apartados; reflexión lingüística con elección de 2 de 4 apartados;
  obra lida y historia da literatura con elección de 1 de 2 apartados).

El examen ya está íntegramente en castellano (no hay bloque bilingüe que
descartar, a diferencia de Historia/Filosofía). El tema (comentario de
texto / 8 categorías de gramática / 4 obras / 11 temas de historia de la
literatura) se asigna después vía IA, no aquí - ver
classify_castellano.py."""
import glob
import os
import re

import fitz

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]

PREGUNTA_RE = re.compile(r"(?:^|\n)\s*PREGUNTA\s+(\d)\.?\s*", re.IGNORECASE)
APARTADO_RE_TMPL = r"(?:^|\n)\s*({num}\.\d)\.(?!\d)\s*"
PUNTOS_RE = re.compile(r"\((\d+(?:[.,]\d+)?)\s*puntos?\)", re.IGNORECASE)


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def make_entry(num, puntuacion, apartados, ley, fuente_rel, body):
    lines = ["---"]
    lines.append(f"id: Lingua Castelá-{{year}}-{{conv}}-{num}")
    lines.append('asignatura: "Lingua Castelá e Literatura"')
    lines.append("año: {year}")
    lines.append("convocatoria: {conv}")
    lines.append(f"numero_pregunta: {num}")
    lines.append("tema: []")
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


def split_preguntas(text):
    matches = list(PREGUNTA_RE.finditer(text))
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


def extract_puntuacion(body, is_new_format):
    m = PUNTOS_RE.search(body[:120])
    if m:
        return f"{m.group(1)} puntos"
    return "2 puntos" if not is_new_format else "? puntos"


def process_file(path, year, conv):
    doc = fitz.open(path)
    text = "\n".join(doc[i].get_text() for i in range(len(doc)))
    preguntas = split_preguntas(text)
    ley = "LOMCE" if int(year) <= 2024 else "LOMLOE"
    is_new_format = int(year) >= 2025

    out_dir = os.path.join("vault", "castelan", year, conv)
    os.makedirs(out_dir, exist_ok=True)

    fuente_rel = path.replace("\\", "/")

    results = []
    for num, body in preguntas:
        apartados = extract_apartados(num, body)
        puntuacion = extract_puntuacion(body, is_new_format)

        entry = make_entry(num, puntuacion, apartados, ley, fuente_rel, body)
        entry = entry.replace("{year}", year).replace("{conv}", conv)

        out_path = os.path.join(out_dir, f"pregunta-{num}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(entry)
        results.append(out_path)
    return results


def main():
    total = []
    problems = []
    for year in YEARS:
        for conv in ["ordinaria", "extraordinaria"]:
            matches = glob.glob(f"fuentes/castelan/{year}/{conv}/*.pdf")
            if not matches:
                problems.append((year, conv, "sin fuente"))
                continue
            path = matches[0]
            results = process_file(path, year, conv)
            expected = 8 if int(year) <= 2024 else 4
            if len(results) != expected:
                problems.append((year, conv, f"{len(results)} preguntas (se esperaban {expected}): {path}"))
            total.extend(results)
            print(f"{year} {conv}: {len(results)} preguntas")

    print(f"\nTotal archivos vault creados: {len(total)}")
    print(f"\n=== PROBLEMAS ===")
    for year, conv, msg in problems:
        print(f"  {year} {conv}: {msg}")


if __name__ == "__main__":
    main()
