"""Operaciones geométricas de manipulación de bloque.

Las técnicas clásicas de patronaje para crear estilos a partir de un bloque son:

* **Pivote / traslado de pinza** (*dart manipulation*): rotar una parte de la
  pieza alrededor de un punto para mover una pinza o abrir volumen.
* **Slash-and-spread** (*cortar y abrir*): cortar la pieza y separar las partes
  para añadir amplitud (vuelo, frunces, pliegues).

Aquí se implementan como funciones puras sobre listas de puntos ``(x, y)``. El
vuelo continuo (A-line) es el **límite** del slash-and-spread con infinitos
cortes: equivale a escalar la anchura proporcionalmente con la profundidad, y así
se implementa `flare`. `widen` y `lift` sirven para frunces/mangas abullonadas.
`pivot` es el primitivo de manipulación de pinza.
"""
from __future__ import annotations

import math


def rotate(p, pivot, ang):
    """Rota el punto ``p`` un ángulo ``ang`` (rad) alrededor de ``pivot``."""
    ca, sa = math.cos(ang), math.sin(ang)
    dx, dy = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + dx * ca - dy * sa, pivot[1] + dx * sa + dy * ca)


def pivot(points, pivot_pt, ang, moving):
    """Rota los puntos para los que ``moving(pt)`` es True alrededor de
    ``pivot_pt`` (primitivo de traslado de pinza / apertura)."""
    return [rotate(pt, pivot_pt, ang) if moving(pt) else tuple(pt) for pt in points]


def flare(points, center_x, top_y, bottom_y, ratio, side=+1):
    """Vuelo A-line: separa la anchura de forma creciente con la profundidad.

    Sólo se abre el lado indicado por ``side`` (+1 = hacia +x, típicamente la
    costura de costado); el centro (``center_x``, doblez o CF) queda recto. En el
    dobladillo (``bottom_y``) la anchura del lado se multiplica por ``1+ratio``.
    Es el límite continuo del slash-and-spread → contorno siempre simple.
    """
    span = max(1e-6, bottom_y - top_y)
    out = []
    for x, y in points:
        t = max(0.0, min(1.0, (y - top_y) / span))
        if (x - center_x) * side > 0:
            xn = center_x + (x - center_x) * (1 + t * ratio)
        else:
            xn = x
        out.append((xn, y))
    return out


def widen(points, center_x, factor, y0=None, y1=None):
    """Escala la anchura respecto de ``center_x`` por ``factor`` (frunce/volumen),
    opcionalmente sólo en la banda ``[y0, y1]``."""
    out = []
    for x, y in points:
        inband = (y0 is None or y >= y0) and (y1 is None or y <= y1)
        xn = center_x + (x - center_x) * factor if inband else x
        out.append((xn, y))
    return out


def lift(points, amount, y_ref, above=True):
    """Sube (resta y) los puntos por encima de ``y_ref`` de forma proporcional
    (para levantar la copa de una manga abullonada)."""
    out = []
    span = max(1e-6, y_ref)
    for x, y in points:
        if above and y < y_ref:
            f = (y_ref - y) / span
            out.append((x, y - amount * f))
        else:
            out.append((x, y))
    return out
