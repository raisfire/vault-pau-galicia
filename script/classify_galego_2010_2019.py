# -*- coding: utf-8 -*-
"""Clasifica (solo para estadisticas, no crea vault/) las opciones de
Lingua Galega e Literatura II 2010-2019 extraidas por
extract_galego_2010_2019.py, contra la lista cerrada combinada de
galego_temas.py, via Haiku 4.5 + Batch API + prompt caching."""
import json
import os
import re

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from galego_temas import TEMAS_GALEGO, TEMA_COMUNICACION, TEMAS_GRAMATICA, TEMAS_LINGUA_FALANTES, TEMAS_LITERATURA

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SYSTEM = (
    "Eres un clasificador temático para preguntas de examen PAU/ABAU de Lingua Galega e "
    "Literatura (Galicia, España), de exámenes históricos 2010-2019 (anteriores al currículo "
    "actual). Se te da el enunciado completo de una opción de examen (texto + varias preguntas de "
    "tipo distinto: comprensión, gramática, lingua e sociedade, literatura). Esta asignatura mezcla "
    "una destreza general de comprensión y producción textual (sin lista cerrada, usa literalmente "
    f"\"{TEMA_COMUNICACION}\" cuando aplique) con tres listas cerradas de contido:\n\n"
    "CATEGORÍAS DE REFLEXIÓN SOBRE A LINGUA (gramática):\n"
    + "\n".join(f"- {t}" for t in TEMAS_GRAMATICA)
    + "\n\nCATEGORÍAS DE A LINGUA E OS SEUS FALANTES (sociolingüística):\n"
    + "\n".join(f"- {t}" for t in TEMAS_LINGUA_FALANTES)
    + "\n\nPERÍODOS DE EDUCACIÓN LITERARIA (identifica o período polo autor, obra ou movemento "
    "citado):\n"
    + "\n".join(f"- {t}" for t in TEMAS_LITERATURA)
    + "\n\nIdentifica TODOS os temas realmente tratados entre as preguntas da opción, elixindo cada "
    "un EXACTAMENTE como está escrito arriba. Non inventes temas fóra destas listas. Como estes "
    "exames son dun currículo anterior, é normal que algunhas preguntas traten cuestións que xa non "
    "están na lista actual: nese caso, para ESA pregunta en concreto, non incluías ningún tema que "
    "non encaixe razoablemente ben; se NINGÚNHA pregunta da opción encaixa, devolve unicamente "
    "\"sin_clasificar\"."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra os temas detectados para esta opción de examen.",
    "input_schema": {
        "type": "object",
        "properties": {
            "temas": {
                "type": "array",
                "items": {"type": "string", "enum": TEMAS_GALEGO + ["sin_clasificar"]},
            }
        },
        "required": ["temas"],
        "additionalProperties": False,
    },
    "strict": True,
}


def main():
    data = json.load(open("script/extracted_galego_2010_2019.json", encoding="utf-8"))

    targets = []
    for r in data:
        if r["status"] != "ok":
            continue
        for i, (label, texto) in enumerate(r["opciones"]):
            custom_id = f"gal1019__{r['year']}__{r['conv']}__op{i}"
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

    with open("script/classify_galego_2010_2019_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_galego_2010_2019_batch_id.txt", "w") as f:
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
