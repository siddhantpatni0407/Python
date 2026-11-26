from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# =====================================================
# OUTPUT FILE PATH
# =====================================================
doc_path = r"C:\Users\Siddhant Patni\Documents\TODO\Jai_Jinendra_Shreekalp_Premium_Letterhead.docx"

# =====================================================
# CREATE DOCUMENT
# =====================================================
doc = Document()

section = doc.sections[0]

# Page Margins
section.top_margin = Inches(0.45)
section.bottom_margin = Inches(0.45)
section.left_margin = Inches(0.7)
section.right_margin = Inches(0.7)

# =====================================================
# HEADER
# =====================================================
header = section.header

# Decorative Top Line
top_line = header.add_paragraph()
top_line.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

top_run = top_line.add_run("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
top_run.font.size = Pt(10)
top_run.font.color.rgb = RGBColor(180, 30, 30)

# =====================================================
# COMPANY NAME
# =====================================================
title_para = header.add_paragraph()
title_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

title_run = title_para.add_run("JAI JINENDRA SHREEKALP")
title_run.bold = True
title_run.font.size = Pt(30)
title_run.font.name = "Georgia"

# Premium Dark Red Color
title_run.font.color.rgb = RGBColor(139, 0, 0)

# =====================================================
# ADDRESS
# =====================================================
address_para = header.add_paragraph()
address_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

address_run = address_para.add_run(
    "C-101, Opus 76, Vinode Vasti, Wakad, PCMC Pune - 411057"
)
address_run.font.size = Pt(11)
address_run.font.name = "Calibri"
address_run.font.color.rgb = RGBColor(70, 70, 70)

# =====================================================
# CONTACT
# =====================================================
contact_para = header.add_paragraph()
contact_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

contact_run = contact_para.add_run("📞 +91 8149158108")
contact_run.bold = True
contact_run.font.size = Pt(12)
contact_run.font.name = "Calibri"

# Royal Blue Accent
contact_run.font.color.rgb = RGBColor(0, 76, 153)

# =====================================================
# PREMIUM DOUBLE BORDER
# =====================================================
border_para = header.add_paragraph()

pPr = border_para._element.get_or_add_pPr()
pBdr = OxmlElement('w:pBdr')

bottom = OxmlElement('w:bottom')
bottom.set(qn('w:val'), 'double')
bottom.set(qn('w:sz'), '12')
bottom.set(qn('w:space'), '6')
bottom.set(qn('w:color'), 'B22222')

pBdr.append(bottom)
pPr.append(pBdr)

# =====================================================
# BODY SPACE (SINGLE PAGE WRITABLE AREA)
# =====================================================
for _ in range(16):
    para = doc.add_paragraph()
    para.space_after = Pt(16)

# =====================================================
# FOOTER
# =====================================================
footer = section.footer
footer_para = footer.paragraphs[0]
footer_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

footer_run = footer_para.add_run("JAI JINENDRA SHREEKALP")
footer_run.bold = True
footer_run.font.size = Pt(9)
footer_run.font.name = "Calibri"
footer_run.font.color.rgb = RGBColor(160, 160, 160)

# =====================================================
# SAVE DOCUMENT
# =====================================================
doc.save(doc_path)

print("Premium Professional Letterhead Created Successfully!")
print(f"Saved at:\n{doc_path}")