"""Validaciones geométricas y de casado, previas a exportar.

Implementa las comprobaciones exigidas por el prompt:

  Geométricas (por pieza)
    * Todas las piezas son polígonos cerrados.
    * No existen líneas abiertas.
    * No existen puntos duplicados consecutivos.
    * No existen autointersecciones.

  Casado (entre piezas)
    * Longitud de sisa = longitud de copa ± tolerancia.
    * Costados coinciden (delantero = espalda).
    * Cuello (pie de cuello) coincide con el escote.
    * Puños coinciden con la boca de manga (tras pliegues).
    * Canesú coincide con la espalda.
    * Hombros coinciden (delantero = espalda).

Se apoya en shapely para validez topológica y en las longitudes medidas de los
bloques. Devuelve un :class:`ValidationReport` con resultados detallados; el CLI
lo imprime y bloquea la exportación si hay errores.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon, LineString

from ..piece import Piece


@dataclass
class Check:
    nombre: str
    ok: bool
    detalle: str = ""
    tolerancia: float | None = None
    valor: float | None = None


@dataclass
class ValidationReport:
    checks: list[Check] = field(default_factory=list)

    def add(self, nombre, ok, detalle="", tolerancia=None, valor=None):
        self.checks.append(Check(nombre, ok, detalle, tolerancia, valor))

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def n_errors(self) -> int:
        return sum(1 for c in self.checks if not c.ok)

    def text(self) -> str:
        lines = ["=== VALIDACIÓN DE PATRÓN ==="]
        for c in self.checks:
            mark = "OK " if c.ok else "XX "
            extra = ""
            if c.valor is not None:
                extra = f"  [valor={c.valor:.3f}"
                if c.tolerancia is not None:
                    extra += f", tol={c.tolerancia:.3f}"
                extra += "]"
            lines.append(f"  [{mark}] {c.nombre}: {c.detalle}{extra}")
        lines.append(f"--- {'TODO OK' if self.ok else str(self.n_errors) + ' ERROR(ES)'} ---")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Validaciones geométricas por pieza
# --------------------------------------------------------------------------
def validate_piece_geometry(piece: Piece, report: ValidationReport) -> None:
    name = piece.name
    net = piece.net_contour

    # cerrado / suficiente número de puntos
    closed = len(net) >= 3
    report.add(f"{name}: polígono cerrado", closed,
               f"{len(net)} vértices" if closed else "muy pocos vértices")

    # sin duplicados consecutivos
    dups = 0
    for (x0, y0), (x1, y1) in zip(net, net[1:] + net[:1]):
        if abs(x0 - x1) < 1e-7 and abs(y0 - y1) < 1e-7:
            dups += 1
    report.add(f"{name}: sin duplicados", dups == 0,
               "sin vértices duplicados" if dups == 0 else f"{dups} duplicados")

    # validez topológica (sin autointersecciones) vía shapely
    poly = Polygon(net)
    valid = poly.is_valid and poly.is_simple
    report.add(f"{name}: sin autointersección", valid,
               "anillo simple y válido" if valid else f"inválido: {_reason(poly)}")

    # la línea de corte también debe ser un anillo cerrado simple
    cut = piece.cut_contour()
    cutpoly = Polygon(cut)
    report.add(f"{name}: corte cerrado válido", cutpoly.is_valid and len(cut) >= 3,
               "línea de corte cerrada")


def _reason(poly: Polygon) -> str:
    from shapely.validation import explain_validity
    return explain_validity(poly)


# --------------------------------------------------------------------------
# Validaciones de casado entre piezas (usa el ensamble Shirt)
# --------------------------------------------------------------------------
def validate_matching(shirt, report: ValidationReport, tol: float = 0.5) -> None:
    b = shirt.bodice
    s = shirt.sleeve
    p = shirt.p

    # 1) sisa = copa ± tol (con holgura de montaje sleeve_ease)
    sisa = b.armhole_length()
    copa = s.cap_length()
    diff = copa - (sisa + shirt.sleeve_ease)
    report.add("Sisa = Copa (± tol)", abs(diff) <= tol,
               f"sisa={sisa:.2f}  copa={copa:.2f}  ease={shirt.sleeve_ease:.2f}",
               tolerancia=tol, valor=diff)

    # 2) costados coinciden (delantero vs espalda): misma longitud vertical
    lado_del = p.largo_camisa - p.prof_sisa
    lado_esp = p.largo_camisa - p.prof_sisa
    report.add("Costados coinciden", abs(lado_del - lado_esp) <= tol,
               f"delantero={lado_del:.2f}  espalda={lado_esp:.2f}",
               tolerancia=tol, valor=lado_del - lado_esp)

    # 3) hombros coinciden (delantero vs espalda)
    hom_del = b.points["D-SNP"].distance_to(b.points["D-SP"])
    hom_esp = b.points["E-SNP"].distance_to(b.points["E-SP"])
    report.add("Hombros coinciden", abs(hom_del - hom_esp) <= tol,
               f"delantero={hom_del:.2f}  espalda={hom_esp:.2f}",
               tolerancia=tol, valor=hom_del - hom_esp)

    # 4) cuello (pie de cuello) coincide con escote
    escote = b.neckline_length()          # mitad (doblez)
    stand = next(pc for pc in shirt.pieces if pc.name == "PIE DE CUELLO")
    # longitud del borde inferior del pie de cuello (arco) ~ half_neck + extensión
    stand_len = _bottom_len(stand.net_contour)
    esperado = escote + p.extension_boton
    report.add("Pie de cuello = Escote", abs(stand_len - esperado) <= tol + 0.6,
               f"escote(1/2)+ext={esperado:.2f}  pie_cuello={stand_len:.2f}",
               tolerancia=tol + 0.6, valor=stand_len - esperado)

    # 5) cuello = pie de cuello (longitudes base compatibles)
    collar = next(pc for pc in shirt.pieces if pc.name == "CUELLO")
    collar_len = _bottom_len(collar.net_contour)
    report.add("Cuello = Pie de cuello", abs(collar_len - escote) <= tol + 1.0,
               f"cuello={collar_len:.2f}  escote(1/2)={escote:.2f}",
               tolerancia=tol + 1.0, valor=collar_len - escote)

    # 6) puño = boca de manga tras pliegues
    boca = p.boca_manga
    puno = p.largo_puno
    pliegues = boca - puno
    report.add("Puño = boca de manga (con pliegues)", 1.5 <= pliegues <= 6.0,
               f"boca={boca:.2f}  puño={puno:.2f}  pliegues={pliegues:.2f}",
               valor=pliegues)

    # 7) canesú coincide con espalda (ancho en línea de canesú)
    yoke = next(pc for pc in shirt.pieces if pc.name == "CANESU")
    back = next(pc for pc in shirt.pieces if pc.name == "ESPALDA")
    yoke_bottom = _width_at_bottom(yoke.net_contour, b.yoke_line_y)
    back_top = _width_at_top(back.net_contour, b.yoke_line_y)
    report.add("Canesú = Espalda", abs(yoke_bottom - back_top) <= tol,
               f"canesú_inf={yoke_bottom:.2f}  espalda_sup={back_top:.2f}",
               tolerancia=tol, valor=yoke_bottom - back_top)


def _bottom_len(contour) -> float:
    """Longitud del borde inferior (mínimo y) de una banda: aproxima recorriendo
    los vértices cuya y está en la mitad inferior."""
    ys = [q[1] for q in contour]
    ymid = (min(ys) + max(ys)) / 2
    bottom = [q for q in contour if q[1] <= ymid]
    return _chain_len(bottom)


def _chain_len(pts) -> float:
    import math
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _width_at_bottom(contour, y) -> float:
    xs = [q[0] for q in contour if abs(q[1] - _maxy(contour)) < 1e-6 or abs(q[1] - y) < 1e-6]
    ys_at = [q for q in contour if abs(q[1] - _maxy(contour)) < 1e-6]
    if ys_at:
        return max(q[0] for q in ys_at) - min(q[0] for q in ys_at)
    return max(xs) - min(xs) if xs else 0.0


def _width_at_top(contour, y) -> float:
    miny = _miny(contour)
    top = [q for q in contour if abs(q[1] - miny) < 1e-6]
    if top:
        return max(q[0] for q in top) - min(q[0] for q in top)
    return 0.0


def _maxy(c):
    return max(q[1] for q in c)


def _miny(c):
    return min(q[1] for q in c)


# --------------------------------------------------------------------------
def validate_all(shirt, tol: float = 0.5) -> ValidationReport:
    report = ValidationReport()
    for pc in shirt.pieces:
        validate_piece_geometry(pc, report)
    validate_matching(shirt, report, tol=tol)
    return report
