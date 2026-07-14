"""Estilos derivados por manipulación de bloque.

A partir del ensamble base (:class:`~patronaje.garment.shirt.Shirt`) se generan
variantes de estilo modificando las piezas con las operaciones geométricas de
`operations.py`. Cada estilo reemplaza los contornos afectados y deja el resto
del sistema (validación geométrica, exportadores, tech pack, marker) intacto.

Estilos incluidos:
* **flare** — camisa acampanada / túnica A-line (vuelo en delantero y espalda).
* **puff** — manga abullonada (volumen + copa levantada; la cabeza se frunce).

Nota: algunos estilos rompen a propósito el casado ``sisa = copa`` (p. ej. la
manga abullonada se **frunce** en la sisa), por lo que se validan sólo las
comprobaciones **geométricas** (polígono cerrado, simple, sin duplicados).
"""
from __future__ import annotations

from ..garment.shirt import Shirt
from . import operations as ops


def _find(shirt, name):
    return next((p for p in shirt.pieces if p.name == name), None)


def flare_shirt(shirt: Shirt, added_hem: float = 10.0) -> Shirt:
    """Convierte la camisa en acampanada/túnica añadiendo ``added_hem`` cm de
    vuelo por costado en delantero y espalda (A-line por slash-and-spread)."""
    p = shirt.p
    top_y = p.prof_sisa
    bot_y = p.largo_camisa
    quarter = (p.busto + p.holgura_busto) / 4.0
    ratio = added_hem / quarter
    for name in ("DELANTERO", "ESPALDA"):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.flare(pc.net_contour, 0.0, top_y, bot_y, ratio, side=+1)
            pc.name = name + " (acampanado)"
    return shirt


def puff_sleeve(shirt: Shirt, width_factor: float = 1.30, cap_lift: float = 3.5) -> Shirt:
    """Manga abullonada: ensancha la manga y levanta la copa (se frunce en la
    cabeza). Rompe intencionalmente el casado sisa=copa."""
    pc = _find(shirt, "MANGA")
    if pc:
        cap_h = shirt.sleeve.cap_height
        pts = ops.widen(pc.net_contour, 0.0, width_factor)
        pts = ops.lift(pts, cap_lift, cap_h, above=True)
        pc.net_contour = pts
        pc.name = "MANGA (abullonada)"
        pc.reference_texts = list(pc.reference_texts) + [((0.0, cap_h * 0.5), "fruncir cabeza")]
    return shirt


STYLES = {
    "flare": flare_shirt,
    "puff": puff_sleeve,
}


def apply_style(shirt: Shirt, style: str, **kw) -> Shirt:
    if style in (None, "", "none"):
        return shirt
    if style not in STYLES:
        raise KeyError(f"Estilo desconocido: '{style}'. Opciones: {list(STYLES)}")
    shirt = STYLES[style](shirt, **kw)
    shirt.layout()
    return shirt
