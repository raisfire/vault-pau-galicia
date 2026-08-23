import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "manifest.csv"), encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

total = len(rows)
by_estado = {}
for r in rows:
    by_estado.setdefault(r["estado"], []).append(r)

print(f"Total de filas en el manifest: {total}")
print(f"(4 asignaturas x {total // 8} años x 2 convocatorias)")
print()
for estado, items in sorted(by_estado.items(), key=lambda kv: -len(kv[1])):
    print(f"  {estado}: {len(items)}")

print()
scanned = [r for r in rows if r["sospecha_escaneado"] == "si"]
print(f"PDFs con sospecha de ser escaneados (sin texto seleccionable): {len(scanned)}")
for r in scanned:
    print(f"  - {r['asignatura']} {r['año']} {r['convocatoria']}")

print()
print("=== Huecos / filas que requieren atención (no 'descargado') ===")
gaps = [r for r in rows if r["estado"] != "descargado"]
gaps.sort(key=lambda r: (r["asignatura"], r["año"], r["convocatoria"]))
current_subj = None
for r in gaps:
    if r["asignatura"] != current_subj:
        current_subj = r["asignatura"]
        print(f"\n{current_subj}:")
    print(f"  {r['año']} {r['convocatoria']:15s} -> {r['estado']}")
