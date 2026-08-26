# -*- coding: utf-8 -*-
"""Aplica los resultados del batch de clasificacion a los
vault/castelan/*.md (tema: [] -> tema: [...])."""
import json
import os
import re

import anthropic

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()

batch_id = open("script/classify_castellano_batch_id.txt").read().strip()
targets = {t["custom_id"]: t for t in json.load(open("script/classify_castellano_targets.json", encoding="utf-8"))}

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

    raw_temas = tool_use.input.get("temas", [])
    if not isinstance(raw_temas, list):
        errores.append((result.custom_id, f"temas no es una lista: {raw_temas!r}"))
        continue
    temas = [x for x in raw_temas if x != "sin_clasificar"]
    if not temas:
        sin_clasificar += 1
    else:
        clasificadas += 1

    path = t["path"]
    text = open(path, encoding="utf-8").read()
    if temas:
        lines = ["tema:"]
        for x in temas:
            escaped = x.replace('"', '\\"')
            lines.append(f'  - "{escaped}"')
        block = "\n".join(lines) + "\n"
    else:
        block = "tema: []\n"
    new_text = re.sub(r"^tema: \[\]\n", block, text, count=1, flags=re.MULTILINE)
    open(path, "w", encoding="utf-8").write(new_text)

cost = (
    total_input / 1e6 * 0.50
    + total_output / 1e6 * 2.50
    + total_cache_write / 1e6 * 0.625
    + total_cache_read / 1e6 * 0.05
)

print(f"Clasificadas: {clasificadas}")
print(f"Sin clasificar: {sin_clasificar}")
print(f"Errores: {len(errores)}")
for cid, e in errores:
    print(" ", cid, e)
print(f"\nCoste real: ${cost:.4f}")
