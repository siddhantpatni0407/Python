"""
ATS-Friendly Resume Generator
=============================

Input:
    resume_data.txt

Output:
    Generated_Resume/
        <Name>_Resume.docx
        <Name>_Resume.pdf

Install:
    pip install python-docx reportlab pillow

Run:
    python generate_resume.py
"""

import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, KeepTogether, Table, TableStyle
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "resume_data.txt"
OUTPUT_DIR = BASE_DIR / "Generated_Resume"

NAVY = "0B2E59"        # name / headings / company
BLUE = "1F5FAD"        # accent (rules, bullets, role, separators)
LIGHT_BLUE = "E8F0FA"  # table label fill
BORDER = "B7C9E2"      # table borders
DARK = "1F2933"        # body text
GREY = "52606D"        # meta text

FONT_NAME = "Calibri"
SEP = "  |  "
RIGHT_TAB = Inches(7.07)


# ============================================================
# PDF FONTS (embed Arial for correct ATS text extraction)
# ============================================================

def _register_pdf_fonts():
    """Embed Arial (Unicode-mapped) when available; fall back to Helvetica."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping

    candidates = [Path("C:/Windows/Fonts"), Path("/Library/Fonts"),
                  Path("/usr/share/fonts/truetype/msttcorefonts")]
    files = {"ResumeSans": "arial.ttf", "ResumeSans-Bold": "arialbd.ttf",
             "ResumeSans-Italic": "ariali.ttf", "ResumeSans-BoldItalic": "arialbi.ttf"}
    for folder in candidates:
        if all((folder / f).exists() for f in files.values()):
            for name, f in files.items():
                pdfmetrics.registerFont(TTFont(name, str(folder / f)))
            addMapping("ResumeSans", 0, 0, "ResumeSans")
            addMapping("ResumeSans", 1, 0, "ResumeSans-Bold")
            addMapping("ResumeSans", 0, 1, "ResumeSans-Italic")
            addMapping("ResumeSans", 1, 1, "ResumeSans-BoldItalic")
            return ("ResumeSans", "ResumeSans-Bold", "ResumeSans-Italic")
    return ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique")


PDF_FONT, PDF_FONT_BOLD, PDF_FONT_ITALIC = _register_pdf_fonts()


# ============================================================
# JSON VALIDATION AND DATA LOADING
# ============================================================

def validate_json_file():
    if not DATA_FILE.exists():
        print(f"\nERROR: Data file not found:\n{DATA_FILE}")
        return False
    try:
        with DATA_FILE.open("r", encoding="utf-8-sig") as file:
            json.load(file)
        print("JSON validation successful.")
        return True
    except json.JSONDecodeError as error:
        print("\n" + "=" * 60)
        print("INVALID JSON IN resume_data.txt")
        print("=" * 60)
        print(f"Line   : {error.lineno}")
        print(f"Column : {error.colno}")
        print(f"Error  : {error.msg}")
        lines = DATA_FILE.read_text(encoding="utf-8-sig").splitlines()
        start = max(0, error.lineno - 3)
        end = min(len(lines), error.lineno + 2)
        print("\nProblematic section:")
        for index in range(start, end):
            marker = ">>" if index + 1 == error.lineno else "  "
            print(f"{marker} {index + 1}: {lines[index]}")
        print("\nCheck commas, double quotes and brackets.")
        return False
    except OSError as error:
        print(f"\nUnable to read data file: {error}")
        return False


def load_resume_data():
    with DATA_FILE.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("The JSON root must be an object.")

    for field in ["personal", "summary", "skills", "experience", "education"]:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    personal = data["personal"]
    if not isinstance(personal, dict):
        raise ValueError("'personal' must be a JSON object.")

    for field in ["name", "email", "phone", "location", "target_role"]:
        if not str(personal.get(field, "")).strip():
            raise ValueError(f"Missing personal information: {field}")

    for field in ["skills", "experience", "education"]:
        if not isinstance(data[field], list):
            raise ValueError(f"'{field}' must be a JSON array.")

    return data


# ============================================================
# COMMON HELPERS
# ============================================================

def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def items(value):
    return value if isinstance(value, list) else []


def xml_text(value):
    return escape(clean(value))


def safe_filename(name):
    result = re.sub(r"[^A-Za-z0-9]+", "_", clean(name))
    return result.strip("_") or "Resume"


def skill_rows(data):
    rows = []
    for skill in items(data.get("skills")):
        if isinstance(skill, dict):
            rows.append((clean(skill.get("category", "Skills")),
                         clean(skill.get("items", ""))))
        elif clean(skill):
            rows.append(("Skills", clean(skill)))
    return rows


def personal_detail_rows(data):
    details = data.get("personal_details") or {}
    if not isinstance(details, dict):
        return []
    return [(clean(k), clean(v)) for k, v in details.items() if clean(v)]


def group_experience(experiences):
    """Group consecutive roles at the same company under one heading."""
    groups = []
    for exp in experiences:
        company = clean(exp.get("company"))
        if groups and groups[-1]["company"].lower() == company.lower():
            groups[-1]["roles"].append(exp)
        else:
            groups.append({"company": company,
                           "location": clean(exp.get("location")),
                           "roles": [exp]})
    return groups


def fit_font_size(text, max_width, start=10.5, minimum=8.5,
                  font=None, step=0.25):
    """Largest font size (<= start) at which text fits on one line."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    font = font or PDF_FONT_BOLD
    size = start
    while size > minimum and stringWidth(text, font, size) > max_width:
        size -= step
    return round(size, 2)


