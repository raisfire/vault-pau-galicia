"""
Fase 1a - Rastreo de las paginas indice de ciug.gal para localizar los PDF
de examenes de Matematicas II, Bioloxia, Fisica y Quimica (2010-2026).

No construye URLs por patron: lee las paginas indice reales y resuelve los
enlaces /link/xxxx (redirects) al PDF final.
"""
import re
import time
import requests
import urllib3
import lxml.html

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://ciug.gal"

# Subject codes as used by CIUG tables -> our folder slug
SUBJECTS = {
    "20": "matematicas_ii",
    "21": "bioloxia",
    "23": "fisica",
    "24": "quimica",
}

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ABAU-catalog-script/1.0)"})


def resolve_link(short_url: str) -> str:
    """Follow a /link/xxxx redirect and return the final URL (no download)."""
    r = SESSION.head(short_url, allow_redirects=True, timeout=30)
    return r.url


def get(url: str) -> str:
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def row_subject_code(strong_text: str):
    m = re.match(r"\s*(\d{2})\s+", strong_text)
    return m.group(1) if m else None


def parse_table_2020_2024():
    """/pau/exames: one <table>, columns = years 2020..2024, one PDF link per cell (bundled file)."""
    html = get(f"{BASE}/pau/exames")
    doc = lxml.html.fromstring(html)
    table = doc.cssselect("table.ql-table-better")[0]
    rows = table.cssselect("tr")
    header_cells = rows[0].cssselect("td")
    years = [c.text_content().strip() for c in header_cells[1:]]  # skip "Materia"

    results = []  # (code, year, pdf_href or None)
    for row in rows[1:]:
        cells = row.cssselect("td")
        subject_label = cells[0].text_content().strip()
        code = row_subject_code(subject_label)
        if code not in SUBJECTS:
            continue
        for year, cell in zip(years, cells[1:]):
            link = cell.cssselect("a")
            href = link[0].get("href") if link else None
            results.append((code, year, href))
    return results


def parse_table_2025():
    """/pau/exames-pau-2025: table with 4 columns: Exames ord, Criterios ord, Exames extra, Criterios extra."""
    html = get(f"{BASE}/pau/exames-pau-2025")
    doc = lxml.html.fromstring(html)
    table = doc.cssselect("table.ql-table-better")[0]
    rows = table.cssselect("tr")
    results = []
    for row in rows[1:]:
        cells = row.cssselect("td")
        subject_label = cells[0].text_content().strip()
        code = row_subject_code(subject_label)
        if code not in SUBJECTS:
            continue
        hrefs = []
        for cell in cells[1:5]:
            a = cell.cssselect("a")
            hrefs.append(a[0].get("href") if a else None)
        # hrefs: [exame_ord, criterios_ord, exame_extra, criterios_extra]
        while len(hrefs) < 4:
            hrefs.append(None)
        results.append((code, hrefs[0], hrefs[1], hrefs[2], hrefs[3]))
    return results


def parse_paragraph_2026():
    """/exames-pau-2026: <p><strong>CODE Name</strong></p><ol><li><a>Exames ordinaria</a>...</ol> per subject."""
    html = get(f"{BASE}/exames-pau-2026")
    doc = lxml.html.fromstring(html)
    article = doc.cssselect("article")[0]
    results = []
    children = list(article.cssselect("div.civil")[0])
    current_code = None
    for el in children:
        if el.tag == "p":
            strong = el.cssselect("strong")
            if strong:
                current_code = row_subject_code(strong[0].text_content().strip())
        elif el.tag == "ol" and current_code in SUBJECTS:
            links = {}
            for li in el.cssselect("li"):
                a = li.cssselect("a")
                if not a:
                    continue
                label = a[0].text_content().strip().lower()
                href = a[0].get("href")
                if "exames ordinaria" in label:
                    links["exame_ord"] = href
                elif "criterios ordinaria" in label:
                    links["criterios_ord"] = href
                elif "exames extraordinaria" in label:
                    links["exame_extra"] = href
                elif "criterios extraordinaria" in label:
                    links["criterios_extra"] = href
            results.append((current_code, links.get("exame_ord"), links.get("criterios_ord"),
                             links.get("exame_extra"), links.get("criterios_extra")))
            current_code = None
    return results


if __name__ == "__main__":
    print("=== 2020-2024 ===")
    for row in parse_table_2020_2024():
        print(row)
    print("=== 2025 ===")
    for row in parse_table_2025():
        print(row)
    print("=== 2026 ===")
    for row in parse_paragraph_2026():
        print(row)
