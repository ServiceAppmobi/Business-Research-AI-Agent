from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def build_report_pdf(report: dict, order_id: str) -> bytes:
    """Render a completed research report as a PDF for download and email delivery."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="AI Business Research Report",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    story = [
        Paragraph("AI Business Research Report", styles["Title"]),
        Paragraph(f"Order reference: {escape(str(order_id))}", styles["Italic"]),
        Spacer(1, 8),
    ]
    sections = [
        ("Executive Summary", "executive_summary"),
        ("Market Overview", "market_overview"),
        ("Target Customers", "target_customers"),
        ("Opportunities", "opportunities"),
        ("Risks", "risks"),
        ("Competitor Landscape", "competitor_landscape"),
        ("Recommended Next Steps", "recommended_next_steps"),
        ("Assumptions and Limitations", "assumptions_and_limitations"),
    ]
    for heading, key in sections:
        value = report.get(key, "")
        if not value:
            continue
        story.append(Paragraph(escape(heading), styles["SectionHeading"]))
        items = value if isinstance(value, list) else [value]
        for item in items:
            text = escape(str(item)).replace("\n", "<br/>")
            story.append(Paragraph("• " + text if isinstance(value, list) else text, styles["BodyText"]))
            story.append(Spacer(1, 3))

    citations = report.get("citations", [])
    if citations:
        story.append(Paragraph("Sources", styles["SectionHeading"]))
        for index, source in enumerate(citations, start=1):
            title = escape(str(source.get("title", "Source")))
            url = escape(str(source.get("url", "")), {'"': "&quot;"})
            snippet = escape(str(source.get("snippet", "")))
            story.append(
                Paragraph(
                    f'[S{index}] <link href="{url}" color="blue">{title}</link>',
                    styles["BodyText"],
                )
            )
            if snippet:
                story.append(Paragraph(snippet, styles["Italic"]))
            story.append(Spacer(1, 5))

    for key in ("research_method", "disclaimer"):
        value = report.get(key, "")
        if value:
            story.append(Spacer(1, 8))
            story.append(Paragraph(escape(str(value)), styles["Italic"]))

    doc.build(story)
    return buffer.getvalue()
