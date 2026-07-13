"""Manga — método Müller & Sohn.

Müller construye la manga con una **altura de copa más alta** que la camisa
plana de Aldrich (copa ≈ 3/5 de la profundidad de sisa) y el ancho de bíceps
derivado para casar la copa con la sisa. Reutiliza el motor de manga genérico
(:class:`SleeveDraft`), que resuelve el bíceps por bisección para cumplir
``copa = sisa + holgura``; sólo cambia la proporción de altura de copa.
"""
from __future__ import annotations

from ..parametric.parameters import Parameters
from .aldrich_sleeve import SleeveDraft

# copa de manga Müller: más alta (manga montada) que la camisa plana (0.45)
MUELLER_CAP_RATIO = 0.58


def draft_mueller_sleeve(p: Parameters, target_armhole: float,
                         sleeve_ease: float = 1.0) -> SleeveDraft:
    return SleeveDraft(p=p, target_armhole=target_armhole,
                       sleeve_ease=sleeve_ease, cap_ratio=MUELLER_CAP_RATIO).build()
