# -*- coding: utf-8 -*-
"""Clasifica (solo para estadisticas, no crea vault/) las preguntas
2010-2019 extraidas por extract_2010_2019.py, usando Haiku 4.5 + Batch
API + prompt caching, contra la taxonomia oficial ya validada contra
los documentos de la CIUG (Orientacions/Criterios 2025-26)."""
import json
import os
import re

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

TEMAS = {
    "fisica": [
        "FÍSICA DEL SIGLO XX",
        "INTERACCIÓN ELECTROMAGNÉTICA",
        "INTERACCIÓN GRAVITACIONAL",
        "VIBRACIÓNS E ONDAS",
        "ÓPTICA",
    ],
    "quimica": [
        "DESTREZAS BÁSICAS DE LA QUÍMICA",
        "REACCIONES QUÍMICAS",
        "ENLACE QUÍMICO Y ESTRUCTURA DE LA MATERIA",
        "QUÍMICA ORGÁNICA",
    ],
    "bioloxia": [
        "LA CÉLULA",
        "BIOTECNOLOGÍA",
        "GENÉTICA MOLECULAR",
        "METABOLISMO CELULAR",
        "LA BASE MOLECULAR DE LA MATERIA VIVA",
        "INMUNOLOGÍA",
    ],
    "matematicas_ii": [
        "Análisis",
        "Estadística y Probabilidad",
        "Geometría",
        "Números y Álgebra",
    ],
}

SUBJECT_LABEL = {
    "fisica": "Física", "quimica": "Química",
    "bioloxia": "Biología", "matematicas_ii": "Matemáticas II",
}


def build_system(subject):
    temas_list = "\n".join(f"- {t}" for t in TEMAS[subject])
    return (
        f"Eres un clasificador temático para preguntas de examen PAU/ABAU de {SUBJECT_LABEL[subject]} "
        f"(Galicia, España), de exámenes históricos 2010-2019. Se te da el fragmento de una pregunta o "
        f"cuestión de examen (puede tener varios apartados). Elige UNO o, si la pregunta combina "
        f"claramente dos áreas distintas, DOS temas de esta lista cerrada, tal cual están escritos:\n\n"
        f"{temas_list}\n\n"
        "No inventes temas fuera de la lista. Si no tienes confianza razonable, responde solo "
        "\"sin_clasificar\" como único tema."
    )


def build_tool(subject):
    return {
        "name": "clasificar_tema",
        "description": "Registra el/los tema(s) clasificados para esta pregunta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "temas": {
                    "type": "array",
                    "items": {"type": "string", "enum": TEMAS[subject] + ["sin_clasificar"]},
                }
            },
            "required": ["temas"],
            "additionalProperties": False,
        },
        "strict": True,
    }


def main():
    data = json.load(open("script/extracted_2010_2019.json", encoding="utf-8"))

    targets = []
    for r in data:
        if r["status"] != "ok":
            continue
        for i, q in enumerate(r["questions"]):
            custom_id = f"{r['subject']}__{r['year']}__{r['conv']}__q{i}"
            custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", custom_id)[:64]
            targets.append({
                "custom_id": custom_id,
                "subject": r["subject"],
                "year": r["year"],
                "conv": r["conv"],
                "texto": q["texto"][:1500],
            })

    print(f"Total preguntas a clasificar: {len(targets)}")

    # aseguramos custom_id unicos (por si dos truncados coinciden)
    seen = {}
    for t in targets:
        base = t["custom_id"]
        n = seen.get(base, 0)
        seen[base] = n + 1
        if n:
            t["custom_id"] = f"{base}_{n}"

    system_cache = {s: [{"type": "text", "text": build_system(s), "cache_control": {"type": "ephemeral"}}]
                     for s in TEMAS}
    tool_cache = {s: build_tool(s) for s in TEMAS}

    batch_requests = []
    for t in targets:
        subject = t["subject"]
        params = MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=256,
            system=system_cache[subject],
            tools=[tool_cache[subject]],
            tool_choice={"type": "tool", "name": "clasificar_tema"},
            messages=[{"role": "user", "content": t["texto"]}],
        )
        batch_requests.append(Request(custom_id=t["custom_id"], params=params))

    with open("script/classify_2010_2019_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_2010_2019_batch_id.txt", "w") as f:
        f.write(batch.id)

    import time
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        print(f"status: {batch.processing_status}, counts: {batch.request_counts}")
        if batch.processing_status == "ended":
            break
        time.sleep(10)

    print("Batch terminado.")


if __name__ == "__main__":
    main()