def competencies(data):
    text = clean(data.get("core_competencies"))
    return [clean(c) for c in re.split(r"[|\u2022]", text) if clean(c)]


def contact_parts(personal):
    return [clean(personal.get(f)) for f in ["location", "phone", "email"]
            if clean(personal.get(f))]


def profile_links(personal):
    """Returns list of (icon_key, display_text, url)."""
    links = []
    for key in ["linkedin", "github", "portfolio"]:
        value = clean(personal.get(key))
        if value:
            url = value if value.startswith("http") else "https://" + value
            links.append((key, value, url))
    return links


# ============================================================
# ICONS (generated with Pillow, no external files needed)
# ============================================================

def _font(size):
    from PIL import ImageFont
    for name in ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_icons(folder):
    """Create small LinkedIn / GitHub / web PNG icons. Returns {key: path}."""
    from PIL import Image, ImageDraw

    folder.mkdir(parents=True, exist_ok=True)
    size = 96
    white = (255, 255, 255)
    icons = {}

    # LinkedIn: blue rounded square with white "in"
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=16, fill=(10, 102, 194))
    font = _font(62)
    box = d.textbbox((0, 0), "in", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1] + 2), "in",
           font=font, fill=white)
    icons["linkedin"] = folder / "linkedin.png"
    img.save(icons["linkedin"])

    # GitHub: dark circle with simple octocat-style silhouette
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = (36, 41, 47)
    d.ellipse([0, 0, size - 1, size - 1], fill=dark)
    d.ellipse([24, 28, 72, 66], fill=white)
    d.polygon([(26, 40), (28, 18), (42, 30)], fill=white)
    d.polygon([(70, 40), (68, 18), (54, 30)], fill=white)
    d.rectangle([40, 62, 56, 84], fill=white)
    d.ellipse([36, 40, 44, 50], fill=dark)
    d.ellipse([52, 40, 60, 50], fill=dark)
    icons["github"] = folder / "github.png"
    img.save(icons["github"])

    # Portfolio / web globe
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=(31, 95, 173))
    d.ellipse([18, 18, 78, 78], outline=white, width=5)
    d.ellipse([36, 18, 60, 78], outline=white, width=4)
    d.line([18, 48, 78, 48], fill=white, width=4)
    icons["portfolio"] = folder / "web.png"
    img.save(icons["portfolio"])

    return icons


