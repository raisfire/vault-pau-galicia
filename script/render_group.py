import fitz
import re
import os

SCRATCH = r"C:\Users\raisa\AppData\Local\Temp\claude\C--Users-raisa-Destructor-de-PAU\f3cb49d5-73a6-4f43-89ff-6ecbabc3ef64\scratchpad\render"
os.makedirs(SCRATCH, exist_ok=True)

INTRO_CAST_RE = re.compile(r"examen\s+consta\s+de", re.IGNORECASE)
CRIT_RE = re.compile(r"CRITERIOS", re.IGNORECASE)

FILES = [
    "fuentes/quimica/2020/extraordinaria/24_quimica_extraordinaria_2020.pdf",
    "fuentes/quimica/2021/ordinaria/24_quimica_ordinaria_2021.pdf",
    "fuentes/quimica/2024/extraordinaria/24_quimica_extraordinaria_2024.pdf",
    "fuentes/quimica/2026/extraordinaria/24_quimica_extraordinaria_2026.pdf",
    "fuentes/quimica/2020/ordinaria/24_quimica_ordinaria_2020.pdf",
    "fuentes/quimica/2021/extraordinaria/24_quimica_extraordinaria_2021.pdf",
    "fuentes/quimica/2022/extraordinaria/24_quimica_extraordinaria_2022.pdf",
    "fuentes/quimica/2023/ordinaria/24_quimica_ordinaria_2023.pdf",
    "fuentes/quimica/2025/extraordinaria/24_quimica_extraordinaria_2025.pdf",
    "fuentes/quimica/2025/ordinaria/24_quimica_ordinaria_2025.pdf",
    "fuentes/fisica/2026/ordinaria/23_fisica_ordinaria_2026.pdf",
    "fuentes/fisica/2025/ordinaria/23_fisica_ordinaria_2025.pdf",
    "fuentes/fisica/2026/extraordinaria/23_fisica_extraordinaria_2026.pdf",
]

for path in FILES:
    doc = fitz.open(path)
    n = len(doc)
    cast_start = next((i for i in range(n) if INTRO_CAST_RE.search(doc[i].get_text())), n // 2)
    crit_idx = next((i for i in range(cast_start, n) if CRIT_RE.search(doc[i].get_text())), n)
    end_page = min(crit_idx + 1, n)  # include the page criteria starts on, just in case boundary is fuzzy, but stop there
    base = path.replace("fuentes/", "").replace("/", "_").replace(".pdf", "")
    for i in range(cast_start, end_page):
        page = doc[i]
        mat = fitz.Matrix(3, 3)
        pix = page.get_pixmap(matrix=mat)
        out = os.path.join(SCRATCH, f"{base}__p{i}.png")
        pix.save(out)
    print(f"{path}: cast_start={cast_start} crit_idx={crit_idx} rendered pages {list(range(cast_start, end_page))}")
