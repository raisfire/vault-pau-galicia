# -*- coding: utf-8 -*-
"""Clasifica el tema (lista cerrada de 34) de las 56 preguntas de
vault/historiaespana/ 2020-2026, via Haiku 4.5 + Batch API + caching.
Cada pregunta puede tener hasta 4 temas (P1 2020-2024 ofrece elegir 1
de 4 sub-temas distintos; las preguntas con menos opciones tendrán
menos temas)."""
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
from historiaespana_temas import TEMAS_HISTORIA_ESPANA

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SYSTEM = (
    "Eres un clasificador temático para preguntas de examen PAU/ABAU de Historia de España "
    "(Galicia, España). Se te da el enunciado completo de una pregunta, que puede ofrecer "
    "elegir entre varios apartados (cada uno sobre un tema histórico distinto). Identifica "
    "TODOS los temas realmente tratados entre las opciones, eligiendo cada uno EXACTAMENTE "
    "como está escrito en esta lista cerrada de 34 temas oficiales:\n\n"
    + "\n".join(f"- {t}" for t in TEMAS_HISTORIA_ESPANA)
    + "\n\nNo inventes temas fuera de la lista. Esta lista es del currículo 2025-2026 (LOMLOE); "
    "preguntas de años anteriores (2020-2024, currículo LOMCE) pueden tratar temas que ya no "
    "están en esta lista - en ese caso, para ESE apartado en concreto, no incluyas ningún tema "
    "de la lista que no encaje razonablemente bien; si NINGÚN apartado de la pregunta encaja, "
    "devuelve únicamente \"sin_clasificar\"."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra los temas detectados para esta pregunta.",
    "input_schema": {
        "type": "object",
        "properties": {
            "temas": {
                "type": "array",
                "items": {"type": "string", "enum": TEMAS_HISTORIA_ESPANA + ["sin_clasificar"]},
            }
        },
        "required": ["temas"],
        "additionalProperties": False,
    },
    "strict": True,
}


def main():
    files = sorted(glob.glob("vault/historiaespana/*/*/*.md"))
    targets = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm, body = text.split("---", 2)[1], text.split("---", 2)[2]
        meta = yaml.safe_load(fm)
        apartados_text = "\n".join(meta.get("apartados") or [])
        full_text = (body.strip() + "\n" + apartados_text)[:3000]
        custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.replace("vault/historiaespana/", "hesp_").replace("/", "_").replace("\\", "_").replace(".md", ""))
        targets.append({"path": path, "custom_id": custom_id, "texto": full_text})

    print(f"Total preguntas a clasificar: {len(targets)}")

    system_cached = [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}]

    batch_requests = []
    for t in targets:
        params = MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=300,
            system=system_cached,
            tools=[TOOL],
            tool_choice={"type": "tool", "name": "clasificar_tema"},
            messages=[{"role": "user", "content": t["texto"]}],
        )
        batch_requests.append(Request(custom_id=t["custom_id"], params=params))

    with open("script/classify_historiaespana_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_historiaespana_batch_id.txt", "w") as f:
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
