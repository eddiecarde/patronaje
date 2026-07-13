"""Registro de parámetros del motor paramétrico.

El sistema no dibuja coordenadas fijas: cada punto del patrón se calcula a
partir de *parámetros* nombrados (medidas del cuerpo, holguras y constantes de
método). Este módulo define el contenedor :class:`Parameters`, que:

* guarda cada parámetro con nombre, valor, unidad y descripción,
* permite acceso por atributo (``p.busto``) y por clave (``p["busto"]``),
* soporta *parámetros derivados* (funciones de otros parámetros) que se
  recalculan solos, de modo que al cambiar una medida todo el patrón se
  regenera (requisito del prompt: "Al modificar una medida todo el patrón debe
  regenerarse automáticamente").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Parameter:
    nombre: str
    valor: float
    unidad: str = "cm"
    descripcion: str = ""
    derivado_de: str | None = None  # expresión legible si es derivado


class Parameters:
    """Contenedor de parámetros con soporte de valores derivados."""

    def __init__(self):
        self._base: dict[str, Parameter] = {}
        self._derived: dict[str, tuple[Callable[["Parameters"], float], str, str]] = {}

    # ---- definición ------------------------------------------------------
    def set(self, nombre: str, valor: float, *, unidad: str = "cm",
            descripcion: str = "") -> "Parameters":
        self._base[nombre] = Parameter(nombre, float(valor), unidad, descripcion)
        return self

    def derive(self, nombre: str, fn: Callable[["Parameters"], float], *,
               descripcion: str = "", expr: str = "") -> "Parameters":
        """Define un parámetro derivado (se calcula bajo demanda)."""
        self._derived[nombre] = (fn, descripcion, expr)
        return self

    # ---- acceso ----------------------------------------------------------
    def __getitem__(self, nombre: str) -> float:
        if nombre in self._base:
            return self._base[nombre].valor
        if nombre in self._derived:
            return float(self._derived[nombre][0](self))
        raise KeyError(f"Parámetro desconocido: {nombre}")

    def __getattr__(self, nombre: str) -> float:
        # sólo se invoca si no es un atributo normal
        if nombre.startswith("_"):
            raise AttributeError(nombre)
        try:
            return self[nombre]
        except KeyError as e:
            raise AttributeError(str(e)) from e

    def __contains__(self, nombre: str) -> bool:
        return nombre in self._base or nombre in self._derived

    def update(self, **kwargs) -> "Parameters":
        """Cambia valores base y devuelve self (los derivados se recalculan)."""
        for k, v in kwargs.items():
            if k not in self._base:
                raise KeyError(f"No se puede actualizar parámetro inexistente: {k}")
            self._base[k].valor = float(v)
        return self

    def copy(self) -> "Parameters":
        new = Parameters()
        for k, p in self._base.items():
            new.set(k, p.valor, unidad=p.unidad, descripcion=p.descripcion)
        new._derived = dict(self._derived)
        return new

    # ---- introspección / documentación ----------------------------------
    def items(self):
        for k, p in self._base.items():
            yield k, p.valor, p.unidad, p.descripcion
        for k, (fn, desc, expr) in self._derived.items():
            yield k, float(fn(self)), "cm", f"{desc} = {expr}" if expr else desc

    def as_dict(self) -> dict[str, float]:
        d = {k: p.valor for k, p in self._base.items()}
        d.update({k: float(fn(self)) for k, (fn, _, _) in self._derived.items()})
        return d
