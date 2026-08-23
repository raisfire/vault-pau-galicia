# -*- coding: utf-8 -*-
"""
Fase 1b Paso 3: aplica las transcripciones/verificaciones visuales a los
70 archivos de vault/ que quedaron sin resolver tras el colapso automático
(excluyendo vault/bioloxia/2020/ordinaria/pregunta-2.md, que es un asunto
distinto ya documentado).

Cada entrada de FIXES es una de:
  - ("verify", path)                       -> ya coincide con la imagen tal
                                               cual; solo se cambia el flag.
  - ("replace", path, old, new)             -> substring exacto a reemplazar
                                               en el archivo completo (incluye
                                               frontmatter y cuerpo).
  - ("truncate_body", path, marker)         -> corta el cuerpo justo antes de
                                               `marker` (contaminación de
                                               páginas de soluciones pegadas).
  - ("doubt", path, note)                   -> no se pudo confirmar con
                                               certeza; se marca
                                               revision_manual_dudosa: true.
"""
import re

VERIFY = []      # list of paths: confirmed correct as-is, just flip the flag
REPLACE = []     # list of (path, old, new)
TRUNCATE = []    # list of (path, marker_text_to_cut_before)
DOUBT = []       # list of (path, note)

# ---------------------------------------------------------------------
# GRUPO B verificados sin cambios de texto (coinciden con la imagen)
# ---------------------------------------------------------------------
VERIFY += [
    "vault/fisica/2020/extraordinaria/pregunta-1.md",
    "vault/fisica/2020/ordinaria/pregunta-2.md",
    "vault/fisica/2022/ordinaria/pregunta-3.md",
    "vault/fisica/2023/extraordinaria/pregunta-3.md",
    "vault/fisica/2026/extraordinaria/pregunta-1.md",
    "vault/fisica/2026/extraordinaria/pregunta-2.md",
    "vault/fisica/2026/ordinaria/pregunta-2.md",
    "vault/quimica/2022/extraordinaria/pregunta-5.md",
    "vault/quimica/2026/extraordinaria/pregunta-1.md",
    "vault/matematicas_ii/2023/extraordinaria/pregunta-1.md",
    "vault/matematicas_ii/2023/extraordinaria/pregunta-2.md",
    "vault/matematicas_ii/2023/extraordinaria/pregunta-3.md",
    "vault/matematicas_ii/2023/extraordinaria/pregunta-4.md",
    "vault/matematicas_ii/2023/extraordinaria/pregunta-5.md",
    "vault/matematicas_ii/2023/extraordinaria/pregunta-6.md",
    "vault/matematicas_ii/2023/extraordinaria/pregunta-7.md",
    "vault/matematicas_ii/2023/ordinaria/pregunta-1.md",
    "vault/matematicas_ii/2023/ordinaria/pregunta-2.md",
    "vault/matematicas_ii/2023/ordinaria/pregunta-3.md",
    "vault/matematicas_ii/2023/ordinaria/pregunta-4.md",
    "vault/matematicas_ii/2023/ordinaria/pregunta-5.md",
    "vault/matematicas_ii/2023/ordinaria/pregunta-6.md",
    "vault/matematicas_ii/2023/ordinaria/pregunta-7.md",
    "vault/matematicas_ii/2025/extraordinaria/pregunta-2.md",
    "vault/matematicas_ii/2025/extraordinaria/pregunta-3.md",
    "vault/matematicas_ii/2025/extraordinaria/pregunta-4.md",
    "vault/matematicas_ii/2026/ordinaria/pregunta-1.md",
    "vault/matematicas_ii/2026/ordinaria/pregunta-2.md",
    "vault/matematicas_ii/2026/ordinaria/pregunta-3.md",
    "vault/matematicas_ii/2026/ordinaria/pregunta-4.md",
]

# ---------------------------------------------------------------------
# GRUPO A / B con texto corregido (reemplazos puntuales, aplicados a todo
# el archivo: frontmatter + cuerpo, de una vez).
# ---------------------------------------------------------------------

# --- Fisica ---
REPLACE.append(("vault/fisica/2022/ordinaria/pregunta-2.md",
    "En la reacción \nU + 𝑛→\nBa + X + 3 𝑛\n0\n1\nZ\nA\n56\n141\n0\n1\n92\n235\n se cumple",
    "En la reacción ²³⁵₉₂U + ¹₀n → ¹⁴¹₅₆Ba + ᴬZX + 3(¹₀n) se cumple"))
