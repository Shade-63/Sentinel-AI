from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# ── Palette ──────────────────────────────────────────────────────────────────
DARK_BG      = colors.HexColor("#0D1117")
PANEL_BG     = colors.HexColor("#161B22")
BORDER_COLOR = colors.HexColor("#30363D")
ACCENT_CYAN  = colors.HexColor("#22D3EE")
ACCENT_PINK  = colors.HexColor("#EC4899")
TEXT_PRIMARY = colors.HexColor("#E6EDF3")
TEXT_MUTED   = colors.HexColor("#8B949E")
TEXT_DIM     = colors.HexColor("#484F58")

RISK_HIGH_BG   = colors.HexColor("#3D1515")
RISK_HIGH_FG   = colors.HexColor("#F87171")
RISK_HIGH_BAR  = colors.HexColor("#EF4444")

RISK_MED_BG    = colors.HexColor("#2D2008")
RISK_MED_FG    = colors.HexColor("#FBBF24")
RISK_MED_BAR   = colors.HexColor("#F59E0B")

RISK_LOW_BG    = colors.HexColor("#0D2818")
RISK_LOW_FG    = colors.HexColor("#4ADE80")
RISK_LOW_BAR   = colors.HexColor("#22C55E")

WHITE          = colors.white
BLACK          = colors.black


# ── Page canvas callback (header + footer on every page) ─────────────────────
def _draw_page(canvas_obj, doc, report_id, timestamp):
    W, H = A4
    canvas_obj.saveState()

    # ── Top header bar ────────────────────────────────────────────────────────
    canvas_obj.setFillColor(DARK_BG)
    canvas_obj.rect(0, H - 58, W, 58, fill=1, stroke=0)

    # Thin cyan accent line under header
    canvas_obj.setFillColor(ACCENT_CYAN)
    canvas_obj.rect(0, H - 60, W, 2, fill=1, stroke=0)

    # Logo / product name
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.drawString(40, H - 36, "SENTINEL")
    canvas_obj.setFillColor(ACCENT_CYAN)
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.drawString(40 + canvas_obj.stringWidth("SENTINEL", "Helvetica-Bold", 16) + 3, H - 36, "AI")

    # Sub-label
    canvas_obj.setFillColor(TEXT_MUTED)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(40, H - 48, "STRUCTURED INTELLIGENCE BRIEF  ·  THREAT ANALYSIS DIVISION")

    # Report ID (right side)
    canvas_obj.setFillColor(TEXT_MUTED)
    canvas_obj.setFont("Helvetica", 7)
    id_text = f"REPORT ID: {report_id}"
    canvas_obj.drawRightString(W - 40, H - 32, id_text)
    canvas_obj.drawRightString(W - 40, H - 44, f"GENERATED: {timestamp}")

    # ── Bottom footer bar ─────────────────────────────────────────────────────
    canvas_obj.setFillColor(DARK_BG)
    canvas_obj.rect(0, 0, W, 36, fill=1, stroke=0)

    # Thin line above footer
    canvas_obj.setFillColor(BORDER_COLOR)
    canvas_obj.rect(0, 36, W, 1, fill=1, stroke=0)

    canvas_obj.setFillColor(TEXT_DIM)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(40, 14, "CONFIDENTIAL — FOR AUTHORIZED USE ONLY  ·  SentinelAI © 2026")
    canvas_obj.drawRightString(W - 40, 14, f"Page {doc.page}")

    canvas_obj.restoreState()


