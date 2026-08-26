# -*- coding: utf-8 -*-
"""Clasifica (solo para estadisticas, no crea vault/) las 36 opciones de
Historia da Filosofía 2010-2019 extraidas por
extract_historiafilosofia_2010_2019.py, contra la lista cerrada oficial
de 14 temas (LOMLOE 2025-26), via Haiku 4.5 + Batch API + prompt
caching. Estos examenes son anteriores al curriculo actual, asi que se
permite dejar temas sin encajar como sin_clasificar en vez de
forzarlos."""
import json
import os
import re

import anthropic
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
    "(Galicia, España), de exámenes históricos 2010-2019 (anteriores al currículo actual). Se te da "
    "el enunciado completo de una opción de examen (comentario de texto filosófico y/o cuestiones "
    "teóricas relacionadas, puede mencionar varios filósofos o temas). Identifica el/los tema(s) "
    "realmente tratados, eligiendo cada uno EXACTAMENTE como está escrito en esta lista cerrada de "
    "14 temas oficiales (currículo 2025-2026, LOMLOE):\n\n"
    + "\n".join(f"- {t}" for t in TEMAS_HISTORIA_FILOSOFIA)
    + "\n\nNo inventes temas fuera de la lista. Como estos exámenes son de un currículo anterior, es "
    "normal que algunos traten autores o cuestiones que ya no están en la lista actual (p.ej. "
    "filosofía medieval, presocráticos, sofistas): en ese caso, si NINGÚN tema de la lista encaja "
    "razonablemente bien, devuelve únicamente \"sin_clasificar\". No fuerces un tema que no encaje "
    "solo por parecido superficial."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra los temas detectados para esta opción de examen.",
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
    data = json.load(open("script/extracted_historiafilosofia_2010_2019.json", encoding="utf-8"))

    targets = []
    for r in data:
        if r["status"] != "ok":
            continue
        for i, (label, texto) in enumerate(r["opciones"]):
            custom_id = f"hfil1019__{r['year']}__{r['conv']}__op{i}"
            custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", custom_id)[:64]
            targets.append({
                "custom_id": custom_id,
                "year": r["year"],
                "conv": r["conv"],
                "texto": texto[:3000],
            })

    print(f"Total opciones a clasificar: {len(targets)}")

    seen = {}
    for t in targets:
        base = t["custom_id"]
        n = seen.get(base, 0)
        seen[base] = n + 1
        if n:
            t["custom_id"] = f"{base}_{n}"

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

    with open("script/classify_historiafilosofia_2010_2019_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_historiafilosofia_2010_2019_batch_id.txt", "w") as f:
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
