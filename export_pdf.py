"""
Exporta data/recipes.json a PDF.
Genera: recetas_refineria_nms.pdf
"""

import json
import os
from datetime import date
from collections import Counter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)

BASE = os.path.dirname(__file__)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def tr(name, translations):
    return translations.get(name, name)

# ── Colores ──────────────────────────────────────────────────────────────────
GOLD      = colors.HexColor("#C8A84B")
DARK_BG   = colors.HexColor("#0D1525")
ROW_ALT   = colors.HexColor("#F3F6F9")
COL_SMALL  = colors.HexColor("#1A4A28")
COL_MEDIUM = colors.HexColor("#1A2E50")
COL_LARGE  = colors.HexColor("#3A1A50")
ARROW_COL  = colors.HexColor("#888888")

def make_styles():
    base = getSampleStyleSheet()
    cell = ParagraphStyle("cell", parent=base["Normal"],
                          fontSize=7.5, leading=9.5)
    bold_cell = ParagraphStyle("bold_cell", parent=cell, fontName="Helvetica-Bold")
    return base, cell, bold_cell

def section_header(label, count, color, styles):
    base, _, _ = styles
    h = ParagraphStyle("sh", parent=base["Heading1"],
                       fontSize=13, spaceBefore=14, spaceAfter=6,
                       textColor=color)
    return [
        Paragraph(f"Refineria {label}  —  {count} recetas", h),
        HRFlowable(width="100%", color=GOLD, thickness=0.8, spaceAfter=6),
    ]

def recipe_table(recipes, refinery_type, translations, styles):
    _, cell, _ = styles
    t = refinery_type
    n_inputs = {"pequeña": 1, "mediana": 2, "grande": 3}[t]
    header_color = {"pequeña": COL_SMALL, "mediana": COL_MEDIUM, "grande": COL_LARGE}[t]

    # Build columns dynamically
    # Each input: Name | Qty
    # Then arrow | Output name | Output qty | Time
    col_widths = []
    for _ in range(n_inputs):
        col_widths += [4.2*cm, 0.9*cm]
    col_widths += [0.6*cm, 4.5*cm, 0.9*cm, 1.6*cm]
    # Scale to fit 17.6cm content width
    total = sum(col_widths)
    scale = 17.6*cm / total
    col_widths = [w * scale for w in col_widths]

    # Header row
    header = []
    for i in range(n_inputs):
        label = "Entrada" if n_inputs == 1 else f"Entrada {i+1}"
        header += [label, "Cant."]
    header += ["", "Salida", "Cant.", "Tiempo"]

    data = [header]
    for r in recipes:
        row = []
        inputs = r["inputs"]
        out = r["output"]
        for i in range(n_inputs):
            if i < len(inputs):
                name = tr(inputs[i]["name"], translations)
                row += [Paragraph(name, cell), str(inputs[i]["qty"])]
            else:
                row += ["", ""]
        out_name = tr(out["name"], translations) if out else ""
        out_qty  = str(out["qty"]) if out else ""
        row += ["→", Paragraph(out_name, cell), out_qty, r.get("time", "")]
        data.append(row)

    n_cols = len(col_widths)
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    arrow_cols = [n_inputs * 2]  # index of the → column

    style_cmds = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        # Body
        ("FONTSIZE",   (0, 1), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        # Grid
        ("GRID",       (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC")),
        # Alignment
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",      (n_inputs*2, 0), (n_inputs*2, -1), "CENTER"),   # arrow
        ("ALIGN",      (n_cols-2, 0), (n_cols-2, -1), "CENTER"),       # qty salida
        ("ALIGN",      (n_cols-1, 0), (n_cols-1, -1), "RIGHT"),        # tiempo
        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        # Qty columns lighter text
        ("TEXTCOLOR", (n_inputs*2, 1), (n_inputs*2, -1), ARROW_COL),
    ]
    # Highlight output name column
    out_col = n_inputs * 2 + 1
    style_cmds += [("FONTNAME", (out_col, 1), (out_col, -1), "Helvetica-Bold")]

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def build_pdf():
    recipes      = load_json(os.path.join(BASE, "data", "recipes.json"))
    translations = load_json(os.path.join(BASE, "data", "translations.json"))
    out_path     = os.path.join(BASE, "recetas_refineria_nms.pdf")

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.7*cm, rightMargin=1.7*cm,
        topMargin=2*cm,    bottomMargin=2*cm,
        title="NMS — Recetas de Refinería",
        author="nms-refinery",
    )

    styles  = make_styles()
    base, cell, _ = styles
    story   = []
    counts  = Counter(r["refinery_type"] for r in recipes)

    # ── Portada ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.5*cm))
    story.append(Paragraph("No Man's Sky", ParagraphStyle(
        "t1", parent=base["Title"], fontSize=24, textColor=GOLD, spaceAfter=4)))
    story.append(Paragraph("Recetas de Refinería", ParagraphStyle(
        "t2", parent=base["Title"], fontSize=18, spaceAfter=4)))
    story.append(Paragraph(
        f"Exportado el {date.today().strftime('%d/%m/%Y')}",
        ParagraphStyle("sub", parent=base["Normal"],
                       fontSize=10, textColor=colors.grey, spaceAfter=24)))
    story.append(HRFlowable(width="100%", color=GOLD, thickness=1.5, spaceAfter=20))

    stats = [
        ["Tipo de refinería",        "Recetas"],
        ["Pequeña  (1 entrada)",  str(counts.get("pequeña", 0))],
        ["Mediana  (2 entradas)", str(counts.get("mediana", 0))],
        ["Grande   (3 entradas)", str(counts.get("grande",  0))],
        ["Total",                 str(len(recipes))],
    ]
    stats_tbl = Table(stats, colWidths=[7*cm, 2.5*cm])
    stats_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [ROW_ALT, colors.white]),
        ("ALIGN",      (1, 0), (1, -1), "CENTER"),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("LINEABOVE", (0,-1), (-1,-1), 1, GOLD),
    ]))
    story.append(stats_tbl)
    story.append(PageBreak())

    # ── Secciones ─────────────────────────────────────────────────────────────
    groups = {
        "pequeña": [r for r in recipes if r["refinery_type"] == "pequeña"],
        "mediana": [r for r in recipes if r["refinery_type"] == "mediana"],
        "grande":  [r for r in recipes if r["refinery_type"] == "grande"],
    }
    labels = {"pequeña": "Pequeña", "mediana": "Mediana", "grande": "Grande"}
    colors_ = {"pequeña": COL_SMALL, "mediana": COL_MEDIUM, "grande": COL_LARGE}

    for key in ["pequeña", "mediana", "grande"]:
        story += section_header(labels[key], len(groups[key]), colors_[key], styles)
        story.append(recipe_table(groups[key], key, translations, styles))
        story.append(PageBreak())

    doc.build(story)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"PDF generado: {out_path}  ({size_kb} KB)")


if __name__ == "__main__":
    build_pdf()
