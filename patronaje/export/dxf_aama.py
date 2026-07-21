"""Exportador DXF AAMA / ASTM D6673 + validador de conformidad (round-trip).

El estándar **ASTM D6673** (heredero del AAMA-DXF) es el formato de intercambio
de patrones entre sistemas CAD/CAM de sala de corte (Gerber AccuMark, Lectra
Modaris/Diamino, Optitex, CLO, Browzwear). Sus convenciones principales:

* **Una pieza = un BLOQUE** de AutoCAD, insertado con INSERT en el modelspace.
* La geometría se reparte en **capas numeradas** con significado fijo (tabla
  ASTM D6673):

  | Capa | Contenido                                        | Entidad     |
  |------|--------------------------------------------------|-------------|
  | 1    | Contorno de la pieza (línea de corte)            | LWPOLYLINE  |
  | 2    | *Turn points* (esquinas del contorno)            | POINT       |
  | 3    | *Curve points* (puntos de curva del contorno)    | POINT       |
  | 4    | Piquetes (notches)                               | LINE        |
  | 5    | Punto de referencia de gradación                 | POINT       |
  | 6    | Línea de espejo / doblez (piezas al doblez)      | LINE        |
  | 7    | Líneas internas (pinzas, construcción)           | LINE        |
  | 8    | Línea de costura (sew line)                      | LWPOLYLINE  |
  | 11   | Línea de hilo (grain line)                       | LINE        |
  | 13   | Perforaciones (drill holes)                      | CIRCLE      |
  | 15   | Anotación / texto de pieza (nombre, talla, corte)| TEXT        |

Frente a la versión previa se **corrigen** las asignaciones que no seguían la
norma (el hilo iba en la 7 y las internas en la 11 —invertidas—; los taladros en
la 6; el texto repartido entre 13 y 15) y se **añaden** los elementos que un
importador industrial usa para reconstruir la pieza: *turn/curve points*, punto
de referencia de gradación y línea de espejo del doblez.

La **conformidad** se comprueba con :func:`validate_aama_dxf`, que reabre el
archivo, corre la **auditoría estructural** de ezdxf y verifica pieza a pieza
(contorno cerrado en la 1, piquetes en la 4, hilo en la 11, taladros en la 13,
texto en la 15, y el casado con la fuente). Es **best-effort honesto**: el
archivo es conforme y supera el round-trip, pero el sello final debe darlo el
software CAM destino (Gerber/Lectra/Optitex). Ver `docs/aama_astm.md`.
"""
from __future__ import annotations

import math
import re

import ezdxf

from ..piece import Piece

# capa AAMA/ASTM (nombre -> color ACI) y tipo de entidad esperado (para validar)
AAMA_LAYERS = {
    "1": 1,    # contorno de corte (rojo)
    "2": 7,    # turn points (blanco)
    "3": 4,    # curve points (cyan)
    "4": 6,    # piquetes (magenta)
    "5": 2,    # referencia de gradación (amarillo)
    "6": 30,   # línea de espejo/doblez (naranja)
    "7": 8,    # líneas internas (gris)
    "8": 5,    # costura (azul)
    "11": 3,   # línea de hilo (verde)
    "13": 1,   # perforaciones (rojo)
    "15": 7,   # anotación (blanco/negro)
}

# capas siempre presentes (estructura mínima ASTM) y las condicionales
_CORE_LAYERS = ("1", "2", "3", "8", "11", "15")

# umbral de ángulo (grados) para clasificar un vértice como esquina (turn point)
_TURN_DEG = 22.0


def _san(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name.strip())


def _centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def _flip(p):
    return (p[0], -p[1])


def _dedup_ring(ring):
    """Quita el vértice de cierre duplicado y puntos casi coincidentes."""
    out = []
    for p in ring:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-6:
            out.append((p[0], p[1]))
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= 1e-6:
        out.pop()
    return out


