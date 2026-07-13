"""Bloque de cuerpo — método Müller & Sohn (sistema proporcional).

M. Müller & Sohn construye el bloque **proporcionalmente** desde el contorno de
busto (*Brustumfang*, B) más el talle de espalda (*Rückenlänge*): la mitad del
busto se reparte en tres secciones —espalda (*Rückenbreite*), sisa
(*Armlochbreite*) y pecho (*Brustbreite*)— y los escotes/hombros se derivan de
divisiones de B/20. Aquí se codifica ese sistema produciendo el mismo
:class:`BodiceDraft` que el resto del motor consume (mismos IDs de punto y
curvas), de modo que validación, exportadores, grading, marker y tech pack lo
aceptan sin cambios.

Convención de marco idéntica a Aldrich: x al costado, y hacia abajo. Las curvas
de escote y sisa son splines G2 (aptas para CNC).

Fórmulas núcleo (mujer):
    prof_sisa (Armlochtiefe)  = B/10 + 12.0            (+ holgura de bloque)
    Rückenbreite (esp.)       = B/8 + 5.5
    Brustbreite (pecho)       = B/8 + 6.5
    escote esp. ancho         = B/20 + 2.5
    escote del. ancho         = B/20 + 2.0
    escote del. profundidad   = B/20 + 3.5
    costado (1/4)             = (B + holgura)/4
Se usa `talle_espalda` para situar la línea de cintura de referencia.
"""
from __future__ import annotations

import math

from ..parametric.parameters import Parameters
from ..core.curves import smooth_curve
from .aldrich_bodice import BodiceDraft


def draft_mueller_bodice(p: Parameters) -> BodiceDraft:
    d = BodiceDraft(p=p)
    B = p.busto
    ease = p.holgura_busto
    scye = B / 10.0 + 12.0            # Armlochtiefe (prof. de sisa)
    quarter = (B + ease) / 4.0         # costado (1/4 con holgura)
    RB = B / 8.0 + 5.5                 # Rückenbreite (ancho de espalda)
    BB = B / 8.0 + 6.5                 # Brustbreite (ancho de pecho)
    bnw = B / 20.0 + 2.5               # escote espalda ancho
    fnw = B / 20.0 + 2.0               # escote delantero ancho
    fnd = B / 20.0 + 3.5               # escote delantero profundidad
    sub = 2.0                          # subida de escote espalda
    drop_b, drop_f = 4.5, 5.0          # caídas de hombro
    largo = p.largo_camisa

    # ================= ESPALDA (fold en CB, x=0) =================
    cb_neck = d._pt("E-CBn", 0.0, sub, "escote espalda en centro (nuca)",
                    ["Müller", "B/20"])
    snp_b = d._pt("E-SNP", bnw, 0.0, "punto de cuello lateral (espalda)",
                  ["escote_esp = B/20 + 2.5"])
    dx_b = math.sqrt(max(0.0, p.hombro ** 2 - drop_b ** 2))
    sp_b = d._pt("E-SP", bnw + dx_b, drop_b, "punto de hombro (espalda)",
                 ["hombro", "caída 4.5"])
    back_line_y = scye * 0.5
    ab = d._pt("E-AB", RB, back_line_y, "Rückenbreite (ancho de espalda)",
               ["RB = B/8 + 5.5"])
    us_b = d._pt("E-US", quarter, scye, "punto de costado/axila (espalda)",
                 ["quarter = (B+holgura)/4", "Armlochtiefe"])
    d._pt("E-Hs", quarter, largo, "dobladillo costado (espalda)", ["largo_camisa"])
    d._pt("E-Hc", 0.0, largo, "dobladillo centro espalda", ["largo_camisa"])

    d.back_neck = smooth_curve([
        cb_neck, (bnw * 0.45, sub * 0.9), (bnw * 0.8, sub * 0.45), snp_b
    ], samples_per_span=10)
    mid_b = (RB + (quarter - RB) * 0.55, back_line_y + (scye - back_line_y) * 0.62)
    d.back_armhole = smooth_curve([sp_b, ab, mid_b, us_b], samples_per_span=12)

    # ================= DELANTERO (CF en x=0) =================
    snp_f = d._pt("D-SNP", fnw, 0.0, "punto de cuello lateral (delantero)",
                  ["escote_del = B/20 + 2.0"])
    cf_neck = d._pt("D-CFn", 0.0, fnd, "escote delantero en centro (CF)",
                    ["escote_del_prof = B/20 + 3.5"])
    dx_f = math.sqrt(max(0.0, p.hombro ** 2 - drop_f ** 2))
    sp_f = d._pt("D-SP", fnw + dx_f, drop_f, "punto de hombro (delantero)",
                 ["hombro", "caída 5.0"])
    front_line_y = scye * 0.55
    fc = d._pt("D-FC", BB, front_line_y, "Brustbreite (ancho de pecho)",
               ["BB = B/8 + 6.5"])
    us_f = d._pt("D-US", quarter, scye, "punto de costado/axila (delantero)",
                 ["quarter", "Armlochtiefe"])
    d._pt("D-Hs", quarter, largo, "dobladillo costado (delantero)", ["largo_camisa"])
    d._pt("D-Hc", 0.0, largo, "dobladillo centro delantero", ["largo_camisa"])

    d.front_neck = smooth_curve([
        snp_f, (fnw * 0.62, fnd * 0.40), (fnw * 0.28, fnd * 0.80), cf_neck
    ], samples_per_span=12)
    mid_f = (BB + (quarter - BB) * 0.55, front_line_y + (scye - front_line_y) * 0.60)
    d.front_armhole = smooth_curve([sp_f, fc, mid_f, us_f], samples_per_span=12)

    d.yoke_line_y = p.linea_canesu
    return d
