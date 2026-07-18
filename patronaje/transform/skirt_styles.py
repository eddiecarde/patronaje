"""Estilos de falda por manipulación del bloque base (recta / lápiz).

Del mismo bloque de falda salen varias siluetas modificando los paneles con las
operaciones de :mod:`patronaje.transform.operations`. Las pinzas de la falda
quedan **por encima de la línea de cadera**, así que los estilos que dan vuelo
**desde la cadera** (evasé, acampanada, circular, tubo) no las tocan; los estilos
de cintura llena (tableada, fruncida) reconstruyen un panel sin pinzas.

Cada estilo deja el resto del sistema (validación, marker, exportadores) intacto.
"""
from __future__ import annotations

from . import operations as ops


def _panels(skirt):
    front = next((p for p in skirt.pieces if p.name.startswith("FALDA DELANTERA")), None)
    back = next((p for p in skirt.pieces if p.name.startswith("FALDA TRASERA")), None)
    return front, back


def _flare_from_hip(skirt, added: float, label: str):
    """Da vuelo A-line desde la cadera (las pinzas, más arriba, no se tocan)."""
    hip_y, hem_y = skirt.block.hip_y, skirt.block.hem_y
    ratio = added / skirt.p.cuarto_cadera
    for pc in _panels(skirt):
        if pc:
            pc.net_contour = ops.flare(pc.net_contour, 0.0, hip_y, hem_y, ratio, side=+1)
            pc.name = pc.name.split(" (")[0] + f" ({label})"
    return skirt


def evase(skirt):
    """Falda evasé / A-line (vuelo moderado desde la cadera)."""
    return _flare_from_hip(skirt, added=9.0, label="evasé")


def acampanada(skirt):
    """Falda acampanada (vuelo amplio)."""
    return _flare_from_hip(skirt, added=20.0, label="acampanada")


def circular(skirt):
    """Falda muy amplia (semi-circular)."""
    return _flare_from_hip(skirt, added=34.0, label="circular")


def tubo(skirt, taper: float = 4.0):
    """Falda tubo / lápiz ajustada: estrecha el bajo y añade abertura trasera."""
    hip_y, hem_y = skirt.block.hip_y, skirt.block.hem_y
    knee = hip_y + (hem_y - hip_y) * 0.55
    ratio = -taper / skirt.p.cuarto_cadera          # vuelo negativo (entra el bajo)
    front, back = _panels(skirt)
    for pc in (front, back):
        if pc:
            pc.net_contour = ops.flare(pc.net_contour, 0.0, knee, hem_y, ratio, side=+1)
            pc.name = pc.name.split(" (")[0] + " (tubo)"
    if back:   # abertura (vent) en el CB, del knee al bajo
        back.construction_lines = list(back.construction_lines) + [
            ((0.0, knee), (0.0, hem_y))]
        back.notches = list(back.notches) + [(0.0, knee)]
        back.reference_texts = list(back.reference_texts) + [((0.6, knee + 2), "abertura")]
    return skirt


def mini(skirt, at: float = 0.42):
    """Falda mini (recorta el largo)."""
    hip_y, hem_y = skirt.block.hip_y, skirt.block.hem_y
    cut = hip_y + (hem_y - hip_y) * at
    for pc in _panels(skirt):
        if pc:
            pc.net_contour = ops.clip_below(pc.net_contour, cut)
            pc.name = pc.name.split(" (")[0] + " (mini)"
    return skirt


def maxi(skirt, extra: float = 35.0, flare_add: float = 10.0):
    """Falda maxi (alarga por debajo de la cadera y da algo de vuelo)."""
    hip_y, hem_y = skirt.block.hip_y, skirt.block.hem_y
    factor = (hem_y - hip_y + extra) / (hem_y - hip_y)
    newhem = hip_y + (hem_y - hip_y) * factor
    ratio = flare_add / skirt.p.cuarto_cadera
    for pc in _panels(skirt):
        if pc:
            pc.net_contour = ops.lengthen(pc.net_contour, hip_y, factor)
            pc.net_contour = ops.flare(pc.net_contour, 0.0, hip_y, newhem, ratio, side=+1)
            pc.name = pc.name.split(" (")[0] + " (maxi)"
    return skirt


def _full_panel(p, hem_y, extra: float):
    """Panel recto sin pinzas: cintura = cadera (+extra) para fruncir/tablear."""
    half = p.cuarto_cadera + extra
    return [(0.0, 0.0), (half, 0.0), (half, hem_y), (0.0, hem_y)]


