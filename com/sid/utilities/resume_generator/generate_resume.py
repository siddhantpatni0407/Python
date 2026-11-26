
"""
ATS-Friendly Resume Generator
=============================

Input:
    resume_data.txt

Output:
    Generated_Resume/
        Siddhant_Patni_Resume.docx
        Siddhant_Patni_Resume.pdf

Install:
    pip install python-docx reportlab

Run:
    python generate_resume.py
"""

import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, KeepTogether
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "resume_data.txt"
OUTPUT_DIR = BASE_DIR / "Generated_Resume"

NAVY = "173B57"
TEAL = "168C8C"
DARK = "20262C"
GREY = "59636E"

FONT_NAME = "Arial"


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

        lines = DATA_FILE.read_text(
            encoding="utf-8-sig"
        ).splitlines()

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

    required_fields = [
        "personal",
        "summary",
        "skills",
        "experience",
        "education"
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    personal = data["personal"]

    if not isinstance(personal, dict):
        raise ValueError("'personal' must be a JSON object.")

    for field in [
        "name", "email", "phone", "location", "target_role"
    ]:
        if not str(personal.get(field, "")).strip():
            raise ValueError(f"Missing personal information: {field}")

    if not isinstance(data["skills"], list):
        raise ValueError("'skills' must be a JSON array.")

    if not isinstance(data["experience"], list):
        raise ValueError("'experience' must be a JSON array.")

    if not isinstance(data["education"], list):
        raise ValueError("'education' must be a JSON array.")

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
    return escape(clean(value)).replace("\n", "<br/>")


def safe_filename(name):
    result = re.sub(r"[^A-Za-z0-9]+", "_", clean(name))
    return result.strip("_") or "Resume"


# ============================================================
# DOCX HELPERS
# ============================================================

def set_font(run, size=9, bold=False, color=DARK, italic=False):

    run.font.name = FONT_NAME
    run._element.get_or_add_rPr().rFonts.set(
        qn("w:eastAsia"), FONT_NAME
    )
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def configure_docx(doc):

    section = doc.sections[0]

    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.68)
    section.right_margin = Inches(0.68)

    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal._element.rPr.rFonts.set(
        qn("w:eastAsia"), FONT_NAME
    )
    normal.font.size = Pt(9)
    normal.font.color.rgb = RGBColor.from_string(DARK)
    normal.paragraph_format.space_after = Pt(2)
    normal.paragraph_format.line_spacing = 1.04


def add_heading_border(paragraph):

    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")

    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "3")
    bottom.set(qn("w:color"), TEAL)

    borders.append(bottom)
    p_pr.append(borders)


def add_section(doc, heading):

    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.keep_with_next = True

    set_font(
        paragraph.add_run(heading.upper()),
        10, True, NAVY
    )

    add_heading_border(paragraph)


def add_bullet(doc, value):

    value = clean(value)

    if not value:
        return

    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.18)
    paragraph.paragraph_format.first_line_indent = Inches(-0.13)
    paragraph.paragraph_format.space_after = Pt(1.5)
    paragraph.paragraph_format.keep_together = True

    set_font(paragraph.add_run("• "), 8.7, True, TEAL)
    set_font(paragraph.add_run(value), 8.7, False, DARK)


def add_labeled_line(doc, label, value):

    if not clean(value):
        return

    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(1.5)
    paragraph.paragraph_format.keep_together = True

    set_font(paragraph.add_run(clean(label) + ": "), 8.5, True, NAVY)
    set_font(paragraph.add_run(clean(value)), 8.5, False, DARK)


# ============================================================
# DOCX HEADER
# ============================================================

