# -*- coding: utf-8 -*-
"""Añade enlaces [[wikilink]] nativos de Obsidian entre las preguntas del
vault y una nota-tema por cada tema real usado en cada asignatura, para
poder explorar las conexiones (grafo, vínculos locales/backlinks) dentro
de la propia app de Obsidian.

No toca el campo `tema:` existente (eso seguiría alimentando
build_data.py / el visor web tal cual). Añade un campo NUEVO
`tema_wikilinks:` con la sintaxis [[archivo-sanitizado|Texto Tema
Original]], que Obsidian sí resuelve como enlaces reales en el panel de
Properties, en "vínculos locales" y en el grafo. El script build_data.py
ignora cualquier clave de frontmatter que no lea explícitamente, así que
esto es 100% invisible para el visor web - solo existe para Obsidian.

Crea también, si no existen, las notas-tema (una por tema real usado) en
vault/<asignatura>/_temas/<tema>.md, con un contenido mínimo. Cada
pregunta que use ese tema enlaza a esa nota; el panel de "vínculos
locales" de Obsidian muestra automáticamente todas las preguntas que
enlazan a cada nota-tema, sin tener que mantener una lista a mano.

Idempotente: relanzable en cualquier momento, no duplica notas-tema ni
entradas si ya existen.
"""
import glob
import os
import re

import yaml

SUBJECTS = [
    "matematicas_ii", "bioloxia", "fisica", "quimica",
    "historiaespana", "historiafilosofia", "ingles",
    "castelan", "galego", "tecnoloxia",
]


def sanitize_filename(name):
    s = re.sub(r'[<>:"/\\|?*]', "", name)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > 120:
        s = s[:120].rstrip()
    return s


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def ensure_tema_note(subject, tema):
    filename = sanitize_filename(tema)
    out_dir = os.path.join("vault", subject, "_temas")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{filename}.md")
    if os.path.exists(out_path):
        return filename
    content = (
        f"# {tema}\n\n"
        f"Nota-tema generada automáticamente para conectar en Obsidian todas las "
        f"preguntas de esta asignatura clasificadas bajo este tema. Consulta el "
        f"panel de \"vínculos locales\" (linked mentions) de esta nota para verlas "
        f"todas juntas.\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def add_wikilinks_to_question(path, subject, temas):
    text = open(path, encoding="utf-8").read()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False
    fm_raw, body = parts[1], parts[2]
    meta = yaml.safe_load(fm_raw) or {}

    if not temas:
        return False

    links = []
    for t in temas:
        filename = ensure_tema_note(subject, t)
        # incluye la carpeta de la asignatura en la ruta para evitar
        # ambigüedad si dos asignaturas generan una nota-tema con el
        # mismo nombre exacto (p.ej. "Clases de palabras" en castelan y
        # galego): sin esto Obsidian no sabría a cuál de las dos enlazar.
        rel = f"{subject}/_temas/{filename}"
        escaped_t = t.replace('"', '\\"')
        links.append(f'  - "[[{rel}|{escaped_t}]]"')

    block = "tema_wikilinks:\n" + "\n".join(links) + "\n"

    if re.search(r"^tema_wikilinks:(\n(  - .*\n?)+|\s*\[\]\n)", fm_raw, flags=re.MULTILINE):
        new_fm = re.sub(r"^tema_wikilinks:(\n(  - .*\n?)+|\s*\[\]\n)", block, fm_raw, count=1, flags=re.MULTILINE)
    else:
        # inserta el nuevo campo justo despues de tema: [...] o tema: []
        if re.search(r"^tema:(\n(  - .*\n?)+)", fm_raw, flags=re.MULTILINE):
            new_fm = re.sub(r"(^tema:(\n(  - .*\n?)+))", r"\1" + block, fm_raw, count=1, flags=re.MULTILINE)
        else:
            new_fm = re.sub(r"^(tema: \[\]\n)", r"\1" + block, fm_raw, count=1, flags=re.MULTILINE)

    if new_fm == fm_raw:
        return False

    new_text = "---" + new_fm + "---" + body
    open(path, "w", encoding="utf-8").write(new_text)
    return True


def main():
    total_notas = 0
    total_preguntas_enlazadas = 0
    resumen = []

    for subject in SUBJECTS:
        files = sorted(glob.glob(f"vault/{subject}/*/*/*.md"))
        temas_subject = set()
        enlazadas = 0

        for path in files:
            text = open(path, encoding="utf-8").read()
            fm = text.split("---", 2)[1]
            meta = yaml.safe_load(fm) or {}
            temas = [t for t in (meta.get("tema") or []) if t and not re.match(r"^\d+$", str(t).strip())]
            if not temas:
                continue
            temas_subject.update(temas)
            if add_wikilinks_to_question(path, subject, temas):
                enlazadas += 1

        notas_creadas = len(glob.glob(f"vault/{subject}/_temas/*.md"))
        total_notas += notas_creadas
        total_preguntas_enlazadas += enlazadas
        resumen.append((subject, len(files), enlazadas, notas_creadas))

    print(f"{'asignatura':20s} {'preguntas':>10s} {'enlazadas':>10s} {'notas-tema':>11s}")
    for subject, total, enlazadas, notas in resumen:
        print(f"{subject:20s} {total:10d} {enlazadas:10d} {notas:11d}")
    print(f"\nTotal notas-tema creadas/existentes: {total_notas}")
    print(f"Total preguntas con tema_wikilinks añadido en esta pasada: {total_preguntas_enlazadas}")


if __name__ == "__main__":
    main()
