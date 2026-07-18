"""Método Sistema Martí — escuela española/latinoamericana de corte.

El Sistema Martí (Escuela Martí) es un método de trazado por **medidas directas**
muy extendido en España y Latinoamérica. Se adapta aquí a la camisa usando su red
de proporciones para escote, sisa y anchos. Bloque sin pinza (camisa).
"""
from __future__ import annotations

from ..parametric.parameters import Parameters
from .base import DraftingMethod
from .aldrich_bodice import BodiceDraft
from .aldrich_sleeve import SleeveDraft
from ._bodice_common import Frame, build_bodice_from_frame


class MartiMethod(DraftingMethod):
    name = "marti"
    label = "Sistema Martí"
    source = "Escuela Martí (corte y confección), adaptado a camisa"
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
            scye=B / 8.0 + 11.0,
            quarter=(B + p.holgura_busto) / 4.0,
            back_width_pt=B / 4.0 - 6.0,
            front_width_pt=B / 4.0 - 7.0,
            bnw=enc / 5.0,
            fnw=enc / 5.0 - 0.5,
            fnd=enc / 5.0 + 2.5,
            back_rise=2.0,
            drop_b=4.5,
            drop_f=5.0,
        )
        return build_bodice_from_frame(p, frame, source_tag="Martí")

    def build_sleeve(self, p: Parameters, target_armhole: float,
                     sleeve_ease: float = 1.0) -> SleeveDraft:
        return SleeveDraft(p=p, target_armhole=target_armhole,
                           sleeve_ease=sleeve_ease, cap_ratio=0.52).build()
