"""Ensamble de la falda base (recta / lápiz) en piezas de patrón.

Toma el bloque de falda (:mod:`patronaje.blocks.skirt`) y construye las piezas
como objetos :class:`~patronaje.piece.Piece`, con pinzas, línea de hilo, doblez
y márgenes por borde (dobladillo real en el bajo). Se ensambla igual que las
demás prendas, de modo que valida y exporta con el mismo motor.

Piezas: Falda delantera (al doblez), Falda trasera (al doblez) y Pretina.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..parametric.parameters import Parameters
from ..parametric.measurements import build_parameters
from ..blocks.skirt import build_skirt_block, SkirtDraft
from ..piece import Piece
from .pieces.simple_shapes import rounded_rect


@dataclass
class Skirt:
    p: Parameters
    method: str = "aldrich"
    prenda: str = "falda_base_recta"
    block: SkirtDraft = None
    pieces: list = field(default_factory=list)
    seam_matching: list = field(default_factory=list)
    # atributos que algunos exportadores consultan de forma genérica
    bodice = None
    sleeve = None

    def build(self) -> "Skirt":
        p = self.p
        size = p._base["talla_nombre"].descripcion.replace("talla ", "")
        self.block = build_skirt_block(p)
        hip_y, hem_y = self.block.hip_y, self.block.hem_y

        front = Piece(
            name="FALDA DELANTERA", number=1, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.block.front, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo,
            grain=((p.cuarto_cadera * 0.5, 3), (p.cuarto_cadera * 0.5, hem_y - 3)),
            darts=self.block.front_darts,
            reference_texts=[((0.4, hem_y * 0.5), "CF")],
        )
        back = Piece(
            name="FALDA TRASERA", number=2, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.block.back, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo,
            grain=((p.cuarto_cadera * 0.5, 3), (p.cuarto_cadera * 0.5, hem_y - 3)),
            darts=self.block.back_darts,
            # piquete de cadera (casa el costado delantero con el trasero)
            notches=[(p.cuarto_cadera, hip_y)],
            reference_texts=[((0.4, hem_y * 0.5), "CB")],
        )
        # pretina (waistband): cintura + holgura + solapa de cierre; se dobla a la mitad
        wlen = self.block.waist_length() + 3.0
        wh = 2.0 * p.ancho_pretina
        band = Piece(
            name="PRETINA", number=3, size=size, quantity=1,
            cut_type="1 (+ entretela)", on_fold=False,
            net_contour=rounded_rect(wlen, wh, radius=0.6),
            seam_allowance=p.margen_costura,
            grain=((1.0, wh * 0.5), (wlen - 1.0, wh * 0.5)),
            buttons=[(wlen - 1.5, wh * 0.5)],
            buttonholes=[(1.5, wh * 0.5, 0.0, 1.6)],
            construction_lines=[((0, wh / 2), (wlen, wh / 2))],  # línea de doblez
            reference_texts=[((wlen / 2, wh / 2 - 0.7), "DOBLEZ")],
        )
        self.pieces = [front, back, band]
        # casado automático de piquetes (costado delantero↔trasero)
        from .notches import add_skirt_notches
        self.seam_matching = add_skirt_notches(self)
        return self

    def layout(self, gap: float = 6.0) -> "Skirt":
        x = 0.0
        for pc in self.pieces:
            minx, miny, maxx, maxy = pc.bbox()
            pc.offset = (x - minx, -miny)
            x += (maxx - minx) + gap
        return self


def build_skirt(size: str = "S", method: str = "aldrich", p: Parameters = None) -> Skirt:
    return Skirt(p=p if p is not None else build_parameters(size), method=method).build()
