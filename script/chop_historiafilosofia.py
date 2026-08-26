# -*- coding: utf-8 -*-
"""Trocea vault/historiafilosofia/ para 2020-2026 (2 formatos de examen).

- 2020-2024 (LOMCE): 4 PREGUNTA, o alumnado responde SO UNHA das catro
  (non se marca no PDF cal, é elección libre). Cada PREGUNTA ten 2
  apartados: N.1 comentario de texto dun filósofo fixo (6 puntos) e N.2
  desenvolver 1 de 3 temas alternativos (4 puntos) -> 10 puntos en total
  por ser a unica pregunta que se corrixe.
- 2025-2026 (LOMLOE): 4 PREGUNTA obligatorias, puntuación variable por
  pregunta (indicada no propio enunciado). PREGUNTA 1 e 2 con elección
  entre N.1/N.2 (cada un sobre un filósofo distinto); PREGUNTA 3 sen
  apartados (resposta única); PREGUNTA 4 con apartados 4.1 (exercicio
  fixo) e 4.2 (elixir 1 de 2 definicións).

O tema (lista pechada de 14 elementos curriculares, currículo 2025-26)
asígnase despois vía IA, non aquí. 2010-2019 NON se trocea aquí (formato
"OPCIÓN A/B" sen PREGUNTA, grao distinto) - pase de solo estadísticas
aparte, ver extract_historiafilosofia_2010_2019.py."""
import glob
import os
import re

import fitz

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]
YEAR_LEY = lambda y: "LOMCE" if int(y) <= 2024 else "LOMLOE"

PREGUNTA_RE = re.compile(r"(?:^|\n)\s*PREGUNTA\s+(\d)\.?\s*", re.IGNORECASE)
HEADER_RE = re.compile(r"Proba de Avaliaci[oó]n do Bacharelato|^[ \t]*(ABAU|PAU)[ \t]*$", re.MULTILINE)
PUNTOS_RE = re.compile(r"\((\d+(?:[.,]\d+)?)\s*puntos?\)", re.IGNORECASE)


def get_castellano_text(doc):
    pages = [doc[i].get_text() for i in range(len(doc))]
    full_pages = "\n".join(pages)
    matches = list(HEADER_RE.finditer(full_pages))
    if len(matches) < 2:
        return full_pages
    return full_pages[matches[1].start():]


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def make_entry(num, tema_list, puntuacion, apartados, ley, fuente_rel, body):
    lines = ["---"]
    lines.append(f"id: Historia da Filosofía-{{year}}-{{conv}}-{num}")
    lines.append('asignatura: "Historia da Filosofía"')
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
    """Detecta marcadores "N.1", "N.2"... al inicio de linea (evitando
    falsos positivos como "4.2.1" via lookahead negativo de digito) y
    devuelve el texto de cada apartado, con la etiqueta incluida."""
    marker_re = re.compile(rf"(?:^|\n)\s*({num}\.\d)\.(?!\d)\s*")
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


def extract_puntuacion(num, body, is_new_format):
    if not is_new_format:
        return "10 puntos"
    m = PUNTOS_RE.search(body[:250])
    if m:
        return f"{m.group(1)} puntos"
    return "? puntos"


def process_file(path, year, conv):
    doc = fitz.open(path)
    text = get_castellano_text(doc)
    preguntas = split_preguntas(text)
    ley = YEAR_LEY(year)
    is_new_format = int(year) >= 2025

    out_dir = os.path.join("vault", "historiafilosofia", year, conv)
    os.makedirs(out_dir, exist_ok=True)

    fuente_rel = path.replace("\\", "/")

    results = []
    for num, body in preguntas:
        if num < 1 or num > 4:
            continue
        apartados = extract_apartados(num, body)
        puntuacion = extract_puntuacion(num, body, is_new_format)

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
            matches = glob.glob(f"fuentes/historiafilosofia/{year}/{conv}/*.pdf")
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
