# -*- coding: utf-8 -*-
"""Normaliza variantes de mayusculas/minusculas en tema: de
vault/castelan/ y script/stats_castellano_2010_2019.json que violan el
enum estricto (mismo patron visto en Historia da Filosofia). Tambien
deduplica temas repetidos."""
import glob
import json
import re
import sys

sys.path.insert(0, "script")
from castellano_temas import TEMAS_CASTELLANO

canon = set(TEMAS_CASTELLANO)
canon_lower = {t.lower(): t for t in TEMAS_CASTELLANO}


def yaml_escape(s):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def fix_vault():
    fixed_files = 0
    for path in glob.glob("vault/castelan/*/*/*.md"):
        text = open(path, encoding="utf-8").read()
        fm = text.split("---", 2)[1]
        import yaml
        meta = yaml.safe_load(fm)
        temas = meta.get("tema") or []
        if not temas:
            continue
        new_temas = []
        changed = False
        for t in temas:
            if t in canon:
                if t not in new_temas:
                    new_temas.append(t)
                else:
                    changed = True
                continue
            c = canon_lower.get(t.lower())
            if c:
                changed = True
                if c not in new_temas:
                    new_temas.append(c)
            else:
                print("NO MATCH:", path, repr(t))
                new_temas.append(t)
        if changed:
            block = "tema:\n" + "\n".join(f"  - {yaml_escape(x)}" for x in new_temas) + "\n"
            new_text = re.sub(r"^tema:(\n(  - .*\n?)+|\s*\[\]\n)", block, text, count=1, flags=re.MULTILINE)
            open(path, "w", encoding="utf-8").write(new_text)
            fixed_files += 1
    print("vault fixed files:", fixed_files)


def fix_stats():
    path = "script/stats_castellano_2010_2019.json"
    import os
    if not os.path.exists(path):
        print("stats file not found yet, skipping")
        return
    data = json.load(open(path, encoding="utf-8"))
    fixed = 0
    for r in data:
        new_temas = []
        changed = False
        for t in r["temas"]:
            if t == "sin_clasificar" or t in canon:
                if t not in new_temas:
                    new_temas.append(t)
                else:
                    changed = True
                continue
            c = canon_lower.get(t.lower())
            if c:
                changed = True
                if c not in new_temas:
                    new_temas.append(c)
            else:
                print("NO MATCH (stats):", r["year"], r["conv"], repr(t))
                new_temas.append(t)
        if changed:
            r["temas"] = new_temas
            fixed += 1
    print("stats fixed records:", fixed)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    fix_vault()
    fix_stats()
