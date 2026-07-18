"""Ensamble de la camisa básica femenina de manga larga (método Aldrich).

Toma los bloques de cuerpo y manga y construye las 10 piezas de patrón como
objetos :class:`patronaje.piece.Piece`, con toda su metadata (nombre, número,
talla, cantidad, tipo de corte, "al doblez"), líneas de hilo, piquetes,
perforaciones, botones, ojales y textos de referencia.

El método :meth:`Shirt.build` es idempotente y depende sólo de los parámetros,
de modo que ``Shirt(build_parameters('M')).build()`` regenera todo para otra
talla (motor paramétrico).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..parametric.parameters import Parameters
from ..parametric.measurements import build_parameters
from ..blocks.aldrich_bodice import BodiceDraft
from ..blocks.aldrich_sleeve import SleeveDraft
from ..blocks.registry import get_method
from ..core.point import polyline_length
from ..piece import Piece
from .pieces.simple_shapes import rounded_rect, arc_band, collar_with_point


def _point_at_arclen(poly, s: float):
    """Punto sobre una polilínea a distancia de arco ``s`` desde el inicio."""
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        if acc + d >= s:
            t = (s - acc) / d if d else 0
            return (x0 + t * (x1 - x0), y0 + t * (y1 - y0))
        acc += d
    return poly[-1]


@dataclass
class Shirt:
    p: Parameters
    bodice: BodiceDraft = None
    sleeve: SleeveDraft = None
    pieces: list[Piece] = field(default_factory=list)
    sleeve_ease: float = 1.0
    method: str = "aldrich"

    # ------------------------------------------------------------------
    def build(self) -> "Shirt":
        p = self.p
        size = p._base["talla_nombre"].descripcion.replace("talla ", "")
        m = get_method(self.method)
        missing = m.check_measurements(p)
        if missing:
            raise ValueError(f"Faltan medidas para el método {m.label}: {missing}")
        self.bodice = m.build_bodice(p)
        self.sleeve = m.build_sleeve(p, self.bodice.armhole_length(), self.sleeve_ease)
        self.pieces = [
            self._front(size),
            self._back(size),
            self._yoke(size),
            self._sleeve_piece(size),
            self._cuff(size),
            self._sleeve_placket(size),
            self._collar(size),
            self._collar_stand(size),
            self._front_facing(size),
            self._pocket(size),
        ]
        return self

    # ------------------------------------------------------------------
    # 01 Delantero
    # ------------------------------------------------------------------
    def _front(self, size) -> Piece:
        p = self.p
        b = self.bodice
        ext = p.extension_boton
        fnd = p.escote_del_prof
        largo = p.largo_camisa
        cuarto = p.cuarto_busto
        # contorno (con extensión de botonadura a la izquierda de CF, x<0)
        contour: list[tuple[float, float]] = []
        contour.append((-ext, fnd))                       # 1 banda arriba (nivel escote)
        contour.append((0.0, fnd))                        # 2 CF en escote
        contour += list(reversed(b.front_neck))[1:]       # escote CF -> SNP
        contour.append(b.points["D-SP"].as_tuple())       # hombro
        contour += b.front_armhole[1:]                    # sisa SP -> axila
        contour.append(b.points["D-Hs"].as_tuple())       # costado a dobladillo
        contour.append((-ext, largo))                     # dobladillo incl. banda
        # cierra subiendo por la banda a (-ext, fnd)
        # línea de hilo (paralela a CF)
        grain = ((cuarto * 0.5, fnd + 3), (cuarto * 0.5, largo - 3))
        # botones y ojales sobre CF (x=0)
        n_but = 7
        y0, y1 = fnd + 1.5, largo - 6.0
        buttons = [(0.0, y0 + (y1 - y0) * i / (n_but - 1)) for i in range(n_but)]
        buttonholes = [(0.0, by, 0.0, 1.6) for (_bx, by) in buttons]   # ojales horizontales
        # piquetes: sisa delantera (single) y costado en cintura
        arm_notch = _point_at_arclen(b.front_armhole, b.front_armhole_length() * 0.35)
        waist_y = p.prof_sisa + (largo - p.prof_sisa) * 0.45
        notches = [arm_notch, (cuarto, waist_y)]
        # perforación: posición de bolsillo (referencia)
        drills = [(cuarto * 0.55, p.prof_sisa + 3.0)]
        return Piece(
            name="DELANTERO", number=1, size=size, quantity=2,
            cut_type="par: izq + der", on_fold=False,
            net_contour=contour, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo,
            grain=grain, notches=notches, drills=drills,
            buttons=buttons, buttonholes=buttonholes,
            construction_lines=[((0.0, fnd), (0.0, largo))],  # línea CF (centro)
            reference_texts=[((0.0, fnd - 1.0), "CF")],
        )

    # ------------------------------------------------------------------
    # 02 Espalda
    # ------------------------------------------------------------------
    def _back(self, size) -> Piece:
        p = self.p
        b = self.bodice
        contour = b.back_lower_outline()
        yl = b.yoke_line_y
        arm_x = contour[1][0]
        grain = ((0.5, yl + 3), (0.5, p.largo_camisa - 3))
        # piquete de casado con canesú en la línea de canesú
        notches = [(arm_x * 0.5, yl)]
        return Piece(
            name="ESPALDA", number=2, size=size, quantity=1,
            cut_type="al doblez", on_fold=True, fold_x=0.0,
            net_contour=contour, seam_allowance=p.margen_costura,
            hem_allowance=p.margen_dobladillo,
            grain=grain, notches=notches,
            reference_texts=[((0.3, (yl + p.largo_camisa) / 2), "CB")],
        )

    # ------------------------------------------------------------------
    # 03 Canesú
    # ------------------------------------------------------------------
    def _yoke(self, size) -> Piece:
        p = self.p
        b = self.bodice
        contour = b.yoke_outline()
        yl = b.yoke_line_y
        # piquete de casado con espalda
        arm_x = None
        for x, y in contour:
            if abs(y - yl) < 1e-6 and x > 0.01:
                arm_x = x
                break
        notches = [(arm_x * 0.5, yl)] if arm_x else []
        grain = ((p.escote_esp_ancho * 0.6, 1.0), (p.escote_esp_ancho * 0.6, yl - 0.5))
        return Piece(
            name="CANESU", number=3, size=size, quantity=2,
            cut_type="al doblez x2 (exterior+interior)", on_fold=True, fold_x=0.0,
            net_contour=contour, seam_allowance=p.margen_costura,
            grain=grain, notches=notches,
        )

    # ------------------------------------------------------------------
    # 04 Manga
    # ------------------------------------------------------------------
    def _sleeve_piece(self, size) -> Piece:
        p = self.p
        s = self.sleeve
        contour = s.outline()
        bh = s.biceps_half
        h = s.cap_height
        largo = p.largo_manga_efec
        grain = ((0.0, h * 0.4), (0.0, largo - 2))
        # piquetes de copa: front (single) y back (double)
        cap = s.cap_curve
        Lcap = polyline_length(cap)
        # el punto medio de cap es SH (0,0); front = mitad derecha, back = izquierda
        front_notch = _point_at_arclen(cap, Lcap * 0.72)   # hacia bíceps delantero
        back_notch = _point_at_arclen(cap, Lcap * 0.28)     # hacia bíceps trasero
        back_notch2 = _point_at_arclen(cap, Lcap * 0.24)
        notches = [front_notch, back_notch, back_notch2]
        # perforación: extremo de abertura de manga (placket) cerca de muñeca
        opening = (bh * 0.25, largo - 12.0)
        drills = [opening]
        return Piece(
            name="MANGA", number=4, size=size, quantity=2,
            cut_type="par: izq + der", on_fold=False,
            net_contour=contour, seam_allowance=p.margen_costura,
            grain=grain, notches=notches, drills=drills,
            construction_lines=[((bh * 0.25, largo), (bh * 0.25, largo - 12.0))],  # abertura
        )

    # ------------------------------------------------------------------
    # 05 Puño
    # ------------------------------------------------------------------
    def _cuff(self, size) -> Piece:
        p = self.p
        length = p.largo_puno + 2.0        # + solapa de botón
        height = 2 * p.ancho_puno          # se dobla a la mitad
        contour = rounded_rect(length, height, radius=0.8)
        grain = ((length * 0.5, 0.5), (length * 0.5, height - 0.5))
        # botón y ojal en los extremos
        buttons = [(1.2, height * 0.5)]
        buttonholes = [(length - 1.2, height * 0.5, math.pi / 2, 1.6)]
        return Piece(
            name="PUNO", number=5, size=size, quantity=4,
            cut_type="4 (2 tela + 2 entretela)", on_fold=False,
            net_contour=contour, seam_allowance=p.margen_costura,
            grain=grain, buttons=buttons, buttonholes=buttonholes,
            construction_lines=[((0, height / 2), (length, height / 2))],  # línea de doblez
            reference_texts=[((length / 2, height / 2 - 0.8), "DOBLEZ")],
        )

    # ------------------------------------------------------------------
    # 06 Tapeta (sleeve placket)
    # ------------------------------------------------------------------
    def _sleeve_placket(self, size) -> Piece:
        p = self.p
        length, height = 12.0, 3.0
        contour = rounded_rect(length, height, radius=0.4)
        grain = ((length * 0.5, 0.4), (length * 0.5, height - 0.4))
        return Piece(
            name="TAPETA MANGA", number=6, size=size, quantity=2,
            cut_type="par", on_fold=False,
            net_contour=contour, seam_allowance=p.margen_costura, grain=grain,
        )

    # ------------------------------------------------------------------
    # 07 Cuello
    # ------------------------------------------------------------------
    def _collar(self, size) -> Piece:
        p = self.p
        half_neck = self.bodice.neckline_length()   # mitad de escote (doblez en CB)
        contour = collar_with_point(half_neck, height=4.5, rise=1.0, point_drop=2.0)
        grain = ((0.5, 0.5), (half_neck - 0.5, 0.5))
        return Piece(
            name="CUELLO", number=7, size=size, quantity=2,
            cut_type="al doblez x2 (+ entretela)", on_fold=True, fold_x=0.0,
            net_contour=contour, seam_allowance=p.margen_costura, grain=grain,
        )

    # ------------------------------------------------------------------
    # 08 Pie de cuello
    # ------------------------------------------------------------------
    def _collar_stand(self, size) -> Piece:
        p = self.p
        half_neck = self.bodice.neckline_length()
        ext = p.extension_boton
        contour = arc_band(half_neck + ext, height=3.0, rise=0.8)
        grain = ((0.5, 0.4), (half_neck + ext - 0.5, 0.4))
        # botón/ojal del pie de cuello
        buttons = [(half_neck + ext - 1.0, 1.5)]
        return Piece(
            name="PIE DE CUELLO", number=8, size=size, quantity=2,
            cut_type="al doblez x2 (+ entretela)", on_fold=True, fold_x=0.0,
            net_contour=contour, seam_allowance=p.margen_costura,
            grain=grain, buttons=buttons,
        )

    # ------------------------------------------------------------------
    # 09 Vista delantera (facing)
    # ------------------------------------------------------------------
    def _front_facing(self, size) -> Piece:
        p = self.p
        b = self.bodice
        ext = p.extension_boton
        fnd = p.escote_del_prof
        largo = p.largo_camisa
        w = 6.0  # ancho de vista
        # sigue el escote y el borde de la banda, con ancho interior w
        neck = list(reversed(b.front_neck))               # CFn -> SNP
        snp = b.points["D-SNP"].as_tuple()
        contour: list[tuple[float, float]] = []
        contour.append((-ext, fnd))
        contour.append((0.0, fnd))
        contour += neck[1:]                                # escote a SNP
        contour.append((snp[0] + 1.0, snp[1] + 0.5))       # pequeño ancho en hombro
        # borde interior de la vista (paralelo aprox.) bajando hasta el dobladillo
        contour.append((max(0.0, snp[0] - w + 3.0), fnd + 3.0))
        contour.append((-ext + w, largo))
        contour.append((-ext, largo))
        grain = ((-ext + w * 0.5, fnd + 5), (-ext + w * 0.5, largo - 3))
        return Piece(
            name="VISTA DELANTERA", number=9, size=size, quantity=2,
            cut_type="par: izq + der", on_fold=False,
            net_contour=contour, seam_allowance=p.margen_costura, grain=grain,
        )

    # ------------------------------------------------------------------
    # 10 Bolsillo (opcional)
    # ------------------------------------------------------------------
    def _pocket(self, size) -> Piece:
        p = self.p
        w, hgt = p.ancho_bolsillo, p.prof_bolsillo
        # rectángulo con punta inferior (bolsillo de parche clásico)
        contour = [
            (0.0, 0.0), (w, 0.0), (w, hgt * 0.72),
            (w / 2, hgt), (0.0, hgt * 0.72),
        ]
        grain = ((w / 2, 1.0), (w / 2, hgt * 0.72))
        return Piece(
            name="BOLSILLO", number=10, size=size, quantity=1,
            cut_type="1 (opcional)", on_fold=False,
            net_contour=contour, seam_allowance=p.margen_costura, grain=grain,
            construction_lines=[((0, hgt * 0.72 - 2.5), (w, hgt * 0.72 - 2.5))],  # doblez boca
            reference_texts=[((w / 2, 1.5), "boca")],
        )

    # ------------------------------------------------------------------
    # Layout automático (posiciona las piezas sin solaparse)
    # ------------------------------------------------------------------
    def layout(self, gap: float = 6.0) -> "Shirt":
        x_cursor = 0.0
        row_h = 0.0
        y_cursor = 0.0
        max_row_w = 170.0
        for pc in self.pieces:
            minx, miny, maxx, maxy = pc.bbox()
            w = maxx - minx + gap
            h = maxy - miny
            if x_cursor + w > max_row_w and x_cursor > 0:
                x_cursor = 0.0
                y_cursor += row_h + gap
                row_h = 0.0
            pc.offset = (x_cursor - minx, y_cursor - miny)
            x_cursor += w
            row_h = max(row_h, h)
        return self


def build_shirt(size: str = "S", sleeve_ease: float = 1.0,
                method: str = "aldrich") -> Shirt:
    return Shirt(p=build_parameters(size), sleeve_ease=sleeve_ease,
                 method=method).build()
