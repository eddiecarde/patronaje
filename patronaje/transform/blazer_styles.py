"""Estilos de chaqueta/blazer por manipulación del bloque.

Actúan sobre las piezas ya montadas: largo (crop / longline), botonadura
(cruzada / un botón), y forro. La solapa, el cuello y la manga de dos piezas se
conservan salvo que el estilo diga lo contrario.
"""
from __future__ import annotations

from . import operations as ops

# piezas cuyo bajo se recorta/alarga con el cuerpo
_BODY = ("CHAQUETA DELANTERO", "CHAQUETA ESPALDA", "VISTA DELANTERA",
         "FORRO DELANTERO", "FORRO ESPALDA")


def _bodies(z):
    return [p for p in z.pieces if any(p.name.startswith(n) for n in _BODY)]


def clasica(z):
    """Blazer clásico (una fila de botones, solapa con pico)."""
    return z


def crop(z, at: float = 0.5):
    """Blazer corto (crop): recorta el cuerpo por encima de la cadera."""
    b = z.body
    cut = b.waist_y + (b.hem_y - b.waist_y) * at
    for pc in _bodies(z):
        pc.net_contour = ops.clip_below(pc.net_contour, cut)
        pc.name = pc.name + " (crop)"
    return z


def longline(z, extra: float = 22.0):
    """Blazer largo (longline): alarga el cuerpo por debajo de la cintura."""
    b = z.body
    factor = (b.hem_y - b.waist_y + extra) / (b.hem_y - b.waist_y)
    for pc in _bodies(z):
        pc.net_contour = ops.lengthen(pc.net_contour, b.waist_y, factor)
        pc.name = pc.name + " (longline)"
    return z


def cruzada(z, overlap: float = 6.0):
    """Cruzada (double-breasted): ensancha la botonadura y añade 2ª fila de botones."""
    front = next((p for p in z.pieces if p.name.startswith("CHAQUETA DELANTERO")), None)
    if front:
        # desplaza el borde delantero (x más negativo) para el cruce
        front.net_contour = [((x - overlap) if x < 0.1 else x, y) for x, y in front.net_contour]
        base = list(front.buttons)
        front.buttons = base + [(bx - overlap, by) for bx, by in base]
        front.name = "CHAQUETA DELANTERO (cruzada)"
    return z


def un_boton(z):
    """Un solo botón (solapa larga)."""
    front = next((p for p in z.pieces if p.name.startswith("CHAQUETA DELANTERO")), None)
    if front and front.buttons:
        front.buttons = front.buttons[:1]
    return z


def sin_forro(z):
    """Sin forro (desestructurado): elimina las piezas de forro."""
    z.pieces = [p for p in z.pieces if not p.name.startswith("FORRO")]
    return z


BLAZER_STYLES = {
    "clasica": clasica,
    "crop": crop,
    "longline": longline,
    "cruzada": cruzada,
    "un_boton": un_boton,
    "sin_forro": sin_forro,
}
