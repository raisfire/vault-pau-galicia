# -*- coding: utf-8 -*-
"""Fase 1b Paso 3, segunda pasada: regex-based fixes for files where exact
literal matching failed the first time (frontmatter apartados wrap
differently than the body). Uses regex per file for robustness."""
import re

FIXES = []  # (path, [(pattern, replacement, flags), ...])

FIXES.append(("vault/fisica/2023/extraordinaria/pregunta-1.md", [
    (r"\( \n?𝑁\n?7\n?14 \)", "(¹⁴₇N)", 0),
    (r"\(\n?𝑁\n?7\n?14 \)", "(¹⁴₇N)", 0),
    (r"\( 𝑁 7 14 \)", "(¹⁴₇N)", 0),
    (r"\( \n?𝐶\n?6\n?14 \)", "(¹⁴₆C)", 0),
    (r"\(\n?𝐶\n?6\n?14 \)", "(¹⁴₆C)", 0),
    (r"\( 𝐶 6 14 \)", "(¹⁴₆C)", 0),
    (r"por \nemisión , se convierte", "por emisión β, se convierte", 0),
    (r"por emisión , se convierte", "por emisión β, se convierte", 0),
    (r"se obtendría \n𝐵\n5\n14 \.", "se obtendría ¹⁴₅B.", 0),
    (r"se obtendría 𝐵 5 14 \.", "se obtendría ¹⁴₅B.", 0),
]))

FIXES.append(("vault/fisica/2023/extraordinaria/pregunta-6.md", [
    (r"𝑔 {1,2}= −9,8 𝑗̂ {1,2}m s−2\.", "𝑔⃗ = −9,8 𝚥̂ m s−2.", 0),
]))

FIXES.append(("vault/fisica/2024/ordinaria/pregunta-1.md", [
    (r"Bሬ⃗=\s*\n?0,6 𝚤𝚤̂ T con una velocidad 𝑣𝑣⃗= 8 × 106 𝚥𝚥̂", "𝐵⃗ = 0,6 𝚤̂ T con una velocidad 𝑣⃗ = 8 × 10⁶ 𝚥̂", 0),
]))

FIXES.append(("vault/fisica/2026/ordinaria/pregunta-2.md", [
    (r"𝑣𝑗⃗ {1,2}en un campo magnético estacionario y uniforme 𝐵⃗⃗= −0\.24𝑘⃗⃗\(𝑇\)", "𝑣𝚥̂ en un campo magnético estacionario y uniforme 𝐵⃗ = −0.24𝑘⃗(𝑇)", 0),
]))

FIXES.append(("vault/quimica/2022/extraordinaria/pregunta-3.md", [
    (r"CH3-CH2-CH2-COOH \+ CH3OH {1,2}\nCH3-CH2-CH2-CH2OH {1,2}\n𝐾𝐾2𝐶𝐶𝐶𝐶2𝑂𝑂7,𝐻𝐻\+\nሱ⎯+ሮ {0,2}",
     "CH3-CH2-CH2-COOH + CH3OH → ____ \nCH3-CH2-CH2-CH2OH --(K2Cr2O7, H+)--> ____ ", 0),
]))

FIXES.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-2.md", [
    (r"el siguiente sistema: ൜\(𝑚𝑚\+ 3\)𝑥𝑥\n−\n𝑚𝑚2𝑦𝑦\n=\n3𝑚𝑚,\n\(𝑚𝑚\+ 3\)𝑥𝑥\n\+\n𝑚𝑚𝑚𝑚\n=\n3𝑚𝑚\+ 6\.",
     "el siguiente sistema: { (m+3)x − m²y = 3m,\n  (m+3)x + my = 3m+6. }", 0),
]))

FIXES.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-4.md", [
    (r"b\) Calcule ∫𝑥𝑥√𝑥𝑥2 −1 𝑑𝑑𝑑𝑑\.", "b) Calcule ∫x√(x²−1) dx.", 0),
]))

FIXES.append(("vault/matematicas_ii/2020/extraordinaria/pregunta-6.md", [
    (r"𝑢𝑢ሬ⃗\(2,0,0\), 𝑣𝑣⃗\(0, 𝑘𝑘, 1\) y 𝑤𝑤ሬሬ⃗\(2,2,2\)", "𝑢⃗(2,0,0), 𝑣⃗(0, 𝑘, 1) y 𝑤⃗(2,2,2)", 0),
]))

