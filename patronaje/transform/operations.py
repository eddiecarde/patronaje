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


def flare_symmetric(points, center_x, top_y, bottom_y, ratio):
    """Vuelo simétrico: abre ambos lados respecto de ``center_x`` crecientemente
    con la profundidad (manga campana, falda acampanada)."""
    span = max(1e-6, bottom_y - top_y)
    out = []
    for x, y in points:
        t = max(0.0, min(1.0, (y - top_y) / span))
        out.append((center_x + (x - center_x) * (1 + t * ratio), y))
    return out


def dedup(contour, tol=1e-6):
    """Elimina vértices consecutivos duplicados (incluido el cierre)."""
    out = []
    for pt in contour:
        pt = (float(pt[0]), float(pt[1]))
        if not out or math.hypot(pt[0] - out[-1][0], pt[1] - out[-1][1]) > tol:
            out.append(pt)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= tol:
        out.pop()
    return out


def clip_below(contour, cut_y):
    """Recorta el polígono al semiplano ``y <= cut_y`` (acortar el largo)."""
    from shapely.geometry import Polygon, box
    poly = Polygon(contour)
    if not poly.is_valid:
        poly = poly.buffer(0)
    minx, miny, maxx, maxy = poly.bounds
    r = poly.intersection(box(minx - 10, miny - 10, maxx + 10, cut_y))
    if r.geom_type == "MultiPolygon":
        r = max(r.geoms, key=lambda g: g.area)
    return dedup([(float(x), float(y)) for x, y in r.exterior.coords])


def _dist_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 < 1e-12:
        return math.hypot(px - ax, py - ay), 0.0
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    cx, cy = ax + t * vx, ay + t * vy
    return math.hypot(px - cx, py - cy), t


def insert_on_contour(contour, pt):
    """Inserta ``pt`` en el segmento de contorno más cercano y devuelve
    (nuevo_contorno, índice_de_pt)."""
    best_i, best_d = 0, float("inf")
    n = len(contour)
    for i in range(n):
        d, _ = _dist_seg(pt, contour[i], contour[(i + 1) % n])
        if d < best_d:
            best_d, best_i = d, i
    new = list(contour[:best_i + 1]) + [tuple(pt)] + list(contour[best_i + 1:])
    return new, best_i + 1


def split_panel(contour, top_pt, bottom_pt, waist_x, n=18):
    """Divide un panel en dos por una curva princesa entre ``top_pt`` (sisa) y
    ``bottom_pt`` (dobladillo), con bombeo hacia ``waist_x``. Devuelve dos
    contornos cerrados (panel centro y panel costado)."""
    from ..core.curves import smooth_curve
    c, _ = insert_on_contour(list(contour), top_pt)
    c, _ = insert_on_contour(c, bottom_pt)
    ia = min(range(len(c)), key=lambda i: math.hypot(c[i][0] - top_pt[0], c[i][1] - top_pt[1]))
    ib = min(range(len(c)), key=lambda i: math.hypot(c[i][0] - bottom_pt[0], c[i][1] - bottom_pt[1]))
    a, b = sorted((ia, ib))
    pa, pb = c[a], c[b]
    seam = smooth_curve([pa, (waist_x, (pa[1] + pb[1]) / 2.0), pb], samples_per_span=n)
    arc1 = c[a:b + 1]
    arc2 = c[b:] + c[:a + 1]
    piece1 = arc1 + list(reversed(seam))[1:-1]
    piece2 = arc2 + list(seam)[1:-1]
    return dedup(piece1), dedup(piece2)


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
