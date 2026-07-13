"""Plano de corte (marker / trazo de corte) y cálculo de consumo.

Coloca todas las piezas a cortar sobre un ancho de tela dado (110/150/160 cm) y
calcula la **longitud de tela** necesaria y el **desperdicio**. El nesting
respeta la **línea de hilo** (no se rotan las piezas 90°, sólo se colocan en su
orientación de corte), como en un marker industrial real.

Algoritmo: empaquetado por estantes (First-Fit Decreasing por altura) usando el
*bounding box* de la línea de corte de cada instancia. Es una aproximación
honesta y conservadora: el nesting de contornos irregulares de un sistema CAM
reduce aún más el desperdicio, pero el bbox da un consumo de tela con el que se
puede comprar material sin quedarse corto.

Se reportan dos métricas:
* **eficiencia de tela** = área real de las piezas / (ancho × largo de tela).
* **desperdicio** = 1 − eficiencia.
"""
from __future__ import annotations

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
        placements, length = nest(shirt, W, gap=gap)
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
    placements, length = nest(shirt, fabric_width, gap=gap)
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
        loc = _cut_instances(pl.piece)  # reobtener contorno de la instancia
        # localizar el contorno correcto según ancho/alto
        contour = None
        for mirror, iw, ih, l in loc:
            if abs(iw - pl.w) < 1e-6 and abs(ih - pl.h) < 1e-6:
                contour = l
                break
        if contour is None:
            contour = loc[0][3]
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
