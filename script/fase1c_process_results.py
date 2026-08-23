# -*- coding: utf-8 -*-
"""Procesa los resultados del batch de Fase 1c y actualiza el frontmatter."""
import json
import os

import anthropic

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()

with open("script/fase1c_batch_id.txt") as f:
    batch_id = f.read().strip()

with open("script/fase1c_targets.json", encoding="utf-8") as f:
    targets = {t["custom_id"]: t for t in json.load(f)}

sin_clasificar = []
clasificadas = []
errores = []

total_input = 0
total_output = 0
total_cache_write = 0
total_cache_read = 0

for result in client.messages.batches.results(batch_id):
    custom_id = result.custom_id
    t = targets.get(custom_id)
    if t is None:
        errores.append((custom_id, "target no encontrado"))
        continue

    if result.result.type != "succeeded":
        errores.append((custom_id, f"{result.result.type}"))
        continue

    msg = result.result.message
    usage = msg.usage
    total_input += usage.input_tokens
    total_output += usage.output_tokens
    total_cache_write += getattr(usage, "cache_creation_input_tokens", 0) or 0
    total_cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0

    tool_use = next((b for b in msg.content if b.type == "tool_use"), None)
    if tool_use is None:
        errores.append((custom_id, "sin tool_use en la respuesta"))
        continue

    tema = tool_use.input.get("tema", "")
    path = t["path"]

    file_text = open(path, encoding="utf-8").read()
    escaped_tema = tema.replace('"', '\\"')
    new_text = file_text.replace(
        'tema: ""',
        f'tema: "{escaped_tema}"\ntema_fuente: "ia"',
        1,
    )
    if new_text == file_text:
        errores.append((custom_id, "no se encontro tema: \"\" en el frontmatter"))
        continue

    open(path, "w", encoding="utf-8").write(new_text)

    if tema == "sin_clasificar":
        sin_clasificar.append(path)
    else:
        clasificadas.append((path, tema))

# batch pricing for Haiku 4.5: input $0.50/1M, output $2.50/1M,
# cache write $0.625/1M, cache read $0.05/1M
cost = (
    total_input / 1e6 * 0.50
    + total_output / 1e6 * 2.50
    + total_cache_write / 1e6 * 0.625
    + total_cache_read / 1e6 * 0.05
)

print(f"Clasificadas con tema real: {len(clasificadas)}")
print(f"Sin clasificar: {len(sin_clasificar)}")
for p in sin_clasificar:
    print("  ", p)
print(f"Errores: {len(errores)}")
for c, e in errores:
    print("  ", c, e)

print(f"\nTokens: input={total_input} output={total_output} cache_write={total_cache_write} cache_read={total_cache_read}")
print(f"Coste real estimado: ${cost:.4f}")

with open("script/fase1c_summary.json", "w", encoding="utf-8") as f:
    json.dump({
        "clasificadas": clasificadas,
        "sin_clasificar": sin_clasificar,
        "errores": errores,
        "cost": cost,
        "tokens": {
            "input": total_input, "output": total_output,
            "cache_write": total_cache_write, "cache_read": total_cache_read,
        },
    }, f, ensure_ascii=False, indent=2)
