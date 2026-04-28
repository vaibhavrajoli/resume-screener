"""
report.py — generates a clean, readable PDF ATS report using fpdf2.
Works for any job role / domain.
"""

import datetime
from fpdf import FPDF


class _AtsReport(FPDF):
    def __init__(self, job_title: str = ""):
        super().__init__()
        self.job_title = job_title

    def header(self):
        self.set_fill_color(30, 64, 175)          # deep blue
        self.rect(0, 0, 210, 20, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "AI Resume ATS Report", align="C", ln=False)
        self.ln(20)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        date_str = datetime.datetime.now().strftime("%d %b %Y %H:%M")
        self.cell(0, 10, f"Generated on {date_str}  |  Page {self.page_no()}", align="C")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section_heading(self, title: str):
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(240, 244, 255)
        self.set_text_color(30, 64, 175)
        self.cell(0, 9, f"  {title}", fill=True, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def _body(self, text: str, color=(30, 30, 30)):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*color)
        safe = text.encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 6, safe)
        self.set_text_color(0, 0, 0)

    def _keyword_row(self, label: str, keywords: list, color):
        if not keywords:
            return
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*color)
        self.cell(32, 6, label, ln=False)
        self.set_font("Helvetica", "", 10)
        safe = ", ".join(keywords).encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 6, safe)
        self.set_text_color(0, 0, 0)

    def _score_bar(self, score: float, width: int = 130):
        """Draw a simple horizontal progress bar."""
        x, y = self.get_x(), self.get_y()
        # background
        self.set_fill_color(220, 220, 220)
        self.rect(x, y, width, 5, "F")
        # filled portion
        filled = int(width * score / 100)
        if score >= 75:
            self.set_fill_color(22, 163, 74)
        elif score >= 55:
            self.set_fill_color(37, 99, 235)
        elif score >= 35:
            self.set_fill_color(234, 88, 12)
        else:
            self.set_fill_color(220, 38, 38)
        self.rect(x, y, filled, 5, "F")
        self.ln(7)


def generate_pdf_report(
    overall: float,
    predicted: float,
    section_results: dict,
    all_matched: list,
    all_missing: list,
    job_title: str = "",
) -> bytes:
    """Build and return a PDF ATS report as bytes."""

    pdf = _AtsReport(job_title=job_title)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.ln(2)

    # ── Summary banner ────────────────────────────────────────────────────────
    if score := overall:
        if score >= 75:
            label, fc = "Excellent Match", (22, 163, 74)
        elif score >= 55:
            label, fc = "Good Match", (37, 99, 235)
        elif score >= 35:
            label, fc = "Moderate Match", (234, 88, 12)
        else:
            label, fc = "Weak Match", (220, 38, 38)

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*fc)
    pdf.cell(0, 12, f"{overall}%", align="C", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Current ATS Score  |  {label}", align="C", ln=True)
    pdf.set_text_color(37, 99, 235)
    pdf.set_font("Helvetica", "B", 11)
    gain = round(predicted - overall, 1)
    pdf.cell(0, 7, f"Predicted score after improvements: {predicted}%   (+{gain}%)", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # overall bar
    pdf.set_x(38)
    pdf._score_bar(overall, width=130)
    pdf.ln(3)

    # ── Matched / Missing overview ────────────────────────────────────────────
    pdf._section_heading("Keyword Overview")
    pdf._keyword_row("Matched:", all_matched, (22, 163, 74))
    pdf.ln(1)
    pdf._keyword_row("Missing:", all_missing, (220, 38, 38))
    pdf.ln(4)

    # ── Section-wise breakdown ────────────────────────────────────────────────
    pdf._section_heading("Section-wise Analysis & Recommendations")
    pdf.ln(1)

    for section, data in section_results.items():
        s = data["score"]
        if s >= 75:
            sc = (22, 163, 74)
        elif s >= 55:
            sc = (37, 99, 235)
        elif s >= 35:
            sc = (234, 88, 12)
        else:
            sc = (220, 38, 38)

        # Section title + score
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*sc)
        pdf.cell(60, 7, f"{section}", ln=False)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, f"{s}% match", ln=True)

        # mini bar
        pdf.set_x(pdf.get_x())
        pdf._score_bar(s, width=100)

        # keywords
        if data["matched"]:
            pdf._keyword_row("  Matched:", data["matched"], (22, 163, 74))
        if data["missing"]:
            pdf._keyword_row("  Missing:", data["missing"], (220, 38, 38))

        # recommendations
        if data["recommendations"]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 64, 175)
            pdf.cell(0, 6, "  Recommendations:", ln=True)
            pdf.set_text_color(0, 0, 0)
            for rec in data["recommendations"]:
                pdf._body(f"    * {rec}")

        pdf.ln(3)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

    # ── Final action plan ─────────────────────────────────────────────────────
    pdf._section_heading("Your Action Plan")
    steps = [
        "1. Update your Skills section to include the missing keywords listed above.",
        "2. Rewrite your Experience bullets to use exact phrases from the JD.",
        "3. Tailor your Summary to mention the job title and 3-4 key requirements.",
        "4. Add relevant projects that demonstrate the skills mentioned in the JD.",
        "5. List any certifications or courses relevant to the missing keywords.",
        "6. Re-run this tool after changes to see your improved score.",
    ]
    for step in steps:
        pdf._body(step)

    return bytes(pdf.output())