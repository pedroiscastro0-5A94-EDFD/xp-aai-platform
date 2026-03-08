"""Doc Formatter Agent

Generates a professional .docx from the final letter using python-docx.
Pure code — no LLM calls needed.
"""

import os
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT


class DocFormatter:
    """Generates professional .docx documents."""

    name = "Doc Formatter"

    def run(
        self,
        letter_text: str,
        client_name: str,
        output_path: str,
        report_type: str = "monthly_letter",
    ) -> dict:
        """
        Generate a .docx document from the letter text.

        Args:
            letter_text: The final letter text
            client_name: Client name for the document
            output_path: Where to save the .docx file
            report_type: Type of report ("monthly_letter" or "workflow_report")

        Returns:
            Dict with output path and metadata
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if report_type == "monthly_letter":
            self._create_monthly_letter(letter_text, client_name, output_path)
        elif report_type == "workflow_report":
            self._create_workflow_report(letter_text, output_path)

        file_size = os.path.getsize(output_path)
        return {
            "agent": self.name,
            "output_path": output_path,
            "file_size_bytes": file_size,
            "report_type": report_type,
            "success": True,
        }

    def _create_monthly_letter(self, letter_text: str, client_name: str, output_path: str):
        """Create a professionally formatted monthly investment letter."""
        doc = Document()

        # Page setup
        section = doc.sections[0]
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

        # --- Header with XP branding ---
        header_para = doc.add_paragraph()
        header_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = header_para.add_run("XP Investimentos")
        run.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

        # Subtitle
        sub = doc.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = sub.add_run("Assessoria de Investimentos")
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x6B, 0x7B, 0x8F)

        # Separator line
        sep = doc.add_paragraph()
        sep.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = sep.add_run("_" * 80)
        run.font.size = Pt(6)
        run.font.color.rgb = RGBColor(0xED, 0xB9, 0x2E)
        sep.space_after = Pt(12)

        # --- Letter body ---
        paragraphs = letter_text.split("\n")
        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                doc.add_paragraph("")
                continue

            # Detect section headers (lines ending with colon or all caps-ish)
            is_title = (
                para_text.startswith("Carta Mensal")
                or para_text.startswith("Prezado")
                or para_text.startswith("Atenciosamente")
            )
            is_section = (
                para_text.endswith(":") and len(para_text) < 60
            ) or any(
                para_text.lower().startswith(h)
                for h in [
                    "cenário macro",
                    "desempenho",
                    "posicionamento",
                    "perspectivas",
                    "recomendações",
                    "alocação",
                ]
            )

            p = doc.add_paragraph()

            if para_text.startswith("Carta Mensal"):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(para_text)
                run.bold = True
                run.font.size = Pt(14)
                run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
                p.space_after = Pt(12)
            elif is_section:
                run = p.add_run(para_text)
                run.bold = True
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
                p.space_before = Pt(8)
            elif para_text.startswith("---"):
                run = p.add_run("_" * 80)
                run.font.size = Pt(6)
                run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
            elif "disclaimer" in para_text.lower() or "não constitui" in para_text.lower() or "rentabilidade passada" in para_text.lower():
                run = p.add_run(para_text)
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
                run.italic = True
            else:
                run = p.add_run(para_text)
                run.font.size = Pt(10.5)
                run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

            # Set font family
            for run in p.runs:
                run.font.name = "Calibri"

        doc.save(output_path)

    def _create_workflow_report(self, content: str, output_path: str):
        """Create the workflow report answering the 3 challenge questions."""
        doc = Document()

        section = doc.sections[0]
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

        # Title
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run("XP AAI Platform — Workflow Report")
        run.bold = True
        run.font.size = Pt(16)
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = subtitle.add_run(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x6B, 0x7B, 0x8F)
        run.font.name = "Calibri"

        # Separator
        doc.add_paragraph("")

        # Content
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                doc.add_paragraph("")
                continue

            p = doc.add_paragraph()

            if line.startswith("# "):
                run = p.add_run(line[2:])
                run.bold = True
                run.font.size = Pt(14)
                run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
            elif line.startswith("## "):
                run = p.add_run(line[3:])
                run.bold = True
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
                p.space_before = Pt(12)
            elif line.startswith("- "):
                run = p.add_run(line)
                run.font.size = Pt(10.5)
                p.paragraph_format.left_indent = Cm(1)
            else:
                run = p.add_run(line)
                run.font.size = Pt(10.5)

            for run in p.runs:
                run.font.name = "Calibri"
                if not run.font.color.rgb:
                    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

        doc.save(output_path)
