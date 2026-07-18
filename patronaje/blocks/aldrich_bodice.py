"""Bloque de cuerpo (delantero + espalda) — método Aldrich.

Construcción paramétrica del bloque de camisa a partir de :class:`Parameters`.
Se traza en un **marco local** donde ``x`` crece hacia el costado y ``y`` crece
hacia abajo (dirección del largo de la prenda); esta convención es la habitual
en patronaje y se documenta en ``docs/metodo_aldrich.md``. La exportación CAD
reorienta a Y-arriba.

Cada landmark es un :class:`Point` con ID, descripción y relaciones. Las curvas
de **escote** y **sisa** se generan con splines naturales G2
(:func:`patronaje.core.curves.smooth_curve`). El bloque además:

* separa la espalda en **canesú** (yoke) + espalda inferior por la línea de
  canesú,
* mide longitudes de escote y sisa (para casar cuello y copa de manga).

Todos los contornos que devuelve son la **línea de costura (net)**; el margen de
costura lo añade la capa de piezas por *offset*.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..core.point import Point, polyline_length
from ..core.curves import smooth_curve
from ..parametric.parameters import Parameters


def _x_at_y(poly: list[tuple[float, float]], y: float) -> float:
    """Interpola la x del punto de la polilínea a la altura ``y`` dada."""
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        lo, hi = min(y0, y1), max(y0, y1)
        if lo - 1e-9 <= y <= hi + 1e-9 and abs(y1 - y0) > 1e-12:
            t = (y - y0) / (y1 - y0)
            return x0 + t * (x1 - x0)
    # fuera de rango: devuelve el extremo más cercano
    return poly[0][0] if abs(poly[0][1] - y) < abs(poly[-1][1] - y) else poly[-1][0]


@dataclass
class BodiceDraft:
    """Resultado del trazo del bloque de cuerpo."""

    p: Parameters
    points: dict[str, Point] = field(default_factory=dict)

    # --- curvas muestreadas (net) ---
    back_neck: list = field(default_factory=list)
    front_neck: list = field(default_factory=list)
    back_armhole: list = field(default_factory=list)
    front_armhole: list = field(default_factory=list)

    # --- landmarks útiles ---
    yoke_line_y: float = 0.0

    # ------------------------------------------------------------------
    def _pt(self, id, x, y, desc, rel=None):
        pt = Point(id=id, x=x, y=y, descripcion=desc, relaciones=rel or [])
        self.points[id] = pt
        return pt

    # ------------------------------------------------------------------
    def build(self) -> "BodiceDraft":
        p = self.p
        bnw = p.escote_esp_ancho
        fnw = p.escote_del_ancho
        fnd = p.escote_del_prof
        sub = p.subida_escote_esp
        scye = p.prof_sisa
        med_esp = p.medio_espalda
        cuarto = p.cuarto_busto
        largo = p.largo_camisa

        # ================= ESPALDA (fold en CB, x=0) =================
        cb_neck = self._pt("E-CBn", 0.0, sub, "escote espalda en centro (nuca)",
                           ["CB", "subida_escote_esp"])
        snp_b = self._pt("E-SNP", bnw, 0.0, "punto de cuello lateral (espalda)",
                         ["escote_esp_ancho"])
        drop_b = p.caida_hombro_esp
        dx_b = math.sqrt(max(0.0, p.hombro ** 2 - drop_b ** 2))
        sp_b = self._pt("E-SP", bnw + dx_b, drop_b, "punto de hombro (espalda)",
                        ["hombro", "caida_hombro_esp"])
        back_line_y = scye * 0.55
        ab = self._pt("E-AB", med_esp, back_line_y, "punto de ancho de espalda (sisa)",
                      ["medio_espalda", "prof_sisa"])
        us_b = self._pt("E-US", cuarto, scye, "punto de costado/axila (espalda)",
                        ["cuarto_busto", "prof_sisa"])
        self._pt("E-Hs", cuarto, largo, "dobladillo costado (espalda)",
                         ["cuarto_busto", "largo_camisa"])
        self._pt("E-Hc", 0.0, largo, "dobladillo centro espalda",
                          ["largo_camisa"])

        # curva de escote espalda (suave, sube de CB a SNP)
        self.back_neck = smooth_curve([
            cb_neck, (bnw * 0.45, sub * 0.9), (bnw * 0.8, sub * 0.45), snp_b
        ], samples_per_span=10)
        # curva de sisa espalda (SP -> ancho espalda -> axila), G2
        mid_b = (med_esp + (cuarto - med_esp) * 0.55, back_line_y + (scye - back_line_y) * 0.62)
        self.back_armhole = smooth_curve([sp_b, ab, mid_b, us_b], samples_per_span=12)

        # ================= DELANTERO (CF en x=0) =================
        snp_f = self._pt("D-SNP", fnw, 0.0, "punto de cuello lateral (delantero)",
                         ["escote_del_ancho"])
        cf_neck = self._pt("D-CFn", 0.0, fnd, "escote delantero en centro (CF)",
                           ["escote_del_prof"])
        drop_f = p.caida_hombro_del
        dx_f = math.sqrt(max(0.0, p.hombro ** 2 - drop_f ** 2))
        sp_f = self._pt("D-SP", fnw + dx_f, drop_f, "punto de hombro (delantero)",
                        ["hombro", "caida_hombro_del"])
        front_line_y = scye * 0.60
        fc = self._pt("D-FC", med_esp - 1.5, front_line_y, "punto de ancho de pecho (sisa)",
                      ["medio_espalda", "prof_sisa"])
        us_f = self._pt("D-US", cuarto, scye, "punto de costado/axila (delantero)",
                        ["cuarto_busto", "prof_sisa"])
        self._pt("D-Hs", cuarto, largo, "dobladillo costado (delantero)",
                         ["cuarto_busto", "largo_camisa"])
        self._pt("D-Hc", 0.0, largo, "dobladillo centro delantero",
                          ["largo_camisa"])

        # curva de escote delantero (scoop profundo), G2
        self.front_neck = smooth_curve([
            snp_f, (fnw * 0.62, fnd * 0.40), (fnw * 0.28, fnd * 0.80), cf_neck
        ], samples_per_span=12)
        # curva de sisa delantera (SP -> ancho pecho -> axila), G2
        mid_f = (fc.x + (cuarto - fc.x) * 0.55, front_line_y + (scye - front_line_y) * 0.60)
        self.front_armhole = smooth_curve([sp_f, fc, mid_f, us_f], samples_per_span=12)

        self.yoke_line_y = p.linea_canesu
        return self

    # ------------------------------------------------------------------
    # Longitudes para casado de piezas
    # ------------------------------------------------------------------
    def back_neck_length(self) -> float:
        return polyline_length(self.back_neck)

    def front_neck_length(self) -> float:
        return polyline_length(self.front_neck)

    def neckline_length(self) -> float:
        """Longitud total del escote (medio cuerpo): espalda + delantero."""
        return self.back_neck_length() + self.front_neck_length()

    def back_armhole_length(self) -> float:
        return polyline_length(self.back_armhole)

    def front_armhole_length(self) -> float:
        return polyline_length(self.front_armhole)

    def armhole_length(self) -> float:
        return self.back_armhole_length() + self.front_armhole_length()

    # ------------------------------------------------------------------
    # Contornos NET (línea de costura) para las piezas
    # ------------------------------------------------------------------
    def yoke_outline(self) -> list[tuple[float, float]]:
        """Canesú (mitad, al doblez en CB). Va del CB por el escote a SNP,
        hombro a SP, baja la sisa hasta la línea de canesú, cruza a CB y sube."""
        yl = self.yoke_line_y
        arm_x = _x_at_y(self.back_armhole, yl)
        # tramo de sisa desde SP hasta la línea de canesú
        arm_seg = [pt for pt in self.back_armhole if pt[1] <= yl]
        outline: list[tuple[float, float]] = []
        outline += [self.points["E-CBn"].as_tuple()]
        outline += self.back_neck[1:]                    # escote a SNP
        outline += [self.points["E-SP"].as_tuple()]      # hombro
        outline += arm_seg                                # sisa hasta ~yoke
        outline += [(arm_x, yl)]                          # punto en línea canesú
        outline += [(0.0, yl)]                            # cruza a CB
        return _dedup(outline)

    def back_lower_outline(self) -> list[tuple[float, float]]:
        """Espalda inferior (mitad, al doblez en CB), desde la línea de canesú
        hasta el dobladillo. El pliegue de canesú se añade en la pieza."""
        yl = self.yoke_line_y
        arm_x = _x_at_y(self.back_armhole, yl)
        arm_seg = [pt for pt in self.back_armhole if pt[1] >= yl]
        outline: list[tuple[float, float]] = []
        outline += [(0.0, yl)]                            # CB en línea canesú
        outline += [(arm_x, yl)]                          # a la sisa
        outline += arm_seg                                # sisa hasta axila
        outline += [self.points["E-Hs"].as_tuple()]       # costado a dobladillo
        outline += [self.points["E-Hc"].as_tuple()]       # dobladillo a CB
        return _dedup(outline)

    def front_outline(self) -> list[tuple[float, float]]:
        """Delantero (mitad; la extensión de botonadura la añade la pieza)."""
        outline: list[tuple[float, float]] = []
        outline += [self.points["D-CFn"].as_tuple()]
        outline += list(reversed(self.front_neck))[1:]    # de CF a SNP
        outline += [self.points["D-SP"].as_tuple()]       # hombro
        outline += self.front_armhole[1:]                 # sisa a axila
        outline += [self.points["D-Hs"].as_tuple()]       # costado a dobladillo
        outline += [self.points["D-Hc"].as_tuple()]       # dobladillo a CF
        return _dedup(outline)


def _dedup(poly: list[tuple[float, float]], tol: float = 1e-6) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for pt in poly:
        if not out or math.hypot(pt[0] - out[-1][0], pt[1] - out[-1][1]) > tol:
            out.append((float(pt[0]), float(pt[1])))
    return out


def build_bodice(p: Parameters) -> BodiceDraft:
    return BodiceDraft(p=p).build()
