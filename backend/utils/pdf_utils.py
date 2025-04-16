from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER
import matplotlib.pyplot as plt
import os


def generate_pdf_report_with_details(candidate_name: str, match_result: dict, full_text: str, output_stream=None, output_path=None):
    if output_stream is None and output_path is None:
        raise ValueError("Either output_stream or output_path must be provided.")

    doc = SimpleDocTemplate(output_stream or output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    flow = []

    # Title
    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    flow.append(Paragraph(f"Career Recommendation Report for {candidate_name}", title_style))
    flow.append(Spacer(1, 20))

    # Pie Chart Visualization
    matched = len(match_result["matched_skills"])
    missing = len(match_result["missing_skills"])
    labels = ["Matched Skills", "Missing Skills"]
    sizes = [matched, missing]
    colors_chart = ["#66bb6a", "#ef5350"]

    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, autopct="%1.0f%%", colors=colors_chart, startangle=140)
    plt.axis("equal")
    pie_path = "temp_pie_chart.png"
    plt.savefig(pie_path, bbox_inches="tight")
    plt.close()

    flow.append(Image(pie_path, width=200, height=200))
    flow.append(Spacer(1, 12))

    # Skills Summary Section
    summary_style = ParagraphStyle(name="Summary", fontSize=10, leading=14)
    skills_summary = [
        f"<b>Resume Skills:</b> {', '.join(match_result['resume_skills'])}",
        f"<b>Job Description Skills:</b> {', '.join(match_result['jd_skills'])}",
        f"<b>Matched:</b> {', '.join(match_result['matched_skills'])}",
        f"<b>Missing:</b> {', '.join(match_result['missing_skills'])}",
        f"<b>Skill Match Score:</b> {match_result['match_score'] * 100:.0f}%",
    ]
    for item in skills_summary:
        flow.append(Paragraph(item, summary_style))
        flow.append(Spacer(1, 6))

    flow.append(Spacer(1, 12))

    # Full Report Text Parsing
    current_section = []
    normal_style = styles["Normal"]

    for line in full_text.strip().splitlines():
        line = line.strip()
        if not line:
            if current_section:
                flow.append(KeepTogether(current_section))
                current_section = []
            flow.append(Spacer(1, 12))
            continue

        # Hyperlink support
        if line.startswith("http"):
            link = f'<link href="{line}">{line}</link>'
            current_section.append(Paragraph(link, normal_style))
        elif line.startswith("- "):
            bullet = line[2:].strip()
            current_section.append(Paragraph(f"• {bullet}", normal_style))
        else:
            current_section.append(Paragraph(line, normal_style))

    if current_section:
        flow.append(KeepTogether(current_section))

    doc.build(flow)

    if os.path.exists(pie_path):
        os.remove(pie_path)