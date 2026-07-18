"""Bloque base ENTALLADO (sloper) con pinzas y equilibrio.

A diferencia del bloque de camisa (holgado, sin pinza, costado recto), el sloper
entallado modela el cuerpo con:

* **Pinza de busto** (bust dart): da forma sobre el pecho; apunta al punto de
  busto (BP) y se toma en el costado.
* **Pinzas de cintura** (delantera y trasera): suprimen la diferencia
  busto–cintura para entallar.
* **Costado entallado**: el costado entra en la cintura.
* **Equilibrio** (balance): la pinza de busto añade largo al delantero de modo
  que, al cerrarla, el costado delantero casa con el trasero; el escote y la
  sisa provienen del método (así cada escuela conserva su carácter).

Reutiliza el trazo de escote/sisa de cada método (`method.build_bodice`) y añade
la cintura y las pinzas según un :class:`DartSpec` (parámetros de pinza/equilibrio
propios de cada escuela). Las pinzas se materializan como muescas (V) en el
contorno neto y se guardan en ``Piece.darts`` para dibujar patas y vértice.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..parametric.parameters import Parameters
from ..core.curves import smooth_curve
from ..core.point import polyline_length
from .aldrich_bodice import BodiceDraft


@dataclass
class DartSpec:
    """Parámetros de pinza y equilibrio (por método)."""
    bust_dart: float = 3.0          # intake de la pinza de busto (cm)
    front_waist_dart: float = 3.5   # intake pinza de cintura delantera
    back_waist_dart: float = 3.5    # intake pinza de cintura trasera
    side_supp: float = 1.5          # entrada del costado en la cintura (por panel)
    back_shoulder_dart: float = 0.8  # pinza de hombro (omóplato)
    bust_point_x: float = 9.3       # semidistancia entre puntos de busto
    bp_drop: float = 1.5            # BP por debajo de la línea de busto
    bust_to_waist: float = 20.0     # largo de talle (busto->cintura)
    waist_ease: float = 4.0         # holgura de cintura


def _insert_dart(edge, center_frac, intake, apex):
    """Inserta una pinza (V) en un borde (polilínea) centrada en ``center_frac``
    con abertura ``intake`` y vértice ``apex``. Devuelve el borde con la V."""
    pts = [tuple(p) for p in edge]
    seglen = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
              for i in range(len(pts) - 1)]
    tot = sum(seglen) or 1.0

    def at(dist):
        acc = 0.0
        for i in range(len(pts) - 1):
            if acc + seglen[i] >= dist:
                t = (dist - acc) / seglen[i] if seglen[i] else 0.0
                return (pts[i][0] + t * (pts[i + 1][0] - pts[i][0]),
                        pts[i][1] + t * (pts[i + 1][1] - pts[i][1]))
            acc += seglen[i]
        return pts[-1]

    c = tot * center_frac
    d1, d2 = c - intake / 2.0, c + intake / 2.0
    leg1, leg2 = at(d1), at(d2)
    cum = [0.0]
    for L in seglen:
        cum.append(cum[-1] + L)
    out = []
    for i, pt in enumerate(pts):
        if cum[i] <= d1 + 1e-9 or cum[i] >= d2 - 1e-9:
            out.append(pt)
        # inserta la V justo después del último punto anterior a d1
        if cum[i] <= d1 + 1e-9 and (i + 1 == len(pts) or cum[i + 1] > d1):
            out += [leg1, apex, leg2]
    return out, (leg1, apex, leg2)


@dataclass
class FittedBodice:
    p: Parameters
    draft: BodiceDraft
    spec: DartSpec
    bust_dart_pos: str = "side"   # side | shoulder | neck | armhole | french | waist

    front: list = None            # contorno neto delantero
    back: list = None
    front_darts: list = None
    back_darts: list = None
    bust_point: tuple = None

    def build(self) -> "FittedBodice":
        p, d, s = self.p, self.draft, self.spec
        bust_y = d.points["D-US"].y
        quarter = d.points["D-US"].x
        waist_y = bust_y + s.bust_to_waist
        quarter_waist = (p.cintura + s.waist_ease) / 4.0
        suppression = quarter - quarter_waist

        # reparto de la supresión: costado + pinza de cintura
        side = min(s.side_supp, suppression)
        fwd = max(0.0, min(s.front_waist_dart, suppression - side))
        bwd = max(0.0, min(s.back_waist_dart, suppression - side))
        w_side = quarter - side

        # BP y equilibrio: el delantero baja `bust_dart` para casar el costado
        BP = (s.bust_point_x, bust_y + s.bp_drop)
        self.bust_point = BP
        bal = s.bust_dart  # largo extra de talle delantero

        # ---------------- DELANTERO (con pinza de busto reubicable) ----------
        cfn = d.points["D-CFn"].as_tuple()
        snp = d.points["D-SNP"].as_tuple()
        sp = d.points["D-SP"].as_tuple()
        bd = s.bust_dart
        pos = self.bust_dart_pos
        fwaist_y = waist_y + bal

        def apex_toward(center, back=2.0):
            vx, vy = center[0] - BP[0], center[1] - BP[1]
            n = math.hypot(vx, vy) or 1.0
            return (BP[0] + vx / n * back, BP[1] + vy / n * back)

        neck_edge = list(reversed(d.front_neck))    # CFn..SNP
        shoulder_edge = [snp, sp]
        armhole_edge = list(d.front_armhole)        # SP..US
        us = (quarter, bust_y)
        side_ctrl = [us, (w_side + 0.6, (bust_y + fwaist_y) / 2), (w_side, fwaist_y)]
        side_edge = smooth_curve(side_ctrl, samples_per_span=6)
        fwd_eff = fwd
        bust_dart = None

        if pos == "shoulder":
            shoulder_edge, bust_dart = _insert_dart([snp, sp], 0.55, bd, apex_toward(
                (snp[0] + (sp[0] - snp[0]) * 0.55, snp[1] + (sp[1] - snp[1]) * 0.55)))
        elif pos == "neck":
            neck_edge, bust_dart = _insert_dart(neck_edge, 0.55, bd,
                                                apex_toward(neck_edge[len(neck_edge) // 2]))
        elif pos == "armhole":
            armhole_edge, bust_dart = _insert_dart(armhole_edge, 0.5, bd,
                                                   apex_toward(armhole_edge[len(armhole_edge) // 2]))
        elif pos == "french":
            side_edge, bust_dart = _insert_dart(side_edge, 0.78, bd,
                                                apex_toward(side_edge[len(side_edge) * 3 // 4]))
        elif pos == "waist":
            fwd_eff = fwd + bd                       # busto absorbido en la cintura
        else:  # side (por defecto): pinza en lo alto del costado, desde la axila
            ap = apex_toward(us, back=bd)
            side_edge = ([us, (BP[0] + 2.0, bust_y + bd / 2.0), (quarter, bust_y + bd)]
                         + smooth_curve([(quarter, bust_y + bd),
                                         (w_side + 0.6, (bust_y + bd + fwaist_y) / 2),
                                         (w_side, fwaist_y)], samples_per_span=6)[1:])
            bust_dart = (us, (BP[0] + 2.0, bust_y + bd / 2.0), (quarter, bust_y + bd))

        # pinza de cintura delantera
        fwx = BP[0]
        fw_apex = (fwx, BP[1] + 3.0)
        fl1 = (fwx + fwd_eff / 2.0, fwaist_y)
        fl2 = (fwx - fwd_eff / 2.0, fwaist_y)

        fc = list(neck_edge)                          # CFn..SNP
        fc += shoulder_edge[1:]                        # ..SP
        fc += armhole_edge[1:]                          # ..US
        fc += side_edge[1:]                             # ..Wside
        fc += [fl1, fw_apex, fl2, (0.0, fwaist_y)]      # cintura + pinza + CF
        self.front = _dedup(fc)
        self.front_darts = [(fl1, fw_apex, fl2)]
        if bust_dart is not None:
            self.front_darts.insert(0, bust_dart)

        # ---------------- ESPALDA ----------------
        cbn = d.points["E-CBn"].as_tuple()
        snpB = d.points["E-SNP"].as_tuple()
        spB = d.points["E-SP"].as_tuple()
        bwx = w_side * 0.42
        bw_apex = (bwx, waist_y - 12.0)   # pinza de cintura trasera (apunta al omóplato)
        bl1 = (bwx + bwd / 2.0, waist_y)
        bl2 = (bwx - bwd / 2.0, waist_y)
        # pinza de hombro (omóplato) en la línea de hombro
        sh_len = polyline_length([snpB, spB])
        t = 0.5
        shd_c = (snpB[0] + (spB[0] - snpB[0]) * t, snpB[1] + (spB[1] - snpB[1]) * t)
        sd = s.back_shoulder_dart
        shd1 = (shd_c[0] - sd / 2.0, shd_c[1])
        shd2 = (shd_c[0] + sd / 2.0, shd_c[1])
        shd_apex = (bwx, shd_c[1] + 8.0)

        bc = [cbn]
        bc += list(d.back_neck[1:])                 # a SNP
        # hombro con pinza de omóplato
        bc += [snpB, shd1, shd_apex, shd2, spB]
        bc += list(d.back_armhole[1:])              # sisa a US
        bc += smooth_curve([(quarter, bust_y), (w_side + 0.6, (bust_y + waist_y) / 2),
                            (w_side, waist_y)], samples_per_span=6)[1:]
        bc += [bl1, bw_apex, bl2]
        bc += [(0.0, waist_y)]
        self.back = _dedup(bc)
        self.back_darts = [((quarter, bust_y), None, (w_side, waist_y))][:0]  # (info)
        self.back_darts = [(bl1, bw_apex, bl2), (shd1, shd_apex, shd2)]

        # métricas de casado/equilibrio
        self._front_side = polyline_length(side_edge)
        self._back_side = polyline_length(smooth_curve([(quarter, bust_y),
                            (w_side + 0.6, (bust_y + waist_y) / 2), (w_side, waist_y)], 6))
        self.waist_suppression = suppression
        self.side_supp = side
        return self


def _dedup(poly, tol=1e-6):
    out = []
    for pt in poly:
        pt = (float(pt[0]), float(pt[1]))
        if not out or math.hypot(pt[0] - out[-1][0], pt[1] - out[-1][1]) > tol:
            out.append(pt)
    return out


def build_fitted(method, p: Parameters, bust_dart_pos: str = "side") -> FittedBodice:
    draft = method.build_bodice(p)
    spec = method.dart_spec(p) if hasattr(method, "dart_spec") else DartSpec()
    return FittedBodice(p=p, draft=draft, spec=spec, bust_dart_pos=bust_dart_pos).build()
