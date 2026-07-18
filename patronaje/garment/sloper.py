"""Bloque base entallado (sloper) como prenda: delantero y espalda con pinzas
y equilibrio, más la manga. Sirve de base para patrones ajustados y para la
manipulación de pinzas (traslados, princesa real).

Reutiliza el trazo de escote/sisa del método elegido y el bloque entallado
(`blocks/fitted.py`), y se ensambla en objetos :class:`~patronaje.piece.Piece`
con sus pinzas, de modo que valida y exporta igual que la camisa.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..parametric.parameters import Parameters
from ..parametric.measurements import build_parameters
from ..blocks.registry import get_method
from ..blocks.fitted import build_fitted, FittedBodice
from ..piece import Piece


@dataclass
class Sloper:
    p: Parameters
    method: str = "aldrich"
    bust_dart_pos: str = "side"
    fitted: FittedBodice = None
    sleeve = None
    pieces: list = field(default_factory=list)

    def build(self) -> "Sloper":
        m = get_method(self.method)
        size = self.p._base["talla_nombre"].descripcion.replace("talla ", "")
        self.fitted = build_fitted(m, self.p, bust_dart_pos=self.bust_dart_pos)
        self.sleeve = m.build_sleeve(self.p, self.fitted.draft.armhole_length(), 1.0)
        bp = self.fitted.bust_point

        front = Piece(
            name="DELANTERO (base entallada)", number=1, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.fitted.front, seam_allowance=self.p.margen_costura,
            grain=((self.p.cuarto_busto * 0.5, self.p.escote_del_prof + 3),
                   (self.p.cuarto_busto * 0.5, self.fitted.draft.points["D-US"].y + 18)),
            darts=self.fitted.front_darts, drills=[bp],
            reference_texts=[((bp[0] + 0.6, bp[1] + 0.4), "BP")],
        )
        back = Piece(
            name="ESPALDA (base entallada)", number=2, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=self.fitted.back, seam_allowance=self.p.margen_costura,
            grain=((1.0, 3), (1.0, self.fitted.draft.points["E-US"].y + 18)),
            darts=self.fitted.back_darts,
        )
        sleeve = Piece(
            name="MANGA", number=3, size=size, quantity=2, cut_type="par",
            net_contour=self.sleeve.outline(), seam_allowance=self.p.margen_costura,
            hem_allowance=self.p.margen_dobladillo,   # muñeca con dobladillo simple
            grain=((0.0, self.sleeve.cap_height * 0.4), (0.0, self.p.largo_manga - 2)),
        )
        self.pieces = [front, back, sleeve]
        return self

    @property
    def bodice(self):
        """Alias del trazo base (para exportadores que esperan .bodice)."""
        return self.fitted.draft

    def layout(self, gap: float = 6.0) -> "Sloper":
        x = 0.0
        for pc in self.pieces:
            minx, miny, maxx, maxy = pc.bbox()
            pc.offset = (x - minx, -miny)
            x += (maxx - minx) + gap
        return self


def build_sloper(size: str = "S", method: str = "aldrich",
                 bust_dart_pos: str = "side") -> Sloper:
    return Sloper(p=build_parameters(size), method=method,
                 bust_dart_pos=bust_dart_pos).build()
