# -*- coding: utf-8 -*-
"""Descarga fuentes/ 2020-2026 para las 5 asignaturas de Oleada 2.

- 2025-2026: la CIUG ya publica un PDF separado por convocatoria -> se
  guarda directamente en ordinaria/extraordinaria.
- 2020-2024: un unico PDF combina ambas convocatorias (y a veces
  modelo/criterios) -> se guarda TAL CUAL, sin dividir todavia, en
  fuentes/<asignatura>/<year>/sin_dividir_<year>.pdf. Dividirlo requiere
  disenar el marcador de bloque para cada asignatura (la frase fija que
  usan Mate/Bio/Fisica/Quimica, "O exame consta de 8 preguntas", es
  especifica de esas 4 y no vale aqui) - eso es un paso aparte, no
  "descargar fuentes".
"""
import os
import sys

import requests
import urllib3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_index import (
    parse_table_2020_2024, parse_table_2025, parse_paragraph_2026,
    resolve_link, SUBJECTS, BASE,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SUBJECTS.clear()
SUBJECTS.update({
    "01": "castelan", "02": "galego", "03": "historiaespana",
    "08": "historiafilosofia", "34": "historiafilosofia", "11": "ingles",
})

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ABAU-catalog-script/1.0)"})

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(ROOT, "fuentes")


def download(url, dest):
    if not url:
        return False
    if url.startswith("/"):
        url = BASE + url
    r = SESSION.get(url, timeout=60, allow_redirects=True)
    r.raise_for_status()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(r.content)
    return True


def main():
    ok = []
    missing = []

    print("=== 2020-2024 (combinado, sin dividir) ===")
    for code, year, href in parse_table_2020_2024():
        subject = SUBJECTS[code]
        if not href:
            missing.append((subject, year, "sin enlace"))
            continue
        dest = os.path.join(FUENTES, subject, year, f"sin_dividir_{year}.pdf")
        try:
            download(href, dest)
            ok.append((subject, year, "combinado"))
            print(f"  {subject} {year}: OK")
        except Exception as e:
            missing.append((subject, year, str(e)))
            print(f"  {subject} {year}: ERROR {e}")

    print("\n=== 2025 (ya dividido en origen) ===")
    for code, ord_href, _crit_ord, extra_href, _crit_extra in parse_table_2025():
        subject = SUBJECTS[code]
        for conv, href in [("ordinaria", ord_href), ("extraordinaria", extra_href)]:
            if not href:
                missing.append((subject, "2025", f"{conv} sin enlace"))
                continue
            dest = os.path.join(FUENTES, subject, "2025", conv, f"{code}_{subject}_{conv}_2025.pdf")
            try:
                download(href, dest)
                ok.append((subject, "2025", conv))
                print(f"  {subject} 2025 {conv}: OK")
            except Exception as e:
                missing.append((subject, "2025", str(e)))
                print(f"  {subject} 2025 {conv}: ERROR {e}")

    print("\n=== 2026 (ya dividido en origen) ===")
    for code, ord_href, _crit_ord, extra_href, _crit_extra in parse_paragraph_2026():
        subject = SUBJECTS[code]
        for conv, href in [("ordinaria", ord_href), ("extraordinaria", extra_href)]:
            if not href:
                missing.append((subject, "2026", f"{conv} sin enlace"))
                continue
            dest = os.path.join(FUENTES, subject, "2026", conv, f"{code}_{subject}_{conv}_2026.pdf")
            try:
                download(href, dest)
                ok.append((subject, "2026", conv))
                print(f"  {subject} 2026 {conv}: OK")
            except Exception as e:
                missing.append((subject, "2026", str(e)))
                print(f"  {subject} 2026 {conv}: ERROR {e}")

    print(f"\nTotal OK: {len(ok)}")
    print(f"Total con problemas: {len(missing)}")
    for m in missing:
        print(" ", m)


if __name__ == "__main__":
    main()
