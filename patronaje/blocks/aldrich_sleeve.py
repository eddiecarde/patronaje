"""Bloque de manga — método Aldrich (manga de camisa de una pieza).

La manga se traza simétrica respecto de su línea central (línea de hilo). El
requisito industrial clave es:

    "longitud de copa = longitud de sisa ± tolerancia"

En la manga de camisa la **altura de copa** se fija por una regla proporcional
de Aldrich (fracción de la profundidad de sisa) y el **ancho de bíceps** se
*resuelve por bisección* para que la longitud de la copa iguale la longitud de
sisa del cuerpo más una pequeña holgura de montaje (``sleeve_ease``). Esto
produce una copa con el "scoop" de axila correcto y a la vez garantiza que el
ancho de manga cubra el contorno de brazo con holgura. Si el bíceps resultante
no cubre ``contorno_brazo + holgura mínima``, se baja la altura de copa hasta
lograrlo. Al cambiar cualquier medida, la manga se regenera y sigue casando.

Marco local: ``x`` = ancho de manga (centro en 0), ``y`` hacia abajo (largo).
La copa delantera (lado +x) es ligeramente más plana que la trasera (lado −x),
como en el método Aldrich.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..core.point import Point, polyline_length
from ..core.curves import smooth_curve
from ..parametric.parameters import Parameters


@dataclass
class SleeveDraft:
    p: Parameters
    target_armhole: float
    sleeve_ease: float = 1.0
    cap_ratio: float = 0.45          # altura de copa = cap_ratio * prof_sisa
    min_arm_ease: float = 2.0        # holgura mínima de bíceps sobre contorno_brazo
    points: dict[str, Point] = field(default_factory=dict)

    cap_curve: list = field(default_factory=list)   # copa completa BL->SH->BR (net)
    cap_height: float = 0.0
    biceps_half: float = 0.0

    # ------------------------------------------------------------------
    def _cap_for(self, h: float, bh: float) -> list[tuple[float, float]]:
        """Construye la curva de copa (net) para altura ``h`` y bíceps medio ``bh``."""
        sh = (0.0, 0.0)                                   # sleeve head (centro alto)
        br = (bh, h)                                      # biceps derecho (delantero)
        bl = (-bh, h)                                     # biceps izquierdo (trasero)
        # lado delantero (derecho): scoop cóncavo cerca de axila, convexo arriba
        front = smooth_curve([
            sh,
            (bh * 0.30, h * 0.10),
            (bh * 0.62, h * 0.42),
            (bh * 0.90, h * 0.82),
            br,
        ], samples_per_span=8)
        # lado trasero (izquierdo): un poco más lleno
        back = smooth_curve([
            sh,
            (-bh * 0.32, h * 0.08),
            (-bh * 0.66, h * 0.40),
            (-bh * 0.92, h * 0.80),
            bl,
        ], samples_per_span=8)
        # copa completa de BL -> SH -> BR
        return list(reversed(back)) + front[1:]

    def _solve_biceps(self, h: float) -> float:
        """Bisección: ancho de bíceps que hace longitud de copa = objetivo."""
        target = self.target_armhole + self.sleeve_ease
        lo, hi = 3.0, self.p.contorno_brazo  # límites de medio bíceps
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if polyline_length(self._cap_for(h, mid)) > target:
                hi = mid   # copa demasiado larga -> estrechar bíceps
            else:
                lo = mid
        return (lo + hi) / 2.0

    def build(self) -> "SleeveDraft":
        p = self.p
        min_half = (p.contorno_brazo + self.min_arm_ease) / 2.0
        # altura de copa por regla proporcional; se baja si el bíceps no cubre el brazo
        h = p.prof_sisa * self.cap_ratio
        for _ in range(40):
            bh = self._solve_biceps(h)
            if bh >= min_half or h <= 3.0:
                break
            h *= 0.92  # copa más plana -> bíceps más ancho
        self.cap_height = h
        self.biceps_half = bh
        self.cap_curve = self._cap_for(h, bh)

        # landmarks
        bh = self.biceps_half
        h = self.cap_height
        self.points["M-SH"] = Point("M-SH", 0.0, 0.0, "cabeza de manga (centro)",
                                    ["línea de hilo"])
        self.points["M-BR"] = Point("M-BR", bh, h, "bíceps delantero",
                                    ["contorno_brazo", "holgura_brazo"])
        self.points["M-BL"] = Point("M-BL", -bh, h, "bíceps trasero",
                                    ["contorno_brazo", "holgura_brazo"])
        # muñeca: boca de manga (antes de pliegues) centrada
        boca_half = p.boca_manga / 2.0
        largo = p.largo_manga_efec
        self.points["M-WR"] = Point("M-WR", boca_half, largo, "boca de manga derecha",
                                    ["boca_manga", "largo_manga"])
        self.points["M-WL"] = Point("M-WL", -boca_half, largo, "boca de manga izquierda",
                                    ["boca_manga", "largo_manga"])
        return self

    # ------------------------------------------------------------------
    def cap_length(self) -> float:
        return polyline_length(self.cap_curve)

    def underseam_length(self) -> float:
        """Largo de la costura del bajo de manga (de bíceps a muñeca)."""
        return self.points["M-BR"].distance_to(self.points["M-WR"])

    def outline(self) -> list[tuple[float, float]]:
        """Contorno NET de la manga: copa + bajos + boca de manga."""
        outline: list[tuple[float, float]] = []
        outline += self.cap_curve                         # BL ... SH ... BR
        outline += [self.points["M-WR"].as_tuple()]        # bajo derecho a muñeca
        outline += [self.points["M-WL"].as_tuple()]        # boca de manga
        # cierra al bíceps izquierdo (BL) automáticamente
        return outline


def build_sleeve(p: Parameters, target_armhole: float, sleeve_ease: float = 1.0) -> SleeveDraft:
    return SleeveDraft(p=p, target_armhole=target_armhole, sleeve_ease=sleeve_ease).build()
