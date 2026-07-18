"""Motor geométrico 2D.

Funciones puras de geometría analítica usadas por los trazos Aldrich y por los
exportadores: operaciones vectoriales, intersección de rectas, punto sobre
recta a distancia/ángulo, *offset* perpendicular (para líneas de costura) y
**arcos tangentes** que unen dos segmentos con continuidad de tangente (G1),
usados en las esquinas suavizadas del patrón.

Todo trabaja con tuplas ``(x, y)`` en centímetros para poder combinarse
libremente con :class:`patronaje.core.point.Point` (que también es iterable a
``(x, y)``).
"""
from __future__ import annotations

import math
from typing import Sequence

Vec = tuple[float, float]


def _xy(p) -> Vec:
    """Normaliza Point | tuple a (x, y)."""
    if hasattr(p, "x") and hasattr(p, "y"):
        return (p.x, p.y)
    return (p[0], p[1])


# --------------------------------------------------------------------------
# Álgebra vectorial
# --------------------------------------------------------------------------
def add(a, b) -> Vec:
    ax, ay = _xy(a); bx, by = _xy(b)
    return (ax + bx, ay + by)


def sub(a, b) -> Vec:
    ax, ay = _xy(a); bx, by = _xy(b)
    return (ax - bx, ay - by)


def scale(a, k: float) -> Vec:
    ax, ay = _xy(a)
    return (ax * k, ay * k)


def dot(a, b) -> float:
    ax, ay = _xy(a); bx, by = _xy(b)
    return ax * bx + ay * by


def cross(a, b) -> float:
    ax, ay = _xy(a); bx, by = _xy(b)
    return ax * by - ay * bx


def norm(a) -> float:
    ax, ay = _xy(a)
    return math.hypot(ax, ay)


def unit(a) -> Vec:
    n = norm(a)
    if n < 1e-12:
        return (0.0, 0.0)
    ax, ay = _xy(a)
    return (ax / n, ay / n)


def distance(a, b) -> float:
    return norm(sub(a, b))


def perpendicular(a, *, ccw: bool = True) -> Vec:
    """Vector perpendicular unitario. ``ccw`` = giro antihorario (+90°)."""
    ux, uy = unit(a)
    return (-uy, ux) if ccw else (uy, -ux)


def angle_of(a) -> float:
    ax, ay = _xy(a)
    return math.atan2(ay, ax)


# --------------------------------------------------------------------------
# Construcciones de patronaje
# --------------------------------------------------------------------------
def point_at_distance(origin, direction, dist: float) -> Vec:
    """Punto a ``dist`` cm desde ``origin`` en la dirección ``direction``."""
    ux, uy = unit(direction)
    ox, oy = _xy(origin)
    return (ox + ux * dist, oy + uy * dist)


def point_at_angle(origin, angle_rad: float, dist: float) -> Vec:
    ox, oy = _xy(origin)
    return (ox + math.cos(angle_rad) * dist, oy + math.sin(angle_rad) * dist)


def line_intersection(p1, p2, p3, p4) -> Vec | None:
    """Intersección de la recta (p1,p2) con la recta (p3,p4).

    Devuelve ``None`` si son paralelas. No se limita al segmento: es
    intersección de rectas infinitas (útil para hallar vértices de esquina).
    """
    x1, y1 = _xy(p1); x2, y2 = _xy(p2)
    x3, y3 = _xy(p3); x4, y4 = _xy(p4)
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def offset_polyline(points: Sequence, dist: float, *, ccw: bool = True) -> list[Vec]:
    """Desplaza una polilínea abierta ``dist`` cm hacia un lado.

    Se usa para derivar la **línea de costura** desde la línea de corte (o
    viceversa) manteniendo esquinas mediante intersección de segmentos
    desplazados. Un ``dist`` positivo con ``ccw=True`` desplaza a la izquierda
    del sentido de avance.
    """
    pts = [_xy(p) for p in points]
    if len(pts) < 2:
        return list(pts)

    # Segmentos desplazados
    shifted: list[tuple[Vec, Vec]] = []
    for a, b in zip(pts, pts[1:]):
        d = sub(b, a)
        n = perpendicular(d, ccw=ccw)
        off = scale(n, dist)
        shifted.append((add(a, off), add(b, off)))

    result: list[Vec] = [shifted[0][0]]
    for (a0, a1), (b0, b1) in zip(shifted, shifted[1:]):
        inter = line_intersection(a0, a1, b0, b1)
        result.append(inter if inter is not None else a1)
    result.append(shifted[-1][1])
    return result


