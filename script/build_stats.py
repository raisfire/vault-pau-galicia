# -*- coding: utf-8 -*-
"""Compila web/data/estadisticas.json: frecuencia de temas por asignatura,
combinando las preguntas trozeadas del vault (2020-2026) con la
clasificacion puramente estadistica de 2010-2019 (esta ultima no vive
en vault/, ver script/stats_2010_2019.json).

Relanzable en cualquier momento tras recompilar build_data.py o
reclasificar 2010-2019.
"""
import glob
import json
from collections import Counter, defaultdict

import yaml

SUBJECT_LABELS = {
    "matematicas_ii": "Matemáticas II",
    "bioloxia": "Biología",
    "fisica": "Física",
    "quimica": "Química",
}


def temas_from_vault():
    counts = defaultdict(Counter)
    n_preguntas = defaultdict(int)
    for path in glob.glob("vault/*/*/*/*.md"):
        subject = path.replace("\\", "/").split("/")[1]
        text = open(path, encoding="utf-8").read()
        fm = text.split("---", 2)[1]
        meta = yaml.safe_load(fm) or {}
        temas = meta.get("tema") or []
        n_preguntas[subject] += 1
        for t in temas:
            counts[subject][t] += 1
    return counts, n_preguntas


def temas_from_2010_2019():
    counts = defaultdict(Counter)
    n_preguntas = defaultdict(int)
    data = json.load(open("script/stats_2010_2019.json", encoding="utf-8"))
    for r in data:
        subject = r["subject"]
        n_preguntas[subject] += 1
        for t in r["temas"]:
            if t != "sin_clasificar":
                counts[subject][t] += 1
    return counts, n_preguntas


def main():
    vault_counts, vault_n = temas_from_vault()
    hist_counts, hist_n = temas_from_2010_2019()

    por_asignatura = {}
    for subject in SUBJECT_LABELS:
        combined = Counter()
        combined.update(vault_counts.get(subject, {}))
        combined.update(hist_counts.get(subject, {}))
        total_preguntas = vault_n.get(subject, 0) + hist_n.get(subject, 0)
        total_asignaciones = sum(combined.values())

        temas = [
            {
                "tema": tema,
                "n": n,
                "pct_preguntas": round(100 * n / total_preguntas, 1) if total_preguntas else 0,
            }
            for tema, n in combined.most_common()
        ]

        por_asignatura[subject] = {
            "asignatura": SUBJECT_LABELS[subject],
            "total_preguntas": total_preguntas,
            "total_preguntas_vault_2020_2026": vault_n.get(subject, 0),
            "total_preguntas_historico_2010_2019": hist_n.get(subject, 0),
            "temas": temas,
        }

    data = {
        "generado": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "anio_min": 2010,
        "anio_max": 2026,
        "nota": "2010-2019 son solo estadisticas (clasificadas por IA a partir del texto extraido de los examenes originales), no forman parte del vault de preguntas trozeadas.",
        "por_asignatura": por_asignatura,
    }

    with open("web/data/estadisticas.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    for subject, d in por_asignatura.items():
        print(f"{subject}: {d['total_preguntas']} preguntas "
              f"({d['total_preguntas_vault_2020_2026']} vault + {d['total_preguntas_historico_2010_2019']} historico), "
              f"{len(d['temas'])} temas")


if __name__ == "__main__":
    main()