def fruncida(skirt, fullness: float = 8.0):
    """Falda fruncida (dirndl): panel recto con cintura llena, sin pinzas."""
    hem_y = skirt.block.hem_y
    for pc in _panels(skirt):
        if pc:
            pc.net_contour = _full_panel(skirt.p, hem_y, fullness)
            pc.darts = []
            pc.name = pc.name.split(" (")[0] + " (fruncida)"
            pc.reference_texts = list(pc.reference_texts) + [
                ((skirt.p.cuarto_cadera * 0.4, 2.0), "fruncir cintura")]
    return skirt


def tableada(skirt, n_pleats: int = 3, pleat: float = 4.0):
    """Falda tableada: panel recto (sin pinzas) con marcas de tabla en la cintura."""
    hem_y = skirt.block.hem_y
    extra = n_pleats * pleat
    for pc in _panels(skirt):
        if pc:
            pc.net_contour = _full_panel(skirt.p, hem_y, extra)
            pc.darts = []
            half = skirt.p.cuarto_cadera + extra
            lines = []
            for i in range(1, n_pleats + 1):
                x = half * i / (n_pleats + 1)
                lines.append(((x, 0.0), (x, hem_y * 0.5)))
            pc.construction_lines = list(pc.construction_lines) + lines
            pc.name = pc.name.split(" (")[0] + " (tableada)"
            pc.reference_texts = list(pc.reference_texts) + [((half * 0.5, 2.0), "tablas")]
    return skirt


def yoke(skirt, flare_add: float = 8.0):
    """Canesú de cadera: yugo (con las pinzas absorbidas por su forma) + falda
    inferior acampanada sin pinzas, cortados en la línea de cadera."""
    from ..piece import Piece
    p = skirt.p
    hip_y, hem_y = skirt.block.hip_y, skirt.block.hem_y
    ratio = flare_add / p.cuarto_cadera
    front, back = _panels(skirt)
    for pc in (front, back):
        if pc is None:
            continue
        upper = ops.clip_below(pc.net_contour, hip_y)      # yugo (conserva pinza)
        lower = ops.clip_above(pc.net_contour, hip_y)
        lower = ops.flare(lower, 0.0, hip_y, hem_y, ratio, side=+1)
        base = pc.name.split(" (")[0]
        pc.net_contour = upper
        pc.name = base + " CANESU"
        pc.hem_allowance = None
        idx = skirt.pieces.index(pc)
        low = Piece(name=base + " INFERIOR", number=pc.number + 20, size=pc.size,
                    quantity=1, cut_type="al doblez", on_fold=True, fold_x=0.0,
                    net_contour=lower, seam_allowance=p.margen_costura,
                    hem_allowance=p.margen_dobladillo,
                    grain=((p.cuarto_cadera * 0.5, hip_y + 2),
                           (p.cuarto_cadera * 0.5, hem_y - 2)))
        skirt.pieces.insert(idx + 1, low)
    return skirt


def godet(skirt, godet_width: float = 22.0, from_frac: float = 0.5):
    """Godets triangulares insertados en los costados (vuelo desde la cadera)."""
    from ..piece import Piece
    p = skirt.p
    hip_y, hem_y = skirt.block.hip_y, skirt.block.hem_y
    top_y = hip_y + (hem_y - hip_y) * from_frac
    h = hem_y - top_y
    size = skirt.pieces[0].size if skirt.pieces else "S"
    contour = [(0.0, 0.0), (godet_width / 2, h), (-godet_width / 2, h)]
    god = Piece(name="GODET FALDA", number=40, size=size, quantity=4,
                cut_type="4 (en costados)", net_contour=contour,
                seam_allowance=p.margen_costura, hem_allowance=p.margen_dobladillo,
                grain=((0.0, 1.0), (0.0, h - 1)),
                reference_texts=[((0.0, h * 0.4), "godet")])
    skirt.pieces.append(god)
    for pc in _panels(skirt):
        if pc:
            pc.construction_lines = list(pc.construction_lines) + [
                ((p.cuarto_cadera, top_y), (p.cuarto_cadera, hem_y))]
    return skirt


SKIRT_STYLES = {
    "evase": evase,
    "acampanada": acampanada,
    "circular": circular,
    "tubo": tubo,
    "mini": mini,
    "maxi": maxi,
    "fruncida": fruncida,
    "tableada": tableada,
    "yoke": yoke,
    "godet": godet,
}
