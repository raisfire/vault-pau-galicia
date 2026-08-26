# -*- coding: utf-8 -*-
"""Reclasifica vault/{bioloxia,fisica,quimica}/ 2020-2026 contra las
nuevas listas cerradas de temas de grano fino (bioloxia_temas.py,
fisica_temas.py, quimica_temas.py), derivadas de los documentos oficiales
"Orientacións xerais" 2025-26. Sustituye a la clasificación anterior por
bloques generales (6/5/4 temas), demasiado gruesa. Mismo patrón Haiku 4.5
+ Batch API + caching usado en el resto de la sesión, un batch por
asignatura para poder usar el system prompt específico de cada una."""
import glob
import json
import os
import re
import sys

import anthropic
import yaml
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bioloxia_temas import TEMAS_BIOLOXIA
from fisica_temas import TEMAS_FISICA
from quimica_temas import TEMAS_QUIMICA

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SUBJECTS = {
    "bioloxia": ("Biología", TEMAS_BIOLOXIA),
    "fisica": ("Física", TEMAS_FISICA),
    "quimica": ("Química", TEMAS_QUIMICA),
}


def build_system(label, temas):
    temas_list = "\n".join(f"- {t}" for t in temas)
    return (
        f"Eres un clasificador temático para preguntas de examen ABAU/PAU de {label} (Galicia, "
        "España). Se te da el enunciado completo de una pregunta (puede tener varios apartados). "
        "Identifica TODOS los temas realmente tratados, eligiendo cada uno EXACTAMENTE como está "
        f"escrito en esta lista cerrada de temas oficiales (currículo 2025-2026):\n\n{temas_list}\n\n"
        "No inventes temas fuera de la lista. Preguntas de años anteriores (2020-2024, currículo "
        "LOMCE) pueden usar una terminología o agrupación de contenidos ligeramente distinta - en "
        "ese caso, elige el tema de la lista actual que mejor encaje con el contenido real de la "
        "pregunta. Si de verdad ningún tema encaja razonablemente, responde únicamente "
        "\"sin_clasificar\"."
    )


def build_tool(temas):
    return {
        "name": "clasificar_tema",
        "description": "Registra los temas detectados para esta pregunta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "temas": {
                    "type": "array",
                    "items": {"type": "string", "enum": temas + ["sin_clasificar"]},
                }
            },
            "required": ["temas"],
            "additionalProperties": False,
        },
        "strict": True,
    }


def main():
    all_targets = {}
    batch_ids = {}

    for subject, (label, temas) in SUBJECTS.items():
        files = sorted(glob.glob(f"vault/{subject}/*/*/*.md"))
        targets = []
        for path in files:
            text = open(path, encoding="utf-8").read()
            fm, body = text.split("---", 2)[1], text.split("---", 2)[2]
            meta = yaml.safe_load(fm)
            apartados_text = "\n".join(meta.get("apartados") or [])
            full_text = (body.strip() + "\n" + apartados_text)[:3000]
            custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.replace("\\", "/").replace(f"vault/{subject}/", f"{subject[:3]}_").replace("/", "_").replace(".md", ""))
            targets.append({"path": path, "custom_id": custom_id, "texto": full_text})

        print(f"{subject}: {len(targets)} preguntas a clasificar")
        all_targets[subject] = targets

        system_cached = [{"type": "text", "text": build_system(label, temas), "cache_control": {"type": "ephemeral"}}]
        tool = build_tool(temas)

        batch_requests = []
        for t in targets:
            params = MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=350,
                system=system_cached,
                tools=[tool],
                tool_choice={"type": "tool", "name": "clasificar_tema"},
                messages=[{"role": "user", "content": t["texto"]}],
            )
            batch_requests.append(Request(custom_id=t["custom_id"], params=params))

        batch = client.messages.batches.create(requests=batch_requests)
        print(f"  batch id: {batch.id}, status: {batch.processing_status}")
        batch_ids[subject] = batch.id

    with open("script/classify_stem_finegrained_targets.json", "w", encoding="utf-8") as f:
        json.dump(all_targets, f, ensure_ascii=False)
    with open("script/classify_stem_finegrained_batch_ids.json", "w", encoding="utf-8") as f:
        json.dump(batch_ids, f)

    import time
    pending = set(batch_ids.values())
    while pending:
        time.sleep(10)
        for bid in list(pending):
            b = client.messages.batches.retrieve(bid)
            print(f"  {bid}: {b.processing_status}, {b.request_counts}")
            if b.processing_status == "ended":
                pending.discard(bid)

    print("Todos los batches terminados.")


if __name__ == "__main__":
    main()
