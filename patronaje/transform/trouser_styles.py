"""Estilos de pantalón por manipulación del bloque base.

Del mismo bloque de pantalón salen varias siluetas modificando la **pierna** (por
debajo del tiro/rodilla): se estrecha o ensancha escalando simétricamente
respecto de la **raya** (grainline), o se recorta el largo. La cadera, el tiro y
las pinzas (arriba) no se tocan, así que el ajuste del cuerpo se conserva.
"""
from __future__ import annotations

from . import operations as ops


def _panels(tr):
    front = next((p for p in tr.pieces if p.name.startswith("PANTALON DELANTERO")), None)
    back = next((p for p in tr.pieces if p.name.startswith("PANTALON TRASERO")), None)
    return [p for p in (front, back) if p]


def _crease_x(pc, hem_y):
    xs = [x for x, y in pc.net_contour if abs(y - hem_y) < 0.6]
    return sum(xs) / len(xs) if xs else 0.0


def _taper(tr, hinge_y, ratio, label):
    """Escala la anchura de la pierna respecto de la raya, desde ``hinge_y`` al
    bajo (ratio<0 estrecha, ratio>0 ensancha)."""
    hem_y = tr.block.hem_y
    for pc in _panels(tr):
        cx = _crease_x(pc, hem_y)
        pc.net_contour = ops.flare_symmetric(pc.net_contour, cx, hinge_y, hem_y, ratio)
        pc.name = pc.name.split(" (")[0] + f" ({label})"
    return tr


def _crop(tr, cut_y, label, note=None):
    for pc in _panels(tr):
        pc.net_contour = ops.clip_below(pc.net_contour, cut_y)
        pc.name = pc.name.split(" (")[0] + f" ({label})"
        if note:
            pc.reference_texts = list(pc.reference_texts) + [((_crease_x(pc, cut_y), cut_y - 3), note)]
    return tr


def recto(tr):
    """Pierna recta (endereza el ligero afinado del bloque)."""
    return _taper(tr, tr.block.knee_y, +0.07, "recto")


def pitillo(tr):
    """Pitillo / skinny: estrecha mucho de la rodilla al bajo."""
    return _taper(tr, tr.block.knee_y, -0.32, "pitillo")


def wide(tr):
    """Pierna ancha (recto ancho): ensancha desde el tiro."""
    return _taper(tr, tr.block.crotch_y, +0.35, "ancho")


def palazzo(tr):
    """Palazzo: muy ancho y fluido desde el tiro."""
    return _taper(tr, tr.block.crotch_y, +0.75, "palazzo")


def campana(tr):
    """Campana / bootcut: entra en la rodilla y acampana hacia el bajo."""
    b = tr.block
    _taper(tr, b.knee_y, -0.10, "campana")
    calf = b.knee_y + (b.hem_y - b.knee_y) * 0.35
    for pc in _panels(tr):
        cx = _crease_x(pc, b.hem_y)
        pc.net_contour = ops.flare_symmetric(pc.net_contour, cx, calf, b.hem_y, 0.55)
    return tr


def capri(tr):
    """Capri / pirata: recortado a media pantorrilla."""
    b = tr.block
    return _crop(tr, b.knee_y + (b.hem_y - b.knee_y) * 0.55, "capri")


def short(tr):
    """Short / bermuda: recortado por encima de la rodilla."""
    b = tr.block
    return _crop(tr, b.knee_y - (b.knee_y - b.crotch_y) * 0.15, "short")


def culotte(tr):
    """Culotte: ancho desde el tiro y recortado (falda-pantalón)."""
    b = tr.block
    _taper(tr, b.crotch_y, +0.55, "culotte")
    return _crop(tr, b.knee_y + (b.hem_y - b.knee_y) * 0.30, "culotte")


def jogger(tr):
    """Jogger: estrecha el bajo y lo frunce a puño elástico."""
    _taper(tr, tr.block.knee_y, -0.18, "jogger")
    for pc in _panels(tr):
        pc.reference_texts = list(pc.reference_texts) + [
            ((_crease_x(pc, tr.block.hem_y), tr.block.hem_y - 4), "puño elástico")]
    return tr


TROUSER_STYLES = {
    "recto": recto,
    "pitillo": pitillo,
    "wide": wide,
    "palazzo": palazzo,
    "campana": campana,
    "capri": capri,
    "short": short,
    "culotte": culotte,
    "jogger": jogger,
}
