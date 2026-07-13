"""Constructores de contornos para piezas geométricamente simples.

Puño, tapeta, cuello, pie de cuello, vista y bolsillo se derivan de rectángulos
o bandas curvas con esquinas redondeadas (arcos tangentes G1). Se centralizan
aquí para reutilizarlos y documentar su construcción.
"""
from __future__ import annotations

import math

from ...core.geometry import tangent_arc


def rounded_rect(width: float, height: float, radius: float = 0.0,
                 x0: float = 0.0, y0: float = 0.0) -> list[tuple[float, float]]:
    """Rectángulo (opcionalmente con esquinas redondeadas por arcos tangentes)."""
    x1, y1 = x0 + width, y0 + height
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if radius <= 0:
        return corners
    out: list[tuple[float, float]] = []
    n = len(corners)
    for i in range(n):
        prev = corners[(i - 1) % n]
        cur = corners[i]
        nxt = corners[(i + 1) % n]
        out += tangent_arc(prev, cur, nxt, radius, segments=8)
    return out


def arc_band(length: float, height: float, rise: float,
             samples: int = 40) -> list[tuple[float, float]]:
    """Banda curva (para cuello / pie de cuello).

    El borde inferior (de costura al escote) es un arco de cuerda ``length`` que
    se eleva ``rise`` en el centro; el borde superior es paralelo a ``height``.
    La longitud de arco del borde inferior es aprox. ``length`` (se usa como
    referencia de casado con el escote). Devuelve el contorno cerrado.
    """
    # arco inferior: parábola suave y = -4*rise*(t-0.5)^2 + rise (rise arriba)
    bottom = []
    for i in range(samples + 1):
        t = i / samples
        x = t * length
        y = -(4 * rise * (t - 0.5) ** 2) + rise
        bottom.append((x, y))
    top = [(x, y + height) for x, y in bottom]
    return bottom + list(reversed(top))


def collar_with_point(length: float, height: float, rise: float,
                      point_drop: float = 1.2, samples: int = 40) -> list[tuple[float, float]]:
    """Cuello con punta (medio cuello, doblez en CB en x=0).

    ``length`` es la mitad del contorno de escote; en el extremo (CF) el cuello
    forma una punta que baja ``point_drop``.
    """
    bottom = []
    for i in range(samples + 1):
        t = i / samples
        x = t * length
        y = -(4 * rise * (t - 0.5) ** 2) + rise
        bottom.append((x, y))
    # borde exterior (superior) con punta en el extremo CF
    tip = (length + point_drop * 0.6, height + point_drop)
    top = [(x, y + height) for x, y in bottom]
    contour = bottom + [tip] + list(reversed(top))
    return contour
