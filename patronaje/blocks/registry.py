"""Registro de métodos de patronaje.

Permite seleccionar el método por nombre (``build_shirt(size, method="aldrich")``)
y descubrir los disponibles. Añadir un método = registrar su clase aquí.
"""
from __future__ import annotations

from .base import DraftingMethod
from .aldrich_method import AldrichMethod
from .mueller_method import MuellerMethod
from .bunka_method import BunkaMethod
from .esmod_method import EsmodMethod

_REGISTRY: dict[str, DraftingMethod] = {}


def register(method: DraftingMethod) -> None:
    _REGISTRY[method.name] = method


def get_method(name: str) -> DraftingMethod:
    key = (name or "").lower()
    if key not in _REGISTRY:
        disponibles = ", ".join(sorted(_REGISTRY))
        raise KeyError(f"Método de patronaje desconocido: '{name}'. "
                       f"Disponibles: {disponibles}")
    m = _REGISTRY[key]
    if not m.available:
        raise NotImplementedError(
            f"El método '{m.label}' está registrado pero aún no implementado "
            f"(planificado). Ver docs/motor_metodos.md."
        )
    return m


def list_methods() -> list[dict]:
    """Lista de métodos con su estado (para CLI/UX)."""
    return [
        {"name": m.name, "label": m.label, "source": m.source,
         "disponible": m.available}
        for m in _REGISTRY.values()
    ]


# métodos registrados
register(AldrichMethod())
register(MuellerMethod())
register(BunkaMethod())
register(EsmodMethod())
