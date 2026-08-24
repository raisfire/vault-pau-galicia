# -*- coding: utf-8 -*-
"""Compila vault/ entero en web/data/preguntas.json.

Relanzable en cualquier momento: no toca nada fuera de web/data/preguntas.json.
Uso: python script/build_data.py
"""
import glob
import json
import re

import yaml

SUBJECT_LABELS = {
    "matematicas_ii": "Matemáticas II",
    "bioloxia": "Biología",
    "fisica": "Física",
    "quimica": "Química",
}


def parse_file(path):
    raw = open(path, encoding="utf-8").read()
    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"frontmatter mal formado: {path}")
    frontmatter_raw, body = parts[1], parts[2]
    meta = yaml.safe_load(frontmatter_raw) or {}
    body = body.strip()

    subject_slug = path.replace("\\", "/").split("/")[1]

    return {
        "id": meta.get("id", ""),
        "asignatura": meta.get("asignatura", SUBJECT_LABELS.get(subject_slug, subject_slug)),
        "asignatura_slug": subject_slug,
        "anio": meta.get("año"),
        "convocatoria": meta.get("convocatoria", ""),
        "numero_pregunta": meta.get("numero_pregunta"),
        "tema": meta.get("tema") or [],
        "tema_fuente": meta.get("tema_fuente"),
        "puntuacion": meta.get("puntuacion", ""),
        "apartados": meta.get("apartados") or [],
        "ley_educativa": meta.get("ley_educativa", ""),
        "fuente": meta.get("fuente", ""),
        "revision_manual": bool(meta.get("revision_manual", False)),
        "revision_manual_dudosa": bool(meta.get("revision_manual_dudosa", False)),
        "enunciado": body,
    }


def main():
    files = sorted(glob.glob("vault/*/*/*/*.md"))
    preguntas = [parse_file(f) for f in files]

    asignaturas = sorted(set(p["asignatura"] for p in preguntas))
    anios = [p["anio"] for p in preguntas if p["anio"] is not None]

    data = {
        "generado": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "total_preguntas": len(preguntas),
        "asignaturas": asignaturas,
        "anio_min": min(anios) if anios else None,
        "anio_max": max(anios) if anios else None,
        "preguntas": preguntas,
    }

    out_path = "web/data/preguntas.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"Compiladas {len(preguntas)} preguntas de {len(asignaturas)} asignaturas "
          f"({data['anio_min']}-{data['anio_max']}) -> {out_path}")


if __name__ == "__main__":
    main()