REPLACE.append(("vault/fisica/2022/ordinaria/pregunta-2.md",
    '"2.2. En la reacción U + 𝑛→ Ba + X + 3 𝑛 0 1 Z A 56 141 0 1 92 235 se cumple que: a) es una fusión nuclear; b) se pone en juego una gran cantidad de energía correspondiente al defecto de masa; c) al element"',
    '"2.2. En la reacción ²³⁵₉₂U + ¹₀n → ¹⁴¹₅₆Ba + ᴬZX + 3(¹₀n) se cumple que: a) es una fusión nuclear; b) se pone en juego una gran cantidad de energía correspondiente al defecto de masa; c) al elemento X le corresponde el número atómico 36 y el número másico 94."'))

REPLACE.append(("vault/fisica/2023/extraordinaria/pregunta-1.md",
    "1.1. Algunos átomos de nitrógeno (\n𝑁\n7\n14 ) atmosférico chocan con un neutrón y se transforman en carbono (\n𝐶\n6\n14 ) que, por \nemisión , se convierte de nuevo en nitrógeno. En este proceso: a) se emite radiación gamma; b) se emite un protón; c) no \npuede existir este proceso ya que se obtendría \n𝐵\n5\n14 . ",
    "1.1. Algunos átomos de nitrógeno (¹⁴₇N) atmosférico chocan con un neutrón y se transforman en carbono (¹⁴₆C) que, por \nemisión β, se convierte de nuevo en nitrógeno. En este proceso: a) se emite radiación gamma; b) se emite un protón; c) no \npuede existir este proceso ya que se obtendría ¹⁴₅B. "))
REPLACE.append(("vault/fisica/2023/extraordinaria/pregunta-1.md",
    '"1.1. Algunos átomos de nitrógeno ( 𝑁 7 14 ) atmosférico chocan con un neutrón y se transforman en carbono ( 𝐶 6 14 ) que, por emisión , se convierte de nuevo en nitrógeno. En este proceso: a) se emite rad"',
    '"1.1. Algunos átomos de nitrógeno (¹⁴₇N) atmosférico chocan con un neutrón y se transforman en carbono (¹⁴₆C) que, por emisión β, se convierte de nuevo en nitrógeno. En este proceso: a) se emite radiación gamma; b) se emite un protón; c) no puede existir este proceso ya que se obtendría ¹⁴₅B."'))

REPLACE.append(("vault/fisica/2023/extraordinaria/pregunta-6.md",
    "𝑔  = −9,8 𝑗̂  m s−2.",
    "𝑔⃗ = −9,8 𝚥̂ m s−2."))

REPLACE.append(("vault/fisica/2024/ordinaria/pregunta-1.md",
    'Bሬ⃗= \n0,6 𝚤𝚤̂ T con una velocidad 𝑣𝑣⃗= 8 × 106 𝚥𝚥̂',
    '𝐵⃗ = \n0,6 𝚤̂ T con una velocidad 𝑣⃗ = 8 × 10⁶ 𝚥̂'))
REPLACE.append(("vault/fisica/2024/ordinaria/pregunta-1.md",
    '"1.1. Una partícula tiene una carga de 5 nC y penetra en una región del espacio donde hay un campo magnético Bሬ⃗= 0,6 𝚤𝚤̂ T con una velocidad 𝑣𝑣𝑣𝑣= 8 × 106 𝚥𝚥̂ m∙s−1, describiendo una circunferencia de 2 μm "',
    '"1.1. Una partícula tiene una carga de 5 nC y penetra en una región del espacio donde hay un campo magnético B⃗ = 0,6 î T con una velocidad v⃗ = 8 × 10⁶ ĵ m·s−1, describiendo una circunferencia de 2 μm de radio. El valor de la masa de la partícula es: a) 7,5×10-22 kg; b) 4,5×10-22 kg; c) 2,5×10-22 kg."'))

REPLACE.append(("vault/fisica/2024/ordinaria/pregunta-6.md",
    '𝐸𝐸ሬ⃗=−80 𝚤𝚤̂ N /C',
    '𝐸⃗ = −80 𝚤̂ N /C'))

REPLACE.append(("vault/fisica/2024/extraordinaria/pregunta-6.md",
    '𝑣𝑣⃗= 8 × 104 𝚤𝚤̂ m/s en un campo magnético uniforme de intensidad 𝐵𝐵ሬ⃗= 0,1 𝑘𝑘෠ ',
    '𝑣⃗ = 8 × 10⁴ 𝚤̂ m/s en un campo magnético uniforme de intensidad 𝐵⃗ = 0,1 𝑘̂ '))