FIXES.append(("vault/matematicas_ii/2022/ordinaria/pregunta-1.md", [
    (r"Despeje 𝑋𝑋 de la ecuación matricial 𝐴𝐴𝐴𝐴\(𝑋𝑋−𝐼𝐼\) = 𝐶𝐶, donde 𝐼𝐼 es la matriz identidad \(asuma que el producto \n𝐴𝐴𝐴𝐴 tiene inversa\)\. Luego, calcule 𝑋𝑋 si",
     "Despeje X de la ecuación matricial AB(X−I) = C, donde I es la matriz identidad (asuma que el producto AB tiene inversa). Luego, calcule X si", 0),
]))

FIXES.append(("vault/matematicas_ii/2022/extraordinaria/pregunta-1.md", [
    (r"Nota: 𝑎𝑎𝑖𝑖𝑖𝑖 es el elemento que está en la fila 𝑖𝑖 y en la columna 𝑗𝑗 de 𝐴𝐴\.",
     "Nota: aᵢⱼ es el elemento que está en la fila i y en la columna j de A.", 0),
]))

FIXES.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-2.md", [
    (r"𝑋= 𝐴𝐴் e 𝑌= 𝐴்𝐴, siendo 𝐴் la matriz traspuesta de A\.",
     "X = AAᵀ e Y = AᵀA, siendo Aᵀ la matriz traspuesta de A.", 0),
]))

FIXES.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-3.md", [
    (r"𝑝\(𝑥\) = 𝑎𝑥ଷ\+ 𝑏𝑥ଶ\+ 𝑐𝑥\+ 𝑑", "p(x) = ax³+bx²+cx+d", 0),
    (r"lim\n?௫→ଶశ𝑓\(𝑥\) = −∞\.", "lim(x→2⁺) f(x) = −∞.", 0),
    (r"𝑔\(𝑥\) =\n?ସ\n?గమቀ𝑥−\n?గ\n?ଶቁ\n?ଶ\n?,", "g(x) = (4/π²)(x−π/2)²,", 0),
]))

FIXES.append(("vault/matematicas_ii/2026/extraordinaria/pregunta-4.md", [
    (r"𝑟:\n?௫ିଵ\n?ଶ=\n?௬ିଵ\n?ଵ=\n?௭\n?ଷ \.", "r: (x−1)/2 = (y−1)/1 = z/3.", 0),
    (r"𝑃ᇱ simétrico", "P′ simétrico", 0),
]))

FIXES.append(("vault/matematicas_ii/2025/ordinaria/pregunta-2.md", [
    (r"2\.1\.1\. Si 𝐴= #2\n?5\n?2\n?−1\(, halle 𝛼, 𝛽∈ℝ tales que 𝐴\. \+ 𝛼𝐴\+ 𝛽𝐼= 0, donde 𝐼 y 0 son las matrices identidad y cero,\s*\nrespectivamente\.",
     "2.1.1. Si A=(2 5; 2 −1), halle α, β∈ℝ tales que A²+αA+βI=0, donde I y 0 son las matrices identidad y cero, \nrespectivamente.", 0),
    (r"2\.1\.2\. Calcule la matriz cuadrada 𝑋 tal que 𝑋𝐴= 𝐵, si 𝐴= #1\n?0\n?1\n?1\( y 𝐵= #2\n?1\n?1\n?1\(\. ¿Son iguales 𝑋𝐴 y 𝐴𝑋\?",
     "2.1.2. Calcule la matriz cuadrada X tal que XA=B, si A=(1 0; 1 1) y B=(2 1; 1 1). ¿Son iguales XA y AX?", 0),
]))

FIXES.append(("vault/matematicas_ii/2025/ordinaria/pregunta-3.md", [
    (r"𝑓\(𝑥\) = =𝑘𝑥\. \+ 2𝑥\n?si\n?𝑥≤1,\n?𝑥\. −𝑚\n?si\n?𝑥> 1,",
     "f(x) = {kx²+2x si x≤1, x²−m si x>1},", 0),
]))


def process():
    touched = []
    errors = []
    for path, patterns in FIXES:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        original = text
        for pattern, repl, flags in patterns:
            new_text, n = re.subn(pattern, repl, text, count=1, flags=flags)
            if n == 0:
                errors.append((path, pattern))
            else:
                text = new_text
        if text != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            touched.append(path)

    print(f"Archivos tocados: {len(touched)}")
    print(f"Patrones sin encontrar: {len(errors)}")
    for path, pat in errors:
        print(f"  {path}: {pat[:80]}")
    return touched, errors


if __name__ == "__main__":
    process()
