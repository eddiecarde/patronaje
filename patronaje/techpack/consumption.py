"""Cálculo de consumo de tela por ancho y por talla.

Envuelve el motor de marker (`marker/layout.py`) y añade una recomendación de
compra con margen de tendido/mermas. El consumo se calcula regenerando el marker
para cada ancho de tela solicitado (110/150/160 cm).
"""
from __future__ import annotations

from ..marker.layout import marker_report

# margen de compra sobre el largo del marker (mermas de tendido, encogimiento)
COMPRA_MARGEN = 0.07  # 7 %


def consumption(shirt, widths=(110.0, 150.0, 160.0)) -> dict:
    rep = marker_report(shirt, widths=widths)
    for W, d in rep["por_ancho"].items():
        d["compra_recomendada_m"] = round(d["largo_m"] * (1 + COMPRA_MARGEN), 3)
    return rep


def consumption_all_sizes(sizes, build_fn, widths=(110.0, 150.0, 160.0)) -> dict:
    """Consumo por talla (para tabla de compra de producción)."""
    out = {}
    for s in sizes:
        sh = build_fn(s).layout()
        out[s] = consumption(sh, widths=widths)
    return out
