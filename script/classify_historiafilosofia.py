# -*- coding: utf-8 -*-
"""Clasifica el tema (lista cerrada de 14) de las 56 preguntas de
vault/historiafilosofia/ 2020-2026, via Haiku 4.5 + Batch API + caching.
Cada pregunta puede tener hasta 4 temas (2020-2024: apartado N.1 fijo +
apartado N.2 con eleccion de 3 alternativas; 2025-2026: hasta 2
alternativas por apartado)."""
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
from historiafilosofia_temas import TEMAS_HISTORIA_FILOSOFIA

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SYSTEM = (
    "Eres un clasificador temático para preguntas de examen PAU/ABAU de Historia da Filosofía "
    "(Galicia, España). Se te da el enunciado completo de una pregunta, que puede ofrecer elegir "
    "entre varios apartados o subtemas (cada uno centrado en un/a filósofo/a o cuestión distinta). "
    "Identifica TODOS los temas realmente tratados entre las opciones (el comentario de texto fijo "
    "más, si los hay, los subtemas alternativos entre los que se puede elegir), eligiendo cada uno "
    "EXACTAMENTE como está escrito en esta lista cerrada de 14 temas oficiales:\n\n"
    + "\n".join(f"- {t}" for t in TEMAS_HISTORIA_FILOSOFIA)
    + "\n\nNo inventes temas fuera de la lista. Esta lista es del currículo 2025-2026 (LOMLOE); "
    "preguntas de años anteriores (2020-2024, currículo LOMCE) pueden tratar autores o cuestiones "
    "que ya no están en esta lista (p.ej. filosofía medieval, presocráticos) - en ese caso, para ESE "
    "apartado en concreto, no incluyas ningún tema de la lista que no encaje razonablemente bien; si "
    "NINGÚN apartado de la pregunta encaja, devuelve únicamente \"sin_clasificar\"."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra los temas detectados para esta pregunta.",
    "input_schema": {
        "type": "object",
        "properties": {
            "temas": {
                "type": "array",
                "items": {"type": "string", "enum": TEMAS_HISTORIA_FILOSOFIA + ["sin_clasificar"]},
            }
        },
        "required": ["temas"],
        "additionalProperties": False,
    },
    "strict": True,
}


def main():
    files = sorted(glob.glob("vault/historiafilosofia/*/*/*.md"))
    targets = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm, body = text.split("---", 2)[1], text.split("---", 2)[2]
        meta = yaml.safe_load(fm)
        apartados_text = "\n".join(meta.get("apartados") or [])
        full_text = (body.strip() + "\n" + apartados_text)[:3000]
        custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.replace("\\", "/").replace("vault/historiafilosofia/", "hfil_").replace("/", "_").replace(".md", ""))
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

    with open("script/classify_historiafilosofia_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_historiafilosofia_batch_id.txt", "w") as f:
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
