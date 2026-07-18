"""Método Helen Joseph-Armstrong — sistema americano.

De *Patternmaking for Fashion Design* (H. J. Armstrong). Sistema americano que
combina medidas directas y divisiones del busto. Se adapta a la camisa (bloque
sin pinza) con su red de proporciones.
"""
from __future__ import annotations

from ..parametric.parameters import Parameters
from .base import DraftingMethod
from .aldrich_bodice import BodiceDraft
from .aldrich_sleeve import SleeveDraft
from ._bodice_common import Frame, build_bodice_from_frame


class ArmstrongMethod(DraftingMethod):
    name = "armstrong"
    label = "Joseph-Armstrong"
    source = "H. J. Armstrong, Patternmaking for Fashion Design, adaptado a camisa"
    available = True

    def required_measurements(self) -> set[str]:
        return {
            "busto", "cintura", "cadera", "largo_camisa", "largo_manga",
            "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo",
            "muneca",
        }

    def build_bodice(self, p: Parameters) -> BodiceDraft:
        B = p.busto
        enc = p.contorno_cuello
        frame = Frame(
            scye=B / 8.0 + 12.0,
            quarter=(B + p.holgura_busto) / 4.0,
            back_width_pt=B / 4.0 - 5.0,
            front_width_pt=B / 4.0 - 4.0,
            bnw=enc / 5.0 + 0.2,
            fnw=enc / 5.0 - 0.3,
            fnd=enc / 5.0 + 1.8,
            back_rise=2.2,
            drop_b=4.0,
            drop_f=5.5,
        )
        return build_bodice_from_frame(p, frame, source_tag="Armstrong")

    def dart_spec(self, p: Parameters):
        from .fitted import DartSpec
        return DartSpec(bust_dart=2.5, front_waist_dart=4.0, back_waist_dart=3.8, back_shoulder_dart=1.0, bust_point_x=p.busto/10+0.5, waist_ease=4.0)

    def build_sleeve(self, p: Parameters, target_armhole: float,
                     sleeve_ease: float = 1.0) -> SleeveDraft:
        return SleeveDraft(p=p, target_armhole=target_armhole,
                           sleeve_ease=sleeve_ease, cap_ratio=0.56).build()
