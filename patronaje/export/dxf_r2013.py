"""Exportador DXF AutoCAD R2013 con capas independientes.

Genera un DXF (versión ``AC1027`` = R2013) con una **capa por tipo de línea**
(CONSTRUCCION, CORTE, COSTURA, PIQUETES, TEXTOS, CENTROS, HILO, DOBLEZ, BOTONES,
OJAL, REFERENCIAS), cada una con su color ACI. Las unidades del dibujo son
centímetros (``$INSUNITS = 5``).

Cada entidad se vuelca a su equivalente CAD real (LWPOLYLINE, LINE, TEXT,
CIRCLE), de modo que el archivo abre como geometría vectorial editable en
AutoCAD, DraftSight, LibreCAD y BricsCAD (no es raster ni una imagen).
"""
from __future__ import annotations

import ezdxf

from ..piece import EPolyline, ELine, EText, ECircle, ENotch, ALL_LAYERS, LAYER_COLORS
from ._common import gather_entities, notch_marks


def export_dxf(shirt, path: str, *, include_seam: bool = True) -> str:
    doc = ezdxf.new("R2013", setup=True)
    doc.header["$INSUNITS"] = 5  # centímetros
    doc.header["$MEASUREMENT"] = 1  # métrico
    msp = doc.modelspace()

    # capas
    for layer in ALL_LAYERS:
        doc.layers.add(name=layer, color=LAYER_COLORS.get(layer, 7))

    ents = gather_entities(shirt, flip=True, include_seam=include_seam)
    for e in ents:
        attribs = {"layer": e.layer}
        if isinstance(e, EPolyline):
            msp.add_lwpolyline(
                [(x, y) for x, y in e.points],
                dxfattribs=attribs,
                close=e.closed,
            )
        elif isinstance(e, ELine):
            msp.add_line(e.p1, e.p2, dxfattribs=attribs)
        elif isinstance(e, ECircle):
            msp.add_circle(e.center, e.radius, dxfattribs=attribs)
        elif isinstance(e, ENotch):
            for a, b in notch_marks(e):
                msp.add_line(a, b, dxfattribs=attribs)
        elif isinstance(e, EText):
            txt = msp.add_text(
                e.text,
                height=e.height,
                dxfattribs={**attribs, "rotation": e.rotation},
            )
            if e.align == "center":
                txt.set_placement(e.pos, align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
            else:
                txt.set_placement(e.pos, align=ezdxf.enums.TextEntityAlignment.LEFT)

    doc.saveas(path)
    return path
