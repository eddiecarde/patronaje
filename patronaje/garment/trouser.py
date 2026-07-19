"""Ensamble del pantalón base (mujer) en piezas de patrón.

Toma el bloque de pantalón (:mod:`patronaje.blocks.trouser`) y construye las
piezas como objetos :class:`~patronaje.piece.Piece`, con pinzas, línea de hilo
(por la raya), dobladillo real en la boca y casado de piquetes en entrepierna y
costado. Se ensambla igual que las demás prendas: valida y exporta con el mismo
motor.

Piezas: Pantalón delantero, Pantalón trasero (par: izq + der) y Pretina.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..parametric.parameters import Parameters
from ..parametric.measurements import build_parameters
from ..blocks.trouser import build_trouser_block, TrouserDraft
from ..piece import Piece
from .pieces.simple_shapes import rounded_rect


@dataclass
class Trouser:
    p: Parameters
    method: str = "aldrich"
    prenda: str = "pantalon_base"
    block: TrouserDraft = None
    pieces: list = field(default_factory=list)
    seam_matching: list = field(default_factory=list)
    bodice = None
    sleeve = None

    def build(self) -> "Trouser":
        p = self.p
        size = p._base["talla_nombre"].descripcion.replace("talla ", "")
        self.block = build_trouser_block(p)
        b = self.block

        def crease_x(contour):
            # x del eje: media de la boca de pierna
            hem_pts = [x for x, y in contour if abs(y - b.hem_y) < 0.5]
            return sum(hem_pts) / len(hem_pts) if hem_pts else 0.0

        fx = crease_x(b.front)
        front = Piece(
            name="PANTALON DELANTERO", number=1, size=size, quantity=2,
            cut_type="par: izq + der", on_fold=False,
            net_contour=b.front, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo,
            grain=((fx, b.hip_y + 2), (fx, b.hem_y - 3)),
            darts=b.front_darts,
            construction_lines=[((fx, b.crotch_y), (fx, b.hem_y))],  # raya
        )
        bx = crease_x(b.back)
        back = Piece(
            name="PANTALON TRASERO", number=2, size=size, quantity=2,
            cut_type="par: izq + der", on_fold=False,
            net_contour=b.back, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo,
            grain=((bx, b.hip_y + 2), (bx, b.hem_y - 3)),
            darts=b.back_darts,
            construction_lines=[((bx, b.crotch_y), (bx, b.hem_y))],
        )
        wlen = b.waist_length() + 3.0
        wh = 2.0 * p.ancho_pretina
        band = Piece(
            name="PRETINA", number=3, size=size, quantity=1,
            cut_type="1 (+ entretela)", on_fold=False,
            net_contour=rounded_rect(wlen, wh, radius=0.6),
            seam_allowance=p.margen_costura,
            grain=((1.0, wh * 0.5), (wlen - 1.0, wh * 0.5)),
            buttons=[(wlen - 1.5, wh * 0.5)],
            buttonholes=[(1.5, wh * 0.5, 0.0, 1.6)],
            construction_lines=[((0, wh / 2), (wlen, wh / 2))],
            reference_texts=[((wlen / 2, wh / 2 - 0.7), "DOBLEZ")],
        )
        self.pieces = [front, back, band]
        from .notches import add_trouser_notches
        self.seam_matching = add_trouser_notches(self)
        return self

    def layout(self, gap: float = 6.0) -> "Trouser":
        x = 0.0
        for pc in self.pieces:
            minx, miny, maxx, maxy = pc.bbox()
            pc.offset = (x - minx, -miny)
            x += (maxx - minx) + gap
        return self


def build_trouser(size: str = "S", method: str = "aldrich", p: Parameters = None) -> Trouser:
    return Trouser(p=p if p is not None else build_parameters(size), method=method).build()
