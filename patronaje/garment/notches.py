"""Casado automático de piquetes entre costuras que se cosen juntas.

Dos bordes que se cosen juntos (costado delantero↔trasero, hombro↔hombro,
sisa↔copa…) deben casar en longitud. Si se colocan piquetes a la **misma
fracción de longitud de arco** desde el extremo homólogo de cada borde, ambos
piquetes caen en puntos que físicamente se unen al coser: el operario alinea los
piquetes y la costura queda equilibrada, sin fruncidos ni desfases.

Este módulo extrae el sub-tramo de contorno que corresponde a cada costura
(entre dos puntos dados) y coloca piquetes coincidentes en ambas piezas. Es
independiente de la prenda: se le pasan las piezas y los extremos de la costura.
"""
from __future__ import annotations

import math

from ..transform.operations import arclen_point


def _polylen(pts) -> float:
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
               for i in range(len(pts) - 1))


def _nearest_idx(contour, pt) -> int:
    return min(range(len(contour)),
               key=lambda i: math.hypot(contour[i][0] - pt[0], contour[i][1] - pt[1]))


def seam_subpath(contour, a, b, prefer: str = "short") -> list:
    """Sub-tramo del contorno entre los vértices más cercanos a ``a`` y ``b``.

    Un polígono cerrado ofrece dos caminos entre dos puntos; ``prefer`` elige
    ``"short"`` (por defecto) o ``"long"``. El resultado se orienta de ``a`` a
    ``b``.
    """
    ia, ib = _nearest_idx(contour, a), _nearest_idx(contour, b)
    fwd = contour[ia:ib + 1] if ia <= ib else contour[ia:] + contour[:ib + 1]
    bwd_raw = contour[ib:ia + 1] if ib <= ia else contour[ib:] + contour[:ia + 1]
    bwd = list(reversed(bwd_raw))                     # también orientado a->b
    if len(fwd) < 2:
        fwd = bwd
    if len(bwd) < 2:
        bwd = fwd
    short, long = (fwd, bwd) if _polylen(fwd) <= _polylen(bwd) else (bwd, fwd)
    return long if prefer == "long" else short


def match_seam(pieceA, a0, a1, pieceB, b0, b1, *,
               fractions=(0.5,), prefer: str = "short") -> tuple[float, float]:
    """Coloca piquetes coincidentes en la costura ``a0-a1`` (pieza A) y su
    homóloga ``b0-b1`` (pieza B). ``a0`` casa con ``b0``. Devuelve las longitudes
    de ambos tramos (para verificar el casado)."""
    subA = seam_subpath(pieceA.net_contour, a0, a1, prefer)
    subB = seam_subpath(pieceB.net_contour, b0, b1, prefer)
    for f in fractions:
        pieceA.notches = list(pieceA.notches) + [arclen_point(subA, f)]
        pieceB.notches = list(pieceB.notches) + [arclen_point(subB, f)]
    return _polylen(subA), _polylen(subB)


def _find(pieces, name):
    exact = next((p for p in pieces if p.name == name), None)
    if exact is not None:
        return exact
    return next((p for p in pieces if p.name.startswith(name)), None)


def add_shirt_notches(shirt) -> list[tuple[str, float, float]]:
    """Casa las costuras principales de la camisa. Devuelve, por costura, el par
    de longitudes de tramo (para el reporte/validación de casado)."""
    b = shirt.bodice
    front, back = _find(shirt.pieces, "DELANTERO"), _find(shirt.pieces, "ESPALDA")
    report: list[tuple[str, float, float]] = []
    if front is None or back is None:
        return report
    dUS, dHs = b.points["D-US"].as_tuple(), b.points["D-Hs"].as_tuple()
    eUS, eHs = b.points["E-US"].as_tuple(), b.points["E-Hs"].as_tuple()
    la, lb = match_seam(front, dUS, dHs, back, eUS, eHs, fractions=(0.4, 0.72))
    report.append(("costado del/esp", la, lb))
    # hombro delantero↔canesú (en la camisa el hombro trasero va en el canesú)
    yoke = _find(shirt.pieces, "CANESU")
    if yoke is not None:
        dSNP, dSP = b.points["D-SNP"].as_tuple(), b.points["D-SP"].as_tuple()
        eSNP, eSP = b.points["E-SNP"].as_tuple(), b.points["E-SP"].as_tuple()
        la, lb = match_seam(front, dSNP, dSP, yoke, eSNP, eSP, fractions=(0.55,))
        report.append(("hombro del/canesú", la, lb))
    return report


def add_skirt_notches(skirt) -> list[tuple[str, float, float]]:
    """Casa el costado delantero↔trasero de la falda (de la cadera al bajo)."""
    p = skirt.p
    front, back = _find(skirt.pieces, "FALDA DELANTERA"), _find(skirt.pieces, "FALDA TRASERA")
    if front is None or back is None:
        return []
    hip = (p.cuarto_cadera, skirt.block.hip_y)
    hem = (p.cuarto_cadera, skirt.block.hem_y)
    la, lb = match_seam(front, hip, hem, back, hip, hem, fractions=(0.5,))
    return [("costado falda", la, lb)]


def add_trouser_notches(trouser) -> list[tuple[str, float, float]]:
    """Casa entrepierna y costado (delantero↔trasero) del pantalón."""
    b = trouser.block
    front, back = _find(trouser.pieces, "PANTALON DELANTERO"), _find(trouser.pieces, "PANTALON TRASERO")
    if front is None or back is None:
        return []
    report = []
    # entrepierna: del gancho (crotch) a la boca interior
    fin, bin_ = b.front_inseam, b.back_inseam
    la, lb = match_seam(front, fin[0], fin[-1], back, bin_[0], bin_[-1], fractions=(0.5,))
    report.append(("entrepierna del/tra", la, lb))
    # costado: de la cintura al bajo, por el lado exterior (camino largo)
    fhem_out = max((pt for pt in front.net_contour if abs(pt[1] - b.hem_y) < 0.5),
                   key=lambda q: q[0])
    bhem_out = max((pt for pt in back.net_contour if abs(pt[1] - b.hem_y) < 0.5),
                   key=lambda q: q[0])
    fwaist_side = max((pt for pt in front.net_contour if pt[1] < 0.5), key=lambda q: q[0])
    bwaist_side = max((pt for pt in back.net_contour if pt[1] < 0.5), key=lambda q: q[0])
    la, lb = match_seam(front, fwaist_side, fhem_out, back, bwaist_side, bhem_out,
                        fractions=(0.55,), prefer="short")
    report.append(("costado del/tra", la, lb))
    return report
