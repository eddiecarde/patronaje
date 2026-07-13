"""Motor de curvas: Bézier cúbicas, splines naturales cúbicas y continuidad G2.

El prompt exige curvas *reales* (no aproximaciones a mano):

    "No aproximar curvas. Calcular mediante: Splines, Bézier, Arcos tangentes,
     Continuidad G2. Las curvas deben ser aptas para corte CNC."

Estrategia:

* Escotes, sisas y copa de manga se modelan como **splines cúbicas naturales**
  que *interpolan* los puntos de control del trazo Aldrich. Una spline natural
  cúbica es C2 (segunda derivada continua) en los nudos interiores, lo que
  implica **continuidad G2** (curvatura continua) — condición pedida para un
  contorno apto a fresado/corte CNC sin marcas.
* Cada tramo de la spline es equivalente a una Bézier cúbica; exponemos
  :class:`CubicBezier` para construcciones locales y para verificar G0/G1/G2
  entre tramos.
* El muestreo a polilínea usa densidad configurable (por defecto fina) y una
  utilidad de *chord tolerance* para garantizar error de cuerda acotado, que es
  lo que un post-procesador CNC necesita.

Convención: trabajamos con puntos ``(x, y)`` (o :class:`Point`, que es iterable
a ``(x, y)``). numpy hace el álgebra del sistema tridiagonal de la spline.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


def _xy(p) -> tuple[float, float]:
    if hasattr(p, "x") and hasattr(p, "y"):
        return (float(p.x), float(p.y))
    return (float(p[0]), float(p[1]))


# ==========================================================================
# Bézier cúbica
# ==========================================================================
@dataclass
class CubicBezier:
    """Bézier cúbica definida por 4 puntos de control P0..P3."""

    p0: tuple[float, float]
    p1: tuple[float, float]
    p2: tuple[float, float]
    p3: tuple[float, float]

    def __post_init__(self):
        self.p0 = _xy(self.p0); self.p1 = _xy(self.p1)
        self.p2 = _xy(self.p2); self.p3 = _xy(self.p3)

    def point(self, t: float) -> tuple[float, float]:
        mt = 1.0 - t
        a = mt * mt * mt
        b = 3 * mt * mt * t
        c = 3 * mt * t * t
        d = t * t * t
        return (
            a * self.p0[0] + b * self.p1[0] + c * self.p2[0] + d * self.p3[0],
            a * self.p0[1] + b * self.p1[1] + c * self.p2[1] + d * self.p3[1],
        )

    def derivative(self, t: float) -> tuple[float, float]:
        mt = 1.0 - t
        a = 3 * mt * mt
        b = 6 * mt * t
        c = 3 * t * t
        return (
            a * (self.p1[0] - self.p0[0]) + b * (self.p2[0] - self.p1[0]) + c * (self.p3[0] - self.p2[0]),
            a * (self.p1[1] - self.p0[1]) + b * (self.p2[1] - self.p1[1]) + c * (self.p3[1] - self.p2[1]),
        )

    def second_derivative(self, t: float) -> tuple[float, float]:
        mt = 1.0 - t
        return (
            6 * mt * (self.p2[0] - 2 * self.p1[0] + self.p0[0]) + 6 * t * (self.p3[0] - 2 * self.p2[0] + self.p1[0]),
            6 * mt * (self.p2[1] - 2 * self.p1[1] + self.p0[1]) + 6 * t * (self.p3[1] - 2 * self.p2[1] + self.p1[1]),
        )

    def curvature(self, t: float) -> float:
        dx, dy = self.derivative(t)
        ddx, ddy = self.second_derivative(t)
        denom = (dx * dx + dy * dy) ** 1.5
        if denom < 1e-12:
            return 0.0
        return (dx * ddy - dy * ddx) / denom

    def sample(self, n: int = 24) -> list[tuple[float, float]]:
        return [self.point(i / n) for i in range(n + 1)]

    def length(self, n: int = 64) -> float:
        pts = self.sample(n)
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


# ==========================================================================
# Spline cúbica natural (interpolante, C2 ⇒ G2)
# ==========================================================================
class NaturalCubicSpline:
    """Spline cúbica natural que interpola una secuencia de puntos.

    Se parametriza por longitud de cuerda acumulada (chordal), lo que da curvas
    visualmente equilibradas para escotes y sisas. La condición "natural"
    (segunda derivada nula en los extremos) más la continuidad C2 interna
    garantizan curvatura continua (G2) en todos los nudos interiores.
    """

    def __init__(self, points: Sequence):
        pts = [_xy(p) for p in points]
        if len(pts) < 2:
            raise ValueError("Se requieren al menos 2 puntos para una spline")
        self.pts = pts
        xs = np.array([p[0] for p in pts], dtype=float)
        ys = np.array([p[1] for p in pts], dtype=float)
        # parámetro chordal
        seg = np.hypot(np.diff(xs), np.diff(ys))
        t = np.concatenate([[0.0], np.cumsum(seg)])
        self.t = t
        self.total_length_param = float(t[-1])
        self._cx = self._solve(t, xs)
        self._cy = self._solve(t, ys)

    @staticmethod
    def _solve(t: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Resuelve las segundas derivadas (M) de la spline natural.

        Sistema tridiagonal clásico con M[0]=M[-1]=0 (extremos naturales).
        Devuelve M en cada nudo.
        """
        n = len(t)
        M = np.zeros(n)
        if n < 3:
            return M
        h = np.diff(t)
        # sistema para nudos interiores 1..n-2
        lower = np.zeros(n)
        diag = np.ones(n)
        upper = np.zeros(n)
        rhs = np.zeros(n)
        for i in range(1, n - 1):
            lower[i] = h[i - 1]
            diag[i] = 2 * (h[i - 1] + h[i])
            upper[i] = h[i]
            rhs[i] = 6 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
        # Thomas
        for i in range(1, n):
            w = lower[i] / diag[i - 1]
            diag[i] -= w * upper[i - 1]
            rhs[i] -= w * rhs[i - 1]
        M[-1] = 0.0
        for i in range(n - 2, -1, -1):
            M[i] = (rhs[i] - upper[i] * M[i + 1]) / diag[i]
        M[0] = 0.0
        M[-1] = 0.0
        return M

    def _eval_axis(self, tv: float, y: np.ndarray, M: np.ndarray) -> float:
        t = self.t
        # localizar intervalo
        i = int(np.clip(np.searchsorted(t, tv) - 1, 0, len(t) - 2))
        h = t[i + 1] - t[i]
        if h <= 0:
            return float(y[i])
        A = (t[i + 1] - tv) / h
        B = (tv - t[i]) / h
        return float(
            A * y[i] + B * y[i + 1]
            + ((A ** 3 - A) * M[i] + (B ** 3 - B) * M[i + 1]) * (h * h) / 6.0
        )

    def point(self, tv: float) -> tuple[float, float]:
        xs = np.array([p[0] for p in self.pts])
        ys = np.array([p[1] for p in self.pts])
        return (self._eval_axis(tv, xs, self._cx), self._eval_axis(tv, ys, self._cy))

    def sample(self, n: int = 60) -> list[tuple[float, float]]:
        """Muestrea ``n+1`` puntos equiespaciados en el parámetro chordal."""
        if self.total_length_param <= 0:
            return list(self.pts)
        return [self.point(self.total_length_param * i / n) for i in range(n + 1)]

    def length(self, n: int = 200) -> float:
        pts = self.sample(n)
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def smooth_curve(points: Sequence, samples_per_span: int = 12) -> list[tuple[float, float]]:
    """Curva suave (spline natural G2) que interpola ``points``.

    Devuelve la polilínea muestreada lista para exportar/validar. El número de
    muestras crece con el número de tramos para mantener densidad uniforme.
    """
    pts = [_xy(p) for p in points]
    if len(pts) <= 2:
        return pts
    spline = NaturalCubicSpline(pts)
    n = samples_per_span * (len(pts) - 1)
    return spline.sample(n)


