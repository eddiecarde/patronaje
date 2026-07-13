"""Exportador SVG vectorial.

Dibuja todas las piezas como entidades SVG reales (``polygon``, ``polyline``,
``line``, ``circle``, ``text``), agrupadas por capa con colores diferenciados y
unidades en centímetros (``1 unidad de usuario = 1 cm``; se fija ``width``/
``height`` en cm y un ``viewBox`` acorde). No se rasteriza nada.

Como el marco interno ya usa ``y`` hacia abajo (igual que SVG), no se invierte
Y; sólo se traslada para que todo quede en coordenadas positivas.
"""
from __future__ import annotations

import svgwrite

from ..piece import EPolyline, ELine, EText, ECircle, ENotch, ALL_LAYERS
from ._common import gather_entities, content_bounds, notch_marks

# color CSS por capa
LAYER_CSS = {
    "CONSTRUCCION": "#888888",
    "CORTE": "#d00000",
    "COSTURA": "#00a000",
    "PIQUETES": "#00b0b0",
    "TEXTOS": "#000000",
    "CENTROS": "#0050ff",
    "HILO": "#c0a000",
    "DOBLEZ": "#c000c0",
    "BOTONES": "#ff8000",
    "OJAL": "#ff40a0",
    "REFERENCIAS": "#b0b0b0",
}


def export_svg(shirt, path: str, *, margin: float = 3.0, include_seam: bool = True) -> str:
    ents = gather_entities(shirt, flip=False, include_seam=include_seam)
    minx, miny, maxx, maxy = content_bounds(ents)
    w = (maxx - minx) + 2 * margin
    h = (maxy - miny) + 2 * margin

    def tx(x):
        return x - minx + margin

    def ty(y):
        return y - miny + margin

    dwg = svgwrite.Drawing(path, size=(f"{w}cm", f"{h}cm"),
                           viewBox=f"0 0 {w} {h}")
    groups = {layer: dwg.g(id=layer, stroke=LAYER_CSS.get(layer, "#000"),
                           fill="none", stroke_width=0.08)
              for layer in ALL_LAYERS}

    for e in ents:
        g = groups[e.layer]
        if isinstance(e, EPolyline):
            pts = [(tx(x), ty(y)) for x, y in e.points]
            if e.closed:
                g.add(dwg.polygon(points=pts))
            else:
                g.add(dwg.polyline(points=pts))
        elif isinstance(e, ELine):
            g.add(dwg.line((tx(e.p1[0]), ty(e.p1[1])), (tx(e.p2[0]), ty(e.p2[1]))))
        elif isinstance(e, ECircle):
            g.add(dwg.circle(center=(tx(e.center[0]), ty(e.center[1])),
                             r=e.radius, fill=LAYER_CSS.get(e.layer, "#000")))
        elif isinstance(e, ENotch):
            for a, b in notch_marks(e):
                g.add(dwg.line((tx(a[0]), ty(a[1])), (tx(b[0]), ty(b[1]))))
        elif isinstance(e, EText):
            anchor = "middle" if e.align == "center" else "start"
            g.add(dwg.text(e.text, insert=(tx(e.pos[0]), ty(e.pos[1])),
                           font_size=e.height, fill=LAYER_CSS["TEXTOS"],
                           stroke="none", text_anchor=anchor,
                           font_family="sans-serif"))

    for g in groups.values():
        dwg.add(g)
    dwg.save()
    return path
