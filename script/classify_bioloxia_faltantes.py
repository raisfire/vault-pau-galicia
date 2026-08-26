# -*- coding: utf-8 -*-
"""Clasifica las preguntas de vault/bioloxia/ que quedaron con tema: []
(2020-2024, LOMCE: nunca se incluyeron en la Fase 1c original, que solo
cubrió física y química). Mismo patrón ya usado en el resto de
asignaturas esta sesión: Haiku 4.5 + Batch API + prompt caching, contra
la lista cerrada de 6 bloques ya usada en 2025-2026.

El bloque LOMCE antiguo a veces fusiona dos bloques actuales en un solo
encabezado ("EL MUNDO DE LOS MICROORGANISMOS...BIOTECNOLOGÍA...EL SISTEMA
INMUNITARIO...INMUNOLOGÍA"), así que hace falta leer el contenido real de
la pregunta para decidir entre los dos, no basta con el encabezado -
por eso se usa clasificación por IA y no una regla determinista."""
import glob
import json
import os
import re

import anthropic
import yaml
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

TEMAS_BIOLOXIA = [
    "LA BASE MOLECULAR DE LA MATERIA VIVA",
    "LA CÉLULA",
    "METABOLISMO CELULAR",
    "GENÉTICA MOLECULAR",
    "BIOTECNOLOGÍA",
    "INMUNOLOGÍA",
]

SYSTEM = (
    "Eres un clasificador temático para preguntas de examen ABAU/PAU de Biología (Galicia, "
    "España), de exámenes históricos 2020-2024 (currículo LOMCE, con un temario de bloques "
    "ligeramente distinto al actual). Se te da el enunciado completo de una pregunta (puede tener "
    "varios apartados). Elige uno o, si combina claramente dos áreas distintas, dos temas de esta "
    "lista cerrada, tal cual están escritos:\n\n"
    + "\n".join(f"- {t}" for t in TEMAS_BIOLOXIA)
    + "\n\nOJO: el bloque antiguo \"El mundo de los microorganismos y sus aplicaciones. "
    "Biotecnología. El sistema inmunitario. La inmunología y sus aplicaciones\" combinaba lo que "
    "ahora son dos temas separados (BIOTECNOLOGÍA e INMUNOLOGÍA) - lee el contenido real de la "
    "pregunta para decidir cuál de los dos encaja mejor, no asumas ambos solo por el encabezado. "
    "No inventes temas fuera de la lista. Si no tienes confianza razonable, responde solo "
    "\"sin_clasificar\"."
)

TOOL = {
    "name": "clasificar_tema",
    "description": "Registra el/los tema(s) clasificados para esta pregunta.",
    "input_schema": {
        "type": "object",
        "properties": {
            "temas": {
                "type": "array",
                "items": {"type": "string", "enum": TEMAS_BIOLOXIA + ["sin_clasificar"]},
            }
        },
        "required": ["temas"],
        "additionalProperties": False,
    },
    "strict": True,
}


def main():
    files = sorted(glob.glob("vault/bioloxia/*/*/*.md"))
    targets = []
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm, body = text.split("---", 2)[1], text.split("---", 2)[2]
        meta = yaml.safe_load(fm)
        if meta.get("tema"):
            continue  # ya clasificada
        apartados_text = "\n".join(meta.get("apartados") or [])
        full_text = (body.strip() + "\n" + apartados_text)[:3000]
        custom_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.replace("\\", "/").replace("vault/bioloxia/", "bio_").replace("/", "_").replace(".md", ""))
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

    with open("script/classify_bioloxia_faltantes_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")
    with open("script/classify_bioloxia_faltantes_batch_id.txt", "w") as f:
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
