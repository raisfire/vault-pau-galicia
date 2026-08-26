# -*- coding: utf-8 -*-
"""Procesa los 3 batches de classify_stem_finegrained_2010_2019.py y
sobrescribe script/stats_2010_2019.json para bioloxia/fisica/quimica
(mantiene matematicas_ii tal cual estaba, fuera de alcance de este
pase)."""
import json
import os

import anthropic

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()

all_targets = json.load(open("script/classify_stem_finegrained_2010_2019_targets.json", encoding="utf-8"))
batch_ids = json.load(open("script/classify_stem_finegrained_2010_2019_batch_ids.json", encoding="utf-8"))

old_data = json.load(open("script/stats_2010_2019.json", encoding="utf-8"))
kept = [r for r in old_data if r["subject"] == "matematicas_ii"]

total_cost = 0.0
new_records = []

for subject, batch_id in batch_ids.items():
    targets = {t["custom_id"]: t for t in all_targets[subject]}

    clasificadas = 0
    sin_clasificar = 0
    errores = []
    total_input = total_output = total_cache_write = total_cache_read = 0

    for result in client.messages.batches.results(batch_id):
        t = targets.get(result.custom_id)
        if t is None:
            errores.append((result.custom_id, "target no encontrado"))
            continue
        if result.result.type != "succeeded":
            errores.append((result.custom_id, result.result.type))
            continue

        msg = result.result.message
        usage = msg.usage
        total_input += usage.input_tokens
        total_output += usage.output_tokens
        total_cache_write += getattr(usage, "cache_creation_input_tokens", 0) or 0
        total_cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0

        tool_use = next((b for b in msg.content if b.type == "tool_use"), None)
        if tool_use is None:
            errores.append((result.custom_id, "sin tool_use"))
            continue

        temas = tool_use.input.get("temas", [])
        if not isinstance(temas, list):
            errores.append((result.custom_id, f"temas no es una lista: {temas!r}"))
            continue
        if not temas or temas == ["sin_clasificar"]:
            sin_clasificar += 1
        else:
            clasificadas += 1

        new_records.append({
            "subject": subject,
            "year": t["year"],
            "conv": t["conv"],
            "temas": temas,
        })

    cost = (
        total_input / 1e6 * 0.50
        + total_output / 1e6 * 2.50
        + total_cache_write / 1e6 * 0.625
        + total_cache_read / 1e6 * 0.05
    )
    total_cost += cost

    print(f"=== {subject} ===")
    print(f"Clasificadas: {clasificadas}")
    print(f"Sin clasificar: {sin_clasificar}")
    print(f"Errores: {len(errores)}")
    for cid, e in errores:
        print(" ", cid, e)
    print(f"Coste: ${cost:.4f}\n")

print(f"Coste total: ${total_cost:.4f}")

final_data = kept + new_records
json.dump(final_data, open("script/stats_2010_2019.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nscript/stats_2010_2019.json actualizado: {len(final_data)} registros ({len(kept)} matematicas_ii sin tocar + {len(new_records)} nuevos)")
