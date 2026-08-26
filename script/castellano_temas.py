# -*- coding: utf-8 -*-
"""Lista cerrada de temas para Lingua Castelá e Literatura II (currículo
2025-2026), traducida/adaptada de la "Circular informativa" y
"Contidos, orientacións e criterios de corrección" oficiales de la CIUG
(https://ciug.gal/pau/lingualiteraturacastela). A diferencia de Historia
o Filosofía, esta asignatura mezcla una destreza fija (comentario de
texto, sin lista cerrada) con tres listas cerradas de contenido:
reflexión lingüística (8 items), obra de lectura obligatoria (4 obras) e
historia de la literatura (11 temas)."""

TEMA_COMENTARIO = "Comentario de texto"

TEMAS_GRAMATICA = [
    "Creación de palabras: composición, derivación, parasíntesis y acronimia",
    "Clases de palabras",
    "Formas verbales y perífrasis verbales",
    "Clases de sintagmas o frases y sus constituyentes",
    "Funciones sintácticas primarias de la cláusula u oración",
    "Relaciones entre estructuras sintácticas (coordinación, subordinación)",
    "Relaciones léxico-semánticas: sinonimia, antonimia, hiperonimia, campo léxico y semántico",
    "Detección y corrección de errores o estructuras agramaticales",
]

TEMAS_OBRAS = [
    "La Fundación (Antonio Buero Vallejo)",
    "Crónica de una muerte anunciada (Gabriel García Márquez)",
    "Romancero gitano (Federico García Lorca)",
    "El lector de Julio Verne (Almudena Grandes)",
]

TEMAS_LITERATURA = [
    "Realismo y naturalismo: Galdós, Clarín y Pardo Bazán",
    "El Modernismo: Rubén Darío y Delmira Agustini",
    "La novela de la generación del 98: Baroja, Unamuno y Azorín",
    "Las trayectorias poéticas de Antonio Machado y Juan Ramón Jiménez",
    "La generación del 27: Salinas, Lorca, Alberti y Cernuda",
    "El teatro español anterior a la Guerra Civil: Lorca y Valle-Inclán",
    "La poesía española posterior a la Guerra Civil: Miguel Hernández, Blas de Otero, Gil de Biedma y Gloria Fuertes",
    "La novela española posterior a la Guerra Civil: Delibes, Cela, Laforet y Martín Santos",
    "Buero Vallejo y Alfonso Sastre en el teatro español posterior a la Guerra Civil",
    "La narrativa hispanoamericana de la segunda mitad del siglo XX: Borges, Cortázar, García Márquez y Vargas Llosa",
    "La narrativa peninsular desde 1975: Almudena Grandes, Muñoz Molina, Mendoza y Rosa Montero",
]

TEMAS_CASTELLANO = [TEMA_COMENTARIO] + TEMAS_GRAMATICA + TEMAS_OBRAS + TEMAS_LITERATURA
