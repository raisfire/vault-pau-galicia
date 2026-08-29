# -*- coding: utf-8 -*-
"""Arregla el hueco determinista de Matemáticas II: 16 preguntas del examen
2022 (ambas convocatorias) traen el tema como texto plano en la primera
línea del enunciado ("1. Números y Álgebra", etc.) pero nunca se copió al
campo tema: - no hace falta IA, solo extraer y mapear contra la lista
cerrada."""
import glob
import re
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8")

CANON = ["Análisis", "Geometría", "Números y Álgebra", "Estadística y Probabilidad"]


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return '"' + s + '"'


def main():
    files = sorted(glob.glob("vault/matematicas_ii/*/*/*.md"))
    fixed = 0
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm = text.split("---", 2)[1]
        meta = yaml.safe_load(fm)
        if meta.get("tema"):
            continue
        body = text.split("---", 2)[2]
        first_line = body.strip().split("\n")[0].strip()
        m = re.match(r"^\d+\.\s*(.+)$", first_line)
        if not m:
            print("NO MATCH regex:", path, repr(first_line))
            continue
        candidate = m.group(1).strip()
        if candidate not in CANON:
            print("NO MATCH canon:", path, repr(candidate))
            continue
        block = "tema:\n  - " + yaml_escape(candidate) + "\n"
        new_text = re.sub(r"^tema: \[\]\n", block, text, count=1, flags=re.MULTILINE)
        if new_text == text:
            print("REGEX DID NOT APPLY (formato tema: inesperado):", path)
            continue
        open(path, "w", encoding="utf-8").write(new_text)
        fixed += 1

    print("\nArreglados:", fixed, "/ 16")


if __name__ == "__main__":
    main()
