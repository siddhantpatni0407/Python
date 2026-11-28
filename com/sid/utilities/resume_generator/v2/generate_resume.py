"""
ATS-Friendly Resume Generator (Professional, Black & White)
===========================================================

ATS best practices applied:
    * Single-column layout, NO tables, NO images/icons, NO text boxes
    * Black text only, standard fonts (Calibri / Arial)
    * Standard section headings (Summary, Skills, Experience, Education ...)
    * Plain text contact details in the document body (not header/footer)
    * Simple bullets, consistent date format on the same line as the role
    * Embedded Unicode font in PDF so text extraction is accurate

Input : resume_data.txt
Output: Generated_Resume/<Name>_Resume.docx and .pdf

Install: pip install python-docx reportlab
Run    : python generate_resume.py
"""

import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Flowable

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "resume_data.txt"
OUTPUT_DIR = BASE_DIR / "Generated_Resume"

BLACK = "000000"
FONT_NAME = "Calibri"
SEP = " | "
RIGHT_TAB = Inches(7.27)
MAX_PAGES = 2          # target page count
MIN_SCALE = 0.80       # never shrink fonts below 80% (keeps text readable)
SCALE = 1.0            # font/spacing scale, auto-tuned in main()


# ============================================================
# PDF FONTS
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
            return "ResumeSans", "ResumeSans-Bold", "ResumeSans-Italic"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


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
        for index in range(max(0, error.lineno - 3), min(len(lines), error.lineno + 2)):
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


def bold_segments(value):
    """Split text with **bold** markers into (text, is_bold) segments."""
    parts = re.split(r"\*\*(.+?)\*\*", clean(value))
    return [(part, index % 2 == 1) for index, part in enumerate(parts) if part]


def plain_text(value):
    """Text without **bold** markers (for metadata and plain output)."""
    return clean(value).replace("**", "")


def rich_xml(value):
    """ReportLab markup with **bold** converted to <b> tags."""
    return "".join(f"<b>{escape(t)}</b>" if b else escape(t) for t, b in bold_segments(value))


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
    """Group consecutive roles at the same company."""
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


def competencies(data):
    text = clean(data.get("core_competencies"))
    return [clean(c) for c in re.split(r"[|\u2022,]", text) if clean(c)]


def contact_line(personal):
    parts = [clean(personal.get(f)) for f in ["location", "phone", "email"]]
    return SEP.join(p for p in parts if p)


def links_line(personal):
    parts = [clean(personal.get(k)) for k in ["linkedin", "github", "portfolio"]]
    return SEP.join(p for p in parts if p)


def award_text(award):
    if isinstance(award, dict):
        org = clean(award.get("organization")) or "Award"
        entries = ", ".join(clean(e) for e in items(award.get("items")) if clean(e))
        return f"{org}: {entries}" if entries else org
    return clean(award)


# ============================================================
# DOCX
# ============================================================

def set_font(run, size=10.5, bold=False, italic=False):
    run.font.name = FONT_NAME
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT_NAME)
    run.font.size = Pt(round(size * SCALE * 2) / 2)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(BLACK)


def configure_docx(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)

    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
    normal.font.size = Pt(round(10.5 * SCALE * 2) / 2)
    normal.font.color.rgb = RGBColor.from_string(BLACK)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0


def add_bottom_rule(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), BLACK)
    borders.append(bottom)
    p_pr.append(borders)


