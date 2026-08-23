import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "manifest.csv")

SUBJECT_LABELS = {
    "matematicas_ii": "Matemáticas II",
    "bioloxia": "Bioloxía",
    "fisica": "Física",
    "quimica": "Química",
}
CODE = {"matematicas_ii": "20", "bioloxia": "21", "fisica": "23", "quimica": "24"}

with open(MANIFEST, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

for r in rows:
    if r["año"] != "2015" or r["asignatura"] not in SUBJECT_LABELS.values():
        continue
    subject = [k for k, v in SUBJECT_LABELS.items() if v == r["asignatura"]][0]
    code = CODE[subject]

    if r["convocatoria"] == "ordinaria":
        r["ruta_local"] = f"fuentes/{subject}/2015/ordinaria/{code}_{subject}_ordinaria_2015.pdf"
        r["estado"] = "descargado"
        r["sospecha_escaneado"] = "no"
        r["notas"] = (
            f"El PDF de 2015 traía 2 archivos: uno combinado (ordinaria+extraordinaria+criterios "
            f"mezclados, como en 2020-2024) y otro '_xun' que resultó ser, al abrirlo, 100% "
            f"convocatoria de XUÑO (ordinaria) en gallego y castellano, sin criterios. Se usó este "
            f"último tal cual por ser la versión más completa y limpia para ordinaria."
        )
    else:  # extraordinaria
        r["ruta_local"] = f"fuentes/{subject}/2015/extraordinaria/{code}_{subject}_extraordinaria_2015.pdf"
        r["estado"] = "descargado"
        r["sospecha_escaneado"] = "no"
        r["notas"] = (
            f"La extraordinaria de 2015 solo existía dentro del PDF combinado (no había archivo "
            f"'_xun' equivalente). Se extrajeron sus páginas marcadas 'SETEMBRO 2015' (examen + "
            f"criterios de esa convocatoria) detectando el texto en cada página; las páginas XUÑO "
            f"del mismo combinado se descartaron por ser redundantes con el archivo de ordinaria."
        )

with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print("manifest.csv actualizado.")
