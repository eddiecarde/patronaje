"""Método Bunka (文化式) — sistema japonés proporcional al busto.

El bloque Bunka deriva todo del contorno de busto (B): profundidad de sisa
``B/12 + 13.7``, anchos de espalda/pecho ``B/8 + k`` y escotes por ``B/24``. El
sloper clásico incluye pinza de busto; para la **camisa relajada** se omite la
pinza (bloque sin pinza, costado recto), manteniendo las proporciones Bunka.
Ver `docs/metodo_bunka.md`.
"""
from __future__ import annotations

from ..parametric.parameters import Parameters
from .base import DraftingMethod
from .aldrich_bodice import BodiceDraft
from .aldrich_sleeve import SleeveDraft
from ._bodice_common import Frame, build_bodice_from_frame

BUNKA_CAP_RATIO = 0.60


class BunkaMethod(DraftingMethod):
    name = "bunka"
    label = "Bunka (文化式)"
    source = "Bunka Fashion College, 文化式婦人原型 (adaptado a camisa)"
    available = True

    def required_measurements(self) -> set[str]:
        return {
            "busto", "cintura", "cadera", "largo_camisa", "largo_manga",
            "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo",
            "muneca", "talle_espalda",
        }

    def build_bodice(self, p: Parameters) -> BodiceDraft:
        B = p.busto
        fnw = B / 24.0 + 3.4
        frame = Frame(
            scye=B / 12.0 + 13.7,
            quarter=(B + p.holgura_busto) / 4.0,
            back_width_pt=B / 8.0 + 7.4,
            front_width_pt=B / 8.0 + 6.2,
            bnw=fnw + 0.2,
            fnw=fnw,
            fnd=fnw + 0.5,
            back_rise=(fnw + 0.2) / 3.0,
            drop_b=4.0,
            drop_f=5.5,
        )
        return build_bodice_from_frame(p, frame, source_tag="Bunka")

    def dart_spec(self, p: Parameters):
        from .fitted import DartSpec
        return DartSpec(bust_dart=4.0, front_waist_dart=3.2, back_waist_dart=3.0, back_shoulder_dart=1.2, bust_point_x=p.busto/12+2.5, waist_ease=4.0)

    def build_sleeve(self, p: Parameters, target_armhole: float,
                     sleeve_ease: float = 1.0) -> SleeveDraft:
        return SleeveDraft(p=p, target_armhole=target_armhole,
                           sleeve_ease=sleeve_ease, cap_ratio=BUNKA_CAP_RATIO).build()