# ============================================================
# DOCX HELPERS
# ============================================================

def set_font(run, size=9.5, bold=False, color=DARK, italic=False):
    run.font.name = FONT_NAME
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT_NAME)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def configure_docx(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.45)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)

    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = RGBColor.from_string(DARK)
    normal.paragraph_format.space_after = Pt(1)
    normal.paragraph_format.line_spacing = 1.0


def add_heading_border(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), BLUE)
    borders.append(bottom)
    p_pr.append(borders)


def add_section(doc, heading):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(7)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.keep_with_next = True
    set_font(paragraph.add_run(heading.upper()), 10.5, True, NAVY)
    add_heading_border(paragraph)


def add_bullet(doc, value, size=9.3):
    value = clean(value)
    if not value:
        return
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.17)
    paragraph.paragraph_format.first_line_indent = Inches(-0.12)
    paragraph.paragraph_format.space_after = Pt(0.5)
    set_font(paragraph.add_run("\u2022 "), size, True, BLUE)
    set_font(paragraph.add_run(value), size, False, DARK)


def add_sep(paragraph, size=8.8):
    set_font(paragraph.add_run(SEP), size, True, BLUE)


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_table_borders(table, color=BORDER):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    tbl_pr.append(borders)


def set_cell_margins(table, top=30, bottom=30, left=80, right=80):
    tbl_pr = table._tbl.tblPr
    margins = OxmlElement("w:tblCellMar")
    for name, value in [("top", top), ("bottom", bottom),
                        ("left", left), ("right", right)]:
        element = OxmlElement(f"w:{name}")
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")
        margins.append(element)
    tbl_pr.append(margins)


def add_key_value_table(doc, rows, label_width, value_width, columns=1):
    """Render (label, value) rows. columns=2 places two pairs per row."""
    if not rows:
        return

    row_count = (len(rows) + columns - 1) // columns
    table = doc.add_table(rows=row_count, cols=2 * columns)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    set_cell_margins(table)

    for row in table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = label_width if i % 2 == 0 else value_width
            if i % 2 == 0:
                shade_cell(cell, LIGHT_BLUE)

    for index, (label, value) in enumerate(rows):
        r, c = divmod(index, columns)
        p = table.cell(r, c * 2).paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        set_font(p.add_run(label), 9, True, NAVY)

        p = table.cell(r, c * 2 + 1).paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        set_font(p.add_run(value), 9, False, DARK)