# ==========================================================================
# Verificación de continuidad entre tramos
# ==========================================================================
def continuity_between(c1: CubicBezier, c2: CubicBezier, *, tol: float = 1e-6) -> str:
    """Clasifica la continuidad en la unión c1(t=1) → c2(t=0).

    Devuelve "G2", "G1", "G0" o "none". Útil para tests y para certificar que
    dos tramos de contorno empalman con curvatura continua.
    """
    p_end = c1.point(1.0)
    p_start = c2.point(0.0)
    if math.hypot(p_end[0] - p_start[0], p_end[1] - p_start[1]) > 1e-4:
        return "none"  # ni siquiera G0
    d1 = c1.derivative(1.0)
    d2 = c2.derivative(0.0)
    # tangentes paralelas y mismo sentido ⇒ G1
    crossv = d1[0] * d2[1] - d1[1] * d2[0]
    dotv = d1[0] * d2[0] + d1[1] * d2[1]
    if abs(crossv) > tol or dotv <= 0:
        return "G0"
    k1 = c1.curvature(1.0)
    k2 = c2.curvature(0.0)
    if abs(k1 - k2) <= 1e-3:
        return "G2"
    return "G1"


def chord_error(spline: NaturalCubicSpline, polyline: Sequence) -> float:
    """Máxima desviación de cuerda (cm) entre la spline y su muestreo.

    Aproxima el error midiendo, para densidad doble, la distancia de los puntos
    intermedios a los segmentos de ``polyline``. Sirve para reportar aptitud CNC.
    """
    poly = [_xy(p) for p in polyline]
    dense = spline.sample(len(poly) * 4)
    max_err = 0.0
    j = 0
    for px, py in dense:
        # busca el segmento más cercano (barrido local)
        best = float("inf")
        for k in range(max(0, j - 2), min(len(poly) - 1, j + 3)):
            ax, ay = poly[k]
            bx, by = poly[k + 1]
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy
            if L2 < 1e-12:
                d = math.hypot(px - ax, py - ay)
            else:
                t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
                cx, cy = ax + t * vx, ay + t * vy
                d = math.hypot(px - cx, py - cy)
            if d < best:
                best = d
                j = k
        max_err = max(max_err, best)
    return max_err
