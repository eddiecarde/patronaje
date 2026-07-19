"""Ensamble del vestido base (con costura de talle).

El vestido reutiliza dos bloques ya existentes y los une en la **línea de talle**:

* el **cuerpo entallado** (`blocks/fitted`) — con pinza de busto (reubicable),
  pinzas de cintura y de hombro, y **por cada método de patronaje** (Aldrich,
  Müller, Bunka, ESMOD, Martí, Armstrong);
* la **falda** (`blocks/skirt`) — dos paneles con pinza y curva de cadera.

Ambas cinturas valen un cuarto de cintura, así que casan en la costura de talle.
Se añade la manga del método (opcional). Piezas: cuerpo delantero/espalda, falda
delantera/trasera y manga. El casado de piquetes une talle↔falda.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..parametric.parameters import Parameters
from ..parametric.measurements import build_parameters
from ..blocks.registry import get_method
from ..blocks.fitted import build_fitted, FittedBodice
from ..blocks.skirt import build_skirt_block, SkirtDraft
from ..piece import Piece


@dataclass
class Dress:
    p: Parameters
    method: str = "aldrich"
    bust_dart_pos: str = "side"
    sleeve_on: bool = True
    prenda: str = "vestido_base"
    fitted: FittedBodice = None
    skirt: SkirtDraft = None
    sleeve = None
    pieces: list = field(default_factory=list)
    seam_matching: list = field(default_factory=list)
    bodice = None

    def build(self) -> "Dress":
        p = self.p
        m = get_method(self.method)
        size = p._base["talla_nombre"].descripcion.replace("talla ", "")
        self.fitted = build_fitted(m, p, bust_dart_pos=self.bust_dart_pos)
        self.skirt = build_skirt_block(p)
        self.bodice = self.fitted.draft
        bp = self.fitted.bust_point
        usy = self.fitted.draft.points["D-US"].y

        bodF = Piece(
            name="VESTIDO DELANTERO (talle)", number=1, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.fitted.front, seam_allowance=p.margen_costura,
            grain=((p.cuarto_busto * 0.5, p.escote_del_prof + 3), (p.cuarto_busto * 0.5, usy + 15)),
            darts=self.fitted.front_darts, drills=[bp],
            reference_texts=[((bp[0] + 0.6, bp[1] + 0.4), "BP")],
        )
        bodB = Piece(
            name="VESTIDO ESPALDA (talle)", number=2, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.fitted.back, seam_allowance=p.margen_costura,
            grain=((1.0, 3), (1.0, usy + 15)), darts=self.fitted.back_darts,
        )
        hemY = self.skirt.hem_y
        skF = Piece(
            name="VESTIDO FALDA DELANTERA", number=3, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.skirt.front, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo, darts=self.skirt.front_darts,
            grain=((p.cuarto_cadera * 0.5, 3), (p.cuarto_cadera * 0.5, hemY - 3)),
        )
        skB = Piece(
            name="VESTIDO FALDA TRASERA", number=4, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.skirt.back, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo, darts=self.skirt.back_darts,
            grain=((p.cuarto_cadera * 0.5, 3), (p.cuarto_cadera * 0.5, hemY - 3)),
        )
        self.pieces = [bodF, bodB, skF, skB]
        if self.sleeve_on:
            self.sleeve = m.build_sleeve(p, self.fitted.draft.armhole_length(), 1.0)
            self.pieces.append(Piece(
                name="MANGA", number=5, size=size, quantity=2, cut_type="par",
                net_contour=self.sleeve.outline(), seam_allowance=p.margen_costura,
                hem_allowance=p.margen_dobladillo,
                grain=((0.0, self.sleeve.cap_height * 0.4), (0.0, p.largo_manga - 2))))

        from .notches import add_dress_notches
        self.seam_matching = add_dress_notches(self)
        return self

    def layout(self, gap: float = 6.0) -> "Dress":
        x = 0.0
        for pc in self.pieces:
            minx, miny, maxx, maxy = pc.bbox()
            pc.offset = (x - minx, -miny)
            x += (maxx - minx) + gap
        return self


def build_dress(size: str = "S", method: str = "aldrich", bust_dart_pos: str = "side",
                sleeve_on: bool = True, p: Parameters = None) -> Dress:
    return Dress(p=p if p is not None else build_parameters(size), method=method,
                 bust_dart_pos=bust_dart_pos, sleeve_on=sleeve_on).build()