def add_hyperlink(paragraph, text, url, size=8.8, color=BLUE):
    r_id = paragraph.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), FONT_NAME)
    fonts.set(qn("w:hAnsi"), FONT_NAME)
    r_pr.append(fonts)
    c = OxmlElement("w:color")
    c.set(qn("w:val"), color)
    r_pr.append(c)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    r_pr.append(sz)
    run.append(r_pr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    run.append(t)
    link.append(run)
    paragraph._p.append(link)


# ============================================================
# DOCX SECTIONS
# ============================================================

def add_docx_header(doc, personal, icons):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(0)
    set_font(paragraph.add_run(clean(personal["name"]).upper()), 21, True, NAVY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(2)
    role_text = clean(personal["target_role"])
    # Calibri is narrower than Helvetica, so measuring with Helvetica is safe.
    set_font(paragraph.add_run(role_text),
             fit_font_size(role_text, 7.07 * 72 - 6, start=11), True, BLUE)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(1)
    for i, part in enumerate(contact_parts(personal)):
        if i:
            add_sep(paragraph)
        set_font(paragraph.add_run(part), 8.8, False, GREY)

    links = profile_links(personal)
    if links:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(2)
        for i, (key, text, url) in enumerate(links):
            if i:
                add_sep(paragraph)
            if icons and key in icons:
                paragraph.add_run().add_picture(str(icons[key]), height=Pt(9))
                paragraph.add_run(" ")
            add_hyperlink(paragraph, text, url)


def add_experience_group_docx(doc, group):
    # COMPANY ................................ Location
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(7)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.tab_stops.add_tab_stop(RIGHT_TAB, 2)
    set_font(paragraph.add_run(group["company"].upper()), 10.5, True, NAVY)
    if group["location"]:
        set_font(paragraph.add_run("\t" + group["location"]), 9, False, GREY, True)

    for index, experience in enumerate(group["roles"]):
        # Role ................................. Dates
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(4 if index else 1)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.keep_with_next = True
        paragraph.paragraph_format.tab_stops.add_tab_stop(RIGHT_TAB, 2)
        set_font(paragraph.add_run(clean(experience.get("role"))), 10, True, BLUE)
        if clean(experience.get("dates")):
            set_font(paragraph.add_run("\t" + clean(experience["dates"])), 9, True, NAVY)

        if clean(experience.get("project")):
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(1.5)
            paragraph.paragraph_format.keep_with_next = True
            set_font(paragraph.add_run("Project: "), 8.8, True, GREY, True)
            set_font(paragraph.add_run(clean(experience["project"])), 8.8, False, GREY, True)

        for bullet in items(experience.get("bullets")):
            add_bullet(doc, bullet)


def generate_docx(path, data, icons=None):
    doc = Document()
    configure_docx(doc)
    personal = data["personal"]

    add_docx_header(doc, personal, icons)

    add_section(doc, "Professional Summary")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_font(p.add_run(clean(data["summary"])), 9.3)

    comps = competencies(data)
    if comps:
        add_section(doc, "Core Competencies")
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for i, comp in enumerate(comps):
            if i:
                add_sep(p, 9.2)
            set_font(p.add_run(comp), 9.2, True, DARK)

    rows = skill_rows(data)
    if rows:
        add_section(doc, "Technical Skills")
        add_key_value_table(doc, rows, Inches(1.75), Inches(5.32))

    add_section(doc, "Professional Experience")
    for group in group_experience(data["experience"]):
        add_experience_group_docx(doc, group)

    projects = items(data.get("projects"))
    if projects:
        add_section(doc, "Personal Projects")
        for project in projects:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.keep_with_next = True
            set_font(p.add_run(clean(project.get("name"))), 9.6, True, NAVY)
            if clean(project.get("technology")):
                add_sep(p, 9)
                set_font(p.add_run(clean(project["technology"])), 9, False, BLUE, True)
            if clean(project.get("description")):
                add_bullet(doc, project["description"])

    if data["education"]:
        add_section(doc, "Education")
        for education in data["education"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.tab_stops.add_tab_stop(RIGHT_TAB, 2)
            set_font(p.add_run(clean(education.get("qualification"))), 9.4, True, NAVY)
            if clean(education.get("dates")):
                set_font(p.add_run("\t" + clean(education["dates"])), 9, True, NAVY)
            if clean(education.get("institution")):
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(2)
                set_font(p.add_run(clean(education["institution"])), 9, False, GREY, True)

    certifications = items(data.get("certifications"))
    if certifications:
        add_section(doc, "Certifications")
        for certification in certifications:
            add_bullet(doc, certification)

    awards = items(data.get("awards"))
    if awards:
        add_section(doc, "Awards and Recognitions")
        for award in awards:
            if isinstance(award, dict):
                org = clean(award.get("organization")) or "Award"
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.17)
                p.paragraph_format.first_line_indent = Inches(-0.12)
                p.paragraph_format.space_after = Pt(0.5)
                set_font(p.add_run("\u2022 "), 9.3, True, BLUE)
                set_font(p.add_run(org + ": "), 9.3, True, NAVY)
                for i, entry in enumerate(e for e in items(award.get("items")) if clean(e)):
                    if i:
                        add_sep(p, 9)
                    set_font(p.add_run(clean(entry)), 9.3, False, DARK)
            else:
                add_bullet(doc, award)

    details = personal_detail_rows(data)
    if details:
        add_section(doc, "Personal Details")
        add_key_value_table(doc, details, Inches(1.0), Inches(1.36), columns=3)

    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(footer.add_run(f"{clean(personal['name'])}  |  Resume"), 7.5, False, GREY)

    doc.core_properties.title = f"{personal['name']} - Resume"
    doc.core_properties.author = personal["name"]
    doc.core_properties.subject = personal["target_role"]
    doc.save(path)


# ============================================================
# PDF
# ============================================================

PDF_SEP = f'<font color="#{BLUE}"><b>&nbsp;&nbsp;|&nbsp;&nbsp;</b></font>'


def create_pdf_styles():
    styles = getSampleStyleSheet()
    navy = colors.HexColor("#" + NAVY)
    blue = colors.HexColor("#" + BLUE)
    dark = colors.HexColor("#" + DARK)
    grey = colors.HexColor("#" + GREY)

    def ps(name, **kw):
        base = dict(parent=styles["BodyText"], fontName=PDF_FONT,
                    fontSize=9.5, leading=10.8, textColor=dark, spaceAfter=0)
        base.update(kw)
        return ParagraphStyle(name, **base)

    return {
        "title": ps("Name", fontName=PDF_FONT_BOLD, fontSize=20, leading=23,
                    alignment=TA_CENTER, textColor=navy),
        "role": ps("Role", fontName=PDF_FONT_BOLD, fontSize=10.5, leading=13,
                   alignment=TA_CENTER, textColor=blue, spaceAfter=1),
        "contact": ps("Contact", fontSize=9, leading=11.5, alignment=TA_CENTER,
                      textColor=grey),
        "heading": ps("Heading", fontName=PDF_FONT_BOLD, fontSize=11,
                      leading=13, textColor=navy, spaceBefore=3, spaceAfter=1,
                      keepWithNext=True),
        "body": ps("Body", alignment=TA_JUSTIFY),
        "comp": ps("Comp", alignment=TA_CENTER, leading=12.5),
        "cell_label": ps("CellLabel", fontName=PDF_FONT_BOLD, fontSize=9,
                         leading=10.8, textColor=navy),
        "cell": ps("Cell", fontSize=9, leading=10.8),
        "bullet": ps("Bullet", leftIndent=10, firstLineIndent=-8, spaceAfter=0.2),
        "company": ps("Company", fontName=PDF_FONT_BOLD, fontSize=10.5,
                      leading=12.6, textColor=navy, keepWithNext=True),
        "job": ps("Job", fontName=PDF_FONT_BOLD, fontSize=10,
                  leading=12, textColor=blue, keepWithNext=True),
        "meta": ps("Meta", fontName=PDF_FONT_ITALIC, fontSize=9,
                   leading=10.8, textColor=grey, spaceAfter=1, keepWithNext=True),
        "project": ps("Project", fontName=PDF_FONT_BOLD, spaceBefore=2,
                      textColor=navy, keepWithNext=True),
    }


def pdf_heading(story, heading, styles):
    story.append(Paragraph(xml_text(heading.upper()), styles["heading"]))
    story.append(HRFlowable(width="100%", thickness=0.8,
                            color=colors.HexColor("#" + BLUE),
                            spaceBefore=0, spaceAfter=2))


def pdf_bullet(story, value, styles):
    if clean(value):
        story.append(Paragraph(
            f'<font color="#{BLUE}"><b>&#8226;</b></font> ' + xml_text(value),
            styles["bullet"]))


def pdf_left_right(left, right, styles, style_key="company", right_color=NAVY):
    """Left-aligned rich text with a right-aligned value on the same line."""
    base = styles[style_key]
    right_style = ParagraphStyle(
        f"R_{style_key}", parent=base, alignment=2,
        textColor=colors.HexColor("#" + right_color),
        fontSize=base.fontSize - 0.6)
    table = Table([[Paragraph(left, base),
                    Paragraph(xml_text(right), right_style)]],
                  colWidths=["70%", "30%"])
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    return table


def pdf_kv_table(rows, styles, col_widths, columns=1):
    data_rows = []
    for i in range(0, len(rows), columns):
        line = []
        for label, value in rows[i:i + columns]:
            line += [Paragraph(xml_text(label), styles["cell_label"]),
                     Paragraph(xml_text(value), styles["cell"])]
        while len(line) < 2 * columns:
            line.append("")
        data_rows.append(line)

    table = Table(data_rows, colWidths=col_widths, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#" + BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for c in range(0, 2 * columns, 2):
        commands.append(("BACKGROUND", (c, 0), (c, -1),
                         colors.HexColor("#" + LIGHT_BLUE)))
    table.setStyle(TableStyle(commands))
    return table


def generate_pdf(path, data, icons=None):
    styles = create_pdf_styles()
    personal = data["personal"]
    name = clean(personal["name"])
    role = clean(personal["target_role"])

    left_margin = right_margin = 12.7 * mm  # 0.5 inch
    width = A4[0] - left_margin - right_margin

    # ---------- Header ----------
    story = [
        Paragraph(xml_text(name.upper()), styles["title"]),
        Paragraph(xml_text(role), ParagraphStyle(
            "RoleFit", parent=styles["role"],
            fontSize=fit_font_size(role, width - 4),
            leading=fit_font_size(role, width - 4) + 2.5)),
        Paragraph(PDF_SEP.join(xml_text(p) for p in contact_parts(personal)),
                  styles["contact"]),
    ]
    link_parts = []
    for key, text, url in profile_links(personal):
        icon = ""
        if icons and key in icons:
            icon = f'<img src="{icons[key]}" width="9" height="9" valign="-1.5"/>&nbsp;'
        link_parts.append(
            f'{icon}<a href="{escape(url)}" color="#{BLUE}">{xml_text(text)}</a>')
    if link_parts:
        story.append(Paragraph(PDF_SEP.join(link_parts), styles["contact"]))
    story.append(Spacer(1, 2))

    # ---------- Summary ----------
    pdf_heading(story, "Professional Summary", styles)
    story.append(Paragraph(xml_text(data["summary"]), styles["body"]))

    # ---------- Core competencies ----------
    comps = competencies(data)
    if comps:
        pdf_heading(story, "Core Competencies", styles)
        story.append(Paragraph(
            PDF_SEP.join(f"<b>{xml_text(c)}</b>" for c in comps), styles["comp"]))

    # ---------- Skills ----------
    rows = skill_rows(data)
    if rows:
        pdf_heading(story, "Technical Skills", styles)
        story.append(pdf_kv_table(rows, styles, [width * 0.25, width * 0.75]))

    # ---------- Experience ----------
    pdf_heading(story, "Professional Experience", styles)
    for group_index, group in enumerate(group_experience(data["experience"])):
        header = [Spacer(1, 3 if group_index else 1),
                  pdf_left_right(xml_text(group["company"].upper()),
                                 group["location"], styles, "company",
                                 right_color=GREY)]
        for role_index, experience in enumerate(group["roles"]):
            block = header if role_index == 0 else [Spacer(1, 3)]
            block.append(pdf_left_right(xml_text(experience.get("role")),
                                        experience.get("dates"), styles, "job"))
            if clean(experience.get("project")):
                block.append(Paragraph(
                    "<b>Project:</b> " + xml_text(experience["project"]),
                    styles["meta"]))

            bullets = items(experience.get("bullets"))
            if bullets:
                pdf_bullet(block, bullets[0], styles)
            story.append(KeepTogether(block))
            for bullet in bullets[1:]:
                pdf_bullet(story, bullet, styles)

    # ---------- Projects ----------
    projects = items(data.get("projects"))
    if projects:
        pdf_heading(story, "Personal Projects", styles)
        for project in projects:
            title = xml_text(project.get("name"))
            if clean(project.get("technology")):
                title += PDF_SEP + (f'<font color="#{BLUE}" name="{PDF_FONT_ITALIC}">'
                                    f'{xml_text(project["technology"])}</font>')
            block = [Paragraph(title, styles["project"])]
            if clean(project.get("description")):
                pdf_bullet(block, project["description"], styles)
            story.append(KeepTogether(block))

    # ---------- Education ----------
    education = items(data.get("education"))
    if education:
        pdf_heading(story, "Education", styles)
        for item in education:
            block = [pdf_left_right(xml_text(item.get("qualification")),
                                    item.get("dates"), styles)]
            if clean(item.get("institution")):
                block.append(Paragraph(xml_text(item["institution"]), styles["meta"]))
            story.append(KeepTogether(block))

    # ---------- Certifications ----------
    certifications = items(data.get("certifications"))
    if certifications:
        pdf_heading(story, "Certifications", styles)
        for certification in certifications:
            pdf_bullet(story, certification, styles)

    # ---------- Awards ----------
    awards = items(data.get("awards"))
    if awards:
        pdf_heading(story, "Awards and Recognitions", styles)
        for award in awards:
            if isinstance(award, dict):
                org = clean(award.get("organization")) or "Award"
                text = PDF_SEP.join(xml_text(i) for i in items(award.get("items")) if clean(i))
                story.append(Paragraph(
                    f'<font color="#{BLUE}"><b>&#8226;</b></font> '
                    f'<font color="#{NAVY}"><b>{xml_text(org)}:</b></font> {text}',
                    styles["bullet"]))
            else:
                pdf_bullet(story, award, styles)

    # ---------- Personal details ----------
    details = personal_detail_rows(data)
    if details:
        block = []
        pdf_heading(block, "Personal Details", styles)
        block.append(pdf_kv_table(
            details, styles,
            [width * f for f in (0.14, 0.18, 0.14, 0.20, 0.13, 0.21)],
            columns=3))
        story.append(KeepTogether(block))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont(PDF_FONT, 8)
        canvas.setFillColor(colors.HexColor("#" + GREY))
        canvas.drawCentredString(A4[0] / 2, 5 * mm,
                                 f"Page {document.page}")
        canvas.restoreState()

    pdf = SimpleDocTemplate(
        str(path), pagesize=A4,
        rightMargin=right_margin, leftMargin=left_margin,
        topMargin=10 * mm, bottomMargin=10 * mm,
        title=f"{name} - Resume", author=name, subject=role,
        creator="Resume Generator", keywords=role.replace("|", ","))
    pdf.build(story, onFirstPage=footer, onLaterPages=footer)
    return pdf.page


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("       PROFESSIONAL ATS RESUME GENERATOR")
    print("=" * 60)
    try:
        print("\nStep 1: Validating resume_data.txt...")
        if not validate_json_file():
            sys.exit(1)

        print("\nStep 2: Loading resume information...")
        data = load_resume_data()
        print("Resume information loaded successfully.")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = safe_filename(data["personal"]["name"])
        docx_path = OUTPUT_DIR / f"{filename}_Resume.docx"
        pdf_path = OUTPUT_DIR / f"{filename}_Resume.pdf"

        try:
            icons = create_icons(OUTPUT_DIR / "_icons")
        except ImportError:
            print("Pillow not installed - generating without icons (pip install pillow).")
            icons = None

        print("\nStep 3: Generating DOCX...")
        generate_docx(docx_path, data, icons)
        print("DOCX generated successfully.")

        print("\nStep 4: Generating PDF...")
        pages = generate_pdf(pdf_path, data, icons)
        print(f"PDF generated successfully ({pages} page(s)).")

        print("\n" + "=" * 60)
        print("       RESUME GENERATION COMPLETED")
        print("=" * 60)
        print(f"\nDOCX: {docx_path}")
        print(f"PDF : {pdf_path}")
        print("\nPlease verify all resume information before applying.")
    except Exception as error:
        print("\n" + "=" * 60)
        print("RESUME GENERATION FAILED")
        print("=" * 60)
        print(f"\nError: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

