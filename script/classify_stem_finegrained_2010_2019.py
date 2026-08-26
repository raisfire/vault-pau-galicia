# -*- coding: utf-8 -*-
"""Reclasifica el backfill estadístico 2010-2019 de bioloxia/fisica/quimica
contra las nuevas listas de grano fino, reutilizando la extracción ya
hecha en extract_2010_2019.py (script/extracted_2010_2019.json) - no
hace falta releer los PDF. Matemáticas II NO se toca (fuera de alcance
de este pase)."""
import json
import os
import re
import sys

import anthropic
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
        "España), de exámenes históricos 2010-2019 (anteriores al currículo actual). Se te da el "
        "enunciado completo de una pregunta. Elige uno o, si combina claramente dos áreas "
        f"distintas, dos temas de esta lista cerrada, tal cual están escritos:\n\n{temas_list}\n\n"
        "No inventes temas fuera de la lista. Como estos exámenes son de un currículo anterior, es "
        "normal que la terminología o agrupación de contenidos sea distinta - elige el tema de la "
        "lista actual que mejor encaje con el contenido real de la pregunta. Si no tienes "
        "confianza razonable, responde solo \"sin_clasificar\"."
    )


def build_tool(temas):
    return {
        "name": "clasificar_tema",
        "description": "Registra el/los tema(s) clasificados para esta pregunta.",
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
    data = json.load(open("script/extracted_2010_2019.json", encoding="utf-8"))

    all_targets = {s: [] for s in SUBJECTS}
    for r in data:
        if r["status"] != "ok" or r["subject"] not in SUBJECTS:
            continue
        for i, q in enumerate(r["questions"]):
            custom_id = f"{r['subject'][:3]}1019__{r['year']}__{r['conv']}__q{i}"
            custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", custom_id)[:64]
            all_targets[r["subject"]].append({
                "custom_id": custom_id,
                "year": r["year"],
                "conv": r["conv"],
                "texto": q["texto"][:1500],
            })

    for subject, targets in all_targets.items():
        seen = {}
        for t in targets:
            base = t["custom_id"]
            n = seen.get(base, 0)
            seen[base] = n + 1
            if n:
                t["custom_id"] = f"{base}_{n}"
        print(f"{subject}: {len(targets)} opciones a clasificar")

    with open("script/classify_stem_finegrained_2010_2019_targets.json", "w", encoding="utf-8") as f:
        json.dump(all_targets, f, ensure_ascii=False)

    batch_ids = {}
    for subject, (label, temas) in SUBJECTS.items():
        targets = all_targets[subject]
        system_cached = [{"type": "text", "text": build_system(label, temas), "cache_control": {"type": "ephemeral"}}]
        tool = build_tool(temas)

        batch_requests = []
        for t in targets:
            params = MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=300,
                system=system_cached,
                tools=[tool],
                tool_choice={"type": "tool", "name": "clasificar_tema"},
                messages=[{"role": "user", "content": t["texto"]}],
            )
            batch_requests.append(Request(custom_id=t["custom_id"], params=params))

        batch = client.messages.batches.create(requests=batch_requests)
        print(f"  {subject} batch id: {batch.id}, status: {batch.processing_status}")
        batch_ids[subject] = batch.id

    with open("script/classify_stem_finegrained_2010_2019_batch_ids.json", "w", encoding="utf-8") as f:
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
