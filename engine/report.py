"""
PDF Report Generator
====================
Creates professional medical-style PDF reports for prediction results.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


def generate_report(prediction: dict) -> io.BytesIO:
    """
    Generate a PDF report for a single prediction result.

    Args:
        prediction: dict with keys from the predictions table

    Returns:
        BytesIO buffer containing the PDF data, ready to send to client
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#0f4c81"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#6b7280"),
    )

    story.append(Paragraph("DermaVision AI", title_style))
    story.append(Paragraph("Skin Lesion Analysis Report", subtitle_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#0f4c81")
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # ── Meta ──────────────────────────────────────────────────────────
    now = datetime.now().strftime("%B %d, %Y at %H:%M")
    story.append(
        Paragraph(f"<b>Report generated:</b> {now}", styles["Normal"])
    )
    story.append(Spacer(1, 0.25 * inch))

    # ── Results table ─────────────────────────────────────────────────
    data = [
        ["Field", "Value"],
        ["Image", str(prediction.get("original_name", "N/A"))],
        ["Diagnosis", str(prediction.get("diagnosis", "N/A"))],
        ["Code", str(prediction.get("short_code", "N/A"))],
        ["Risk Level", str(prediction.get("risk_level", "N/A"))],
        ["Confidence", f"{prediction.get('confidence', 0)}%"],
        ["Date", str(prediction.get("created_at", "N/A"))],
    ]

    tbl = Table(data, colWidths=[2 * inch, 4.2 * inch])
    tbl.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f4c81")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Label column
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#e8f0fe")),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                # Global
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 0.3 * inch))

    # ── AI Explanation ────────────────────────────────────────────────
    explanation_title = ParagraphStyle(
        "ExpTitle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#0f4c81"),
    )
    story.append(Paragraph("AI Explanation", explanation_title))
    story.append(Spacer(1, 0.1 * inch))

    desc = prediction.get("description", "")
    if desc:
        story.append(Paragraph(desc, styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))

    rec = prediction.get("recommendation", "")
    if rec:
        rec_style = ParagraphStyle(
            "Rec",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#1e40af"),
            leftIndent=12,
            borderPadding=6,
        )
        story.append(Paragraph(f"<b>Recommendation:</b> {rec}", rec_style))
    story.append(Spacer(1, 0.35 * inch))

    # ── Risk assessment badge ─────────────────────────────────────────
    risk = prediction.get("risk_level", "Benign")
    risk_map = {
        "Benign": colors.HexColor("#16a34a"),
        "Pre-malignant": colors.HexColor("#d97706"),
        "Malignant": colors.HexColor("#dc2626"),
    }
    risk_color = risk_map.get(risk, colors.grey)
    risk_style = ParagraphStyle(
        "RiskBadge",
        parent=styles["Normal"],
        fontSize=14,
        textColor=risk_color,
        fontName="Helvetica-Bold",
    )
    story.append(Paragraph(f"Overall Risk: {risk}", risk_style))
    story.append(Spacer(1, 0.4 * inch))

    # ── Disclaimer ────────────────────────────────────────────────────
    story.append(
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d1d5db"))
    )
    story.append(Spacer(1, 0.1 * inch))
    disc_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#9ca3af"),
    )
    story.append(
        Paragraph(
            "<b>Disclaimer:</b> This report is generated by an AI system and is "
            "intended for informational purposes only. It does NOT constitute a "
            "medical diagnosis. Always consult a board-certified dermatologist "
            "or qualified healthcare professional for clinical decisions.",
            disc_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer
