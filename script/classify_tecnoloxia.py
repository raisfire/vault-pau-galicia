# -*- coding: utf-8 -*-
"""Clasifica el tema de las 32 preguntas de vault/tecnoloxia/ (2024-2026)
via Haiku 4.5 + Batch API + caching, contra la lista cerrada de 4
bloques oficiales (tecnoloxia_temas.py)."""
import glob
import json
import os
import re

import anthropic
import yaml
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tecnoloxia_temas import TEMAS_TECNOLOXIA

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SYSTEM = (
    "Eres un clasificador temático para preguntas de examen PAU/ABAU de Tecnología e Ingeniería "
    "(Galicia, España). Se te da el enunciado completo de una pregunta (puede tener varios "
    "apartados). Elige UNO de estos 4 bloques de contenido oficiales, tal cual está escrito:\n\n"
    + "\n".join(f"- {t}" for t in TEMAS_TECNOLOXIA)
    + "\n\nNo inventes temas fuera de la lista. Si no tienes confianza razonable, responde solo "
    "\"sin_clasificar\"."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra el tema detectado para esta pregunta.",
    "input_schema": {
        "type": "object",
        "properties": {
            "temas": {
                "type": "array",
                "items": {"type": "string", "enum": TEMAS_TECNOLOXIA + ["sin_clasificar"]},
            }
        },
        "required": ["temas"],
        "additionalProperties": False,
    },
    "strict": True,
}


def main():
    files = sorted(glob.glob("vault/tecnoloxia/*/*/*.md"))
    targets = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm, body = text.split("---", 2)[1], text.split("---", 2)[2]
        meta = yaml.safe_load(fm)
        apartados_text = "\n".join(meta.get("apartados") or [])
        full_text = (body.strip() + "\n" + apartados_text)[:3000]
        custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.replace("\\", "/").replace("vault/tecnoloxia/", "tec_").replace("/", "_").replace(".md", ""))
        targets.append({"path": path, "custom_id": custom_id, "texto": full_text})

    print(f"Total preguntas a clasificar: {len(targets)}")

    system_cached = [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}]

    batch_requests = []
    for t in targets:
        params = MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=200,
            system=system_cached,
            tools=[TOOL],
            tool_choice={"type": "tool", "name": "clasificar_tema"},
            messages=[{"role": "user", "content": t["texto"]}],
        )
        batch_requests.append(Request(custom_id=t["custom_id"], params=params))

    with open("script/classify_tecnoloxia_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_tecnoloxia_batch_id.txt", "w") as f:
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
