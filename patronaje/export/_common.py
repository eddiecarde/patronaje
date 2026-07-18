"""Utilidades compartidas por los exportadores.

* Aplana un :class:`~patronaje.garment.shirt.Shirt` (o lista de piezas) a una
  lista de entidades CAD ya posicionadas (con el ``offset`` de layout aplicado).
* Reorienta el marco interno (``y`` hacia abajo) al marco CAD (``y`` hacia
  arriba) invirtiendo Y, para que la prenda quede "de pie" en AutoCAD/SVG.
"""
from __future__ import annotations

from ..piece import (
    Entity, EPolyline, ELine, EText, ECircle, ENotch,
)


def flip_entity(e: Entity) -> Entity:
    """Invierte Y (marco patronaje -> marco CAD)."""
    if isinstance(e, EPolyline):
        return EPolyline(e.layer, [(x, -y) for x, y in e.points], e.closed)
    if isinstance(e, ELine):
        return ELine(e.layer, (e.p1[0], -e.p1[1]), (e.p2[0], -e.p2[1]))
    if isinstance(e, EText):
        return EText(e.layer, (e.pos[0], -e.pos[1]), e.text, e.height, e.rotation, e.align)
    if isinstance(e, ECircle):
        return ECircle(e.layer, (e.center[0], -e.center[1]), e.radius)
    if isinstance(e, ENotch):
        return ENotch(e.layer, (e.pos[0], -e.pos[1]),
                      (e.direction[0], -e.direction[1]), e.depth)
    return e


def gather_entities(shirt_or_pieces, *, flip: bool = True, include_seam: bool = True):
    """Devuelve todas las entidades de todas las piezas, ya posicionadas."""
    pieces = getattr(shirt_or_pieces, "pieces", shirt_or_pieces)
    ents: list[Entity] = []
    for pc in pieces:
        for e in pc.get_entities(include_seam=include_seam):
            ents.append(flip_entity(e) if flip else e)
    return ents


def content_bounds(entities) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for e in entities:
        if isinstance(e, EPolyline):
            xs += [x for x, _ in e.points]; ys += [y for _, y in e.points]
        elif isinstance(e, ELine):
            xs += [e.p1[0], e.p2[0]]; ys += [e.p1[1], e.p2[1]]
        elif isinstance(e, EText):
            xs += [e.pos[0]]; ys += [e.pos[1]]
        elif isinstance(e, ECircle):
            xs += [e.center[0] - e.radius, e.center[0] + e.radius]
            ys += [e.center[1] - e.radius, e.center[1] + e.radius]
        elif isinstance(e, ENotch):
            xs += [e.pos[0]]; ys += [e.pos[1]]
    if not xs:
        return (0.0, 0.0, 1.0, 1.0)
    return (min(xs), min(ys), max(xs), max(ys))


def notch_marks(e: ENotch):
    """Devuelve dos segmentos (V) que representan el piquete apuntando al
    interior de la pieza. Cada segmento es ((x0,y0),(x1,y1))."""
    import math
    x, y = e.pos
    dx, dy = e.direction
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    # perpendicular
    px, py = -dy, dx
    tip = (x + dx * e.depth, y + dy * e.depth)
    a = (x + px * e.depth * 0.4, y + py * e.depth * 0.4)
    b = (x - px * e.depth * 0.4, y - py * e.depth * 0.4)
    return [(a, tip), (b, tip)]
