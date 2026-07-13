"""Motor de grading: regenera todas las tallas y produce el nido de escalado.

Como el patrón es paramétrico, "gradar" es simplemente **regenerar** la prenda
para cada talla con `build_shirt(size)` — no se redibuja ni se deforma nada. Este
módulo orquesta esa regeneración y genera un **nido de grading** (las líneas de
corte de una misma pieza superpuestas para todas las tallas, alineadas en un
punto de referencia), que es la comprobación visual clásica de que el escalado
es proporcional y consistente.
"""
from __future__ import annotations

import svgwrite

from ..garment.shirt import build_shirt, Shirt
from .rules import SIZE_ORDER

# color por talla para el nido
SIZE_COLORS = {
    "XS": "#8e44ad", "S": "#2980b9", "M": "#27ae60",
    "L": "#f39c12", "XL": "#d35400", "XXL": "#c0392b",
}


def grade_all(sizes=None) -> dict[str, Shirt]:
    """Regenera y posiciona la prenda para cada talla."""
    sizes = sizes or SIZE_ORDER
    return {s: build_shirt(s).layout() for s in sizes}


def _anchor(piece):
    """Punto de referencia de nido (esquina inferior-izquierda del bbox net)."""
    minx, miny, maxx, maxy = piece.bbox()
    return (minx, miny)


def export_grade_nest(piece_name: str, path: str, sizes=None,
                      margin: float = 3.0) -> str:
    """Exporta a SVG el nido de grading de una pieza para todas las tallas.

    Todas las tallas se alinean por la esquina inferior-izquierda de su bbox,
    de modo que las curvas se abren proporcionalmente (nido de grading).
    """
    sizes = sizes or SIZE_ORDER
    shirts = grade_all(sizes)

    # recolecta contornos de la pieza pedida, trasladados al mismo ancla
    curves: list[tuple[str, list[tuple[float, float]]]] = []
    all_pts: list[tuple[float, float]] = []
    for s in sizes:
        pc = next((p for p in shirts[s].pieces if p.name == piece_name), None)
        if pc is None:
            continue
        ax, ay = _anchor(pc)
        cut = [(x - ax, y - ay) for x, y in pc.cut_contour()]
        curves.append((s, cut))
        all_pts += cut

    xs = [p[0] for p in all_pts]; ys = [p[1] for p in all_pts]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    w = (maxx - minx) + 2 * margin
    h = (maxy - miny) + 2 * margin

    def tx(x): return x - minx + margin
    def ty(y): return y - miny + margin

    dwg = svgwrite.Drawing(path, size=(f"{w}cm", f"{h}cm"), viewBox=f"0 0 {w} {h}")
    dwg.add(dwg.text(f"NIDO DE GRADING — {piece_name} — tallas {', '.join(sizes)}",
                     insert=(margin, margin - 0.6), font_size=1.0,
                     font_family="sans-serif", fill="#000"))
    for s, cut in curves:
        color = SIZE_COLORS.get(s, "#000")
        pts = [(tx(x), ty(y)) for x, y in cut]
        dwg.add(dwg.polygon(points=pts, fill="none", stroke=color, stroke_width=0.08))
        # etiqueta de talla en la esquina superior de cada contorno
        lx, ly = pts[0]
        dwg.add(dwg.text(s, insert=(lx, ly), font_size=0.9, fill=color,
                         font_family="sans-serif"))
    dwg.save()
    return path
