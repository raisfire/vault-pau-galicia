# -*- coding: utf-8 -*-
"""Fase 1c: clasifica el campo 'tema' de preguntas de Fisica/Quimica 2020-2024
sin tema, usando Haiku 4.5 via Batch API con prompt caching."""
import glob
import json
import os
import re
import time

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

# --- cargar API key desde .env ---
with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()

MODEL = "claude-haiku-4-5"

TEMAS = {
    "fisica": [
        "FÍSICA DEL SIGLO XX",
        "FÍSICA DO SÉCULO XX",
        "INTERACCIÓN ELECTROMAGNÉTICA",
        "INTERACCIÓN GRAVITATORIA",
        "ONDAS Y ÓPTICA GEOMÉTRICA",
    ],
    "quimica": [
        "DESTREZAS BÁSICAS DE LA QUÍMICA",
        "REACCIONES QUÍMICAS",
        "ENLACE QUÍMICO Y ESTRUCTURA DE LA MATERIA",
        "QUÍMICA ORGÁNICA",
    ],
}

SUBJECT_LABEL = {"fisica": "Física", "quimica": "Química"}


def build_system(subject):
    temas_list = "\n".join(f"- {t}" for t in TEMAS[subject])
    return (
        f"Eres un clasificador temático para preguntas de examen ABAU/PAU de {SUBJECT_LABEL[subject]} "
        f"(Galicia, España). Se te da el enunciado completo de una pregunta (puede incluir varios "
        f"apartados). Debes elegir EXACTAMENTE UNO de los siguientes temas, tal cual está escrito, "
        f"según el contenido real de la pregunta:\n\n{temas_list}\n\n"
        "No inventes un tema fuera de esta lista. Si el contenido no encaja con confianza razonable "
        "en ninguno de ellos, o la pregunta es ambigua, responde exactamente \"sin_clasificar\" en vez "
        "de forzar una respuesta."
    )


def collect_targets():
    targets = []
    for subject in ["fisica", "quimica"]:
        for year in range(2020, 2025):
            for path in sorted(glob.glob(f"vault/{subject}/{year}/*/*.md")):
                text = open(path, encoding="utf-8").read()
                m = re.search(r'tema: "([^"]*)"', text)
                tema = m.group(1) if m else ""
                if tema.strip() == "":
                    body = text.split("---", 2)[2].strip()
                    custom_id = path.replace("vault/", "").replace("\\", "/").replace("/", "__").replace(".md", "")
                    targets.append({"path": path, "subject": subject, "body": body, "custom_id": custom_id})
    return targets


def build_tool(subject):
    return {
        "name": "clasificar_tema",
        "description": "Registra el tema clasificado para esta pregunta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tema": {
                    "type": "string",
                    "enum": TEMAS[subject] + ["sin_clasificar"],
                }
            },
            "required": ["tema"],
            "additionalProperties": False,
        },
        "strict": True,
    }


def main():
    targets = collect_targets()
    print(f"Total preguntas a clasificar: {len(targets)}")

    system_cache = {
        subject: [
            {
                "type": "text",
                "text": build_system(subject),
                "cache_control": {"type": "ephemeral"},
            }
        ]
        for subject in ["fisica", "quimica"]
    }
    tool_cache = {subject: build_tool(subject) for subject in ["fisica", "quimica"]}

    batch_requests = []
    for t in targets:
        subject = t["subject"]
        params = MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=256,
            system=system_cache[subject],
            tools=[tool_cache[subject]],
            tool_choice={"type": "tool", "name": "clasificar_tema"},
            messages=[{"role": "user", "content": t["body"]}],
        )
        batch_requests.append(Request(custom_id=t["custom_id"], params=params))

    print("Enviando lote a la Batch API...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch id: {batch.id}, status: {batch.processing_status}")

    with open("script/fase1c_batch_id.txt", "w") as f:
        f.write(batch.id)

    # save target mapping for later processing
    with open("script/fase1c_targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)

    # poll
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        print(f"status: {batch.processing_status}, counts: {batch.request_counts}")
        if batch.processing_status == "ended":
            break
        time.sleep(10)

    print("Batch terminado. Descargando resultados...")


if __name__ == "__main__":
    main()
