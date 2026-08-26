# -*- coding: utf-8 -*-
"""Clasifica el tema de las 96 preguntas de vault/castelan/ 2020-2026, via
Haiku 4.5 + Batch API + caching, contra la lista cerrada combinada de
castellano_temas.py (comentario de texto + 8 categorías de gramática + 4
obras de lectura obligatoria + 11 temas de historia de la literatura).
Cada pregunta puede tener varios temas si combina apartados de distinto
tipo (p.ej. 1.1 comentario + 1.2 gramática en el formato 2020-2024)."""
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
from castellano_temas import TEMAS_CASTELLANO, TEMA_COMENTARIO, TEMAS_GRAMATICA, TEMAS_OBRAS, TEMAS_LITERATURA

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SYSTEM = (
    "Eres un clasificador temático para preguntas de examen PAU/ABAU de Lingua Castelá e "
    "Literatura (Galicia, España). Se te da el enunciado completo de una pregunta, que puede tener "
    "varios apartados de tipo distinto. Esta asignatura mezcla una destreza general de comentario "
    f"de texto (sin lista cerrada, usa literalmente \"{TEMA_COMENTARIO}\" cuando aplique: resumen, "
    "esquema o comentario crítico sobre el texto inicial del examen) con tres listas cerradas de "
    "contenido:\n\n"
    "CATEGORÍAS DE REFLEXIÓN LINGÜÍSTICA (gramática):\n"
    + "\n".join(f"- {t}" for t in TEMAS_GRAMATICA)
    + "\n\nOBRAS DE LECTURA OBLIGATORIA (cuando la pregunta trata un fragmento de una de estas "
    "obras, identifícala por el título o autor citado):\n"
    + "\n".join(f"- {t}" for t in TEMAS_OBRAS)
    + "\n\nTEMAS DE HISTORIA DE LA LITERATURA (cuando la pregunta pide desarrollar la trayectoria "
    "de un autor o las características de un movimiento; identifícalo por el autor/movimiento "
    "citado):\n"
    + "\n".join(f"- {t}" for t in TEMAS_LITERATURA)
    + "\n\nIdentifica TODOS los temas realmente tratados entre los apartados de la pregunta, "
    "eligiendo cada uno EXACTAMENTE como está escrito arriba. No inventes temas fuera de estas "
    "listas. Estas listas son del currículo 2025-2026; preguntas de años anteriores (2020-2024) "
    "pueden tratar obras o autores que ya no están en la lista actual (p.ej. el Romanticismo, u "
    "otras obras de lectura) - en ese caso, para ESE apartado en concreto, no incluyas ningún tema "
    "que no encaje razonablemente bien; si NINGÚN apartado de la pregunta encaja, devuelve "
    "únicamente \"sin_clasificar\"."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra los temas detectados para esta pregunta.",
    "input_schema": {
        "type": "object",
        "properties": {
            "temas": {
                "type": "array",
                "items": {"type": "string", "enum": TEMAS_CASTELLANO + ["sin_clasificar"]},
            }
        },
        "required": ["temas"],
        "additionalProperties": False,
    },
    "strict": True,
}


def main():
    files = sorted(glob.glob("vault/castelan/*/*/*.md"))
    targets = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm, body = text.split("---", 2)[1], text.split("---", 2)[2]
        meta = yaml.safe_load(fm)
        apartados_text = "\n".join(meta.get("apartados") or [])
        full_text = (body.strip() + "\n" + apartados_text)[:3000]
        custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.replace("\\", "/").replace("vault/castelan/", "cast_").replace("/", "_").replace(".md", ""))
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

    with open("script/classify_castellano_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_castellano_batch_id.txt", "w") as f:
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