REPLACE.append(("vault/fisica/2026/ordinaria/pregunta-2.md",
    '𝑣𝑗⃗  en un campo magnético estacionario y uniforme 𝐵𝐵⃗⃗= −0.24𝑘𝑘⃗⃗(𝑇)',
    '𝑣𝚥̂ en un campo magnético estacionario y uniforme 𝐵⃗ = −0.24𝑘⃗(𝑇)'))
REPLACE.append(("vault/fisica/2026/ordinaria/pregunta-2.md",
    "con una velocidad 𝑣𝑗⃗  en un campo m",
    "con una velocidad 𝑣𝚥̂ en un campo m"))

# --- Quimica ---
REPLACE.append(("vault/quimica/2022/extraordinaria/pregunta-3.md",
    "CH3-CH2-CH2-COOH + CH3OH  \nCH3-CH2-CH2-CH2OH  \n𝐾𝐾2𝐶𝐶𝐶𝐶2𝑂𝑂7,𝐻𝐻+\nሱ⎯⎯⎯⎯⎯⎯⎯ሮ  ",
    "CH3-CH2-CH2-COOH + CH3OH → ____ \nCH3-CH2-CH2-CH2OH --(K2Cr2O7, H+)--> ____ "))
REPLACE.append(("vault/quimica/2022/extraordinaria/pregunta-3.md",
    '"3.1. Complete las siguientes reacciones nombrando todos los productos orgánicos presentes en ellas, tanto reactivos como productos, e indique a qué tipo de reacción se corresponden: CH3-CH2-CH2-COOH + CH3O"',
    '"3.1. Complete las siguientes reacciones nombrando todos los productos orgánicos presentes en ellas, tanto reactivos como productos, e indique a qué tipo de reacción se corresponden: CH3-CH2-CH2-COOH + CH3OH → ____ (primera reacción); CH3-CH2-CH2-CH2OH --(K2Cr2O7,H+)--> ____ (segunda reacción, dos esquemas de reacción independientes lado a lado)"'))

REPLACE.append(("vault/quimica/2024/extraordinaria/pregunta-8.md", None, None))  # handled via TRUNCATE

# --- Matematicas II ---
REPLACE.append(("vault/matematicas_ii/2020/ordinaria/pregunta-1.md",
    "b) Calcular la matriz 𝑋𝑋 que cumple la igualdad 𝑋𝑋𝑋𝑋+ (𝐴𝐴+ 𝐵𝐵)𝑇𝑇= 2𝐼𝐼+ 𝑋𝑋𝑋𝑋, siendo 𝐼𝐼 la matriz identidad de orden \n2 y (𝐴𝐴+ 𝐵𝐵)𝑇𝑇 la traspuesta de 𝐴𝐴+ 𝐵𝐵.",
    "b) Calcular la matriz X que cumple la igualdad XA + (A+B)ᵀ = 2I + XB, siendo I la matriz identidad de orden \n2 y (A+B)ᵀ la traspuesta de A+B."))
REPLACE.append(("vault/matematicas_ii/2020/ordinaria/pregunta-1.md",
    '"b) Calcular la matriz 𝑋𝑋 que cumple la igualdad 𝑋𝑋𝑋𝑋+ (𝐴𝐴+ 𝐵𝐵)𝑇𝑇= 2𝐼𝐼+ 𝑋𝑋𝑋𝑋, siendo 𝐼𝐼 la matriz identidad de orden 2 y (𝐴𝐴+ 𝐵𝐵)𝑇𝑇 la traspuesta de 𝐴𝐴+ 𝐵𝐵."',
    '"b) Calcular la matriz X que cumple la igualdad XA + (A+B)ᵀ = 2I + XB, siendo I la matriz identidad de orden 2 y (A+B)ᵀ la traspuesta de A+B."'))

REPLACE.append(("vault/matematicas_ii/2020/ordinaria/pregunta-2.md",
    "ቐ\n𝑚𝑚𝑚𝑚\n+\n𝑦𝑦\n=\n2𝑚𝑚,\n𝑥𝑥\n+\n𝑧𝑧\n=\n0,\n𝑥𝑥\n+\n𝑚𝑚𝑚𝑚\n=\n0.",
    "{ mx + y = 2m,\n  x + z = 0,\n  x + my = 0. }"))

REPLACE.append(("vault/matematicas_ii/2020/ordinaria/pregunta-4.md",
    "𝑏𝑏𝑏𝑏+ 𝑐𝑐\nsi\n𝑥𝑥> 0",
    "𝑏𝑥+ 𝑐𝑐\nsi\n𝑥𝑥> 0"))
