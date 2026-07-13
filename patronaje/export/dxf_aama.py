"""Exportador DXF AAMA / ASTM D6673 (best-effort).

El estándar **ASTM D6673** (heredero del AAMA-DXF) es el formato de intercambio
de patrones entre sistemas CAD/CAM de sala de corte (Gerber AccuMark, Lectra
Modaris/Diamino, Optitex, CLO, Browzwear). Sus convenciones principales:

* **Una pieza = un BLOQUE** de AutoCAD, insertado con INSERT en el modelspace.
* La geometría se reparte en **capas numeradas** con significado fijo:

  | Capa | Contenido                                   |
  |------|---------------------------------------------|
  | 1    | Contorno de la pieza (línea de corte)       |
  | 4    | Piquetes (notches)                          |
  | 6    | Perforaciones internas (drill holes)        |
  | 7    | Línea de hilo (grain / grain reference)     |
  | 8    | Línea de costura interna / espejo           |
  | 11   | Líneas internas (dobleces, referencias)     |
  | 13   | Anotación / texto de pieza                  |
  | 15   | Textos de talla / cantidad                  |

Este exportador escribe DXF R2013 con esa estructura. Es **best-effort**:
la geometría es correcta y abre en CAD estándar, pero conviene **verificar la
importación en el software CAM destino** (algunos esperan variantes de código de
punto o metadatos ASTM adicionales). Ver `docs/aama_astm.md`.
"""
from __future__ import annotations

import math
import re

import ezdxf

from ..piece import Piece

# capas AAMA/ASTM (nombre -> color ACI)
AAMA_LAYERS = {
    "1": 1,    # contorno de corte (rojo)
    "4": 4,    # piquetes (cyan)
    "6": 2,    # perforaciones (amarillo)
    "7": 3,    # línea de hilo (verde)
    "8": 5,    # costura/espejo (azul)
    "11": 8,   # líneas internas (gris)
    "13": 7,   # anotación (blanco/negro)
    "15": 6,   # textos talla/cantidad (magenta)
}


def _san(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name.strip())


def _centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def _flip(p):
    return (p[0], -p[1])


def _add_piece_block(doc, piece: Piece):
    """Crea un bloque AAMA con la geometría local (Y invertida) de la pieza."""
    bname = f"P{piece.number:02d}_{_san(piece.name)}"
    blk = doc.blocks.new(name=bname)

    # contorno de corte (capa 1)
    cut = [_flip(p) for p in piece.cut_contour()]
    blk.add_lwpolyline(cut, close=True, dxfattribs={"layer": "1"})
    # costura interna (capa 8)
    net = [_flip(p) for p in piece.net_contour]
    blk.add_lwpolyline(net, close=True, dxfattribs={"layer": "8"})
    # línea de hilo (capa 7) con flechas
    if piece.grain:
        (x1, y1), (x2, y2) = piece.grain
        a, b = _flip((x1, y1)), _flip((x2, y2))
        blk.add_line(a, b, dxfattribs={"layer": "7"})
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for tip, base_ang in [(b, ang + math.pi), (a, ang)]:
            for da in (0.4, -0.4):
                blk.add_line(tip, (tip[0] + math.cos(base_ang + da) * 1.2,
                                   tip[1] + math.sin(base_ang + da) * 1.2),
                             dxfattribs={"layer": "7"})
    # piquetes (capa 4): tick hacia el interior
    cen = _centroid(piece.net_contour)
    for nx, ny in piece.notches:
        dx, dy = cen[0] - nx, cen[1] - ny
        d = math.hypot(dx, dy) or 1.0
        p0 = _flip((nx, ny))
        p1 = _flip((nx + dx / d * 0.7, ny + dy / d * 0.7))
        blk.add_line(p0, p1, dxfattribs={"layer": "4"})
    # perforaciones (capa 6)
    for dx, dy in piece.drills:
        blk.add_circle(_flip((dx, dy)), 0.15, dxfattribs={"layer": "6"})
    # líneas internas (capa 11)
    for a, b in piece.construction_lines:
        blk.add_line(_flip(a), _flip(b), dxfattribs={"layer": "11"})
    # anotación de pieza (capa 13) y talla/cantidad (capa 15)
    cx, cy = _flip(cen)
    t1 = blk.add_text(f"{piece.name} #{piece.number:02d}", height=0.9,
                      dxfattribs={"layer": "13"})
    t1.set_placement((cx, cy + 1.0), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    fold = "  AL DOBLEZ" if piece.on_fold else ""
    t2 = blk.add_text(f"T:{piece.size}  x{piece.quantity}{fold}", height=0.6,
                      dxfattribs={"layer": "15"})
    t2.set_placement((cx, cy - 0.4), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    return bname


def export_dxf_aama(shirt, path: str) -> str:
    doc = ezdxf.new("R2013", setup=True)
    doc.header["$INSUNITS"] = 5   # cm
    doc.header["$MEASUREMENT"] = 1
    msp = doc.modelspace()
    for name, color in AAMA_LAYERS.items():
        doc.layers.add(name=name, color=color)

    for piece in shirt.pieces:
        bname = _add_piece_block(doc, piece)
        ox, oy = piece.offset
        msp.add_blockref(bname, (ox, -oy))

    doc.saveas(path)
    return path