# ── Style factory ─────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()

    def ps(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=9, leading=13,
                        textColor=TEXT_PRIMARY, spaceAfter=0, spaceBefore=0)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    return {
        "section_label": ps("sl",
            fontName="Helvetica-Bold", fontSize=7, textColor=ACCENT_CYAN,
            spaceBefore=18, spaceAfter=4, leading=9,
        ),
        "section_rule": ps("sr"),   # placeholder, we use HRFlowable
        "body": ps("body", fontSize=9, leading=14, textColor=TEXT_PRIMARY),
        "body_muted": ps("bm", fontSize=8, leading=12, textColor=TEXT_MUTED),
        "risk_score": ps("rs",
            fontName="Helvetica-Bold", fontSize=36, leading=40,
            textColor=WHITE, alignment=TA_CENTER,
        ),
        "risk_label": ps("rl",
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=WHITE, alignment=TA_CENTER,
        ),
        "risk_sublabel": ps("rsl",
            fontSize=7, leading=10, textColor=TEXT_MUTED, alignment=TA_CENTER,
        ),
        "signal_item": ps("si", fontSize=8, leading=13, textColor=TEXT_PRIMARY,
                           leftIndent=10),
        "disclaimer": ps("disc", fontSize=7, leading=10, textColor=TEXT_DIM,
                          alignment=TA_CENTER),
        "meta_key": ps("mk", fontName="Helvetica-Bold", fontSize=7,
                        textColor=TEXT_MUTED, leading=11),
        "meta_val": ps("mv", fontSize=8, textColor=TEXT_PRIMARY, leading=11),
        "table_header": ps("th", fontName="Helvetica-Bold", fontSize=7,
                            textColor=ACCENT_CYAN, leading=10),
        "table_cell": ps("tc", fontSize=8, textColor=TEXT_PRIMARY, leading=11),
    }


# ── Section header helper ─────────────────────────────────────────────────────
def _section(title, styles, elements):
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"▸  {title.upper()}", styles["section_label"]))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=BORDER_COLOR, spaceAfter=8, spaceBefore=2
    ))


# ── Dark panel table helper ───────────────────────────────────────────────────
def _panel(inner_elements, bg=None, border=BORDER_COLOR, padding=10):
    """Wraps content in a dark-background rounded-ish table cell."""
    bg = bg or PANEL_BG
    t = Table([[inner_elements]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), bg),
        ("BOX",         (0, 0), (-1, -1), 0.5, border),
        ("TOPPADDING",  (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING",(0,0), (-1, -1), padding),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING",(0, 0), (-1, -1), padding),
    ]))
    return t