REPLACE.append(("vault/matematicas_ii/2020/ordinaria/pregunta-4.md",
    "∫𝑥𝑥(ln 𝑥𝑥−1)𝑑𝑑𝑑𝑑\n2\n1\n.",
    "∫₁² 𝑥(ln 𝑥−1)𝑑𝑥."))
REPLACE.append(("vault/matematicas_ii/2020/ordinaria/pregunta-4.md",
    '"b) Calcule ∫𝑥𝑥(ln 𝑥𝑥−1)𝑑𝑑𝑑𝑑 2 1 ."',
    '"b) Calcule ∫₁² x(ln x−1)dx."'))
REPLACE.append(("vault/matematicas_ii/2020/ordinaria/pregunta-4.md",
    '"a) Calcule los valores de 𝑏𝑏 y 𝑐𝑐 para que la función 𝑓𝑓(𝑥𝑥) = ൜e2𝑥𝑥 si 𝑥𝑥≤0, 𝑥𝑥2 + 𝑏𝑏𝑏𝑏+ 𝑐𝑐 si 𝑥𝑥> 0 sea, primero continua, y luego derivable en 𝑥𝑥= 0."',
    '"a) Calcule los valores de b y c para que la función f(x) = {e^(2x) si x≤0, x²+bx+c si x>0} sea, primero continua, y luego derivable en x=0."'))

REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-1.md",
    "Para la ecuación matricial 𝐴𝐴2𝑋𝑋+ 𝐴𝐴𝐴𝐴= 𝐵𝐵, se pide: ",
    "Para la ecuación matricial A²X + AB = B, se pide: "))
REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-1.md",
    "a) Despejar 𝑋𝑋 suponiendo que 𝐴𝐴 (y por tanto 𝐴𝐴2) es invertible, y decir cuáles serían las dimensiones de 𝑋𝑋 y de 𝐵𝐵 \nsi 𝐴𝐴 tuviera dimensión 4 × 4 y 𝐵𝐵 tuviera 3 columnas. ",
    "a) Despejar X suponiendo que A (y por tanto A²) es invertible, y decir cuáles serían las dimensiones de X y de B \nsi A tuviera dimensión 4 × 4 y B tuviera 3 columnas. "))
REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-1.md",
    '"a) Despejar 𝑋𝑋 suponiendo que 𝐴𝐴 (y por tanto 𝐴𝐴2) es invertible, y decir cuáles serían las dimensiones de 𝑋𝑋 y de 𝐵𝐵 si 𝐴𝐴 tuviera dimensión 4 × 4 y 𝐵𝐵 tuviera 3 columnas."',
    '"a) Despejar X suponiendo que A (y por tanto A²) es invertible, y decir cuáles serían las dimensiones de X y de B si A tuviera dimensión 4 × 4 y B tuviera 3 columnas."'))

REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-2.md",
    "ቐ(𝑚𝑚+ 3)𝑥𝑥\n−\n𝑚𝑚2𝑦𝑦\n=\n3𝑚𝑚,\n(𝑚𝑚+ 3)𝑥𝑥\n+\n𝑚𝑚𝑚𝑚\n=\n3𝑚𝑚+ 6.",
    "{ (m+3)x − m²y = 3m,\n  (m+3)x + my = 3m+6. }"))

REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-3.md",
    "𝑏𝑏𝑏𝑏\nsi\n𝑥𝑥≥0\n",
    "𝑏𝑥\nsi\n𝑥𝑥≥0\n"))

REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-4.md",
    "b) Calcule ∫𝑥𝑥√𝑥𝑥2 −1 𝑑𝑑𝑑𝑑.",
    "b) Calcule ∫x√(x²−1) dx."))
REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-4.md",
    '"b) Calcule ∫𝑥𝑥√𝑥𝑥2 −1 𝑑𝑑𝑑𝑑."',
    '"b) Calcule ∫x√(x²−1) dx."'))

REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-6.md",
    "𝑢𝑢ሬ⃗(2,0,0), 𝑣𝑣⃗(0, 𝑘𝑘, 1) y 𝑤𝑤ሬሬ⃗(2,2,2)",
    "𝑢⃗(2,0,0), 𝑣⃗(0, 𝑘, 1) y 𝑤⃗(2,2,2)"))
REPLACE.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-6.md",
    '"a) Calcule 𝑘𝑘 sabiendo que los vectores 𝑢𝑢ሬ⃗(2,0,0), 𝑣𝑣⃗(0, 𝑘𝑘, 1) y 𝑤𝑤ሬሬ⃗(2,2,2) son coplanarios."',
    '"a) Calcule k sabiendo que los vectores u⃗(2,0,0), v⃗(0,k,1) y w⃗(2,2,2) son coplanarios."'))

# --- mat2021 ordinaria ---
REPLACE.append(("vault/matematicas_ii/2021/ordinaria/pregunta-8.md", None, None))  # TRUNCATE
# --- mat2021 extraordinaria ---
REPLACE.append(("vault/matematicas_ii/2021/extraordinaria/pregunta-8.md", None, None))  # TRUNCATE

REPLACE.append(("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    "Despeje 𝑋𝑋 de la ecuación matricial 𝐴𝐴𝐴𝐴(𝑋𝑋−𝐼𝐼) = 𝐶𝐶, donde 𝐼𝐼 es la matriz identidad (asuma que el producto \n𝐴𝐴𝐴𝐴 tiene inversa). Luego, calcule 𝑋𝑋 si ",
    "Despeje X de la ecuación matricial AB(X−I) = C, donde I es la matriz identidad (asuma que el producto \nAB tiene inversa). Luego, calcule X si "))
REPLACE.append(("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    '"1. Números y Álgebra \nDespeje 𝑋𝑋 de la ecuación matricial 𝐴𝐴𝐴𝐴(𝑋𝑋−𝐼𝐼) = 𝐶𝐶,',
    '"1. Números y Álgebra \nDespeje X de la ecuación matricial AB(X−I) = C,'))

REPLACE.append(("vault/matematicas_ii/2022/extraordinaria/pregunta-1.md",
    "Nota: 𝑎𝑎𝑖𝑖𝑖𝑖 es el elemento que está en la fila 𝑖𝑖 y en la columna 𝑗𝑗 de 𝐴𝐴.",
    "Nota: aᵢⱼ es el elemento que está en la fila i y en la columna j de A."))
REPLACE.append(("vault/matematicas_ii/2022/extraordinaria/pregunta-1.md",
    '"a) Obtenga la matriz antisimétrica 𝐴𝐴 de orden 2 × 2 tal que 𝑎𝑎12 = 1. Luego, calcule su inversa en caso de que exista. Nota: 𝑎𝑎𝑖𝑖𝑖𝑖 es el elemento que está en la fila 𝑖𝑖 y en la columna 𝑗𝑗 de 𝐴𝐴."',
    '"a) Obtenga la matriz antisimétrica A de orden 2 × 2 tal que a₁₂ = 1. Luego, calcule su inversa en caso de que exista. Nota: aᵢⱼ es el elemento que está en la fila i y en la columna j de A."'))

REPLACE.append(("vault/matematicas_ii/2024/extraordinaria/pregunta-1.md",
    "𝐴𝐴𝐴𝐴= 𝑋𝑋𝑋𝑋 para toda matriz antisimétrica 𝑋𝑋 de orden 2. \nb) Si 𝑥𝑥= −1 e 𝑦𝑦= 1, calcule la matriz 𝑀𝑀 que satisface la igualdad 2𝑀𝑀= 𝐴𝐴−1 −𝐴𝐴𝐴𝐴.",
    "AX = XA para toda matriz antisimétrica X de orden 2. \nb) Si x=−1 e y=1, calcule la matriz M que satisface la igualdad 2M = A⁻¹ − AM."))
REPLACE.append(("vault/matematicas_ii/2024/extraordinaria/pregunta-1.md",
    '"a) Calcule los valores de 𝑥𝑥 e 𝑦𝑦 que hacen que 𝐴𝐴 conmute con todas las matrices antisimétricas 𝑋𝑋 de orden 2, es decir, que hacen que se cumpla la igualdad 𝐴𝐴𝐴𝐴= 𝑋𝑋𝑋𝑋 para toda matriz antisimétrica 𝑋𝑋 "',
    '"a) Calcule los valores de x e y que hacen que A conmute con todas las matrices antisimétricas X de orden 2, es decir, que hacen que se cumpla la igualdad AX = XA para toda matriz antisimétrica X de orden 2."'))
REPLACE.append(("vault/matematicas_ii/2024/extraordinaria/pregunta-1.md",
    '"b) Si 𝑥𝑥= −1 e 𝑦𝑦= 1, calcule la matriz 𝑀𝑀 que satisface la igualdad 2𝑀𝑀= 𝐴𝐴−1 −𝐴𝐴𝐴𝐴."',
    '"b) Si x=−1 e y=1, calcule la matriz M que satisface la igualdad 2M = A⁻¹ − AM."'))

