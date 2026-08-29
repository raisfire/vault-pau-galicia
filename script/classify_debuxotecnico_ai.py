# -*- coding: utf-8 -*-
"""Clasifica con IA las preguntas de Debuxo Técnico que extract_debuxotecnico_stats.py
no pudo resolver por palabra clave (el enunciado no nombra el bloque
explícitamente, va directo a la instrucción de dibujo: "Debuxe as
circunferencias tanxentes...", "Determine a verdadeira magnitude..."). Son
pocas (~26) y el texto es corto, así que se resuelven con llamadas
directas (sin Batch API - el volumen no lo justifica), con tope de gasto
visible antes de lanzar."""
import json
import os

import anthropic

from debuxotecnico_temas import TEMAS_DEBUXOTECNICO

with open(".env", encoding="utf-8") as f:
    for line in f:
        if line.startswith("CLAVE_API_CLAUDE="):
            os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]
            break

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5"

SYSTEM = (
    "Eres un clasificador temático para preguntas de examen ABAU/PAU de Debuxo "
    "Técnico II (Galicia, España). Se te da el enunciado de una pregunta que "
    "pide construir o resolver un dibujo técnico (la figura que acompaña no se "
    "te muestra, solo el texto). Aunque el enunciado no nombre el bloque "
    "explícitamente, elige el que mejor encaje según qué pide construir, "
    "usando esta lista cerrada de bloques oficiales:\n\n"
    "- FUNDAMENTOS GEOMÉTRICOS: xeometría plana básica - tangencias, "
    "circunferencias, homología/afinidad, curvas cónicas (elipse, hipérbola, "
    "parábola), construcciones de polígonos/triángulos por datos angulares, "
    "arco capaz, potencia.\n"
    "- SISTEMA DIÉDRICO: hallar la verdadera magnitud, proyecciones, "
    "abatimientos, giros o cambios de plano de puntos/rectas/figuras/sólidos "
    "dados por sus proyecciones diédricas, intersecciones y secciones planas "
    "de poliedros en diédrico.\n"
    "- SISTEMA DIÉDRICO / SISTEMA AXONOMÉTRICO: pide EXPLÍCITAMENTE pasar de "
    "proyecciones diédricas a una perspectiva/isometría axonométrica (o al "
    "revés) como resultado final del ejercicio.\n"
    "- NORMALIZACIÓN Y DOCUMENTACIÓN GRÁFICA DE PROYECTOS: dado un objeto o "
    "pieza en perspectiva/axonometría (no en diédrico), dibujar sus vistas "
    "normalizadas (planta, alzado, perfil), bosquejos a mano alzada de vistas, "
    "acotación de piezas, o diseño/dimensionado de un objeto cotidiano (un "
    "mueble, un objeto de uso).\n\n"
    "Responde con el tema que mejor encaje. Si de verdad no hay información "
    "suficiente para decidir, responde \"sin_clasificar\"."
)


def build_tool():
    return {
        "name": "clasificar_tema",
        "description": "Registra el tema clasificado para esta pregunta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tema": {"type": "string", "enum": TEMAS_DEBUXOTECNICO + ["sin_clasificar"]}
            },
            "required": ["tema"],
            "additionalProperties": False,
        },
        "strict": True,
    }


def main():
    records = json.load(open("script/stats_debuxotecnico_raw.json", encoding="utf-8"))
    pendientes = [r for r in records if not r["temas"]]
    print(f"Preguntas a clasificar con IA: {len(pendientes)}")
    # coste estimado: Haiku 4.5 sin cache, ~350 tokens entrada + 300 max salida
    # por pregunta -> muy por debajo de 0.01$ para 26 preguntas
    est = len(pendientes) * (350 / 1e6 * 1.0 + 100 / 1e6 * 5.0)
    print(f"Coste estimado: ${est:.4f}")

    tool = build_tool()
    total_input = total_output = 0
    clasificadas = 0
    sin_clasificar = 0

    for r in pendientes:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=SYSTEM,
            tools=[tool],
            tool_choice={"type": "tool", "name": "clasificar_tema"},
            messages=[{"role": "user", "content": r["texto"]}],
        )
        total_input += msg.usage.input_tokens
        total_output += msg.usage.output_tokens
        tool_use = next((b for b in msg.content if b.type == "tool_use"), None)
        tema = tool_use.input.get("tema") if tool_use else None
        if not tema or tema == "sin_clasificar":
            sin_clasificar += 1
            r["temas"] = []
        else:
            clasificadas += 1
            r["temas"] = [tema]

    cost = total_input / 1e6 * 1.0 + total_output / 1e6 * 5.0
    print(f"\nClasificadas: {clasificadas}")
    print(f"Sin clasificar: {sin_clasificar}")
    print(f"Coste real: ${cost:.4f}")

    with open("script/stats_debuxotecnico.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)
    print("\nGuardado script/stats_debuxotecnico.json")


if __name__ == "__main__":
    main()
