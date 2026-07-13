"""Reglas de grading (escalado industrial) XS–XXL.

El escalado NO se hace redibujando: el motor paramétrico regenera cada talla a
partir de su diccionario de medidas (`SIZE_CHART` en
`patronaje/parametric/measurements.py`). Este módulo documenta y expone los
**incrementos** entre tallas (la "regla de grading") derivados de esa tabla, y
ofrece utilidades para consultarlos.

La talla base de referencia es la **S**. Los incrementos entre tallas contiguas
son los saltos estándar de la industria (busto/cadera ≈ 4 cm por talla, etc.).
"""
from __future__ import annotations

from ..parametric.measurements import SIZE_CHART

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
BASE_SIZE = "S"

# medidas que participan en el grading
GRADED_KEYS = ["busto", "cintura", "cadera", "largo_camisa", "largo_manga",
               "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo", "muneca"]


def increments() -> dict[str, dict[str, float]]:
    """Incremento de cada medida al pasar de una talla a la siguiente.

    Devuelve ``{'XS->S': {medida: delta, ...}, 'S->M': {...}, ...}``.
    """
    out: dict[str, dict[str, float]] = {}
    for a, b in zip(SIZE_ORDER, SIZE_ORDER[1:]):
        out[f"{a}->{b}"] = {
            k: round(SIZE_CHART[b][k] - SIZE_CHART[a][k], 3) for k in GRADED_KEYS
        }
    return out


def delta_from_base(size: str) -> dict[str, float]:
    """Diferencia de cada medida respecto de la talla base (S)."""
    return {k: round(SIZE_CHART[size][k] - SIZE_CHART[BASE_SIZE][k], 3)
            for k in GRADED_KEYS}


def grading_table_text() -> str:
    lines = ["=== REGLA DE GRADING (incrementos entre tallas) ===",
             "medida            " + "  ".join(f"{p:>8}" for p in
                                              [f"{a}->{b}" for a, b in zip(SIZE_ORDER, SIZE_ORDER[1:])])]
    inc = increments()
    pares = list(inc.keys())
    for k in GRADED_KEYS:
        row = f"{k:<18}" + "  ".join(f"{inc[p][k]:>8.2f}" for p in pares)
        lines.append(row)
    return "\n".join(lines)
