"""Exportador Adobe Illustrator (.ai) — compatible con PDF.

El formato **.ai** moderno es un PDF con estructura de Illustrator; Illustrator y
la mayoría de editores vectoriales abren un PDF renombrado a ``.ai`` como un
documento editable con una sola mesa de trabajo (artboard). Aquí generamos ese
PDF-compatible a **escala real 1:1** en un único artboard que contiene todas las
piezas como trazos vectoriales reales (no imágenes).

Best-effort honesto: se abre en Illustrator / Inkscape / Affinity como vectores;
para un AI nativo con capas de Illustrator exactas conviene reimportar el DXF o
el SVG. Ver `docs/aama_astm.md`.
"""
from __future__ import annotations

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

from ._common import gather_entities, content_bounds
from .pdf import _draw_entities


def export_ai(shirt, path: str, *, margin_cm: float = 1.5,
              include_seam: bool = True) -> str:
    ents = gather_entities(shirt, flip=True, include_seam=include_seam)
    minx, miny, maxx, maxy = content_bounds(ents)
    w_cm = (maxx - minx) + 2 * margin_cm
    h_cm = (maxy - miny) + 2 * margin_cm

    c = canvas.Canvas(path, pagesize=(w_cm * cm, h_cm * cm))
    c.setTitle("Camisa basica femenina ML - Talla S - Aldrich")
    c.setAuthor("patronaje")
    c.saveState()
    c.translate(margin_cm * cm, margin_cm * cm)
    _draw_entities(c, ents, minx, miny, cm)   # 1:1 (1 cm = 1 cm)
    c.restoreState()
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 8)
    c.drawString(margin_cm * cm, (h_cm - margin_cm * 0.5) * cm,
                 "AI compatible con PDF (Illustrator) - escala 1:1")
    c.showPage()
    c.save()
    return path
