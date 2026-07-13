"""Constructor genérico de bloque de cuerpo a partir de un *frame* de valores.

Los métodos proporcionales/directos (Müller, Bunka, ESMOD) comparten exactamente
la misma **estructura** de bloque (mismos IDs de punto y curvas G2); solo cambian
los valores calculados por sus fórmulas. Este helper toma esos valores ya
calculados (`Frame`) y produce el :class:`BodiceDraft` genérico, evitando
duplicar la construcción en cada método.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..parametric.parameters import Parameters
from ..core.curves import smooth_curve
from .aldrich_bodice import BodiceDraft


@dataclass
class Frame:
    scye: float            # profundidad de sisa
    quarter: float         # costado (1/4 con holgura)
    back_width_pt: float   # x del punto de ancho de espalda (sisa)
    front_width_pt: float  # x del punto de ancho de pecho (sisa)
    bnw: float             # escote espalda: ancho
    fnw: float             # escote delantero: ancho
    fnd: float             # escote delantero: profundidad
    back_rise: float       # subida de escote espalda (CB)
    drop_b: float          # caída de hombro espalda
    drop_f: float          # caída de hombro delantero
    back_line_frac: float = 0.5
    front_line_frac: float = 0.55


def build_bodice_from_frame(p: Parameters, f: Frame, source_tag: str = "") -> BodiceDraft:
    d = BodiceDraft(p=p)
    largo = p.largo_camisa
    scye = f.scye
    back_line_y = scye * f.back_line_frac
    front_line_y = scye * f.front_line_frac
    tag = f"[{source_tag}]" if source_tag else ""

    # ================= ESPALDA (fold en CB, x=0) =================
    cb_neck = d._pt("E-CBn", 0.0, f.back_rise, "escote espalda en centro (nuca)", [tag])
    snp_b = d._pt("E-SNP", f.bnw, 0.0, "punto de cuello lateral (espalda)", [tag])
    dx_b = math.sqrt(max(0.0, p.hombro ** 2 - f.drop_b ** 2))
    sp_b = d._pt("E-SP", f.bnw + dx_b, f.drop_b, "punto de hombro (espalda)",
                 ["hombro", tag])
    ab = d._pt("E-AB", f.back_width_pt, back_line_y, "ancho de espalda (sisa)", [tag])
    us_b = d._pt("E-US", f.quarter, scye, "punto de costado/axila (espalda)", [tag])
    d._pt("E-Hs", f.quarter, largo, "dobladillo costado (espalda)", ["largo_camisa"])
    d._pt("E-Hc", 0.0, largo, "dobladillo centro espalda", ["largo_camisa"])

    d.back_neck = smooth_curve([
        cb_neck, (f.bnw * 0.45, f.back_rise * 0.9), (f.bnw * 0.8, f.back_rise * 0.45), snp_b
    ], samples_per_span=10)
    mid_b = (f.back_width_pt + (f.quarter - f.back_width_pt) * 0.55,
             back_line_y + (scye - back_line_y) * 0.62)
    d.back_armhole = smooth_curve([sp_b, ab, mid_b, us_b], samples_per_span=12)

    # ================= DELANTERO (CF en x=0) =================
    snp_f = d._pt("D-SNP", f.fnw, 0.0, "punto de cuello lateral (delantero)", [tag])
    cf_neck = d._pt("D-CFn", 0.0, f.fnd, "escote delantero en centro (CF)", [tag])
    dx_f = math.sqrt(max(0.0, p.hombro ** 2 - f.drop_f ** 2))
    sp_f = d._pt("D-SP", f.fnw + dx_f, f.drop_f, "punto de hombro (delantero)",
                 ["hombro", tag])
    fc = d._pt("D-FC", f.front_width_pt, front_line_y, "ancho de pecho (sisa)", [tag])
    us_f = d._pt("D-US", f.quarter, scye, "punto de costado/axila (delantero)", [tag])
    d._pt("D-Hs", f.quarter, largo, "dobladillo costado (delantero)", ["largo_camisa"])
    d._pt("D-Hc", 0.0, largo, "dobladillo centro delantero", ["largo_camisa"])

    d.front_neck = smooth_curve([
        snp_f, (f.fnw * 0.62, f.fnd * 0.40), (f.fnw * 0.28, f.fnd * 0.80), cf_neck
    ], samples_per_span=12)
    mid_f = (f.front_width_pt + (f.quarter - f.front_width_pt) * 0.55,
             front_line_y + (scye - front_line_y) * 0.60)
    d.front_armhole = smooth_curve([sp_f, fc, mid_f, us_f], samples_per_span=12)

    d.yoke_line_y = p.linea_canesu
    return d
