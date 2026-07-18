"""Método Aldrich como implementación de referencia de :class:`DraftingMethod`.

Envuelve los trazos existentes (`aldrich_bodice.build_bodice` y
`aldrich_sleeve.build_sleeve`) en la interfaz de método. La construcción y las
fórmulas están documentadas en ``docs/metodo_aldrich.md`` y ``docs/formulas.md``.
"""
from __future__ import annotations

from ..parametric.parameters import Parameters
from .base import DraftingMethod
from .aldrich_bodice import build_bodice, BodiceDraft
from .aldrich_sleeve import build_sleeve, SleeveDraft


class AldrichMethod(DraftingMethod):
    name = "aldrich"
    label = "Aldrich"
    source = "W. Aldrich, Metric Pattern Cutting for Women's Wear"
    available = True

    def required_measurements(self) -> set[str]:
        return {
            "busto", "cintura", "cadera", "largo_camisa", "largo_manga",
            "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo",
            "muneca",
        }

    def build_bodice(self, p: Parameters) -> BodiceDraft:
        return build_bodice(p)

    def dart_spec(self, p: Parameters):
        from .fitted import DartSpec
        return DartSpec(bust_dart=3.0, front_waist_dart=3.5, back_waist_dart=3.5, back_shoulder_dart=0.8, bust_point_x=p.busto/10+0.5, waist_ease=4.0)

    def build_sleeve(self, p: Parameters, target_armhole: float,
                     sleeve_ease: float = 1.0) -> SleeveDraft:
        return build_sleeve(p, target_armhole, sleeve_ease)
