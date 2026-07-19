"""Estilos de vestido por manipulación de los bloques del vestido.

El vestido base es cuerpo entallado + falda unidos en el talle. Los estilos
actúan sobre la **falda** (vuelo desde la cadera, largo, godets) o sobre la
prenda (sin mangas), sin tocar la **cintura**, de modo que la costura de talle
sigue casando y el ajuste del cuerpo se conserva.
"""
from __future__ import annotations

from . import operations as ops


def _skirt_panels(d):
    return [p for p in d.pieces if p.name.startswith("VESTIDO FALDA")]


def _flare(d, added, label):
    hip_y, hem_y = d.skirt.hip_y, d.skirt.hem_y
    ratio = added / d.p.cuarto_cadera
    for pc in _skirt_panels(d):
        pc.net_contour = ops.flare(pc.net_contour, 0.0, hip_y, hem_y, ratio, side=+1)
        pc.name = pc.name.split(" (")[0] + f" ({label})"
    return d


def recto(d):
    """Vestido recto (falda tubo, silueta del bloque)."""
    return d


def evase(d):
    """Vestido evasé / A-line (vuelo moderado de falda)."""
    return _flare(d, 9.0, "evasé")


def acampanada(d):
    """Vestido de falda amplia."""
    return _flare(d, 22.0, "acampanada")


def sin_mangas(d):
    """Vestido sin mangas (sisa acabada con vista/bies)."""
    d.pieces = [p for p in d.pieces if not p.name.startswith("MANGA")]
    return d


def mini(d, at: float = 0.45):
    """Vestido corto: recorta la falda."""
    hip_y, hem_y = d.skirt.hip_y, d.skirt.hem_y
    cut = hip_y + (hem_y - hip_y) * at
    for pc in _skirt_panels(d):
        pc.net_contour = ops.clip_below(pc.net_contour, cut)
        pc.name = pc.name.split(" (")[0] + " (mini)"
    return d


def maxi(d, extra: float = 32.0, flare_add: float = 10.0):
    """Vestido largo: alarga la falda y le da algo de vuelo."""
    hip_y, hem_y = d.skirt.hip_y, d.skirt.hem_y
    factor = (hem_y - hip_y + extra) / (hem_y - hip_y)
    newhem = hip_y + (hem_y - hip_y) * factor
    ratio = flare_add / d.p.cuarto_cadera
    for pc in _skirt_panels(d):
        pc.net_contour = ops.lengthen(pc.net_contour, hip_y, factor)
        pc.net_contour = ops.flare(pc.net_contour, 0.0, hip_y, newhem, ratio, side=+1)
        pc.name = pc.name.split(" (")[0] + " (maxi)"
    return d


def godet(d, godet_width: float = 22.0, from_frac: float = 0.5):
    """Godets triangulares en los costados de la falda (vuelo desde media falda)."""
    from ..piece import Piece
    p = d.p
    hip_y, hem_y = d.skirt.hip_y, d.skirt.hem_y
    top_y = hip_y + (hem_y - hip_y) * from_frac
    h = hem_y - top_y
    size = d.pieces[0].size if d.pieces else "S"
    contour = [(0.0, 0.0), (godet_width / 2, h), (-godet_width / 2, h)]
    d.pieces.append(Piece(name="GODET VESTIDO", number=40, size=size, quantity=4,
                          cut_type="4 (en costados)", net_contour=contour,
                          seam_allowance=p.margen_costura, hem_allowance=p.margen_dobladillo,
                          grain=((0.0, 1.0), (0.0, h - 1)),
                          reference_texts=[((0.0, h * 0.4), "godet")]))
    for pc in _skirt_panels(d):
        pc.construction_lines = list(pc.construction_lines) + [
            ((p.cuarto_cadera, top_y), (p.cuarto_cadera, hem_y))]
    return d


DRESS_STYLES = {
    "recto": recto,
    "evase": evase,
    "acampanada": acampanada,
    "sin_mangas": sin_mangas,
    "mini": mini,
    "maxi": maxi,
    "godet": godet,
}
