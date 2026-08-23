# -*- coding: utf-8 -*-
"""Third and final pass: precise fixes based on exact current file dumps."""
import re

def sub_or_report(path, pattern, repl, flags=0, count=1):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_text, n = re.subn(pattern, repl, text, count=count, flags=flags)
    if n == 0:
        print(f"MISS: {path}: {pattern[:80]}")
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return True


def flip_flag(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if "revision_manual: true" in text:
        text = text.replace("revision_manual: true", 'revision_manual: false\nlimpieza: "transcripcion_visual"', 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


# A) fisica/2023/extraordinaria/pregunta-6
sub_or_report("vault/fisica/2023/extraordinaria/pregunta-6.md",
    r"𝑔\s*=\s*−9,8\s*𝑗̂\s*m s−2\.",
    "𝑔⃗ = −9,8 𝚥̂ m s−2.")
flip_flag("vault/fisica/2023/extraordinaria/pregunta-6.md")

# B) fisica/2026/ordinaria/pregunta-2 : double arrows B, k in body
sub_or_report("vault/fisica/2026/ordinaria/pregunta-2.md",
    r"𝐵⃗⃗= −0\.24𝑘⃗⃗\(𝑇\)",
    "𝐵⃗ = −0.24𝑘⃗(𝑇)")
sub_or_report("vault/fisica/2026/ordinaria/pregunta-2.md",
    r'"2\.2\. Resuelva uno de estos dos problemas\. \(1,5 puntos\) 2\.2\.1\. Un electrón se acelera desde el reposo mediante una diferencia de potencial de 1000 V; a continuación entra con una velocidad 𝑣𝑗⃗ en un campo m"',
    '"2.2. Resuelva uno de estos dos problemas. (1,5 puntos) 2.2.1. Un electrón se acelera desde el reposo mediante una diferencia de potencial de 1000 V; a continuación entra con una velocidad v ĵ en un campo magnético estacionario y uniforme B⃗ = −0.24 k⃗ (T)."')

# C) quimica/2022/extraordinaria/pregunta-3 : body still has old arrow text
sub_or_report("vault/quimica/2022/extraordinaria/pregunta-3.md",
    r"CH3-CH2-CH2-COOH \+ CH3OH\s*\nCH3-CH2-CH2-CH2OH\s*\n𝐾𝐾2𝐶𝐶𝐶𝐶2𝑂𝑂7,𝐻𝐻\+\nሱ⎯+ሮ\s*",
    "CH3-CH2-CH2-COOH + CH3OH → ____ \nCH3-CH2-CH2-CH2OH --(K2Cr2O7, H+)--> ____ \n")

# D) matematicas_ii/2022/ordinaria/pregunta-1 : collapse remaining safe AA/BB/CC pairs
sub_or_report("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    r"𝐴𝐴= ൭",
    "A = (", count=1)
sub_or_report("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    r"𝐵𝐵= ൭",
    "B = (", count=1)
sub_or_report("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    r"𝐶𝐶= ൭",
    "C = (", count=1)
sub_or_report("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    r"൱\.",
    ").", count=1)
sub_or_report("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    r"൱, \n",
    "), \n", count=1)
sub_or_report("vault/matematicas_ii/2022/ordinaria/pregunta-1.md",
    r"൱ \n",
    ") \n", count=1)

# E) matematicas_ii/2026/extraordinaria/pregunta-3 : sync apartados to match fixed body
sub_or_report("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    r'"3\.1\. Dado el polinomio p\(x\) = ax³\+bx²\+cx\+d, calcule los coeficientes 𝑎, 𝑏, 𝑐 y 𝑑 si se sabe que 𝑝 tiene un extremo relativo en \(1, −6\) y que la ecuación de la recta tangente a la gráfica de 𝑝 en 𝑥= −1 e"',
    '"3.1. Dado el polinomio p(x) = ax³+bx²+cx+d, calcule los coeficientes a, b, c y d si se sabe que p tiene un extremo relativo en (1, −6) y que la ecuación de la recta tangente a la gráfica de p en x=−1 es y=4x+2."')
sub_or_report("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md",
    r'"3\.2\. Dibuje la gráfica de una función 𝑓: ℝ∖\{2\} →ℝ que tenga las siguientes propiedades:  𝑓, 𝑓′ y 𝑓′′ tienen el mismo signo en el intervalo \(−1,2\) y  lim ௫→ଶశ𝑓\(𝑥\) = −∞\. Luego, dé explicaciones relacionand"',
    '"3.2. Dibuje la gráfica de una función f: ℝ∖{2}→ℝ que tenga las siguientes propiedades: f, f′ y f″ tienen el mismo signo en el intervalo (−1,2) y lim(x→2⁺) f(x) = −∞. Luego, dé explicaciones relacionando el dibujo con la monotonía, la convexidad o concavidad y el concepto de asíntota."')

# F) matematicas_ii/2026/extraordinaria/pregunta-4 : sync apartados
sub_or_report("vault/matematicas_ii/2026/extraordinaria/pregunta-4.md",
    r'"4\.1\. Considere la recta 𝑟: ௫ିଵ ଶ= ௬ିଵ ଵ= ௭ ଷ \. 4\.1\.1\. Calcule la ecuación implícita o general del plano 𝜋 que contiene a la recta 𝑟 y al punto 𝑄\(2, −1,1\)\. 4\.1\.2\. Compruebe que la recta 𝑟 es paralela al pla"',
    '"4.1. Considere la recta r: (x−1)/2 = (y−1)/1 = z/3. 4.1.1. Calcule la ecuación implícita o general del plano π que contiene a la recta r y al punto Q(2,−1,1). 4.1.2. Compruebe que la recta r es paralela al plano π*: x+y−z−1=0. Calcule la distancia de r a π*."')
sub_or_report("vault/matematicas_ii/2026/extraordinaria/pregunta-4.md",
    r'"4\.2\. Considere el punto 𝑃\(3,0, −1\)\. 4\.2\.1\. Calcule el punto P′ simétrico de P con respecto al punto Q\(2, −1,2\)\. 4\.2\.2\. Calcule el punto 𝑃′′ simétrico de 𝑃 con respecto al plano 𝜋: 𝑥\+ 2 𝑦 \+ 𝑧−8 = 0\."',
    '"4.2. Considere el punto P(3,0,−1). 4.2.1. Calcule el punto P′ simétrico de P con respecto al punto Q(2,−1,2). 4.2.2. Calcule el punto P″ simétrico de P con respecto al plano π: x+2y+z−8=0."')

# G) matematicas_ii/2025/ordinaria/pregunta-2 : stray "5" + reformat system 2.2
sub_or_report("vault/matematicas_ii/2025/ordinaria/pregunta-2.md",
    r"el sistema {2}5\n𝑥\n\+\n𝑦\n\+\n𝑚𝑧\n=\n1,\n𝑥\n\+\n𝑚𝑦\n\+\n𝑧\n=\n1,\n𝑚𝑥\n\+\n𝑦\n\+\n𝑧\n=\n1\.",
    "el sistema { x+y+mz=1, x+my+z=1, mx+y+z=1. }")
sub_or_report("vault/matematicas_ii/2025/ordinaria/pregunta-2.md",
    r'"2\.2\. Discuta, según los valores del parámetro 𝑚, el sistema 5 𝑥 \+ 𝑦 \+ 𝑚𝑧 = 1, 𝑥 \+ 𝑚𝑦 \+ 𝑧 = 1, 𝑚𝑥 \+ 𝑦 \+ 𝑧 = 1\."',
    '"2.2. Discuta, según los valores del parámetro m, el sistema x+y+mz=1, x+my+z=1, mx+y+z=1."')
sub_or_report("vault/matematicas_ii/2025/ordinaria/pregunta-2.md",
    r'"2\.1\. Responda a las dos cuestiones siguientes: 2\.1\.1\. Si 𝐴= #2 5 2 −1\(, halle 𝛼, 𝛽∈ℝ tales que 𝐴\. \+ 𝛼𝐴\+ 𝛽𝐼= 0, donde 𝐼 y 0 son las matrices identidad y cero, respectivamente\. 2\.1\.2\. Calcule la matriz cuadr"',
    '"2.1. Responda a las dos cuestiones siguientes: 2.1.1. Si A=(2 5; 2 −1), halle α,β∈ℝ tales que A²+αA+βI=0, donde I y 0 son las matrices identidad y cero, respectivamente. 2.1.2. Calcule la matriz cuadrada X tal que XA=B, si A=(1 0; 1 1) y B=(2 1; 1 1). ¿Son iguales XA y AX?"')

# H) matematicas_ii/2025/ordinaria/pregunta-3 : sync apartados
sub_or_report("vault/matematicas_ii/2025/ordinaria/pregunta-3.md",
    r'"3\.1\. Dada la función 𝑓\(𝑥\) = =𝑘𝑥\. \+ 2𝑥 si 𝑥≤1, 𝑥\. −𝑚 si 𝑥> 1, se pide responder a las siguientes cuestiones: 3\.1\.1\. ¿Qué condición deben cumplir 𝑘 y 𝑚 para que 𝑓 sea continua en 𝑥= 1\? 3\.1\.2\. ¿Para qué valor"',
    '"3.1. Dada la función f(x) = {kx²+2x si x≤1, x²−m si x>1}, se pide responder a las siguientes cuestiones: 3.1.1. ¿Qué condición deben cumplir k y m para que f sea continua en x=1? 3.1.2. ¿Para qué valores de k y m es f derivable en x=1?"')

print("done")