REPLACE.append(("vault/matematicas_ii/2024/extraordinaria/pregunta-2.md",
    "𝑚𝑚𝑚𝑚\n+\n3𝑧𝑧\n=\n𝑚𝑚.",
    "mx + 3z = m. }"))
REPLACE.append(("vault/matematicas_ii/2024/extraordinaria/pregunta-2.md",
    "Discuta, según los valores del parámetro 𝑚𝑚, el siguiente sistema: ൝\n2𝑥𝑥\n+\n𝑦𝑦\n+\n𝑧𝑧\n=\n𝑚𝑚,\n𝑥𝑥\n−\n𝑦𝑦\n+\n2𝑧𝑧\n=\n2𝑚𝑚,\n",
    "Discuta, según los valores del parámetro m, el siguiente sistema: { 2x + y + z = m,\n  x − y + 2z = 2m,\n  "))

REPLACE.append(("vault/matematicas_ii/2024/extraordinaria/pregunta-3.md",
    "𝑥𝑥2 + 𝑏𝑏𝑏𝑏−1\nsi\n𝑥𝑥≤0,",
    "𝑥𝑥2 + 𝑏𝑥−1\nsi\n𝑥𝑥≤0,"))

# --- mat2024 ordinaria pregunta-2 (mm -> mx) ---
REPLACE.append(("vault/matematicas_ii/2024/ordinaria/pregunta-2.md",
    "ቐ\n𝑚𝑚𝑚𝑚\n+\n(𝑚𝑚+ 2)𝑦𝑦\n+\n𝑧𝑧\n=\n3,\n2𝑚𝑚𝑚𝑚\n+\n3𝑚𝑚𝑚𝑚\n+\n2𝑧𝑧\n=\n5,\n(𝑚𝑚−4)𝑦𝑦\n+\n𝑚𝑚𝑚𝑚\n=\n𝑚𝑚.",
    "{ mx + (m+2)y + z = 3,\n  2mx + 3my + 2z = 5,\n  (m−4)y + mz = m. }"))

# --- mat2026 extraordinaria (Tamil/Telugu font substitution) ---
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-2.md",
    "𝑋= 𝐴𝐴் e 𝑌= 𝐴்𝐴, siendo 𝐴் la matriz traspuesta de A.",
    "X = AAᵀ e Y = AᵀA, siendo Aᵀ la matriz traspuesta de A."))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-2.md",
    '"2.1. Dadas las matrices 𝐴= ቀ1 0 1 0 2 0ቁ y 𝐵= ൭ 1 0 1 0 1 0 1 0 1 ൱, se pide responder las siguientes cuestiones: 2.1.1. Calcule las matrices 𝑋= 𝐴𝐴் e 𝑌= 𝐴்𝐴, siendo 𝐴் la matriz traspuesta de A. ¿Son X o "',
    '"2.1. Dadas las matrices A=(1 0 1; 0 2 0) y B=(1 0 1; 0 1 0; 1 0 1), se pide responder las siguientes cuestiones: 2.1.1. Calcule las matrices X = AAᵀ e Y = AᵀA, siendo Aᵀ la matriz traspuesta de A. ¿Son X o Y invertibles? Razone la respuesta y calcule las inversas en caso de que sea posible."'))

REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    "𝑝(𝑥) = 𝑎𝑥ଷ+ 𝑏𝑥ଶ+ 𝑐𝑥+ 𝑑",
    "p(x) = ax³+bx²+cx+d"))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    "lim\n௫→ଶశ𝑓(𝑥) = −∞.",
    "lim(x→2⁺) f(x) = −∞."))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    "𝑔(𝑥) =\nସ\nగమቀ𝑥−\nగ\nଶቁ\nଶ\n, dibuje",
    "g(x) = (4/π²)(x−π/2)², dibuje"))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    '"3.1. Dado el polinomio 𝑝(𝑥) = 𝑎𝑥ଷ+ 𝑏𝑥ଶ+ 𝑐𝑥+ 𝑑, calcule los coeficientes 𝑎, 𝑏, 𝑐 y 𝑑 si se sabe que 𝑝 tiene un extremo relativo en (1, −6) y que la ecuación de la recta tangente a la gráfica de 𝑝 en 𝑥= −1 e"',
    '"3.1. Dado el polinomio p(x) = ax³+bx²+cx+d, calcule los coeficientes a, b, c y d si se sabe que p tiene un extremo relativo en (1, −6) y que la ecuación de la recta tangente a la gráfica de p en x=−1 es y=4x+2."'))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    '"3.2. Dibuje la gráfica de una función 𝑓: ℝ∖{2} →ℝ que tenga las siguientes propiedades:  𝑓, 𝑓′ y 𝑓′′ tienen el mismo signo en el intervalo (−1,2) y  lim ௫→ଶశ𝑓(𝑥) = −∞. Luego, dé explicaciones relacionand"',
    '"3.2. Dibuje la gráfica de una función f: ℝ∖{2}→ℝ que tenga las siguientes propiedades: f, f′ y f″ tienen el mismo signo en el intervalo (−1,2) y lim(x→2⁺) f(x) = −∞. Luego, dé explicaciones relacionando el dibujo con la monotonía, la convexidad o concavidad y el concepto de asíntota."'))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    '"3.3. Dadas las funciones 𝑓(𝑥) = cos 𝑥 y 𝑔(𝑥) = ସ గమቀ𝑥− గ ଶቁ ଶ , dibuje la región encerrada por sus gráficas y calcule su área."',
    '"3.3. Dadas las funciones f(x) = cos x y g(x) = (4/π²)(x−π/2)², dibuje la región encerrada por sus gráficas y calcule su área."'))

REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-4.md",
    "𝑟:\n௫ିଵ\nଶ=\n௬ିଵ\nଵ=\n௭\nଷ .",
    "r: (x−1)/2 = (y−1)/1 = z/3 ."))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-4.md",
    "4.2.1. Calcule el punto 𝑃ᇱ simétrico de 𝑃 con respecto al punto 𝑄(2, −1,2).",
    "4.2.1. Calcule el punto P′ simétrico de P con respecto al punto Q(2, −1,2)."))
REPLACE.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-4.md",
    '"4.1. Considere la recta 𝑟:\n௫ିଵ\nଶ=\n௬ିଵ\nଵ=\n௭\nଷ ."',
    '"4.1. Considere la recta r: (x−1)/2 = (y−1)/1 = z/3."'))

# --- mat2025 ordinaria (# ( . F H substitution) ---
REPLACE.append(("vault/matematicas_ii/2025/ordinaria/pregunta-2.md",
    "). Responda uno de estos dos apartados: 2.1. o 2.2. \n2.1. Responda a las dos cuestiones siguientes: \n \n2.1.1. Si 𝐴= #2\n5\n2\n−1(, halle 𝛼, 𝛽∈ℝ tales que 𝐴. + 𝛼𝐴+ 𝛽𝐼= 0, donde 𝐼 y 0 son las matrices identidad y cero, \nrespectivamente.  \n2.1.2. Calcule la matriz cuadrada 𝑋 tal que 𝑋𝐴= 𝐵, si 𝐴= #1\n0\n1\n1( y 𝐵= #2\n1\n1\n1(. ¿Son iguales 𝑋𝐴 y 𝐴𝑋? \n",
    "Responda uno de estos dos apartados: 2.1. o 2.2. \n2.1. Responda a las dos cuestiones siguientes: \n \n2.1.1. Si A=(2 5; 2 −1), halle α, β∈ℝ tales que A²+αA+βI=0, donde I y 0 son las matrices identidad y cero, \nrespectivamente.  \n2.1.2. Calcule la matriz cuadrada X tal que XA=B, si A=(1 0; 1 1) y B=(2 1; 1 1). ¿Son iguales XA y AX? \n"))
REPLACE.append(("vault/matematicas_ii/2025/ordinaria/pregunta-2.md",
    '"2.1.1. Si 𝐴= #2 5 2 −1(, halle 𝛼, 𝛽∈ℝ tales que 𝐴. + 𝛼𝐴+ 𝛽𝐼= 0, donde 𝐼 y 0 son las matrices identidad y cero, respectivamente."',
    '"2.1.1. Si A=(2 5; 2 −1), halle α,β∈ℝ tales que A²+αA+βI=0, donde I y 0 son las matrices identidad y cero, respectivamente."'))
REPLACE.append(("vault/matematicas_ii/2025/ordinaria/pregunta-2.md",
    '"2.1.2. Calcule la matriz cuadrada 𝑋 tal que 𝑋𝐴= 𝐵, si 𝐴= #1 0 1 1( y 𝐵= #2 1 1 1(. ¿Son iguales 𝑋𝐴 y 𝐴𝑋?"',
    '"2.1.2. Calcule la matriz cuadrada X tal que XA=B, si A=(1 0; 1 1) y B=(2 1; 1 1). ¿Son iguales XA y AX?"'))

