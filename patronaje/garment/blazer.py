"""Ensamble de la chaqueta/blazer en piezas de patrón.

Reúne el cuerpo con solapa, la **manga de dos piezas** (mangón + soplillo), el
cuello sastre, la vista y el forro (delantero y espalda), por **método** de
patronaje. Casa el costado y las costuras de la manga.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..parametric.parameters import Parameters
from ..parametric.measurements import build_parameters
from ..blocks.registry import get_method
from ..blocks.blazer import build_jacket_body, build_two_piece_sleeve, JacketBody, TwoPieceSleeve
from ..piece import Piece


@dataclass
class Blazer:
    p: Parameters
    method: str = "aldrich"
    prenda: str = "chaqueta_blazer"
    lining: bool = True
    body: JacketBody = None
    sleeve: TwoPieceSleeve = None
    bodice = None
    pieces: list = field(default_factory=list)
    seam_matching: list = field(default_factory=list)

    def build(self) -> "Blazer":
        p = self.p
        m = get_method(self.method)
        size = p._base["talla_nombre"].descripcion.replace("talla ", "")
        self.body = build_jacket_body(m, p)
        self.bodice = self.body  # exportadores genéricos
        arm = m.build_bodice(p).armhole_length()
        self.sleeve = build_two_piece_sleeve(p, arm)
        b, s = self.body, self.sleeve
        hemA = p.margen_dobladillo

        F = Piece(name="CHAQUETA DELANTERO", number=1, size=size, quantity=2,
                  cut_type="par: izq + der", net_contour=b.front,
                  seam_allowance=p.margen_costura, hem_allowance=hemA,
                  darts=b.front_darts, buttons=b.buttons,
                  construction_lines=[b.roll_line] if b.roll_line else [],
                  grain=((p.cuarto_busto * 0.5, b.waist_y - 10), (p.cuarto_busto * 0.5, b.hem_y - 3)),
                  reference_texts=[((b.bust_point[0], b.bust_point[1]), "línea de quiebre")])
        B = Piece(name="CHAQUETA ESPALDA", number=2, size=size, quantity=1,
                  cut_type="al doblez", on_fold=True, fold_x=0.0, net_contour=b.back,
                  seam_allowance=p.margen_costura, hem_allowance=hemA, darts=b.back_darts,
                  grain=((1.0, 3), (1.0, b.hem_y - 3)))
        MS = Piece(name="MANGA SUPERIOR", number=3, size=size, quantity=2, cut_type="par (mangón)",
                   net_contour=s.top, seam_allowance=p.margen_costura, hem_allowance=hemA,
                   grain=((0.0, s.biceps_y + 4), (0.0, s.wrist_y - 3)))
        MI = Piece(name="MANGA INFERIOR", number=4, size=size, quantity=2, cut_type="par (soplillo)",
                   net_contour=s.under, seam_allowance=p.margen_costura, hem_allowance=hemA,
                   grain=((0.0, s.biceps_y + 4), (0.0, s.wrist_y - 3)))
        CO = Piece(name="CUELLO SASTRE", number=5, size=size, quantity=2, cut_type="par (+ entretela)",
                   net_contour=b.collar, seam_allowance=p.margen_costura)
        VI = Piece(name="VISTA DELANTERA", number=6, size=size, quantity=2, cut_type="par: izq + der",
                   net_contour=b.facing, seam_allowance=p.margen_costura, hem_allowance=hemA)
        self.pieces = [F, B, MS, MI, CO, VI]
        if self.lining:
            self.pieces.append(Piece(name="FORRO DELANTERO", number=7, size=size, quantity=2,
                               cut_type="par: izq + der (forro)", net_contour=b.lining_front,
                               seam_allowance=p.margen_costura, hem_allowance=hemA))
            self.pieces.append(Piece(name="FORRO ESPALDA", number=8, size=size, quantity=1,
                               cut_type="al doblez (forro)", on_fold=True, fold_x=0.0,
                               net_contour=b.lining_back, seam_allowance=p.margen_costura,
                               hem_allowance=hemA,
                               construction_lines=[((0.0, b.waist_y - 20), (0.0, b.hem_y))],
                               reference_texts=[((1.5, b.waist_y), "pliegue holgura")]))

        from .notches import add_blazer_notches
        self.seam_matching = add_blazer_notches(self)
        return self

    def layout(self, gap: float = 6.0) -> "Blazer":
        x = 0.0
        for pc in self.pieces:
            minx, miny, maxx, maxy = pc.bbox()
            pc.offset = (x - minx, -miny)
            x += (maxx - minx) + gap
        return self


def build_blazer(size: str = "S", method: str = "aldrich", lining: bool = True,
                 p: Parameters = None) -> Blazer:
    return Blazer(p=p if p is not None else build_parameters(size), method=method,
                  lining=lining).build()