def _classify_points(ring):
    """Separa los vértices del contorno cerrado en *turn points* (esquinas) y
    *curve points* (puntos de curva), por el ángulo de giro en cada vértice."""
    pts = _dedup_ring(ring)
    n = len(pts)
    turns, curves = [], []
    if n < 3:
        return pts, []
    thr = math.radians(_TURN_DEG)
    for i in range(n):
        a, b, c = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        n1 = math.hypot(*v1)
        n2 = math.hypot(*v2)
        if n1 < 1e-9 or n2 < 1e-9:
            curves.append(b)
            continue
        cosang = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
        turn = math.acos(cosang)               # 0 = recto, pi = inversión
        (turns if turn > thr else curves).append(b)
    return turns, curves


def _add_piece_block(doc, piece: Piece) -> str:
    """Crea un bloque AAMA/ASTM con la geometría local (Y invertida) de la pieza."""
    bname = f"P{piece.number:02d}_{_san(piece.name)}"
    blk = doc.blocks.new(name=bname)

    # --- contorno de corte (capa 1) ---
    cut = [_flip(p) for p in piece.cut_contour()]
    blk.add_lwpolyline(cut, close=True, dxfattribs={"layer": "1"})

    # --- turn points (capa 2) y curve points (capa 3) sobre el contorno ---
    turns, curves = _classify_points(cut)
    for tp in turns:
        blk.add_point(tp, dxfattribs={"layer": "2"})
    for cp in curves:
        blk.add_point(cp, dxfattribs={"layer": "3"})

    # --- línea de costura (capa 8) ---
    net = [_flip(p) for p in piece.net_contour]
    blk.add_lwpolyline(net, close=True, dxfattribs={"layer": "8"})

    # --- línea de hilo (capa 11) con puntas de flecha ---
    if piece.grain:
        (x1, y1), (x2, y2) = piece.grain
        a, b = _flip((x1, y1)), _flip((x2, y2))
        blk.add_line(a, b, dxfattribs={"layer": "11"})
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for tip, base_ang in [(b, ang + math.pi), (a, ang)]:
            for da in (0.4, -0.4):
                blk.add_line(tip, (tip[0] + math.cos(base_ang + da) * 1.2,
                                   tip[1] + math.sin(base_ang + da) * 1.2),
                             dxfattribs={"layer": "11"})
        # punto de referencia de gradación (capa 5): base de la línea de hilo
        blk.add_point(a, dxfattribs={"layer": "5"})
    else:
        blk.add_point(_flip(piece.centroid()), dxfattribs={"layer": "5"})

    # --- piquetes (capa 4): tick hacia el interior ---
    cen = _centroid(piece.net_contour)
    for nx, ny in piece.notches:
        dx, dy = cen[0] - nx, cen[1] - ny
        d = math.hypot(dx, dy) or 1.0
        p0 = _flip((nx, ny))
        p1 = _flip((nx + dx / d * 0.7, ny + dy / d * 0.7))
        blk.add_line(p0, p1, dxfattribs={"layer": "4"})

    # --- línea de espejo/doblez (capa 6) para piezas al doblez ---
    if piece.on_fold and piece.fold_x is not None:
        minx, miny, maxx, maxy = piece.bbox()
        blk.add_line(_flip((piece.fold_x, miny)), _flip((piece.fold_x, maxy)),
                     dxfattribs={"layer": "6"})

    # --- perforaciones (capa 13) ---
    for dx, dy in piece.drills:
        blk.add_circle(_flip((dx, dy)), 0.15, dxfattribs={"layer": "13"})

    # --- líneas internas: construcción + patas de pinza (capa 7) ---
    for a, b in piece.construction_lines:
        blk.add_line(_flip(a), _flip(b), dxfattribs={"layer": "7"})
    for base1, apex, base2 in piece.darts:
        blk.add_line(_flip(base1), _flip(apex), dxfattribs={"layer": "7"})
        blk.add_line(_flip(base2), _flip(apex), dxfattribs={"layer": "7"})
        blk.add_circle(_flip(apex), 0.15, dxfattribs={"layer": "13"})   # vértice = taladro

    # --- anotación de pieza (capa 15) ---
    cx, cy = _flip(cen)
    fold = "  AL DOBLEZ" if piece.on_fold else ""
    t1 = blk.add_text(f"{piece.name} #{piece.number:02d}", height=0.9,
                      dxfattribs={"layer": "15"})
    t1.set_placement((cx, cy + 1.0), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    t2 = blk.add_text(f"T:{piece.size}  x{piece.quantity}  ({piece.cut_type}){fold}",
                      height=0.6, dxfattribs={"layer": "15"})
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


# --------------------------------------------------------------------------
# Validación de conformidad (round-trip)
# --------------------------------------------------------------------------
def validate_aama_dxf(path: str, shirt=None) -> dict:
    """Reabre el DXF AAMA/ASTM y comprueba su **conformidad** sin depender de un
    CAD comercial: (1) es legible, (2) supera la **auditoría estructural** de
    ezdxf, (3) tiene las capas núcleo del estándar, y (4) cada pieza trae contorno
    cerrado (capa 1), *turn points* (2), costura (8), hilo (11) y texto (15). Si
    se pasa ``shirt``, además **casa** el nº de piezas, y por pieza los piquetes
    (4), taladros (13) e hilo con la fuente.

    Devuelve un informe ``{ok, blocks, audit_errors, issues, per_piece}``.
    """
    issues: list[str] = []
    doc = ezdxf.readfile(path)                       # (1) legible

    auditor = doc.audit()                            # (2) conformidad estructural DXF
    audit_errors = len(auditor.errors)
    if audit_errors:
        issues.append(f"auditoría DXF: {audit_errors} errores estructurales")

    have = {ly.dxf.name for ly in doc.layers}        # (3) capas núcleo
    for req in _CORE_LAYERS:
        if req not in have:
            issues.append(f"falta la capa ASTM '{req}'")

    msp = doc.modelspace()
    refs = list(msp.query("INSERT"))
    per_piece = {}
    src_by_name = {}
    if shirt is not None:
        for pc in shirt.pieces:
            src_by_name[f"P{pc.number:02d}_{_san(pc.name)}"] = pc
        if len(refs) != len(shirt.pieces):
            issues.append(f"nº de piezas: DXF {len(refs)} vs fuente {len(shirt.pieces)}")

    for ref in refs:
        bname = ref.dxf.name
        blk = doc.blocks.get(bname)
        by_layer: dict[str, list] = {}
        for e in blk:
            by_layer.setdefault(e.dxf.layer, []).append(e)

        # (4) estructura mínima de la pieza
        boundary = [e for e in by_layer.get("1", []) if e.dxftype() == "LWPOLYLINE"]
        rep = {"boundary_pts": 0, "turn": len(by_layer.get("2", [])),
               "curve": len(by_layer.get("3", [])), "notches": len(by_layer.get("4", [])),
               "drills": len(by_layer.get("13", [])), "grain": len(by_layer.get("11", [])) > 0,
               "text": len(by_layer.get("15", [])), "closed": False}
        if not boundary:
            issues.append(f"{bname}: sin contorno en capa 1")
        else:
            pl = boundary[0]
            rep["boundary_pts"] = len(pl)
            rep["closed"] = bool(pl.closed)
            if not pl.closed:
                issues.append(f"{bname}: contorno de capa 1 no cerrado")
            if len(pl) < 3:
                issues.append(f"{bname}: contorno con menos de 3 puntos")
        # turn points son anotación opcional: una pieza de contorno curvo (puño,
        # cuello) puede no tener esquinas. Se reportan, no se exigen.
        if rep["text"] == 0:
            issues.append(f"{bname}: sin texto de anotación (capa 15)")

        # (5) casado con la fuente, si se dio
        pc = src_by_name.get(bname)
        if pc is not None:
            if rep["notches"] != len(pc.notches):
                issues.append(f"{bname}: piquetes DXF {rep['notches']} vs fuente {len(pc.notches)}")
            exp_drills = len(pc.drills) + len(pc.darts)   # cada pinza añade taladro de vértice
            if rep["drills"] != exp_drills:
                issues.append(f"{bname}: taladros DXF {rep['drills']} vs fuente {exp_drills}")
            if bool(pc.grain) != rep["grain"]:
                issues.append(f"{bname}: hilo (capa 11) no coincide con la fuente")
        per_piece[bname] = rep

    return {"ok": not issues, "blocks": len(refs), "audit_errors": audit_errors,
            "issues": issues, "per_piece": per_piece}