REPLACE.append(("vault/matematicas_ii/2025/ordinaria/pregunta-3.md",
    "). Responda uno de estos dos apartados: 3.1. o 3.2. \n \n3.1. Dada la función  𝑓(𝑥) = =𝑘𝑥. + 2𝑥\nsi\n𝑥≤1,\n𝑥. −𝑚\nsi\n𝑥> 1, se pide responder a las siguientes cuestiones: ",
    "Responda uno de estos dos apartados: 3.1. o 3.2. \n \n3.1. Dada la función  f(x) = {kx²+2x si x≤1, x²−m si x>1}, se pide responder a las siguientes cuestiones: "))
REPLACE.append(("vault/matematicas_ii/2025/ordinaria/pregunta-3.md",
    '"3.1. Dada la función 𝑓(𝑥) = =𝑘𝑥. + 2𝑥 si 𝑥≤1, 𝑥. −𝑚 si 𝑥> 1, se pide responder a las siguientes cuestiones:"',
    '"3.1. Dada la función f(x) = {kx²+2x si x≤1, x²−m si x>1}, se pide responder a las siguientes cuestiones:"'))

REPLACE.append(("vault/matematicas_ii/2025/ordinaria/pregunta-4.md",
    "). Responda uno de estos dos apartados: 4.1. o 4.2. \n \n4.1. Determine el valor que debe tomar 𝑘 para que los planos \n𝜋F:𝑘𝑥+ 𝑦+\nF\nH 𝑧+ 2 = 0      y \n𝜋.:3𝑥+ 4𝑦+ 𝑧+ 3 = 0 \nsean paralelos.",
    "Responda uno de estos dos apartados: 4.1. o 4.2. \n \n4.1. Determine el valor que debe tomar k para que los planos \nπ₁: kx+y+(1/4)z+2 = 0      y \nπ₂: 3x+4y+z+3 = 0 \nsean paralelos."))
REPLACE.append(("vault/matematicas_ii/2025/ordinaria/pregunta-4.md",
    '"4.1. Determine el valor que debe tomar 𝑘 para que los planos 𝜋F:𝑘𝑥+ 𝑦+ F H 𝑧+ 2 = 0 y 𝜋.:3𝑥+ 4𝑦+ 𝑧+ 3 = 0 sean paralelos. Calcule también el valor de 𝑘 que hace que esos mismos planos sean perpendiculares."',
    '"4.1. Determine el valor que debe tomar k para que los planos π₁: kx+y+(1/4)z+2=0 y π₂: 3x+4y+z+3=0 sean paralelos. Calcule también el valor de k que hace que esos mismos planos sean perpendiculares."'))

TRUNCATE.append(("vault/matematicas_ii/2021/ordinaria/pregunta-8.md",
    "\n\n \nProba de Avaliación do Bacharelato \npara o Acceso á Universidade \n2021 - ordinaria"))
TRUNCATE.append(("vault/matematicas_ii/2021/extraordinaria/pregunta-8.md",
    "\n\n \nProba de Avaliación do Bacharelato \npara o Acceso á Universidade \n2021 - extraordinaria"))
TRUNCATE.append(("vault/quimica/2024/extraordinaria/pregunta-8.md",
    "\nCH3\nC\nH3C\nNH"))


# =======================================================================
# RUNNER
# =======================================================================
def flip_flag(text, limpieza_value):
    assert "revision_manual: true" in text, "no revision_manual:true flag found"
    return text.replace("revision_manual: true", f'revision_manual: false\nlimpieza: "{limpieza_value}"', 1)


def process():
    touched = set()
    errors = []

    for path in VERIFY:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        try:
            text = flip_flag(text, "verificado_visual")
        except AssertionError as e:
            errors.append((path, str(e)))
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        touched.add(path)

    for entry in REPLACE:
        path, old, new = entry
        if old is None:
            continue  # handled via TRUNCATE
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if old not in text:
            errors.append((path, f"OLD STRING NOT FOUND: {old[:80]!r}..."))
            continue
        text = text.replace(old, new, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        touched.add(path)

    for path, marker in TRUNCATE:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        idx = text.find(marker)
        if idx == -1:
            errors.append((path, f"TRUNCATE MARKER NOT FOUND: {marker[:60]!r}..."))
            continue
        text = text[:idx].rstrip() + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        touched.add(path)

    # Flip the flag for every REPLACE/TRUNCATE-touched file that still says revision_manual: true
    for path in touched:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if "revision_manual: true" in text:
            text = flip_flag(text, "transcripcion_visual")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    print(f"Archivos tocados: {len(touched)}")
    print(f"Errores: {len(errors)}")
    for path, msg in errors:
        print(f"  {path}: {msg}")
    return touched, errors


if __name__ == "__main__":
    process()
