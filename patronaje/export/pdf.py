"""Exportador PDF: escala real 1:1 (mosaico) y ajuste a A4.

* :func:`export_pdf_1to1` produce un PDF a **escala real** (1 cm = 1 cm)
  repartido en mosaico sobre hojas A4 apaisadas, con marcas de registro y
  etiquetas de fila/columna para pegar las hojas y cortar en tela.
* :func:`export_pdf_a4` ajusta **todo el patrón a una sola hoja A4** (con su
  factor de escala indicado), útil como vista de conjunto.

Ambos dibujan entidades vectoriales reales (no imágenes). Se usa el marco
CAD (Y hacia arriba), coherente con el sistema de coordenadas de reportlab.
"""
from __future__ import annotations

import math

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

from ..piece import EPolyline, ELine, EText, ECircle, ENotch
from ._common import gather_entities, content_bounds, notch_marks
from .svg import LAYER_CSS


def _set_layer(c, layer):
    c.setStrokeColor(HexColor(LAYER_CSS.get(layer, "#000000")))
    c.setFillColor(HexColor(LAYER_CSS.get(layer, "#000000")))


def _draw_entities(c, ents, tx, ty, sc):
    """Dibuja entidades aplicando (x,y)->((x-tx)*sc, (y-ty)*sc) en puntos PDF."""
    def X(x):
        return (x - tx) * sc
    def Y(y):
        return (y - ty) * sc
    for e in ents:
        _set_layer(c, e.layer)
        if isinstance(e, EPolyline):
            c.setLineWidth(0.4 if e.layer == "COSTURA" else 0.7)
            p = c.beginPath()
            pts = e.points
            p.moveTo(X(pts[0][0]), Y(pts[0][1]))
            for x, y in pts[1:]:
                p.lineTo(X(x), Y(y))
            if e.closed:
                p.close()
            c.drawPath(p, stroke=1, fill=0)
        elif isinstance(e, ELine):
            c.setLineWidth(0.5)
            c.line(X(e.p1[0]), Y(e.p1[1]), X(e.p2[0]), Y(e.p2[1]))
        elif isinstance(e, ECircle):
            c.circle(X(e.center[0]), Y(e.center[1]), e.radius * sc, stroke=1,
                     fill=1 if e.layer in ("CENTROS", "REFERENCIAS") else 0)
        elif isinstance(e, ENotch):
            c.setLineWidth(0.6)
            for a, b in notch_marks(e):
                c.line(X(a[0]), Y(a[1]), X(b[0]), Y(b[1]))
        elif isinstance(e, EText):
            c.setFont("Helvetica", max(4.0, e.height * sc))
            if e.align == "center":
                c.drawCentredString(X(e.pos[0]), Y(e.pos[1]), e.text)
            else:
                c.drawString(X(e.pos[0]), Y(e.pos[1]), e.text)


def export_pdf_1to1(shirt, path: str, *, margin_cm: float = 1.0,
                    include_seam: bool = True) -> str:
    ents = gather_entities(shirt, flip=True, include_seam=include_seam)
    minx, miny, maxx, maxy = content_bounds(ents)
    w_cm, h_cm = (maxx - minx), (maxy - miny)

    page_w, page_h = landscape(A4)
    usable_w = page_w - 2 * margin_cm * cm
    usable_h = page_h - 2 * margin_cm * cm
    tile_w_cm = usable_w / cm
    tile_h_cm = usable_h / cm

    nx = max(1, math.ceil(w_cm / tile_w_cm))
    ny = max(1, math.ceil(h_cm / tile_h_cm))

    c = canvas.Canvas(path, pagesize=landscape(A4))
    for j in range(ny):
        for i in range(nx):
            # región del patrón para esta hoja (en cm, marco contenido)
            tile_minx = minx + i * tile_w_cm
            tile_miny = miny + j * tile_h_cm
            # clip a la zona útil
            c.saveState()
            c.translate(margin_cm * cm, margin_cm * cm)
            path_clip = c.beginPath()
            path_clip.rect(0, 0, usable_w, usable_h)
            c.clipPath(path_clip, stroke=0, fill=0)
            _draw_entities(c, ents, tile_minx, tile_miny, cm)
            c.restoreState()
            # marco y etiqueta de mosaico
            c.setStrokeColor(HexColor("#bbbbbb"))
            c.setLineWidth(0.3)
            c.rect(margin_cm * cm, margin_cm * cm, usable_w, usable_h)
            c.setFillColor(HexColor("#666666"))
            c.setFont("Helvetica", 8)
            c.drawString(margin_cm * cm + 4, margin_cm * cm + 4,
                         f"Camisa S — 1:1 — Fila {j+1}/{ny}  Col {i+1}/{nx}  "
                         f"(pegar por marcas de registro)")
            # marcas de registro en esquinas
            _reg_marks(c, margin_cm * cm, margin_cm * cm, usable_w, usable_h)
            c.showPage()
    c.save()
    return path


def _reg_marks(c, x0, y0, w, h, s=10):
    c.setStrokeColor(HexColor("#000000"))
    c.setLineWidth(0.5)
    for (x, y) in [(x0, y0), (x0 + w, y0), (x0, y0 + h), (x0 + w, y0 + h)]:
        c.line(x - s, y, x + s, y)
        c.line(x, y - s, x, y + s)


def export_pdf_a4(shirt, path: str, *, margin_cm: float = 1.2,
                  include_seam: bool = True) -> str:
    ents = gather_entities(shirt, flip=True, include_seam=include_seam)
    minx, miny, maxx, maxy = content_bounds(ents)
    w_cm, h_cm = (maxx - minx), (maxy - miny)

    page_w, page_h = landscape(A4)
    usable_w = page_w - 2 * margin_cm * cm
    usable_h = page_h - 2 * margin_cm * cm
    sc = min(usable_w / (w_cm * cm), usable_h / (h_cm * cm)) * cm
    scale_factor = sc / cm  # 1:x

    c = canvas.Canvas(path, pagesize=landscape(A4))
    c.saveState()
    c.translate(margin_cm * cm, margin_cm * cm)
    _draw_entities(c, ents, minx, miny, sc)
    c.restoreState()
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 9)
    c.drawString(margin_cm * cm, page_h - margin_cm * cm + 4,
                 f"Camisa básica femenina ML — Talla S — Vista de conjunto — "
                 f"escala 1:{1/scale_factor:.2f}  (NO cortar a esta escala)")
    c.showPage()
    c.save()
    return path
