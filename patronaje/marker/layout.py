"""Plano de corte (marker / trazo de corte) y cálculo de consumo.

Coloca todas las piezas a cortar sobre un ancho de tela dado (110/150/160 cm) y
calcula la **longitud de tela** necesaria y el **desperdicio**. El nesting
respeta la **línea de hilo** (no se rotan las piezas 90°, sólo se colocan en su
orientación de corte), como en un marker industrial real.

Algoritmos:
* ``nest`` — empaquetado por estantes (bounding box); conservador, garantiza
  no solapamiento de bbox (se usa en tests).
* ``nest_skyline`` — **nesting por skyline con el perfil real del contorno**:
  las piezas se dejan caer sobre la silueta ya colocada y **encajan en las
  concavidades** unas de otras, con rotación 180° (respeta la línea de hilo).
  Es el método de sala de corte; reduce el largo/desperdicio de forma notable
  (p. ej. ~30% menos largo a 110 cm). Lo usan `marker_report` y el export.

Se reportan dos métricas:
* **eficiencia de tela** = área real de las piezas / (ancho × largo de tela).
* **desperdicio** = 1 − eficiencia.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..piece import Piece


@dataclass
class Placement:
    piece: Piece
    instance: int          # índice de copia
    x: float               # traslación aplicada al bbox (esquina inf-izq)
    y: float
    w: float
    h: float
    mirror: bool = False   # copia espejada (par izq/der o al doblez)
    contour: list = None   # contorno local ya orientado (para dibujar)


def _cut_instances(piece: Piece) -> list[tuple[bool, float, float, list]]:
    """Instancias de tela de una pieza: (mirror, w, h, contorno_local).

    - Piezas al doblez: se cortan como pieza COMPLETA (se refleja en el doblez),
      por lo que el ancho se duplica; 1 instancia.
    - Piezas en par: 2 instancias (2ª espejada).
    - Se excluyen copias de entretela (se cortan aparte); se usa la cantidad de
      tela principal razonable.
    """
    cut = piece.cut_contour()
    minx = min(p[0] for p in cut); maxx = max(p[0] for p in cut)
    miny = min(p[1] for p in cut); maxy = max(p[1] for p in cut)
    local = [(x - minx, y - miny) for x, y in cut]
    w = maxx - minx
    h = maxy - miny

    if piece.on_fold and piece.fold_x is not None:
        # pieza completa: refleja en el doblez -> ancho doble
        fx = piece.fold_x
        mirrored = [(2 * fx - x, y) for x, y in cut]  # reflejo
        full = cut + mirrored
        fminx = min(p[0] for p in full); fmaxx = max(p[0] for p in full)
        fminy = min(p[1] for p in full); fmaxy = max(p[1] for p in full)
        floc = [(x - fminx, y - fminy) for x, y in full]
        return [(False, fmaxx - fminx, fmaxy - fminy, floc)]

    # cantidad de tela principal (excluye entretela: cuenta pares/simples)
    n = piece.quantity
    if "entretela" in piece.cut_type.lower():
        n = 2  # p.ej. puño x4 (2 tela + 2 entretela) -> 2 de tela
    inst = []
    for i in range(n):
        inst.append((i % 2 == 1, w, h, local))
    return inst


def nest(shirt, fabric_width: float, gap: float = 1.0) -> tuple[list[Placement], float]:
    """Empaqueta las piezas en estantes sobre el ancho de tela.

    Devuelve (placements, largo_total_cm).
    """
    items: list[tuple[Piece, int, bool, float, float, list]] = []
    for piece in shirt.pieces:
        for k, (mirror, w, h, loc) in enumerate(_cut_instances(piece)):
            items.append((piece, k, mirror, w, h, loc))
    # First-Fit Decreasing por altura
    items.sort(key=lambda it: it[4], reverse=True)

    placements: list[Placement] = []
    shelf_y = 0.0
    shelf_x = 0.0
    shelf_h = 0.0
    for piece, k, mirror, w, h, loc in items:
        if shelf_x + w > fabric_width and shelf_x > 0:
            # nuevo estante
            shelf_y += shelf_h + gap
            shelf_x = 0.0
            shelf_h = 0.0
        placements.append(Placement(piece, k, shelf_x, shelf_y, w, h, mirror))
        shelf_x += w + gap
        shelf_h = max(shelf_h, h)
    total_length = shelf_y + shelf_h
    return placements, total_length


def _column_profile(contour, step):
    """Perfil superior e inferior por columna de un contorno (min-corner en 0,0).

    Devuelve (profile, ncol) donde profile[j] = (top_y, bot_y) para la columna j
    (x en [j*step, (j+1)*step]); columnas que la pieza no ocupa se omiten. Es la
    forma real de la pieza usada para el nesting por skyline (encaje de contornos).
    """
    xs = [p[0] for p in contour]
    w = max(xs)
    ncol = max(1, int(math.ceil(w / step)))
    n = len(contour)
    profile = {}
    for j in range(ncol):
        xc = (j + 0.5) * step
        ys = []
        for i in range(n):
            x0, y0 = contour[i]
            x1, y1 = contour[(i + 1) % n]
            if (x0 - xc) * (x1 - xc) <= 0 and abs(x1 - x0) > 1e-12:
                t = (xc - x0) / (x1 - x0)
                ys.append(y0 + t * (y1 - y0))
        if ys:
            profile[j] = (min(ys), max(ys))
    return profile, ncol


def _flip180(contour, w, h):
    return [(w - x, h - y) for x, y in contour]


def nest_skyline(shirt, fabric_width: float, gap: float = 1.0,
                 step: float = 1.5) -> tuple[list[Placement], float]:
    """Nesting por **skyline con perfil de contorno** (encaje real de piezas) y
    rotación 180° (respeta la línea de hilo). Las piezas se dejan caer sobre la
    silueta ya colocada, encajando en sus concavidades — como un marker real.
    """
    import math as _m
    instances = []
    for piece in shirt.pieces:
        for k, (mirror, w, h, loc) in enumerate(_cut_instances(piece)):
            instances.append([piece, k, mirror, w, h, loc])
    instances.sort(key=lambda it: it[3] * it[4], reverse=True)  # área bbox desc

    ncol_total = int(_m.ceil(fabric_width / step)) + 2
    skyline = [0.0] * ncol_total
    placements: list[Placement] = []

    for piece, k, mirror, w, h, loc in instances:
        best = None  # (place_y, c0, flip, prof, pw_cols, w, h, contour)
        for flip in (False, True):
            contour = _flip180(loc, w, h) if flip else loc
            prof, pcols = _column_profile(contour, step)
            if not prof:
                continue
            max_c0 = int((fabric_width - w) / step)
            for c0 in range(0, max(1, max_c0 + 1)):
                place_y = 0.0
                ok = True
                for j, (top, bot) in prof.items():
                    gc = c0 + j
                    if gc >= ncol_total:
                        ok = False
                        break
                    place_y = max(place_y, skyline[gc] - top)
                if not ok:
                    continue
                cand = (place_y, c0, flip, prof, w, h, contour)
                if best is None or place_y < best[0] - 1e-6:
                    best = cand
        if best is None:
            continue
        place_y, c0, flip, prof, w, h, contour = best
        for j, (top, bot) in prof.items():
            skyline[c0 + j] = place_y + bot + gap
        placements.append(Placement(piece, k, c0 * step, place_y, w, h, mirror or flip))
        placements[-1].contour = contour  # guarda la orientación usada
    total_length = max(skyline) - gap if skyline else 0.0
    return placements, total_length


def marker_report(shirt, widths=(110.0, 150.0, 160.0), gap: float = 1.0) -> dict:
    """Consumo y desperdicio por ancho de tela."""
    # área real de piezas de tela
    used_area = 0.0
    for piece in shirt.pieces:
        for mirror, w, h, loc in _cut_instances(piece):
            from shapely.geometry import Polygon
            used_area += Polygon(loc).area
    report = {"area_piezas_cm2": round(used_area, 1), "por_ancho": {}}
    for W in widths:
        placements, length = nest_skyline(shirt, W, gap=gap)
        fabric_area = W * length
        eff = used_area / fabric_area if fabric_area else 0.0
        report["por_ancho"][W] = {
            "ancho_cm": W,
            "largo_cm": round(length, 1),
            "largo_m": round(length / 100.0, 3),
            "area_tela_cm2": round(fabric_area, 1),
            "eficiencia": round(eff, 4),
            "desperdicio": round(1 - eff, 4),
            "n_piezas": len(placements),
        }
    return report


def export_marker_svg(shirt, fabric_width: float, path: str, gap: float = 1.0) -> str:
    """Dibuja el plano de corte para un ancho de tela (contornos reales)."""
    import svgwrite
    placements, length = nest_skyline(shirt, fabric_width, gap=gap)
    margin = 4.0
    w = fabric_width + 2 * margin
    h = length + 2 * margin
    dwg = svgwrite.Drawing(path, size=(f"{w}cm", f"{h}cm"), viewBox=f"0 0 {w} {h}")
    # borde de la tela
    dwg.add(dwg.rect(insert=(margin, margin), size=(fabric_width, length),
                     fill="#f7f3ea", stroke="#333", stroke_width=0.15))
    dwg.add(dwg.text(f"PLANO DE CORTE — ancho {fabric_width:.0f} cm — largo "
                     f"{length/100:.2f} m", insert=(margin, margin - 1.0),
                     font_size=1.4, font_family="sans-serif", fill="#000"))
    for pl in placements:
        contour = pl.contour if pl.contour is not None else _cut_instances(pl.piece)[0][3]
        pts = [(margin + pl.x + x, margin + pl.y + y) for x, y in contour]
        dwg.add(dwg.polygon(points=pts, fill="#cfe3f7", fill_opacity=0.5,
                            stroke="#1f6fb2", stroke_width=0.1))
        cx = margin + pl.x + pl.w / 2
        cy = margin + pl.y + pl.h / 2
        dwg.add(dwg.text(f"{pl.piece.number:02d}", insert=(cx, cy),
                         font_size=1.6, text_anchor="middle",
                         font_family="sans-serif", fill="#0a3d62"))
    dwg.save()
    return path
