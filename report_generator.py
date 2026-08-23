import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

MIDNIGHT  = colors.HexColor("#0f1e2d")
NAVY      = colors.HexColor("#1a3347")
GOLD      = colors.HexColor("#e8a020")
AMBER     = colors.HexColor("#b8760a")
OCEAN     = colors.HexColor("#2a5070")
SKY       = colors.HexColor("#8fa8bf")
BORDER    = colors.HexColor("#d8d4cc")
WHITE     = colors.white

SCORE_COLORS = {1: colors.HexColor("#c0392b"), 2: colors.HexColor("#c0392b"),
                3: colors.HexColor("#e67e22"), 4: colors.HexColor("#27ae60"),
                5: colors.HexColor("#27ae60")}


def _styles():
    base = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle("title", parent=base["Title"], textColor=MIDNIGHT,
                                 fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=2)
    s["eyebrow"] = ParagraphStyle("eyebrow", parent=base["Normal"], textColor=AMBER,
                                   fontName="Helvetica-Bold", fontSize=8, leading=10, spaceAfter=14)
    s["tagline"] = ParagraphStyle("tagline", parent=base["Normal"], textColor=OCEAN,
                                   fontSize=10, leading=13, spaceAfter=16)
    s["h2"] = ParagraphStyle("h2", parent=base["Heading2"], textColor=MIDNIGHT,
                              fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=14, spaceAfter=6)
    s["body"] = ParagraphStyle("body", parent=base["Normal"], textColor=MIDNIGHT,
                                fontSize=9.5, leading=13)
    s["muted"] = ParagraphStyle("muted", parent=base["Normal"], textColor=SKY,
                                 fontSize=8, leading=11)
    s["criterion_name"] = ParagraphStyle("cn", parent=base["Normal"], textColor=MIDNIGHT,
                                          fontName="Helvetica-Bold", fontSize=9.5, leading=12)
    s["criterion_id"] = ParagraphStyle("cid", parent=base["Normal"], textColor=SKY, fontSize=7.5, leading=10)
    s["rationale"] = ParagraphStyle("rat", parent=base["Normal"], textColor=OCEAN,
                                     fontSize=8.5, leading=11.5, spaceBefore=2)
    s["remediation"] = ParagraphStyle("rem", parent=base["Normal"], textColor=AMBER,
                                       fontSize=8.5, leading=11.5, spaceBefore=2)
    s["score_num"] = ParagraphStyle("score", fontSize=26, leading=31, textColor=MIDNIGHT, fontName="Helvetica-Bold")
    s["band"] = ParagraphStyle("band", fontSize=10, leading=13, textColor=WHITE,
                                fontName="Helvetica-Bold", alignment=TA_CENTER)
    s["function_label"] = ParagraphStyle("fn", fontSize=10, leading=13, textColor=OCEAN,
                                          fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    return s


def generate_pdf_report(session: dict, results: list, checklist_items: list) -> io.BytesIO:
    """Build a branded PDF audit report from the real persisted session,
    results, and checklist data (not the old in-memory eval_result shape
    generate_text_report used, that never matched what's actually stored)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    s = _styles()
    story = []

    # ── Header ──
    story.append(Paragraph("ZETA HEALTH AI &nbsp;&middot;&nbsp; GOVERNANCE AUDIT", s["eyebrow"]))
    story.append(Paragraph(session.get("title") or "AI Governance Audit Report", s["title"]))
    story.append(Paragraph("Clinical operations, intelligently governed.", s["tagline"]))

    meta_rows = [
        ["Generated", datetime.now().strftime("%B %d, %Y")],
        ["Submitted by", f"{session.get('display_name', '')} ({session.get('email', '')})"],
        ["Vendor", session.get("vendor_name") or "None detected"],
        ["Framework", "NIST AI RMF + HIPAA + HITRUST CSF"],
    ]
    meta_table = Table(meta_rows, colWidths=[1.3 * inch, 4.7 * inch])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (0, -1), SKY),
        ("TEXTCOLOR", (1, 0), (1, -1), MIDNIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # ── Score summary ──
    overall = session.get("overall_pct")
    band_color = colors.HexColor(session.get("maturity_color") or "#8fa8bf")
    score_table = Table(
        [[Paragraph(f"<b>{overall}%</b>" if overall is not None else "—", s["score_num"]),
          Paragraph((session.get("maturity_label") or "—").upper(), s["band"]),
          Paragraph(session.get("maturity_desc") or "", s["body"])]],
        colWidths=[1.3 * inch, 1.3 * inch, 4.4 * inch],
    )
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#f7f4ee")),
        ("BACKGROUND", (1, 0), (1, 0), band_color),
        ("ALIGN", (0, 0), (1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (0, 0), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (2, 0), (2, 0), 14),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 6))

    critical = [r for r in results if r.get("critical_flag")]
    if critical:
        story.append(Paragraph(
            "CRITICAL BLOCKERS — address before deployment",
            ParagraphStyle("crit_h2", parent=s["h2"], textColor=colors.HexColor("#c0392b")),
        ))
        for r in critical:
            story.append(Paragraph(f"[{r['criterion_id']}] {r['criterion_name']}", s["criterion_name"]))
            story.append(Paragraph(r.get("rationale") or "", s["rationale"]))

    # ── Results by function ──
    story.append(Paragraph("GOVERNANCE CRITERIA", s["h2"]))
    groups = {}
    for r in results:
        groups.setdefault(r["function"], []).append(r)

    for fn, rows in groups.items():
        story.append(Paragraph(fn, s["function_label"]))
        for r in rows:
            score = r.get("score", 1)
            badge = Table([[str(score)]], colWidths=[0.3 * inch], rowHeights=[0.22 * inch])
            badge.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), SCORE_COLORS.get(score, SKY)),
                ("TEXTCOLOR", (0, 0), (0, 0), WHITE),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (0, 0), 9),
            ]))
            name_cell = [
                Paragraph(r["criterion_name"], s["criterion_name"]),
                Paragraph(r["criterion_id"], s["criterion_id"]),
                Paragraph(r.get("rationale") or "", s["rationale"]),
            ]
            if r.get("remediation"):
                name_cell.append(Paragraph(f"Remediation: {r['remediation']}", s["remediation"]))

            row_table = Table([[badge, name_cell]], colWidths=[0.45 * inch, 5.85 * inch])
            row_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER),
            ]))
            story.append(KeepTogether(row_table))

    # ── Action items ──
    if checklist_items:
        story.append(Paragraph("REMEDIATION ACTION ITEMS", s["h2"]))
        rows = [["Action", "Owner", "Due", "Status"]]
        for item in checklist_items:
            rows.append([
                Paragraph(item.get("action") or "", s["body"]),
                item.get("owner") or "—",
                item.get("due_date") or "—",
                (item.get("status") or "pending").replace("_", " ").title(),
            ])
        action_table = Table(rows, colWidths=[3.6 * inch, 1.3 * inch, 0.9 * inch, 0.9 * inch])
        action_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, BORDER),
        ]))
        story.append(action_table)

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Generated by the Zeta Health AI Governance Audit Tool &middot; "
        "github.com/zabeelbasheer/ai-governance-audit-tool",
        s["muted"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf


def generate_text_report(eval_result: dict) -> str:
    """Generate a plain-text audit report suitable for download."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append("=" * 70)
    lines.append("AI GOVERNANCE AUDIT REPORT")
    lines.append(f"Generated: {now}")
    lines.append("Framework: NIST AI RMF + HIPAA Healthcare Lens")
    lines.append("=" * 70)
    lines.append("")
    lines.append("USE CASE")
    lines.append("-" * 40)
    lines.append(eval_result["use_case"])
    lines.append("")
    lines.append("OVERALL GOVERNANCE SCORE")
    lines.append("-" * 40)
    lines.append(f"Score:    {eval_result['overall_pct']}%")
    lines.append(f"Maturity: {eval_result['maturity_label']}")
    lines.append(f"Summary:  {eval_result['maturity_desc']}")
    lines.append("")

    if eval_result["critical_items"]:
        lines.append("⚠  CRITICAL BLOCKERS (address before any deployment)")
        lines.append("-" * 40)
        for r in eval_result["critical_items"]:
            lines.append(f"  [{r['criterion_id']}] {r['criterion_name']}")
            lines.append(f"  Rationale:   {r['rationale']}")
            lines.append(f"  Remediation: {r['remediation']}")
            lines.append("")

    for label, items in [
        ("RED — High Risk (score 1–2)", eval_result["red_items"]),
        ("AMBER — Moderate Risk (score 3)", eval_result["amber_items"]),
        ("GREEN — Adequate (score 4–5)", eval_result["green_items"]),
    ]:
        lines.append(label)
        lines.append("-" * 40)
        for r in items:
            lines.append(f"  [{r['criterion_id']}] {r['criterion_name']}  —  Score: {r['score']}/5  |  {r['function']}")
            lines.append(f"  {r['rationale']}")
            if r["remediation"]:
                lines.append(f"  → {r['remediation']}")
            lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("Generated by AI Governance Audit Tool | github.com/zabeelbasheer/ai-governance-audit-tool")

    return "\n".join(lines)
