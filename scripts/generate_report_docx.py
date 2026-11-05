"""
Generador del Reporte Técnico en Word (.docx), mismo contenido y formato clásico que el PDF.
Reutiliza el contenido de generate_report_pdf.py para que ambos documentos sean idénticos.

Formato: Arial 12, interlineado 1.5, justificado, títulos 16, subtítulos 14,
tablas con cuadrícula negra, sin colores, solo número de página.
"""

import html
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from reportlab.platypus import PageBreak, Spacer, Table

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_report_pdf as gen  # noqa: E402


def set_font(run_or_style, name="Arial", size=None, bold=None):
    f = run_or_style.font
    f.name = name
    f.color.rgb = RGBColor(0, 0, 0)
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    rpr = run_or_style.element.get_or_add_rPr() if hasattr(run_or_style, "element") and hasattr(run_or_style.element, "get_or_add_rPr") else None
    if rpr is None:
        rpr = run_or_style._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def configure_styles(doc):
    normal = doc.styles["Normal"]
    set_font(normal, size=12)
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(6)
    pf.space_before = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size, before, after in (("Heading 1", 16, 12, 8), ("Heading 2", 14, 10, 6)):
        st = doc.styles[name]
        set_font(st, size=size, bold=True)
        st.font.italic = False
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.line_spacing = 1.5
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        st.paragraph_format.keep_with_next = True


def add_page_number_footer(section):
    section.different_first_page_header_footer = True
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    set_font(run, size=10)
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)


def clean_text(raw):
    """Convierte el marcado interno de reportlab en texto plano con saltos de línea."""
    align = None
    m = re.search(r"<para[^>]*align='(\w+)'", raw)
    if m:
        align = m.group(1)
    raw = re.sub(r"</?para[^>]*>", "", raw)
    raw = re.sub(r"<br\s*/?>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return html.unescape(raw), align


def write_runs(paragraph, text, size, bold=False):
    parts = text.split("\n")
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        set_font(run, size=size, bold=bold)
        if i < len(parts) - 1:
            run.add_break(WD_BREAK.LINE)


def set_cell_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)


def add_table(doc, flowable):
    rows = flowable._cellvalues
    widths = flowable._colWidths
    table = doc.add_table(rows=len(rows), cols=len(widths))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_cell_borders(table)
    for r, row in enumerate(rows):
        for c, cell_flow in enumerate(row):
            cell = table.cell(r, c)
            cell.width = Pt(widths[c])
            text, _ = clean_text(cell_flow.text)
            size = 8 if cell_flow.style.name == "TableCellTiny" else 10
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            write_runs(p, text, size, bold=(r == 0))
    # encabezado repetido en cada página
    trPr = table.rows[0]._tr.get_or_add_trPr()
    hdr = OxmlElement("w:tblHeader")
    hdr.set(qn("w:val"), "true")
    trPr.append(hdr)
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        cant.set(qn("w:val"), "true")
        trPr.append(cant)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)


COVER = {"CoverUniv": (16, True), "CoverCareer": (14, True), "CoverTitle": (14, True), "CoverMeta": (12, False)}


def convert(story, out_path):
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    configure_styles(doc)
    add_page_number_footer(sec)

    pending = 0.0
    for fl in story:
        if isinstance(fl, Spacer):
            pending += fl.height
            continue
        if isinstance(fl, PageBreak):
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            pending = 0.0
            continue
        if isinstance(fl, Table):
            add_table(doc, fl)
            pending = 0.0
            continue
        if fl.__class__.__name__ == "Image":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.line_spacing = 1.0
            p.add_run().add_picture(fl.filename, width=Pt(fl.drawWidth))
            pending = 0.0
            continue

        # Párrafo
        name = fl.style.name
        text, align = clean_text(fl.text)
        if name == "H1":
            p = doc.add_paragraph(style="Heading 1")
            write_runs(p, text, 16, bold=True)
        elif name == "H2":
            p = doc.add_paragraph(style="Heading 2")
            write_runs(p, text, 14, bold=True)
        elif name in COVER:
            size, bold = COVER[name]
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            write_runs(p, text, size, bold=bold)
        elif name == "Caption":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.15
            write_runs(p, text, 10)
        else:
            p = doc.add_paragraph()
            if align == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif align == "left":
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            write_runs(p, text, 12)
        if pending:
            p.paragraph_format.space_before = Pt(min(pending, 60))
            pending = 0.0

    doc.core_properties.title = "CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION"
    doc.core_properties.author = "Clemente Velasco Alhan (233319)"
    doc.save(str(out_path))
    print(f"DOCX generado exitosamente en: {out_path}")


class _FakeDoc:
    """Sustituye a SimpleDocTemplate para capturar la historia y convertirla a .docx."""

    def __init__(self, filename, **kwargs):
        self.path = Path(filename).with_suffix(".docx")

    def build(self, story, **kwargs):
        convert(list(story), self.path)


if __name__ == "__main__":
    gen.SimpleDocTemplate = _FakeDoc
    gen.generar_pdf()
