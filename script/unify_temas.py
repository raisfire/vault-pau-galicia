# -*- coding: utf-8 -*-
"""Unifica variantes de 'tema' en todo el vault y convierte el campo a lista
(YAML), separando etiquetas compuestas tema1/tema2 en dos temas reales en
vez de dejarlas como una sola cadena mixta."""
import glob
import re

FISICA_MAP = {
    "FÍSICA DEL SIGLO XX": "FÍSICA DEL SIGLO XX",
    "Física del siglo XX. Responda indicando y justificando la opción correcta": "FÍSICA DEL SIGLO XX",
    "FÍSICA DO SÉCULO XX": "FÍSICA DEL SIGLO XX",
    "Problema de física del siglo XX": "FÍSICA DEL SIGLO XX",
    "Problema de Física del siglo XX": "FÍSICA DEL SIGLO XX",
    "Práctica de Física del siglo XX": "FÍSICA DEL SIGLO XX",
    "INTERACCIÓN ELECTROMAGNÉTICA": "INTERACCIÓN ELECTROMAGNÉTICA",
    "Interacción electromagnética. Responda indicando y justificando la opción correcta": "INTERACCIÓN ELECTROMAGNÉTICA",
    "Problema de interacción electromagnética": "INTERACCIÓN ELECTROMAGNÉTICA",
    "INTERACCIÓN GRAVITATORIA": "INTERACCIÓN GRAVITATORIA",
    "Interacción gravitatoria. Responda indicando y justificando la opción correcta": "INTERACCIÓN GRAVITATORIA",
    "Problema de interacción gravitatoria": "INTERACCIÓN GRAVITATORIA",
    "Práctica de interacción gravitatoria": "INTERACCIÓN GRAVITATORIA",
    "ONDAS Y ÓPTICA GEOMÉTRICA": "ONDAS Y ÓPTICA GEOMÉTRICA",
    "Ondas y óptica geométrica. Responda indicando y justificando la opción correcta": "ONDAS Y ÓPTICA GEOMÉTRICA",
    "Problema de ondas y óptica geométrica": "ONDAS Y ÓPTICA GEOMÉTRICA",
}

QUIMICA_ATOMS = {
    "DESTREZAS BÁSICAS DE LA QUÍMICA": "DESTREZAS BÁSICAS DE LA QUÍMICA",
    "REACCIONES QUÍMICAS": "REACCIONES QUÍMICAS",
    "ENLACE QUÍMICO Y ESTRUCTURA DE LA MATERIA": "ENLACE QUÍMICO Y ESTRUCTURA DE LA MATERIA",
    "QUÍMICA ORGÁNICA": "QUÍMICA ORGÁNICA",
}

BIOLOXIA_ATOMS = {
    "LA CÉLULA": "LA CÉLULA",
    "A CÉLULA": "LA CÉLULA",
    "BIOTECNOLOGÍA": "BIOTECNOLOGÍA",
    "BIOTECNOLOXÍA": "BIOTECNOLOGÍA",
    "GENÉTICA MOLECULAR": "GENÉTICA MOLECULAR",
    "METABOLISMO CELULAR": "METABOLISMO CELULAR",
    "LA BASE MOLECULAR DE LA MATERIA VIVA": "LA BASE MOLECULAR DE LA MATERIA VIVA",
    "INMUNOLOGÍA": "INMUNOLOGÍA",
}
# la única variante bioloxia que no es un compuesto "A. B" limpio
BIOLOXIA_SPECIAL = {
    "La BASE MOLECULAR Y FISÍCOQUÍMICA DE LA VIDA": ["LA BASE MOLECULAR DE LA MATERIA VIVA"],
}

MATE_ATOMS = {
    "Análisis": "Análisis",
    "Estadística y Probabilidad": "Estadística y Probabilidad",
    "Geometría": "Geometría",
    "Números y Álgebra": "Números y Álgebra",
}

# temas basura conocidos (dígitos sueltos de una extracción fallida en Química)
GARBAGE = {"1", "3", "8"}


def resolve_temas(subject, raw):
    raw = (raw or "").strip()
    if raw == "" or raw in GARBAGE:
        return []

    if subject == "fisica":
        canon = FISICA_MAP.get(raw)
        if canon is None:
            raise ValueError(f"tema de fisica sin mapear: {raw!r}")
        return [canon]

    if subject == "matematicas_ii":
        canon = MATE_ATOMS.get(raw)
        if canon is None:
            raise ValueError(f"tema de matematicas_ii sin mapear: {raw!r}")
        return [canon]

    if subject == "quimica":
        parts = [p.strip() for p in raw.split("/")]
        out = []
        for p in parts:
            canon = QUIMICA_ATOMS.get(p)
            if canon is None:
                raise ValueError(f"tema de quimica sin mapear: {p!r} (de {raw!r})")
            if canon not in out:
                out.append(canon)
        return out

    if subject == "bioloxia":
        if raw in BIOLOXIA_SPECIAL:
            return BIOLOXIA_SPECIAL[raw]
        parts = [p.strip() for p in raw.split(".") if p.strip()]
        out = []
        for p in parts:
            canon = BIOLOXIA_ATOMS.get(p)
            if canon is None:
                raise ValueError(f"tema de bioloxia sin mapear: {p!r} (de {raw!r})")
            if canon not in out:
                out.append(canon)
        return out

    raise ValueError(f"asignatura desconocida: {subject}")


def yaml_tema_block(temas):
    if not temas:
        return "tema: []"
    lines = ["tema:"]
    for t in temas:
        escaped = t.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'  - "{escaped}"')
    return "\n".join(lines)


TEMA_LINE_RE = re.compile(r'^tema: "[^"]*"$', re.MULTILINE)


def main():
    files = sorted(glob.glob("vault/*/*/*/*.md"))
    changed = 0
    errors = []
    for path in files:
        subject = path.replace("\\", "/").split("/")[1]
        text = open(path, encoding="utf-8").read()
        m = TEMA_LINE_RE.search(text)
        if not m:
            errors.append((path, "no se encontró una línea 'tema: \"...\"'"))
            continue
        raw = re.match(r'^tema: "([^"]*)"$', m.group(0)).group(1)
        try:
            temas = resolve_temas(subject, raw)
        except ValueError as e:
            errors.append((path, str(e)))
            continue
        new_block = yaml_tema_block(temas)
        if new_block != m.group(0):
            text = text[: m.start()] + new_block + text[m.end() :]
            open(path, "w", encoding="utf-8").write(text)
            changed += 1

    print(f"Archivos cambiados: {changed}")
    print(f"Errores: {len(errors)}")
    for p, e in errors:
        print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
