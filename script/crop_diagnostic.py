import fitz
import os

SCRATCH = r"C:\Users\raisa\AppData\Local\Temp\claude\C--Users-raisa-Destructor-de-PAU\f3cb49d5-73a6-4f43-89ff-6ecbabc3ef64\scratchpad"


def crop_between(path, pageno, start_text, end_text, outname, pad=15):
    doc = fitz.open(path)
    page = doc[pageno]
    rects_start = page.search_for(start_text)
    rects_end = page.search_for(end_text) if end_text else []
    page_rect = page.rect
    y0 = rects_start[0].y0 - pad if rects_start else page_rect.y0
    y1 = rects_end[0].y0 - pad if rects_end else page_rect.y1
    clip = fitz.Rect(page_rect.x0, max(y0, page_rect.y0), page_rect.x1, min(y1, page_rect.y1))
    mat = fitz.Matrix(4, 4)
    pix = page.get_pixmap(matrix=mat, clip=clip)
    out = os.path.join(SCRATCH, outname)
    pix.save(out)
    print(outname, pix.width, pix.height, "clip=", clip)


crop_between("fuentes/fisica/2020/extraordinaria/23_fisica_extraordinaria_2020.pdf", 1,
             "PREGUNTA 1", "PREGUNTA 2", "fisica_2020_extra_q1.png")
crop_between("fuentes/quimica/2022/extraordinaria/24_quimica_extraordinaria_2022.pdf", 1,
             "PREGUNTA 3", "PREGUNTA 4", "quimica_2022_extra_q3.png")
crop_between("fuentes/matematicas_ii/2020/extraordinaria/20_matematicas_ii_extraordinaria_2020.pdf", 1,
             "1. Números", "2. Números", "mat_2020_extra_q1.png")
