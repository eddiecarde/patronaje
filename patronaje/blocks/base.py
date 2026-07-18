"""Capa de abstracción de métodos de patronaje.

El motor de geometría (`patronaje/core/`) y todo lo que va después (piezas,
validación, exportadores, grading, marker, tech pack) es **agnóstico del
método**. Lo único que cambia entre Aldrich, Müller & Sohn, ESMOD o Bunka es la
**capa de trazo**: las fórmulas y la secuencia de construcción del bloque de
cuerpo y de manga.

Esta capa define la interfaz :class:`DraftingMethod` que cada método implementa
para producir los *drafts* (`BodiceDraft`, `SleeveDraft`) que el resto del
sistema ya sabe consumir. Así, añadir un método nuevo = escribir una clase; no
se toca nada aguas abajo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..parametric.parameters import Parameters
from .aldrich_bodice import BodiceDraft
from .aldrich_sleeve import SleeveDraft


class DraftingMethod(ABC):
    """Contrato que cumple todo método de patronaje.

    Attributes
    ----------
    name : str
        Identificador corto (p. ej. ``"aldrich"``).
    label : str
        Nombre legible (p. ej. ``"Aldrich"``).
    source : str
        Referencia bibliográfica del método.
    available : bool
        ``True`` si el método está implementado; ``False`` si es un placeholder
        planificado (permite listarlo aunque aún no drafte).
    """

    name: str = ""
    label: str = ""
    source: str = ""
    available: bool = True

    @abstractmethod
    def required_measurements(self) -> set[str]:
        """Medidas del cuerpo que el método necesita en :class:`Parameters`."""
        raise NotImplementedError

    @abstractmethod
    def build_bodice(self, p: Parameters) -> BodiceDraft:
        """Traza el bloque de cuerpo (delantero + espalda)."""
        raise NotImplementedError

    @abstractmethod
    def build_sleeve(self, p: Parameters, target_armhole: float,
                     sleeve_ease: float = 1.0) -> SleeveDraft:
        """Traza la manga casando la copa con la sisa medida."""
        raise NotImplementedError

    def dart_spec(self, p: Parameters):
        """Parámetros de pinza/equilibrio para el sloper entallado. Por defecto
        derivados genéricos; cada método puede afinarlos."""
        from .fitted import DartSpec
        return DartSpec(bust_point_x=p.busto / 10.0 + 0.5)

    # -- utilidad compartida ------------------------------------------------
    def check_measurements(self, p: Parameters) -> list[str]:
        """Devuelve las medidas requeridas que faltan en ``p`` (vacío = OK)."""
        return [m for m in self.required_measurements() if m not in p]

    def __repr__(self):
        state = "" if self.available else " (planificado)"
        return f"<DraftingMethod {self.name}: {self.label}{state}>"
