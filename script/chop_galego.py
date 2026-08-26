# -*- coding: utf-8 -*-
"""Trocea vault/galego/ para 2020-2026 (2 formatos de examen).

- 2020-2024 (LOMCE): 6 PREGUNTA de 2,5 puntos, responde un máximo de 4,
  combinadas como queira (comprensión, gramática, produción textual,
  lingua e sociedade, literatura x2).
- 2025-2026 (LOMLOE): 4 PREGUNTA obrigatorias (comunicación sen
  optatividade; reflexión sobre a lingua, a lingua e os seus falantes e
  educación literaria con optatividade variable).

El examen ya está íntegramente en galego (no hay bloque bilingüe que
descartar). El tema se asigna después vía IA - ver classify_galego.py."""
import glob
import os
import re

import fitz

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]

PREGUNTA_RE = re.compile(r"(?:^|\n)\s*PREGUNTA\s+(\d)\.?\s*", re.IGNORECASE)
APARTADO_RE_TMPL = r"(?:^|\n)\s*({num}\.\d)\.(?!\d)\s*"
PUNTOS_RE = re.compile(r"\((\d+(?:[.,]\d+)?)\s*puntos?\)", re.IGNORECASE)
TEXTO_RE = re.compile(r"(?:^|\n)\s*TEXTO\s*\n", re.IGNORECASE)


def extract_texto(text):
    """O TEXTO inicial cítase ("o texto", "do texto"...) desde varias
    preguntas posteriores, pero cada PREGUNTA trocéase por separado e
    perde ese texto compartido. Extraémolo aquí para axuntalo a todas as
    preguntas do exame."""
    m = TEXTO_RE.search(text)
    if not m:
        return ""
    pm = PREGUNTA_RE.search(text, m.end())
    end = pm.start() if pm else len(text)
    return text[m.end():end].strip()


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def make_entry(num, puntuacion, apartados, ley, fuente_rel, body):
    lines = ["---"]
    lines.append(f"id: Lingua Galega-{{year}}-{{conv}}-{num}")
    lines.append('asignatura: "Lingua Galega e Literatura"')
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
    m = PUNTOS_RE.search(body[:150])
    if m:
        return f"{m.group(1)} puntos"
    return "2,5 puntos" if not is_new_format else "? puntos"


def process_file(path, year, conv):
    doc = fitz.open(path)
    text = "\n".join(doc[i].get_text() for i in range(len(doc)))
    preguntas = split_preguntas(text)
    texto = extract_texto(text)
    ley = "LOMCE" if int(year) <= 2024 else "LOMLOE"
    is_new_format = int(year) >= 2025

    out_dir = os.path.join("vault", "galego", year, conv)
    os.makedirs(out_dir, exist_ok=True)

    fuente_rel = path.replace("\\", "/")

    results = []
    for num, body in preguntas:
        apartados = extract_apartados(num, body)
        puntuacion = extract_puntuacion(body, is_new_format)
        full_body = body
        if texto and texto not in body:
            full_body = body.rstrip() + "\n\n---\n\nTEXTO:\n\n" + texto

        entry = make_entry(num, puntuacion, apartados, ley, fuente_rel, full_body)
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
            matches = glob.glob(f"fuentes/galego/{year}/{conv}/*.pdf")
            if not matches:
                problems.append((year, conv, "sin fuente"))
                continue
            path = matches[0]
            results = process_file(path, year, conv)
            expected = 6 if int(year) <= 2024 else 4
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
