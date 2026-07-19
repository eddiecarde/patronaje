"""Bloque de pantalón base (mujer) — construcción paramétrica (Aldrich, best-effort).

Dos paneles (delantero y trasero) con **curva de tiro** (entrepierna), **pinza(s)
de cintura**, curva de cadera en el costado, entrepierna y costado hacia la boca
de pierna. El trasero tiene el gancho (fork) más profundo, más pinza y algo más
de ancho; su costura central va inclinada (equilibrio del asiento).

Marco local por panel: ``x = 0`` en la **línea central** (CF/CB), ``x`` hacia el
costado, ``y`` hacia abajo desde la cintura (``y = 0``). Los contornos son la
línea de costura (net); el margen lo añade la pieza.

Las constantes (fork 1/20–1/10 de cadera, reparto de supresión, etc.) siguen las
proporciones de Aldrich; se marca *best-effort* y se recomienda verificar la
horma en una prueba real, como el resto de métodos del sistema.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import math

from ..core.curves import smooth_curve
from ..core.point import polyline_length
from ..parametric.parameters import Parameters
from .fitted import _insert_dart


def _dedup(poly, tol=1e-6):
    out = []
    for pt in poly:
        pt = (float(pt[0]), float(pt[1]))
        if not out or math.hypot(pt[0] - out[-1][0], pt[1] - out[-1][1]) > tol:
            out.append(pt)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= tol:
        out.pop()
    return out


@dataclass
class TrouserDraft:
    p: Parameters
    front: list = field(default_factory=list)
    back: list = field(default_factory=list)
    front_darts: list = field(default_factory=list)
    back_darts: list = field(default_factory=list)
    front_inseam: list = field(default_factory=list)
    back_inseam: list = field(default_factory=list)
    hip_y: float = 0.0
    crotch_y: float = 0.0
    knee_y: float = 0.0
    hem_y: float = 0.0

    def _panel(self, back: bool):
        p = self.p
        hip_q = p.cuarto_cadera_pant
        waist_q = p.cuarto_cintura_pant
        rise = p.tiro
        hip_y = p.altura_cadera
        hem_y = p.largo_pantalon
        knee_y = rise + (hem_y - rise) * 0.47
        self.hip_y, self.crotch_y, self.knee_y, self.hem_y = hip_y, rise, knee_y, hem_y

        fork = hip_q * (0.45 if back else 0.20)          # gancho: trasero más profundo
        knee_half = (p.ancho_rodilla_pant / 4.0) * (1.05 if back else 0.92)
        hem_half = (p.boca_pantalon / 4.0) * (1.05 if back else 0.92)
        dart_in = p.pinza_pant_tra if back else p.pinza_pant_del
        dart_len = p.largo_pinza_pant_tra if back else p.largo_pinza_pant_del
        tilt = 2.0 if back else 0.0                      # inclinación de la costura central trasera

        supp = max(0.0, hip_q - waist_q)
        dart = min(dart_in, supp)
        side_supp = supp - dart
        side_waist_x = hip_q - side_supp

        leg_center = (hip_q - fork) / 2.0                # eje de la raya (crease)
        kn_in, kn_out = leg_center - knee_half, leg_center + knee_half
        hm_in, hm_out = leg_center - hem_half, leg_center + hem_half

        # costura central (CF/CB) + curva de tiro hasta el gancho
        cf = smooth_curve([(tilt, 0.0), (0.0, hip_y * 0.7), (0.0, hip_y),
                           (-fork * 0.45, rise - 2.5), (-fork, rise)], samples_per_span=8)
        # entrepierna: gancho -> rodilla interior -> boca interior
        inseam = smooth_curve([(-fork, rise), (kn_in, knee_y), (hm_in, hem_y)],
                              samples_per_span=8)
        hem = [(hm_in, hem_y), (hm_out, hem_y)]
        # costado: boca exterior -> rodilla -> cadera -> cintura costado
        outseam = smooth_curve([(hm_out, hem_y), (kn_out, knee_y),
                                (hip_q, hip_y), (side_waist_x, 0.0)], samples_per_span=8)
        # cintura (costado -> centro) con la pinza
        waist = [(side_waist_x, 0.0), (tilt, 0.0)]
        center_x = side_waist_x * (0.45 if not back else 0.42)
        apex = (center_x, dart_len)
        frac = (side_waist_x - center_x) / max(1e-6, side_waist_x - tilt)
        waist, dart_tuple = _insert_dart(waist, frac, dart, apex)

        contour = list(cf)
        contour += inseam[1:]
        contour += hem[1:]
        contour += outseam[1:]
        contour += waist[1:]
        return _dedup(contour), dart_tuple, inseam

    def build(self) -> "TrouserDraft":
        self.front, fd, self.front_inseam = self._panel(back=False)
        self.back, bd, self.back_inseam = self._panel(back=True)
        self.front_darts = [fd]
        self.back_darts = [bd]
        return self

    # ---- longitudes de casado ------------------------------------------
    def inseam_length(self, back: bool = False) -> float:
        return polyline_length(self.back_inseam if back else self.front_inseam)

    def waist_length(self) -> float:
        return 4.0 * self.p.cuarto_cintura_pant


def build_trouser_block(p: Parameters) -> TrouserDraft:
    return TrouserDraft(p=p).build()