# ── Main generator ────────────────────────────────────────────────────────────
def generate_pdf(data, filepath):
    W, H = A4
    timestamp = datetime.now().strftime("%d %B %Y  %H:%M UTC+5:30")
    report_id = datetime.now().strftime("SIB-%Y%m%d-%H%M%S")

    # Margins: leave room for header (58+2=60) and footer (36+1=37)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=75,
        bottomMargin=50,
    )

    styles = _styles()
    elements = []

    # ── 1. CLASSIFICATION BANNER ──────────────────────────────────────────────
    banner = Table(
        [[ Paragraph("⬛  THREAT INTELLIGENCE REPORT  —  CONFIDENTIAL", ParagraphStyle(
            "banner", fontName="Helvetica-Bold", fontSize=8,
            textColor=ACCENT_CYAN, alignment=TA_CENTER, leading=10
        )) ]],
        colWidths=[W - 80]
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), DARK_BG),
        ("BOX",          (0,0),(-1,-1), 1, ACCENT_CYAN),
        ("TOPPADDING",   (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ]))
    elements.append(banner)
    elements.append(Spacer(1, 14))

    # ── 2. METADATA ROW ───────────────────────────────────────────────────────
    meta_rows = [
        [
            Paragraph("CLASSIFICATION", styles["meta_key"]),
            Paragraph("REPORT TYPE", styles["meta_key"]),
            Paragraph("ANALYSIS ENGINE", styles["meta_key"]),
            Paragraph("TIMESTAMP", styles["meta_key"]),
        ],
        [
            Paragraph("RESTRICTED", styles["meta_val"]),
            Paragraph("Digital Threat Assessment", styles["meta_val"]),
            Paragraph("SentinelAI v2 · Transformer NLP", styles["meta_val"]),
            Paragraph(timestamp, styles["meta_val"]),
        ],
    ]
    meta_table = Table(meta_rows, colWidths=[(W - 80) / 4] * 4)
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), PANEL_BG),
        ("BOX",          (0,0),(-1,-1), 0.5, BORDER_COLOR),
        ("LINEBELOW",    (0,0),(-1,0),  0.5, BORDER_COLOR),
        ("LINEBEFORE",   (1,0),(3,-1),  0.5, BORDER_COLOR),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
        ("RIGHTPADDING", (0,0),(-1,-1), 10),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 18))

    # ── 3. RISK ASSESSMENT PANEL ──────────────────────────────────────────────
    risk_level = data.get("risk_level", "LOW")
    risk_score = float(data.get("risk_score", 0))

    if risk_level == "HIGH":
        risk_bg, risk_fg, risk_bar = RISK_HIGH_BG, RISK_HIGH_FG, RISK_HIGH_BAR
        risk_label_text = "HIGH RISK  —  SCAM DETECTED"
        risk_desc = "This message exhibits strong indicators of a digital arrest or financial scam. Immediate action is advised."
        threat_icon = "🔴"
    elif risk_level == "MEDIUM":
        risk_bg, risk_fg, risk_bar = RISK_MED_BG, RISK_MED_FG, RISK_MED_BAR
        risk_label_text = "MEDIUM RISK  —  SUSPICIOUS"
        risk_desc = "This message contains several suspicious patterns. Exercise caution and verify through official channels."
        threat_icon = "🟡"
    else:
        risk_bg, risk_fg, risk_bar = RISK_LOW_BG, RISK_LOW_FG, RISK_LOW_BAR
        risk_label_text = "LOW RISK  —  LIKELY SAFE"
        risk_desc = "No significant scam indicators detected. The message appears to be legitimate communication."
        threat_icon = "🟢"

    score_style = ParagraphStyle("score_dyn", fontName="Helvetica-Bold",
                                  fontSize=42, leading=48, textColor=risk_fg,
                                  alignment=TA_CENTER)
    label_style = ParagraphStyle("label_dyn", fontName="Helvetica-Bold",
                                  fontSize=10, leading=14, textColor=risk_fg,
                                  alignment=TA_CENTER)
    desc_style  = ParagraphStyle("desc_dyn", fontSize=8, leading=12,
                                  textColor=TEXT_MUTED, alignment=TA_CENTER)

    # Progress bar simulation via a two-cell table
    bar_filled = max(2, int((risk_score / 100) * 100))
    bar_empty  = 100 - bar_filled
    bar_table  = Table(
        [["", ""]],
        colWidths=[((W - 80 - 40) * bar_filled / 100),
                   ((W - 80 - 40) * bar_empty  / 100)]
    )
    bar_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(0,0), risk_bar),
        ("BACKGROUND",   (1,0),(1,0), BORDER_COLOR),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
    ]))

    risk_inner = [
        Paragraph(f"{threat_icon}  {risk_label_text}", label_style),
        Spacer(1, 6),
        Paragraph(f"{risk_score:.1f}%", score_style),
        Spacer(1, 8),
        bar_table,
        Spacer(1, 8),
        Paragraph(risk_desc, desc_style),
    ]

    risk_panel = Table([[risk_inner]], colWidths=[W - 80])
    risk_panel.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), risk_bg),
        ("BOX",          (0,0),(-1,-1), 1, risk_bar),
        ("TOPPADDING",   (0,0),(-1,-1), 16),
        ("BOTTOMPADDING",(0,0),(-1,-1), 16),
        ("LEFTPADDING",  (0,0),(-1,-1), 20),
        ("RIGHTPADDING", (0,0),(-1,-1), 20),
    ]))
    elements.append(risk_panel)
    elements.append(Spacer(1, 18))

    # ── 4. ANALYZED MESSAGE ───────────────────────────────────────────────────
    _section("01  ·  Intercepted Communication", styles, elements)

    msg_text = data.get("message", "No message provided.")
    msg_para = Paragraph(msg_text, ParagraphStyle(
        "msg", fontSize=9, leading=15, textColor=TEXT_PRIMARY,
        fontName="Courier", leftIndent=0
    ))
    msg_panel = Table([[msg_para]], colWidths=[W - 80])
    msg_panel.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), PANEL_BG),
        ("LINEAFTER",    (0,0),(0,-1),  3, ACCENT_CYAN),   # left accent bar
        ("BOX",          (0,0),(-1,-1), 0.5, BORDER_COLOR),
        ("TOPPADDING",   (0,0),(-1,-1), 12),
        ("BOTTOMPADDING",(0,0),(-1,-1), 12),
        ("LEFTPADDING",  (0,0),(-1,-1), 14),
        ("RIGHTPADDING", (0,0),(-1,-1), 14),
    ]))
    elements.append(msg_panel)
    elements.append(Spacer(1, 14))

    # ── 5. DETECTED SIGNALS ───────────────────────────────────────────────────
    _section("02  ·  Detected Risk Indicators", styles, elements)

    signals = data.get("signals", [])
    if signals:
        signal_rows = []
        for i, sig in enumerate(signals, 1):
            signal_rows.append([
                Paragraph(f"{i:02d}", ParagraphStyle(
                    "snum", fontName="Helvetica-Bold", fontSize=8,
                    textColor=ACCENT_CYAN, alignment=TA_CENTER, leading=12
                )),
                Paragraph(f"⚠  {sig}", ParagraphStyle(
                    "stxt", fontSize=8, leading=13, textColor=TEXT_PRIMARY
                )),
            ])

        sig_table = Table(signal_rows, colWidths=[30, W - 80 - 30])
        sig_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), PANEL_BG),
            ("BOX",          (0,0),(-1,-1), 0.5, BORDER_COLOR),
            ("LINEBELOW",    (0,0),(-1,-2), 0.3, BORDER_COLOR),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",   (0,0),(-1,-1), 7),
            ("BOTTOMPADDING",(0,0),(-1,-1), 7),
            ("LEFTPADDING",  (0,0),(-1,-1), 10),
            ("RIGHTPADDING", (0,0),(-1,-1), 10),
            ("BACKGROUND",   (0,0),(0,-1), colors.HexColor("#0D1F2D")),
        ]))
        elements.append(sig_table)
    else:
        no_sig = Table(
            [[Paragraph("✔  No high-confidence scam indicators detected in this message.", ParagraphStyle(
                "nosig", fontSize=8, leading=12, textColor=RISK_LOW_FG
            ))]],
            colWidths=[W - 80]
        )
        no_sig.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), RISK_LOW_BG),
            ("BOX",          (0,0),(-1,-1), 0.5, RISK_LOW_BAR),
            ("TOPPADDING",   (0,0),(-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1), 10),
            ("LEFTPADDING",  (0,0),(-1,-1), 14),
            ("RIGHTPADDING", (0,0),(-1,-1), 14),
        ]))
        elements.append(no_sig)

    elements.append(Spacer(1, 14))

    # ── 6. AI INTERPRETATION ──────────────────────────────────────────────────
    _section("03  ·  AI Model Interpretation", styles, elements)

    interp_rows = [
        ["Model Architecture", "Fine-tuned Transformer (BERT-class) · Digital Scam Corpus"],
        ["Detection Method",   "Linguistic pattern matching + structural scam framework analysis"],
        ["Confidence Basis",   f"{max(risk_score, 100 - risk_score):.1f}% model confidence on primary classification"],
        ["Threat Category",    "Digital Arrest Scam / Impersonation / Financial Coercion"],
    ]
    interp_table = Table(
        [[Paragraph(k, styles["meta_key"]), Paragraph(v, styles["table_cell"])]
         for k, v in interp_rows],
        colWidths=[130, W - 80 - 130]
    )
    interp_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), PANEL_BG),
        ("BACKGROUND",   (0,0),(0,-1),  colors.HexColor("#0D1F2D")),
        ("BOX",          (0,0),(-1,-1), 0.5, BORDER_COLOR),
        ("LINEBELOW",    (0,0),(-1,-2), 0.3, BORDER_COLOR),
        ("LINEAFTER",    (0,0),(0,-1),  0.5, BORDER_COLOR),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
        ("RIGHTPADDING", (0,0),(-1,-1), 10),
    ]))
    elements.append(interp_table)
    elements.append(Spacer(1, 14))

    # ── 7. RECOMMENDED ACTIONS ────────────────────────────────────────────────
    _section("04  ·  Recommended Immediate Actions", styles, elements)

    actions = [
        ("CRITICAL", "Do NOT transfer funds, share OTP, passwords, or any personal credentials."),
        ("CRITICAL", "Disconnect immediately from the suspicious communication channel."),
        ("HIGH",     "Verify the sender's identity through official government or bank websites only."),
        ("HIGH",     "Report the incident to the National Cybercrime Portal: cybercrime.gov.in"),
        ("MEDIUM",   "Preserve all evidence — screenshots, call logs, and message history."),
        ("MEDIUM",   "Alert family members and close contacts about this threat pattern."),
    ]

    priority_colors = {
        "CRITICAL": (colors.HexColor("#3D1515"), RISK_HIGH_FG),
        "HIGH":     (colors.HexColor("#2D2008"), RISK_MED_FG),
        "MEDIUM":   (colors.HexColor("#0D2818"), RISK_LOW_FG),
    }

    action_data = []
    for priority, text in actions:
        bg, fg = priority_colors[priority]
        action_data.append([
            Paragraph(priority, ParagraphStyle(
                "pri", fontName="Helvetica-Bold", fontSize=6,
                textColor=fg, alignment=TA_CENTER, leading=9
            )),
            Paragraph(text, ParagraphStyle(
                "act", fontSize=8, leading=13, textColor=TEXT_PRIMARY
            )),
        ])

    action_table = Table(action_data, colWidths=[55, W - 80 - 55])
    action_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), PANEL_BG),
        ("BOX",          (0,0),(-1,-1), 0.5, BORDER_COLOR),
        ("LINEBELOW",    (0,0),(-1,-2), 0.3, BORDER_COLOR),
        ("LINEAFTER",    (0,0),(0,-1),  0.5, BORDER_COLOR),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("RIGHTPADDING", (0,0),(-1,-1), 8),
        # Per-row background for priority column
        ("BACKGROUND",   (0,0),(0,1),  colors.HexColor("#3D1515")),
        ("BACKGROUND",   (0,2),(0,3),  colors.HexColor("#2D2008")),
        ("BACKGROUND",   (0,4),(0,5),  colors.HexColor("#0D2818")),
    ]))
    elements.append(action_table)
    elements.append(Spacer(1, 20))

    # ── 8. DISCLAIMER ─────────────────────────────────────────────────────────
    disc_table = Table(
        [[Paragraph(
            "DISCLAIMER  ·  SentinelAI provides AI-based probabilistic risk estimation and does not constitute "
            "legal advice. All findings are based on pattern recognition and should be verified through official "
            "law enforcement or financial authorities. This report is generated for informational purposes only.",
            styles["disclaimer"]
        )]],
        colWidths=[W - 80]
    )
    disc_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), DARK_BG),
        ("BOX",          (0,0),(-1,-1), 0.5, BORDER_COLOR),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",  (0,0),(-1,-1), 14),
        ("RIGHTPADDING", (0,0),(-1,-1), 14),
    ]))
    elements.append(disc_table)

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(
        elements,
        onFirstPage=lambda c, d: _draw_page(c, d, report_id, timestamp),
        onLaterPages=lambda c, d: _draw_page(c, d, report_id, timestamp),
    )