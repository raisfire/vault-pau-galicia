# -*- coding: utf-8 -*-
"""Lista cerrada de temas para Lingua Galega e Literatura II (currículo
2025-2026), tomada de la "Primeira circular" oficial de la CIUG
(https://ciug.gal/pau/lingualiteraturagalega). Igual que en castellano,
mezcla una destreza fija (comunicación/comprensión textual) con tres
listas cerradas de contenido: reflexión sobre a lingua (8 items), a
lingua e os seus falantes (4 items) e educación literaria. A diferencia
de castellano, el currículo NO fija autores/obras concretas para
literatura, solo 3 grandes períodos - así que se usan esos 3 períodos en
vez de una lista de autores."""

TEMA_COMUNICACION = "Comunicación"

TEMAS_GRAMATICA = [
    "Fonética e fonoloxía da lingua galega",
    "Clases de palabras",
    "Creación de palabras: composición, derivación, parasíntese e acronimia",
    "Formas verbais e perífrases",
    "Sintagmas ou frases, os seus constituíntes e as súas funcións",
    "Funcións primarias da cláusula ou oración (suxeito, predicado, complementos)",
    "Relacións entre estruturas sintácticas",
    "Relacións léxico-semánticas: sinonimia, antonimia, hiperonimia, hiponimia e campo semántico",
]

TEMAS_LINGUA_FALANTES = [
    "As linguas da Península Ibérica",
    "As variedades dialectais do galego",
    "A variedade estándar, os sociolectos e os rexistros de lingua",
    "Os prexuízos e estereotipos lingüísticos",
]

TEMAS_LITERATURA = [
    "A literatura galega no primeiro terzo do século XX (1916-1936)",
    "A literatura galega entre 1936 e 1975",
    "A literatura galega de fins do século XX e comezos do XXI",
]

TEMAS_GALEGO = [TEMA_COMUNICACION] + TEMAS_GRAMATICA + TEMAS_LINGUA_FALANTES + TEMAS_LITERATURA
