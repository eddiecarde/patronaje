"""Método ESMOD (francés) — basado en medidas directas.

A diferencia de los sistemas proporcionales, ESMOD trabaja con **medidas
directas** del cuerpo (*demi-mesure*): la carrura (ancho de espalda) y la
encolure (contorno de cuello) se usan tal cual, no por proporción del busto. El
bloque base ESMOD lleva pinza de busto; para la **camisa relajada** se omite la
pinza. Ver `docs/metodo_esmod.md`.
"""
from __future__ import annotations

from ..parametric.parameters import Parameters
from .base import DraftingMethod
from .aldrich_bodice import BodiceDraft
from .aldrich_sleeve import SleeveDraft
from ._bodice_common import Frame, build_bodice_from_frame

ESMOD_CAP_RATIO = 0.55


class EsmodMethod(DraftingMethod):
    name = "esmod"
    label = "ESMOD"
    source = "ESMOD, méthode française (adaptado a camisa)"
    available = True

    def required_measurements(self) -> set[str]:
        return {
            "busto", "cintura", "cadera", "largo_camisa", "largo_manga",
            "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo",
            "muneca",
        }

    def build_bodice(self, p: Parameters) -> BodiceDraft:
        B = p.busto
        carrure = p.ancho_espalda   # medida directa (carrure dos)
        enc = p.contorno_cuello     # encolure
        frame = Frame(
            scye=B / 10.0 + 12.5,
            quarter=(B + p.holgura_busto) / 4.0,
            back_width_pt=carrure / 2.0,          # carrura directa
            front_width_pt=carrure / 2.0 - 1.5,   # carrure devant
            bnw=enc / 6.0 + 0.5,
            fnw=enc / 6.0 + 0.3,
            fnd=enc / 6.0 + 2.2,
            back_rise=2.0,
            drop_b=4.5,
            drop_f=5.0,
        )
        return build_bodice_from_frame(p, frame, source_tag="ESMOD")

    def dart_spec(self, p: Parameters):
        from .fitted import DartSpec
        return DartSpec(bust_dart=3.2, front_waist_dart=3.8, back_waist_dart=3.5, back_shoulder_dart=0.8, bust_point_x=p.busto/10, waist_ease=4.0)

    def build_sleeve(self, p: Parameters, target_armhole: float,
                     sleeve_ease: float = 1.0) -> SleeveDraft:
        return SleeveDraft(p=p, target_armhole=target_armhole,
                           sleeve_ease=sleeve_ease, cap_ratio=ESMOD_CAP_RATIO).build()
