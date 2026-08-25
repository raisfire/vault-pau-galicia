# -*- coding: utf-8 -*-
"""Procesa los resultados del batch de clasificacion 2010-2019 y
construye script/stats_2010_2019.json (solo temas + metadatos, sin
texto, no toca vault/)."""
import json
import os

import anthropic

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()

batch_id = open("script/classify_2010_2019_batch_id.txt").read().strip()
targets = {t["custom_id"]: t for t in json.load(open("script/classify_2010_2019_targets.json", encoding="utf-8"))}

sin_clasificar = 0
clasificadas = 0
errores = []
total_input = total_output = total_cache_write = total_cache_read = 0

out = []
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

    temas = tool_use.input.get("temas", [])[:2]
    if not temas or temas == ["sin_clasificar"]:
        sin_clasificar += 1
    else:
        clasificadas += 1

    out.append({
        "subject": t["subject"], "year": t["year"], "conv": t["conv"],
        "temas": temas,
    })

cost = (
    total_input / 1e6 * 0.50
    + total_output / 1e6 * 2.50
    + total_cache_write / 1e6 * 0.625
    + total_cache_read / 1e6 * 0.05
)

print(f"Clasificadas: {clasificadas}")
print(f"Sin clasificar: {sin_clasificar}")
print(f"Errores: {len(errores)}")
for cid, e in errores[:20]:
    print(" ", cid, e)
print(f"\nCoste real: ${cost:.4f}")

with open("script/stats_2010_2019.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"\nGuardado {len(out)} registros en script/stats_2010_2019.json")
