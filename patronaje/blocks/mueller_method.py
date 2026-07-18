"""Método Müller & Sohn (M. Müller & Sohn) — placeholder planificado.

Sistema alemán **proporcional**: el bloque se construye desde el contorno de
busto (*Brustumfang*) y el talle de espalda (*Rückenlänge*) mediante líneas
auxiliares (*Hilfslinien*) y divisiones proporcionales. Se registra ya en el
sistema para poder listarlo y validar sus medidas; el trazo se implementará en
una fase dedicada.

Plan de fórmulas (bloque de cuerpo, mujer), a codificar en `build_bodice`:

* Profundidad de sisa (Armlochtiefe):  ``busto/10 + 10.5``  (+ holgura)
* Ancho de espalda (Rückenbreite):     ``busto/8 + 5.5``
* Ancho de sisa (Armlochbreite):       ``busto/8 − 1.5``
* Ancho de pecho (Brustbreite):        ``busto/4 − 4``
* Altura de escote espalda:            ``busto/20 + 0.5``
* Ancho de escote:                     ``busto/20 + 3``
* Pinza de busto: derivada de la diferencia busto–cintura repartida en costados,
  costadillo y pinza francesa/de talle según el modelo.
* Talle de espalda (Rückenlänge) y altura de cadera: medidas directas.

Manga (Ärmel): altura de copa ≈ ``prof_sisa × 3/4`` con anchura de bíceps
derivada para casar la copa con la sisa (igual criterio que el motor actual).

Medidas adicionales respecto de Aldrich: ``talle_espalda`` (Rückenlänge) y
``altura_cadera``; se añadirán a ``SIZE_CHART`` al implementar el método.
"""
from __future__ import annotations

from ..parametric.parameters import Parameters
from .base import DraftingMethod
from .aldrich_bodice import BodiceDraft
from .aldrich_sleeve import SleeveDraft
from .mueller_bodice import draft_mueller_bodice
from .mueller_sleeve import draft_mueller_sleeve


class MuellerMethod(DraftingMethod):
    name = "mueller"
    label = "Müller & Sohn"
    source = "M. Müller & Sohn, Schnittkonstruktion für Damen"
    available = True

    def required_measurements(self) -> set[str]:
        return {
            "busto", "cintura", "cadera", "largo_camisa", "largo_manga",
            "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo",
            "muneca", "talle_espalda", "altura_cadera",
        }

    def build_bodice(self, p: Parameters) -> BodiceDraft:
        return draft_mueller_bodice(p)

    def dart_spec(self, p: Parameters):
        from .fitted import DartSpec
        return DartSpec(bust_dart=3.5, front_waist_dart=3.0, back_waist_dart=3.5, back_shoulder_dart=1.0, bust_point_x=p.busto/10+1.0, waist_ease=3.0)

    def build_sleeve(self, p: Parameters, target_armhole: float,
                     sleeve_ease: float = 1.0) -> SleeveDraft:
        return draft_mueller_sleeve(p, target_armhole, sleeve_ease)
