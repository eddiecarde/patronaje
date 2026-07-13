"""Exportador SCR (script de AutoCAD).

Genera un script ``.scr`` que, ejecutado con el comando SCRIPT en AutoCAD (o
BricsCAD), reconstruye el patrón: crea las capas y dibuja cada contorno con
PLINE, líneas con LINE, círculos con CIRCLE y textos con TEXT. Alternativa a la
importación DXF y prueba adicional de que la geometría son entidades CAD reales.
"""
from __future__ import annotations

from ..piece import EPolyline, ELine, EText, ECircle, ENotch, ALL_LAYERS, LAYER_COLORS
from ._common import gather_entities, notch_marks


def _p(x, y):
    return f"{x:.4f},{y:.4f}"


def export_scr(shirt, path: str, *, include_seam: bool = True) -> str:
    ents = gather_entities(shirt, flip=True, include_seam=include_seam)
    lines: list[str] = []
    lines.append("._UNITS")  # asegura entorno; comentario informativo abajo
    lines = ["; Script AutoCAD generado por patronaje — Camisa S (Aldrich)",
             "._-OSNAP _none"]
    # crear capas
    for layer in ALL_LAYERS:
        color = LAYER_COLORS.get(layer, 7)
        lines.append(f"._-LAYER _M {layer} _C {color} {layer} ")

    for e in ents:
        lines.append(f"._-LAYER _S {e.layer} ")
        if isinstance(e, EPolyline):
            cmd = ["._PLINE"] + [_p(x, y) for x, y in e.points]
            if e.closed:
                cmd.append("_C")
            else:
                cmd.append("")
            lines.append(" ".join(cmd))
        elif isinstance(e, ELine):
            lines.append(f"._LINE {_p(*e.p1)} {_p(*e.p2)} ")
        elif isinstance(e, ECircle):
            lines.append(f"._CIRCLE {_p(*e.center)} {e.radius:.4f}")
        elif isinstance(e, ENotch):
            for a, b in notch_marks(e):
                lines.append(f"._LINE {_p(*a)} {_p(*b)} ")
        elif isinstance(e, EText):
            just = "_MC" if e.align == "center" else "_L"
            lines.append(f"._-TEXT _J {just} {_p(*e.pos)} {e.height:.3f} 0 {e.text}")

    lines.append("._ZOOM _E")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path