def tangent_arc(p_prev, corner, p_next, radius: float, *, segments: int = 16):
    """Arco de radio ``radius`` tangente a los dos segmentos que forman una
    esquina en ``corner`` (fillet). Devuelve la lista de puntos muestreados del
    arco, con continuidad de tangente (G1) respecto de ambos segmentos.

    Si el radio no cabe en el ángulo, devuelve ``[corner]`` (sin redondeo).
    """
    c = _xy(corner)
    v1 = unit(sub(p_prev, corner))
    v2 = unit(sub(p_next, corner))
    # ángulo interior de la esquina
    cosang = max(-1.0, min(1.0, dot(v1, v2)))
    ang = math.acos(cosang)
    if ang < 1e-6 or math.pi - ang < 1e-6:
        return [c]
    # distancia desde la esquina a los puntos de tangencia
    tan_dist = radius / math.tan(ang / 2.0)
    t1 = add(c, scale(v1, tan_dist))
    t2 = add(c, scale(v2, tan_dist))
    # centro del arco: sobre la bisectriz
    bis = unit(add(v1, v2))
    center_dist = radius / math.sin(ang / 2.0)
    center = add(c, scale(bis, center_dist))
    a1 = math.atan2(t1[1] - center[1], t1[0] - center[0])
    a2 = math.atan2(t2[1] - center[1], t2[0] - center[0])
    # normaliza para recorrer el arco menor
    da = a2 - a1
    while da <= -math.pi:
        da += 2 * math.pi
    while da > math.pi:
        da -= 2 * math.pi
    return [
        (center[0] + radius * math.cos(a1 + da * i / segments),
         center[1] + radius * math.sin(a1 + da * i / segments))
        for i in range(segments + 1)
    ]


def offset_polygon_variable(contour: Sequence, dists: Sequence[float]) -> list[Vec]:
    """Desplaza hacia AFUERA cada segmento de un polígono cerrado por su propia
    distancia ``dists[i]`` y reconecta las esquinas por intersección.

    Permite márgenes de costura distintos por borde (dobladillo mayor, doblez
    con margen 0, costuras estándar). ``contour`` no debe repetir el primer
    punto al final. Devuelve el contorno de corte (mismo número de vértices).
    """
    pts = [_xy(p) for p in contour]
    if len(pts) < 3:
        return list(pts)
    n = len(pts)
    outward_sign = -1.0 if polygon_area(pts) > 0 else 1.0  # normal hacia afuera
    lines = []
    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        d = sub(b, a)
        nrm = perpendicular(d, ccw=(outward_sign > 0))
        off = scale(unit(nrm), dists[i])
        lines.append((add(a, off), add(b, off)))
    out = []
    for i in range(n):
        p0, p1 = lines[(i - 1) % n]
        q0, q1 = lines[i]
        inter = line_intersection(p0, p1, q0, q1)
        out.append(inter if inter is not None else q0)
    return out


def polygon_area(points: Sequence) -> float:
    """Área con signo (shoelace). Positiva si el contorno es antihorario."""
    pts = [_xy(p) for p in points]
    if len(pts) < 3:
        return 0.0
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def bbox(points: Sequence) -> tuple[float, float, float, float]:
    """(xmin, ymin, xmax, ymax) de una colección de puntos."""
    xs = [_xy(p)[0] for p in points]
    ys = [_xy(p)[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))