def add_para(doc, text="", size=10.5, bold=False, italic=False,
             align=None, before=0, after=1, keep=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_before = Pt(before * SCALE)
    p.paragraph_format.space_after = Pt(after * SCALE)
    p.paragraph_format.keep_with_next = keep
    if text:
        set_font(p.add_run(text), size, bold, italic)
    return p


def add_section(doc, heading):
    p = add_para(doc, heading.upper(), 11.5, True, before=6, after=2, keep=True)
    add_bottom_rule(p)


def add_bullet(doc, value):
    value = clean(value)
    if not value:
        return
    try:
        p = doc.add_paragraph(style="List Bullet")
    except KeyError:
        p = doc.add_paragraph()
        set_font(p.add_run("\u2022 "), 10.5)
    p.paragraph_format.space_after = Pt(1)
    set_font(p.add_run(value), 10.5)


def add_left_right(doc, left, right, bold=True, before=0, italic_right=False):
    p = add_para(doc, before=before, after=0, keep=True)
    p.paragraph_format.tab_stops.add_tab_stop(RIGHT_TAB, WD_TAB_ALIGNMENT.RIGHT)
    set_font(p.add_run(left), 10.5, bold)
    if right:
        set_font(p.add_run("\t" + right), 10.5, False, italic_right)
    return p


def generate_docx(path, data):
    doc = Document()
    configure_docx(doc)
    personal = data["personal"]
    center = WD_ALIGN_PARAGRAPH.CENTER

    # Header (in body, not in Word header - ATS often ignores headers)
    add_para(doc, clean(personal["name"]).upper(), 18, True, align=center, after=0)
    add_para(doc, clean(personal["target_role"]), 11, True, align=center, after=1)
    add_para(doc, contact_line(personal), 10, align=center, after=0)
    if links_line(personal):
        add_para(doc, links_line(personal), 10, align=center, after=2)

    add_section(doc, "Professional Summary")
    p = add_para(doc, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    for text, is_bold in bold_segments(data["summary"]):
        set_font(p.add_run(text), 10.5, is_bold)

    comps = competencies(data)
    if comps:
        add_section(doc, "Core Competencies")
        add_para(doc, SEP.join(comps))

    rows = skill_rows(data)
    if rows:
        add_section(doc, "Technical Skills")
        for label, value in rows:
            p = add_para(doc, after=1)
            set_font(p.add_run(f"{label}: "), 10.5, True)
            set_font(p.add_run(value), 10.5)

    add_section(doc, "Professional Experience")
    for g_index, group in enumerate(group_experience(data["experience"])):
        for r_index, exp in enumerate(group["roles"]):
            title = clean(exp.get("role"))
            company = group["company"]
            if group["location"]:
                company += f", {group['location']}"
            add_left_right(doc, title, clean(exp.get("dates")),
                           before=6 if (g_index or r_index) else 2)
            add_para(doc, company, 10.5, italic=True, after=1, keep=True)
            if clean(exp.get("project")):
                p = add_para(doc, after=1, keep=True)
                set_font(p.add_run("Project: "), 10.5, True)
                set_font(p.add_run(clean(exp["project"])), 10.5)
            for bullet in items(exp.get("bullets")):
                add_bullet(doc, bullet)

    projects = items(data.get("projects"))
    if projects:
        add_section(doc, "Projects")
        for project in projects:
            title = clean(project.get("name"))
            if clean(project.get("technology")):
                title += f" ({clean(project['technology'])})"
            add_para(doc, title, 10.5, True, before=3, after=0, keep=True)
            add_bullet(doc, project.get("description"))

    if data["education"]:
        add_section(doc, "Education")
        for edu in data["education"]:
            add_left_right(doc, clean(edu.get("qualification")),
                           clean(edu.get("dates")), before=2)
            if clean(edu.get("institution")):
                add_para(doc, clean(edu["institution"]), 10.5, after=2)

    certifications = items(data.get("certifications"))
    if certifications:
        add_section(doc, "Certifications")
        for cert in certifications:
            add_bullet(doc, cert)

    awards = items(data.get("awards"))
    if awards:
        add_section(doc, "Awards")
        for award in awards:
            add_bullet(doc, award_text(award))

    details = personal_detail_rows(data)
    if details:
        add_section(doc, "Personal Details")
        for label, value in details:
            p = add_para(doc, after=0)
            set_font(p.add_run(f"{label}: "), 10.5, True)
            set_font(p.add_run(value), 10.5)

    doc.core_properties.title = f"{personal['name']} - Resume"
    doc.core_properties.author = personal["name"]
    doc.core_properties.subject = personal["target_role"]
    doc.core_properties.keywords = ", ".join(comps)
    doc.save(path)


# ============================================================
# PDF
# ============================================================

def create_pdf_styles(scale=1.0):
    styles = getSampleStyleSheet()
    black = colors.black

    def ps(name, **kw):
        base = dict(parent=styles["BodyText"], fontName=PDF_FONT,
                    fontSize=10, leading=12, textColor=black,
                    spaceBefore=0, spaceAfter=0.5)
        base.update(kw)
        for key in ("fontSize", "leading", "spaceBefore", "spaceAfter",
                    "leftIndent", "bulletIndent"):
            if key in base:
                base[key] = base[key] * scale
        return ParagraphStyle(name, **base)

    return {
        "title": ps("Name", fontName=PDF_FONT_BOLD, fontSize=18, leading=21,
                    alignment=TA_CENTER, spaceAfter=0),
        "role": ps("Role", fontName=PDF_FONT_BOLD, fontSize=11, leading=14,
                   alignment=TA_CENTER),
        "contact": ps("Contact", fontSize=9.5, leading=12, alignment=TA_CENTER,
                      spaceAfter=0),
        "heading": ps("Heading", fontName=PDF_FONT_BOLD, fontSize=11.5,
                      leading=14, spaceBefore=5, spaceAfter=0, keepWithNext=True),
        "body": ps("Body", alignment=TA_JUSTIFY),
        "text": ps("Text", alignment=TA_LEFT),
        "bullet": ps("Bullet", leftIndent=12, bulletIndent=2, spaceAfter=1),
        "job": ps("Job", fontName=PDF_FONT_BOLD, spaceBefore=5,
                  keepWithNext=True, spaceAfter=0),
        "company": ps("Company", fontName=PDF_FONT_ITALIC, keepWithNext=True),
    }


def pdf_heading(story, heading, styles):
    story.append(Paragraph(xml_text(heading.upper()), styles["heading"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=colors.black,
                            spaceBefore=1, spaceAfter=3))


def pdf_bullet(story, value, styles):
    if clean(value):
        story.append(Paragraph(xml_text(value), styles["bullet"], bulletText="\u2022"))


class TitleDateLine(Flowable):
    """One text line: bold title on the left, date right-aligned (ATS-safe text)."""

    def __init__(self, left, right, style):
        super().__init__()
        self.left, self.right, self.style = left, right, style

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        self.height = self.style.leading
        return self.width, self.height

    def getSpaceBefore(self):
        return self.style.spaceBefore

    def getSpaceAfter(self):
        return self.style.spaceAfter

    def draw(self):
        size = self.style.fontSize
        y = self.height - size
        canvas = self.canv
        canvas.setFillColor(colors.black)
        canvas.setFont(PDF_FONT_BOLD, size)
        canvas.drawString(0, y, self.left)
        canvas.setFont(PDF_FONT, size)
        canvas.drawRightString(self.width, y, self.right)


def pdf_title_date(left, right, style, width):
    """Bold title and right-aligned date on the same line."""
    left, right = clean(left), clean(right)
    if not right:
        return Paragraph(xml_text(left), style)
    if stringWidth(left, PDF_FONT_BOLD, style.fontSize) + \
            stringWidth(right, PDF_FONT, style.fontSize) + 8 > width:
        # Too long for one line: keep all text readable
        return Paragraph(f'{xml_text(left)} <font name="{PDF_FONT}">'
                         f'({xml_text(right)})</font>', style)
    return TitleDateLine(left, right, style)


def generate_pdf(path, data, scale=1.0):
    styles = create_pdf_styles(scale)
    personal = data["personal"]
    name = clean(personal["name"])
    role = clean(personal["target_role"])
    margin = 12.7 * mm
    width = A4[0] - 2 * margin

    story = [Paragraph(xml_text(name.upper()), styles["title"]),
             Paragraph(xml_text(role), styles["role"]),
             Paragraph(xml_text(contact_line(personal)), styles["contact"])]
    if links_line(personal):
        story.append(Paragraph(xml_text(links_line(personal)), styles["contact"]))
    story.append(Spacer(1, 3))

    pdf_heading(story, "Professional Summary", styles)
    story.append(Paragraph(rich_xml(data["summary"]), styles["body"]))

    comps = competencies(data)
    if comps:
        pdf_heading(story, "Core Competencies", styles)
        story.append(Paragraph(xml_text(SEP.join(comps)), styles["text"]))

    rows = skill_rows(data)
    if rows:
        pdf_heading(story, "Technical Skills", styles)
        for label, value in rows:
            story.append(Paragraph(f"<b>{xml_text(label)}:</b> {xml_text(value)}",
                                   styles["text"]))

    pdf_heading(story, "Professional Experience", styles)
    for group in group_experience(data["experience"]):
        company = group["company"] + (f", {group['location']}" if group["location"] else "")
        for exp in group["roles"]:
            story.append(pdf_title_date(exp.get("role"), exp.get("dates"),
                                        styles["job"], width))
            story.append(Paragraph(xml_text(company), styles["company"]))
            if clean(exp.get("project")):
                story.append(Paragraph(f"<b>Project:</b> {xml_text(exp['project'])}",
                                       styles["text"]))
            for bullet in items(exp.get("bullets")):
                pdf_bullet(story, bullet, styles)

    projects = items(data.get("projects"))
    if projects:
        pdf_heading(story, "Projects", styles)
        for project in projects:
            title = xml_text(project.get("name"))
            if clean(project.get("technology")):
                title += f" ({xml_text(project['technology'])})"
            story.append(Paragraph(f"<b>{title}</b>", styles["text"]))
            pdf_bullet(story, project.get("description"), styles)

    education = items(data.get("education"))
    if education:
        pdf_heading(story, "Education", styles)
        for edu in education:
            story.append(pdf_title_date(edu.get("qualification"), edu.get("dates"),
                                        styles["job"], width))
            if clean(edu.get("institution")):
                story.append(Paragraph(xml_text(edu["institution"]), styles["text"]))

    certifications = items(data.get("certifications"))
    if certifications:
        pdf_heading(story, "Certifications", styles)
        for cert in certifications:
            pdf_bullet(story, cert, styles)

    awards = items(data.get("awards"))
    if awards:
        pdf_heading(story, "Awards", styles)
        for award in awards:
            pdf_bullet(story, award_text(award), styles)

    details = personal_detail_rows(data)
    if details:
        pdf_heading(story, "Additional Information", styles)
        for label, value in details:
            story.append(Paragraph(f"<b>{xml_text(label)}:</b> {xml_text(value)}",
                                   styles["text"]))

    pdf = SimpleDocTemplate(
        str(path), pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=11 * mm, bottomMargin=11 * mm,
        title=f"{name} - Resume", author=name, subject=role,
        creator="Resume Generator", keywords=", ".join(comps))
    pdf.build(story)
    return pdf.page


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("       ATS-FRIENDLY RESUME GENERATOR")
    print("=" * 60)
    try:
        print("\nStep 1: Validating resume_data.txt...")
        if not validate_json_file():
            sys.exit(1)

        print("\nStep 2: Loading resume information...")
        data = load_resume_data()

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = safe_filename(data["personal"]["name"])
        docx_path = OUTPUT_DIR / f"{filename}_Resume.docx"
        pdf_path = OUTPUT_DIR / f"{filename}_Resume.pdf"

        print(f"\nStep 3: Generating PDF (fitting to {MAX_PAGES} pages)...")
        global SCALE
        scale = 1.0
        pages = generate_pdf(pdf_path, data, scale)
        while pages > MAX_PAGES and scale - 0.02 >= MIN_SCALE - 1e-9:
            scale = round(scale - 0.02, 2)
            pages = generate_pdf(pdf_path, data, scale)
        print(f"  Scale used: {scale:.2f} -> {pages} page(s)")
        if pages > MAX_PAGES:
            print(f"  WARNING: Content still exceeds {MAX_PAGES} pages at minimum "
                  f"font size. Shorten bullets in resume_data.txt.")

        print("\nStep 4: Generating DOCX (same scale)...")
        SCALE = scale
        generate_docx(docx_path, data)


        print("\n" + "=" * 60)
        print("       RESUME GENERATION COMPLETED")
        print("=" * 60)
        print(f"\nDOCX: {docx_path}")
        print(f"PDF : {pdf_path} ({pages} page(s))")
        print("\nTip: Upload the DOCX to ATS portals - it parses most reliably.")
    except Exception as error:
        print(f"\nRESUME GENERATION FAILED: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
