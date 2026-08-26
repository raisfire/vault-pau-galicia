# -*- coding: utf-8 -*-
"""Clasifica el tema de las preguntas de vault/galego/ 2020-2026, via
Haiku 4.5 + Batch API + caching, contra la lista cerrada combinada de
galego_temas.py (comunicación + 8 categorías de gramática + 4 de lingua
e falantes + 3 períodos de literatura)."""
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
    "Literatura (Galicia, España). Se te da el enunciado completo de una pregunta, que puede tener "
    "varios apartados de tipo distinto. Esta asignatura mezcla una destreza general de comprensión "
    f"y producción textual (sin lista cerrada, usa literalmente \"{TEMA_COMUNICACION}\" cuando "
    "aplique: resumo, esquema, tema, estrutura, significado de palabras ou produción textual sobre "
    "o texto inicial do exame) con tres listas cerradas de contido:\n\n"
    "CATEGORÍAS DE REFLEXIÓN SOBRE A LINGUA (gramática):\n"
    + "\n".join(f"- {t}" for t in TEMAS_GRAMATICA)
    + "\n\nCATEGORÍAS DE A LINGUA E OS SEUS FALANTES (sociolingüística):\n"
    + "\n".join(f"- {t}" for t in TEMAS_LINGUA_FALANTES)
    + "\n\nPERÍODOS DE EDUCACIÓN LITERARIA (identifica o período polo autor, obra ou movemento "
    "citado no fragmento ou enunciado):\n"
    + "\n".join(f"- {t}" for t in TEMAS_LITERATURA)
    + "\n\nIdentifica TODOS os temas realmente tratados entre os apartados da pregunta, elixindo "
    "cada un EXACTAMENTE como está escrito arriba. Non inventes temas fóra destas listas. Estas "
    "listas son do currículo 2025-2026; preguntas de anos anteriores (2020-2024) poden tratar "
    "cuestións que xa non están explicitamente na lista actual (p.ex. análise sintáctica ou "
    "morfolóxica formal) - nese caso, para ESE apartado en concreto, non incluías ningún tema que "
    "non encaixe razoablemente ben; se NINGÚN apartado da pregunta encaixa, devolve unicamente "
    "\"sin_clasificar\"."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra os temas detectados para esta pregunta.",
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
    files = sorted(glob.glob("vault/galego/*/*/*.md"))
    targets = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm, body = text.split("---", 2)[1], text.split("---", 2)[2]
        meta = yaml.safe_load(fm)
        apartados_text = "\n".join(meta.get("apartados") or [])
        full_text = (body.strip() + "\n" + apartados_text)[:3000]
        custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.replace("\\", "/").replace("vault/galego/", "gal_").replace("/", "_").replace(".md", ""))
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

    with open("script/classify_galego_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_galego_batch_id.txt", "w") as f:
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
