"""
doc_generator.py — Convert tailored resume text into a formatted .docx file.

Parses Claude's plain-text output into sections and builds a clean Word document.
Attempts PDF conversion via docx2pdf; falls back to .docx-only if unavailable.
"""

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


SECTION_HEADERS = {
    "PROFESSIONAL SUMMARY",
    "TECHNICAL SKILLS",
    "WORK EXPERIENCE",
    "PROJECTS",
    "EDUCATION",
    "CERTIFICATIONS & ACTIVITIES",
    "CERTIFICATIONS",
    "ACTIVITIES",
}


def _slug(title: str) -> str:
    """Convert job title to a filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def _is_section_header(line: str) -> bool:
    return line.strip().upper() in SECTION_HEADERS


def _build_docx(tailored_text: str) -> Document:
    """Parse the plain-text resume and build a styled Document."""
    doc = Document()

    # Narrow margins for a professional look
    for section in doc.sections:
        section.top_margin = Pt(36)
        section.bottom_margin = Pt(36)
        section.left_margin = Pt(54)
        section.right_margin = Pt(54)

    lines = tailored_text.split("\n")
    in_header_block = True  # First few lines are name + contact

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()

        if not line:
            if not in_header_block:
                doc.add_paragraph("")
            continue

        # Name line (first non-empty line)
        if i == 0 or (in_header_block and i <= 2 and not _is_section_header(line)):
            p = doc.add_paragraph()
            run = p.add_run(line)
            if i == 0:
                # Candidate name — large and bold
                run.bold = True
                run.font.size = Pt(16)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                # Contact line
                run.font.size = Pt(10)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
            continue

        # Section header
        if _is_section_header(line):
            in_header_block = False
            p = doc.add_paragraph()
            run = p.add_run(line)
            run.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(0x1A, 0x56, 0xDB)  # Blue accent
            # Horizontal rule via bottom border on the paragraph
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            continue

        # Bullet points
        if line.startswith("•") or line.startswith("-") or line.startswith("*"):
            in_header_block = False
            text = line.lstrip("•-* ").strip()
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(text).font.size = Pt(10)
            p.paragraph_format.space_after = Pt(1)
            continue

        # Bold sub-headers (role title lines, project names etc.)
        # Heuristic: all-caps short line or ends with " | " pattern
        if re.match(r"^[A-Z][A-Za-z\s/,\-\.]+\s*\|", line) or (
            line.isupper() and len(line) < 60
        ):
            in_header_block = False
            p = doc.add_paragraph()
            run = p.add_run(line)
            run.bold = True
            run.font.size = Pt(10)
            p.paragraph_format.space_before = Pt(4)
            continue

        # Date/location lines (contain em dash or date patterns)
        if re.search(r"\d{4}", line) and len(line) < 80:
            in_header_block = False
            p = doc.add_paragraph()
            run = p.add_run(line)
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            run.italic = True
            p.paragraph_format.space_after = Pt(1)
            continue

        # Regular body text
        in_header_block = False
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.size = Pt(10)
        p.paragraph_format.space_after = Pt(2)

    return doc


def generate_document(tailored_text: str, job: dict, output_dir: str) -> str:
    """
    Save the tailored resume as a .docx file (and attempt PDF conversion).

    Args:
        tailored_text: Plain-text resume from Claude
        job: Job dict (used for filename)
        output_dir: Directory to save files into

    Returns:
        Path to the generated file (PDF if conversion succeeded, else .docx)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"resume_alex_morgan_{_slug(job['title'])}"
    docx_path = output_path / f"{filename}.docx"

    doc = _build_docx(tailored_text)
    doc.save(str(docx_path))
    print(f"  Saved: {docx_path.name}")

    # Attempt PDF conversion (requires Word on macOS or LibreOffice)
    try:
        from docx2pdf import convert
        pdf_path = output_path / f"{filename}.pdf"
        convert(str(docx_path), str(pdf_path))
        print(f"  Converted to PDF: {pdf_path.name}")
        return str(pdf_path)
    except Exception as e:
        print(f"  PDF conversion skipped ({type(e).__name__}): using .docx instead")
        return str(docx_path)
