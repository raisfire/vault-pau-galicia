# -*- coding: utf-8 -*-
"""Inglés no tiene un temario de contenidos cerrado como Historia/Filosofía
(es un examen de idioma: la misma prueba evalúa varias destrezas
lingüísticas sobre un texto o consigna que cambia cada año, así que el
"tema" con sentido aquí es el TIPO DE DESTREZA/EJERCICIO, no un contenido
curricular). La detección es 100% determinista por palabras clave del
propio enunciado - no hace falta IA ni tiene coste."""
import re

TEMAS_INGLES = [
    "Comprensión lectora",
    "Gramática y transformación de frases",
    "Pronunciación",
    "Vocabulario",
    "Writing / Composición",
    "Listening",
]

_RULES = [
    ("Comprensión lectora", re.compile(
        r"true.{0,15}false|true or false|not given|summary of the text|"
        r"find (a )?words? or phrases?|synonym|antonym|read the text|"
        r"answer the following questions in your own words",
        re.IGNORECASE)),
    ("Gramática y transformación de frases", re.compile(
        r"write a new sentence|complete the second sentence",
        re.IGNORECASE)),
    ("Pronunciación", re.compile(
        r"pronunciation|pronounced|\brhyme\b|homophone|\bstress\b|syllable",
        re.IGNORECASE)),
    ("Vocabulario", re.compile(
        r"fill (each|in) the gap|word taken from the box|fill each one of the gaps",
        re.IGNORECASE)),
    ("Writing / Composición", re.compile(
        r"write a composition|write an e-?mail|write an opinion|write an article|"
        r"write a blog",
        re.IGNORECASE)),
    ("Listening", re.compile(r"listening test|listening comprehension", re.IGNORECASE)),
]


def classify_by_keywords(text):
    found = []
    for tema, pattern in _RULES:
        if pattern.search(text) and tema not in found:
            found.append(tema)
    return found
