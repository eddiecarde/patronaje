"""Modelo de punto paramétrico.

Cada punto de construcción del patrón es una entidad con identidad propia:
lleva un ``id`` legible, una ``descripcion`` de su rol en el trazo, sus
coordenadas cartesianas ``(x, y)`` en centímetros, las *relaciones geométricas*
que lo originaron (de qué otros puntos/medidas depende) y las *restricciones*
que debe cumplir. Esto materializa el requisito del prompt:

    "Cada punto debe tener: ID, Descripción, Coordenadas, Relaciones
     geométricas, Restricciones."

El sistema de coordenadas es siempre X (horizontal, hacia la derecha) e
Y (vertical, hacia arriba), en centímetros, coherente con CAD (DXF/SVG se
adaptan en la capa de exportación).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Point:
    """Un punto de construcción con trazabilidad completa.

    Attributes
    ----------
    id:
        Identificador corto y único dentro de una pieza (p. ej. ``"B12"``).
    x, y:
        Coordenadas en centímetros.
    descripcion:
        Rol del punto en la construcción Aldrich (p. ej. "escote espalda").
    relaciones:
        Lista legible de las dependencias que lo generan (parámetros u otros
        puntos), para documentación y depuración.
    restricciones:
        Restricciones geométricas declarativas (p. ej. "sobre línea de pecho").
    """

    id: str
    x: float
    y: float
    descripcion: str = ""
    relaciones: list[str] = field(default_factory=list)
    restricciones: list[str] = field(default_factory=list)

    # ---- Operaciones vectoriales básicas ---------------------------------
    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def __iter__(self):
        yield self.x
        yield self.y

    def distance_to(self, other: "Point | tuple[float, float]") -> float:
        ox, oy = (other.x, other.y) if isinstance(other, Point) else other
        return math.hypot(self.x - ox, self.y - oy)

    def translated(self, dx: float, dy: float, *, id: str | None = None,
                   descripcion: str | None = None) -> "Point":
        return Point(
            id=id or f"{self.id}'",
            x=self.x + dx,
            y=self.y + dy,
            descripcion=descripcion or self.descripcion,
            relaciones=list(self.relaciones),
            restricciones=list(self.restricciones),
        )

    def midpoint(self, other: "Point", *, id: str, descripcion: str = "") -> "Point":
        return Point(
            id=id,
            x=(self.x + other.x) / 2.0,
            y=(self.y + other.y) / 2.0,
            descripcion=descripcion or f"punto medio {self.id}-{other.id}",
            relaciones=[f"medio({self.id},{other.id})"],
        )

    def rounded(self, ndigits: int = 4) -> tuple[float, float]:
        return (round(self.x, ndigits), round(self.y, ndigits))


def polyline_length(points: Iterable[Point | tuple[float, float]]) -> float:
    """Longitud acumulada de una polilínea (para casar costuras)."""
    pts = [p.as_tuple() if isinstance(p, Point) else p for p in points]
    total = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        total += math.hypot(x1 - x0, y1 - y0)
    return total