def add_docx_header(doc, personal):

    name = clean(personal["name"])
    role = clean(personal["target_role"])

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(1)

    set_font(paragraph.add_run(name.upper()), 21, True, NAVY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(4)

    set_font(paragraph.add_run(role.upper()), 9.2, True, TEAL)

    contact = " | ".join(
        clean(personal.get(field))
        for field in ["location", "phone", "email"]
        if clean(personal.get(field))
    )

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(1)

    set_font(paragraph.add_run(contact), 8, False, GREY)

    links = []

    for label, field in [
        ("LinkedIn", "linkedin"),
        ("GitHub", "github"),
        ("Portfolio", "portfolio")
    ]:
        if clean(personal.get(field)):
            links.append(f"{label}: {clean(personal[field])}")

    if links:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(1)

        set_font(
            paragraph.add_run(" | ".join(links)),
            8, False, GREY
        )

    if clean(personal.get("availability")):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(3)

        set_font(
            paragraph.add_run(personal["availability"]),
            7.8, False, GREY, True
        )


# ============================================================
# DOCX EXPERIENCE
# ============================================================

def add_experience_docx(doc, experience):

    company = clean(experience.get("company"))
    role = clean(experience.get("role"))

    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(5)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.keep_with_next = True

    set_font(
        paragraph.add_run(f"{company} | {role}"),
        9.3, True, NAVY
    )

    metadata = " | ".join(
        value for value in [
            clean(experience.get("dates")),
            clean(experience.get("location"))
        ] if value
    )

    if metadata:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(1)
        paragraph.paragraph_format.keep_with_next = True

        set_font(paragraph.add_run(metadata), 8, False, GREY, True)

    if clean(experience.get("project")):
        add_labeled_line(doc, "Project", experience["project"])

    for bullet in items(experience.get("bullets")):
        add_bullet(doc, bullet)


# ============================================================
# DOCX PROJECTS
# ============================================================

def add_projects_docx(doc, projects):

    if not projects:
        return

    add_section(doc, "Selected Projects")

    for project in projects:

        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(3)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.keep_with_next = True

        set_font(
            paragraph.add_run(clean(project.get("name"))),
            8.9, True, NAVY
        )

        if clean(project.get("technology")):
            add_labeled_line(
                doc, "Technology", project["technology"]
            )

        if clean(project.get("description")):
            paragraph = doc.add_paragraph(
                clean(project["description"])
            )
            paragraph.paragraph_format.space_after = Pt(2)


# ============================================================
# GENERATE DOCX
# ============================================================

def generate_docx(path, data):

    doc = Document()
    configure_docx(doc)

    personal = data["personal"]

    add_docx_header(doc, personal)

    add_section(doc, "Professional Summary")
    doc.add_paragraph(clean(data["summary"]))

    if clean(data.get("core_competencies")):
        add_section(doc, "Core Competencies")
        doc.add_paragraph(clean(data["core_competencies"]))

    if data["skills"]:
        add_section(doc, "Technical Skills")

        for skill in data["skills"]:

            if isinstance(skill, dict):
                add_labeled_line(
                    doc,
                    skill.get("category", "Skills"),
                    skill.get("items", "")
                )
            else:
                add_bullet(doc, skill)

    add_section(doc, "Professional Experience")

    for experience in data["experience"]:
        add_experience_docx(doc, experience)

    add_projects_docx(doc, items(data.get("projects")))

    if data["education"]:
        add_section(doc, "Education")

        for education in data["education"]:

            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.paragraph_format.keep_together = True

            set_font(
                paragraph.add_run(
                    clean(education.get("qualification"))
                ),
                8.7, True, NAVY
            )

            details = " | ".join(
                clean(education.get(field))
                for field in ["institution", "dates"]
                if clean(education.get(field))
            )

            if details:
                set_font(
                    paragraph.add_run(" | " + details),
                    8.2, False, DARK
                )

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

                organization = clean(award.get("organization"))

                if organization:
                    paragraph = doc.add_paragraph()
                    paragraph.paragraph_format.space_after = Pt(0)
                    paragraph.paragraph_format.keep_with_next = True

                    set_font(
                        paragraph.add_run(organization),
                        8.5, True, NAVY
                    )

                for item in items(award.get("items")):
                    add_bullet(doc, item)

            else:
                add_bullet(doc, award)

    additional = data.get("additional_information", {})

    if additional:
        add_section(doc, "Additional Information")

        for key, value in additional.items():
            add_labeled_line(
                doc,
                str(key).replace("_", " ").title(),
                value
            )

    # Simple text footer
    for section in doc.sections:

        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

        set_font(
            footer.add_run(
                f"{personal['name']} | {personal['target_role']}"
            ),
            7, False, GREY
        )

    doc.core_properties.title = f"{personal['name']} - Resume"
    doc.core_properties.author = personal["name"]
    doc.core_properties.subject = personal["target_role"]

    doc.save(path)


# ============================================================
# PDF STYLES
# ============================================================

def create_pdf_styles():

    styles = getSampleStyleSheet()

    navy = colors.HexColor("#" + NAVY)
    teal = colors.HexColor("#" + TEAL)
    dark = colors.HexColor("#" + DARK)
    grey = colors.HexColor("#" + GREY)

    return {
        "title": ParagraphStyle(
            "ResumeName",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=22,
            alignment=TA_CENTER,
            textColor=navy,
            spaceAfter=1
        ),

        "role": ParagraphStyle(
            "ResumeRole",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.8,
            leading=10,
            alignment=TA_CENTER,
            textColor=teal,
            spaceAfter=4
        ),

        "contact": ParagraphStyle(
            "ResumeContact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.6,
            leading=9,
            alignment=TA_CENTER,
            textColor=grey,
            spaceAfter=1
        ),

        "heading": ParagraphStyle(
            "ResumeHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=11,
            textColor=navy,
            spaceBefore=7,
            spaceAfter=3,
            keepWithNext=True
        ),

        "body": ParagraphStyle(
            "ResumeBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=9.8,
            textColor=dark,
            spaceAfter=2
        ),

        "small": ParagraphStyle(
            "ResumeSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=9.2,
            textColor=dark,
            spaceAfter=1.5
        ),

        "bullet": ParagraphStyle(
            "ResumeBullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=9.8,
            textColor=dark,
            leftIndent=10,
            firstLineIndent=-7,
            spaceAfter=1.3
        ),

        "company": ParagraphStyle(
            "ResumeCompany",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=10.5,
            textColor=navy,
            spaceBefore=4,
            spaceAfter=0,
            keepWithNext=True
        ),

        "meta": ParagraphStyle(
            "ResumeMeta",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.8,
            leading=9.2,
            textColor=grey,
            spaceAfter=1,
            keepWithNext=True
        )
    }


# ============================================================
# PDF HELPER FUNCTIONS
# ============================================================

def pdf_heading(story, heading, styles):

    story.append(
        Paragraph(
            xml_text(heading.upper()),
            styles["heading"]
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.6,
            color=colors.HexColor("#" + TEAL),
            spaceBefore=0,
            spaceAfter=3
        )
    )


def pdf_bullet(story, value, styles):

    if clean(value):
        story.append(
            Paragraph(
                "&#8226; " + xml_text(value),
                styles["bullet"]
            )
        )


# ============================================================
# GENERATE PDF
# ============================================================

def generate_pdf(path, data):

    styles = create_pdf_styles()

    personal = data["personal"]

    name = clean(personal["name"])
    role = clean(personal["target_role"])

    story = []

    # Header
    story.append(Paragraph(xml_text(name.upper()), styles["title"]))
    story.append(Paragraph(xml_text(role.upper()), styles["role"]))

    contact = " | ".join(
        clean(personal.get(field))
        for field in ["location", "phone", "email"]
        if clean(personal.get(field))
    )

    story.append(
        Paragraph(xml_text(contact), styles["contact"])
    )

    links = []

    for label, field in [
        ("LinkedIn", "linkedin"),
        ("GitHub", "github"),
        ("Portfolio", "portfolio")
    ]:
        if clean(personal.get(field)):
            links.append(f"{label}: {personal[field]}")

    if links:
        story.append(
            Paragraph(
                xml_text(" | ".join(links)),
                styles["contact"]
            )
        )

    if clean(personal.get("availability")):
        story.append(
            Paragraph(
                xml_text(personal["availability"]),
                styles["contact"]
            )
        )

    story.append(Spacer(1, 3))

    # Summary
    pdf_heading(story, "Professional Summary", styles)

    story.append(
        Paragraph(xml_text(data["summary"]), styles["body"])
    )

    # Competencies
    if clean(data.get("core_competencies")):

        pdf_heading(story, "Core Competencies", styles)

        story.append(
            Paragraph(
                xml_text(data["core_competencies"]),
                styles["body"]
            )
        )

    # Skills
    if data["skills"]:

        pdf_heading(story, "Technical Skills", styles)

        for skill in data["skills"]:

            if isinstance(skill, dict):

                story.append(
                    Paragraph(
                        f"<b>{xml_text(skill.get('category'))}:</b> "
                        f"{xml_text(skill.get('items'))}",
                        styles["small"]
                    )
                )

            else:
                pdf_bullet(story, skill, styles)

    # Experience
    pdf_heading(story, "Professional Experience", styles)

    for experience in data["experience"]:

        company_role = " | ".join(
            value for value in [
                clean(experience.get("company")),
                clean(experience.get("role"))
            ] if value
        )

        block = [
            Paragraph(
                xml_text(company_role),
                styles["company"]
            )
        ]

        metadata = " | ".join(
            value for value in [
                clean(experience.get("dates")),
                clean(experience.get("location"))
            ] if value
        )

        if metadata:
            block.append(
                Paragraph(xml_text(metadata), styles["meta"])
            )

        if clean(experience.get("project")):
            block.append(
                Paragraph(
                    "<b>Project:</b> " +
                    xml_text(experience["project"]),
                    styles["small"]
                )
            )

        story.append(KeepTogether(block))

        for bullet in items(experience.get("bullets")):
            pdf_bullet(story, bullet, styles)

    # Projects
    projects = items(data.get("projects"))

    if projects:

        pdf_heading(story, "Selected Projects", styles)

        for project in projects:

            block = [
                Paragraph(
                    "<b>" + xml_text(project.get("name")) + "</b>",
                    styles["body"]
                )
            ]

            if clean(project.get("technology")):
                block.append(
                    Paragraph(
                        "<b>Technology:</b> " +
                        xml_text(project["technology"]),
                        styles["small"]
                    )
                )

            if clean(project.get("description")):
                block.append(
                    Paragraph(
                        xml_text(project["description"]),
                        styles["body"]
                    )
                )

            story.append(KeepTogether(block))

    # Education
    education = items(data.get("education"))

    if education:

        pdf_heading(story, "Education", styles)

        for item in education:

            details = " | ".join(
                clean(item.get(field))
                for field in ["institution", "dates"]
                if clean(item.get(field))
            )

            qualification = xml_text(item.get("qualification"))

            story.append(
                Paragraph(
                    f"<b>{qualification}</b>" +
                    (" | " + xml_text(details) if details else ""),
                    styles["small"]
                )
            )

    # Certifications
    certifications = items(data.get("certifications"))

    if certifications:

        pdf_heading(story, "Certifications", styles)

        for certification in certifications:
            pdf_bullet(story, certification, styles)

    # Awards
    awards = items(data.get("awards"))

    if awards:

        pdf_heading(story, "Awards and Recognitions", styles)

        for award in awards:

            if isinstance(award, dict):

                block = []

                organization = clean(award.get("organization"))

                if organization:
                    block.append(
                        Paragraph(
                            "<b>" + xml_text(organization) + "</b>",
                            styles["small"]
                        )
                    )

                for item in items(award.get("items")):
                    block.append(
                        Paragraph(
                            "&#8226; " + xml_text(item),
                            styles["small"]
                        )
                    )

                if block:
                    story.append(KeepTogether(block))

            else:
                pdf_bullet(story, award, styles)

    # Additional Information
    additional = data.get("additional_information", {})

    if additional:

        pdf_heading(story, "Additional Information", styles)

        for key, value in additional.items():

            story.append(
                Paragraph(
                    f"<b>{xml_text(str(key).replace('_', ' ').title())}:</b> "
                    f"{xml_text(value)}",
                    styles["small"]
                )
            )

    # Footer
    def footer(canvas, document):

        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#" + GREY))

        canvas.drawCentredString(
            A4[0] / 2,
            8 * mm,
            f"{name} | {role} | Page {document.page}"
        )

        canvas.restoreState()

    pdf = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title=f"{name} - Resume",
        author=name
    )

    pdf.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )


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

        filename = safe_filename(
            data["personal"]["name"]
        )

        docx_path = OUTPUT_DIR / f"{filename}_Resume.docx"
        pdf_path = OUTPUT_DIR / f"{filename}_Resume.pdf"

        print("\nStep 3: Generating DOCX...")

        generate_docx(docx_path, data)

        print("DOCX generated successfully.")

        print("\nStep 4: Generating PDF...")

        generate_pdf(pdf_path, data)

        print("PDF generated successfully.")

        print("\n" + "=" * 60)
        print("       RESUME GENERATION COMPLETED")
        print("=" * 60)

        print(f"\nDOCX: {docx_path}")
        print(f"PDF : {pdf_path}")

        print("\nOutput directory:")
        print(OUTPUT_DIR)

        print("\nPlease verify all resume information before applying.")

    except Exception as error:

        print("\n" + "=" * 60)
        print("RESUME GENERATION FAILED")
        print("=" * 60)

        print(f"\nError: {error}")

        sys.exit(1)


if __name__ == "__main__":
    main()
