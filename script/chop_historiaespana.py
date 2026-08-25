# -*- coding: utf-8 -*-
"""Trocea vault/historiaespana/ para 2020-2026 (2 formatos de examen).

- 2020-2024 (LOMCE): 4 PREGUNTA de 5 puntos, responde un maximo de 2.
  PREGUNTA 1 tiene apartados 1.1 (definiciones) y 1.2 (elige 1 de 4 temas).
  PREGUNTA 2-4 son un ensayo unico ("Elabore unha composicion historica").
- 2025-2026 (LOMLOE): 4 PREGUNTA obligatorias de 2,5 puntos. La 1 sin
  eleccion (1.1/1.2/1.3 fijos); las demas con eleccion entre 2 apartados
  (2.1/2.2 etc.), cada apartado sobre un tema distinto.

El tema (de la lista cerrada de 34) se asigna despues via IA, no aqui.
2010-2019 NO se trocea aqui (formato "OPCION A/B" sin PREGUNTA, distinto
grano) - eso es un pase de solo estadisticas aparte, igual que se hizo
con las 4 asignaturas de Oleada 1.
"""
import glob
import os
import re

import fitz

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]
YEAR_LEY = lambda y: "LOMCE" if int(y) <= 2024 else "LOMLOE"

PREGUNTA_RE = re.compile(r"(?:^|\n)\s*PREGUNTA\s+(\d)\.?\s*", re.IGNORECASE)
HEADER_RE = re.compile(r"Proba de Avaliaci[oó]n do Bacharelato|^[ \t]*(ABAU|PAU)[ \t]*$", re.MULTILINE)
APARTADO_RE = re.compile(r"(?:^|\n)\s*(\d\.\d)\.?\s+")


def get_castellano_text(doc):
    pages = [doc[i].get_text() for i in range(len(doc))]
    full_pages = "\n".join(pages)
    matches = list(HEADER_RE.finditer(full_pages))
    if len(matches) < 2:
        # ya viene solo en castellano (algun archivo antiguo) o no se detecto
        return full_pages
    return full_pages[matches[1].start():]


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def make_entry(num, tema_list, puntuacion, apartados, ley, fuente_rel, body):
    lines = ["---"]
    lines.append(f"id: Historia de España-{{year}}-{{conv}}-{num}")
    lines.append('asignatura: "Historia de España"')
    lines.append("año: {year}")
    lines.append("convocatoria: {conv}")
    lines.append(f"numero_pregunta: {num}")
    if tema_list:
        lines.append("tema:")
        for t in tema_list:
            lines.append(f"  - {yaml_escape(t)}")
    else:
        lines.append("tema: []")
    lines.append(f"puntuacion: {yaml_escape(puntuacion)}")
    if apartados:
        lines.append("apartados:")
        for a in apartados:
            lines.append(f"  - {yaml_escape(a[:200])}")
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


def extract_apartados_2020_2024(num, body):
    """PREGUNTA 1: 1.1 y 1.2 (con 1.2.1-1.2.4 dentro). PREGUNTA 2-4: sin apartados,
    el propio enunciado ya es una unica pregunta-ensayo."""
    if num != 1:
        return []
    apartados = []
    # 1.1 definiciones
    m1 = re.search(r"1\.1\.?\s+(.*?)(?=1\.2\.?\s)", body, re.DOTALL)
    if m1:
        apartados.append("1.1. " + " ".join(m1.group(1).split()))
    m2 = re.search(r"1\.2\.?\s+(.*)", body, re.DOTALL)
    if m2:
        apartados.append("1.2. " + " ".join(m2.group(1).split()))
    return apartados


def extract_apartados_2025_2026(num, body):
    """PREGUNTA 1: sin eleccion, no se listan apartados de eleccion (todo el
    cuerpo es la pregunta). PREGUNTA 2-4: "Responda un/uno destes dous
    apartados" seguido de N.1/N.2."""
    if num == 1:
        return []
    parts = re.split(rf"(?:^|\n)\s*({num}\.\d)\.?\s+", body)
    apartados = []
    for i in range(1, len(parts), 2):
        label = parts[i]
        text = parts[i + 1] if i + 1 < len(parts) else ""
        apartados.append(f"{label}. " + " ".join(text.split()))
    return apartados


def process_file(path, year, conv):
    doc = fitz.open(path)
    text = get_castellano_text(doc)
    preguntas = split_preguntas(text)
    ley = YEAR_LEY(year)
    is_new_format = int(year) >= 2025

    out_dir = os.path.join("vault", "historiaespana", year, conv)
    os.makedirs(out_dir, exist_ok=True)

    fuente_rel = path.replace("\\", "/")

    results = []
    for num, body in preguntas:
        if num < 1 or num > 4:
            continue
        if is_new_format:
            apartados = extract_apartados_2025_2026(num, body)
            puntuacion = "2.5 puntos"
        else:
            apartados = extract_apartados_2020_2024(num, body)
            puntuacion = "5 puntos"

        entry = make_entry(num, [], puntuacion, apartados, ley, fuente_rel, body)
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
            matches = glob.glob(f"fuentes/historiaespana/{year}/{conv}/*.pdf")
            if not matches:
                problems.append((year, conv, "sin fuente"))
                continue
            path = matches[0]
            results = process_file(path, year, conv)
            if len(results) != 4:
                problems.append((year, conv, f"{len(results)} preguntas (se esperaban 4): {path}"))
            total.extend(results)
            print(f"{year} {conv}: {len(results)} preguntas")

    print(f"\nTotal archivos vault creados: {len(total)}")
    print(f"\n=== PROBLEMAS ===")
    for year, conv, msg in problems:
        print(f"  {year} {conv}: {msg}")


if __name__ == "__main__":
    main()
