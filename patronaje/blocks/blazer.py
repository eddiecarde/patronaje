"""Bloque de chaqueta/blazer (mujer) — construcción paramétrica (best-effort).

Reúne los elementos sastre que faltaban en el sistema:

* **Manga de dos piezas** (mangón + soplillo): el mangón (superior) es más ancho
  y su costura delantera va **convexa**; el soplillo (inferior) es más estrecho y
  su costura **cóncava**. Ambas costuras se construyen a la **misma longitud**
  (bombeo calculado), de modo que casan al coser y forman el codo.
* **Delantero con solapa** (notched lapel): línea de quiebre (roll line), solapa
  con pico y extensión de botonadura; la pinza de cintura se modela **interior**
  (ojo de pez) para no cortar el bajo.
* **Cuello sastre**, **vista** (facing) y **forro** (delantero y espalda con
  pliegue de holgura en el CB).

Reutiliza el cuerpo entallado (`blocks/fitted`, por método) con holgura de
chaqueta, así el blazer sale para cualquier escuela de patronaje.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..core.curves import smooth_curve
from ..core.point import polyline_length
from ..parametric.parameters import Parameters
from .fitted import build_fitted


def _bow(p0, p1, target_len, sign):
    """Curva (spline) de ``p0`` a ``p1`` con la longitud de arco ``target_len``,
    bombeando hacia el lado ``sign`` (±1). Si el objetivo no supera la cuerda,
    devuelve casi una recta."""
    c = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    if target_len <= c + 1e-6 or c < 1e-9:
        return [p0, p1]
    sag = math.sqrt(max(0.0, 3.0 * c * (target_len - c) / 8.0))   # sagita parábola
    mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
    nx, ny = -(p1[1] - p0[1]) / c, (p1[0] - p0[0]) / c            # normal unitaria
    ctrl = (mx + nx * sag * sign, my + ny * sag * sign)
    return smooth_curve([p0, ctrl, p1], samples_per_span=8)


@dataclass
class TwoPieceSleeve:
    p: Parameters
    target_armhole: float
    top: list = field(default_factory=list)      # mangón (superior)
    under: list = field(default_factory=list)     # soplillo (inferior)
    seam_len_front: float = 0.0
    seam_len_back: float = 0.0
    elbow_y: float = 0.0
    cap_len: float = 0.0
    biceps_y: float = 0.0
    wrist_y: float = 0.0

    def build(self) -> "TwoPieceSleeve":
        p = self.p
        # copa proporcional (misma regla que la manga de una pieza)
        scye = p.busto / 8.0 + 10.5 + 0.5
        h = scye * 0.55
        bh = (p.contorno_brazo + 10.0) / 4.0    # medio ancho de cada panel al bíceps
        L = p.largo_manga
        wristf = (p.muneca + 10.0)               # boca de manga (holgura de chaqueta)
        ft = 0.60                                # reparto mangón/soplillo
        Wt, Wu = 2 * bh * ft, 2 * bh * (1 - ft)
        wt, wu = wristf * ft, wristf * (1 - ft)
        self.elbow_y = h + (L - h) * 0.55

        # objetivo de longitud de costura (igual para mangón y soplillo -> casan)
        chord_t = math.hypot(Wt / 2 - wt / 2, L - h)
        chord_u = math.hypot(Wu / 2 - wu / 2, L - h)
        Lseam = max(chord_t, chord_u) + 1.2

        # ---- mangón (superior): copa alta, costuras convexas ----
        capT = smooth_curve([(-Wt / 2, h), (-Wt * 0.24, h * 0.16), (0.0, 0.0),
                             (Wt * 0.24, h * 0.16), (Wt / 2, h)], samples_per_span=8)
        fsT = _bow((Wt / 2, h), (wt / 2, L), Lseam, +1)          # delantera convexa
        bsT = _bow((-wt / 2, L), (-Wt / 2, h), Lseam, -1)        # trasera convexa (otro lado)
        self.top = _dedup(capT + fsT[1:] + [(-wt / 2, L)] + bsT[1:])

        # ---- soplillo (inferior): scoop de axila, costuras cóncavas ----
        us = h * 0.34
        scoopU = smooth_curve([(-Wu / 2, h), (0.0, h + us), (Wu / 2, h)], samples_per_span=8)
        fsU = _bow((Wu / 2, h), (wu / 2, L), Lseam, -1)          # delantera cóncava
        bsU = _bow((-wu / 2, L), (-Wu / 2, h), Lseam, +1)
        self.under = _dedup(scoopU + fsU[1:] + [(-wu / 2, L)] + bsU[1:])

        self.seam_len_front = polyline_length(fsT)
        self.seam_len_back = polyline_length(bsT)
        self.cap_len = polyline_length(capT)
        self.biceps_y, self.wrist_y = h, L
        return self


def build_two_piece_sleeve(p: Parameters, target_armhole: float) -> TwoPieceSleeve:
    return TwoPieceSleeve(p=p, target_armhole=target_armhole).build()


# ==========================================================================
# Cuerpo de la chaqueta (delantero con solapa, espalda, cuello, vista, forro)
# ==========================================================================
@dataclass
class JacketBody:
    p: Parameters
    method: object
    lapel_w: float = 8.0          # ancho de solapa
    jacket_drop: float = 24.0     # largo por debajo de la cintura
    ext: float = 2.0              # extensión de botonadura (media)
    front: list = field(default_factory=list)
    back: list = field(default_factory=list)
    front_darts: list = field(default_factory=list)
    back_darts: list = field(default_factory=list)
    facing: list = field(default_factory=list)
    lining_front: list = field(default_factory=list)
    lining_back: list = field(default_factory=list)
    collar: list = field(default_factory=list)
    roll_line: tuple = None
    buttons: list = field(default_factory=list)
    break_y: float = 0.0
    hem_y: float = 0.0
    waist_y: float = 0.0
    bust_y: float = 0.0
    bust_point: tuple = None

    def build(self) -> "JacketBody":
        p, m = self.p, self.method
        fb = build_fitted(m, p, bust_dart_pos="side")
        d = fb.draft
        ext, lapw = self.ext, self.lapel_w
        fnw = d.points["D-SNP"].x
        fnd = d.points["D-CFn"].y
        usx = d.points["D-US"].x
        bust_y = d.points["D-US"].y
        waist_y = bust_y + fb.spec.bust_to_waist
        hem_y = waist_y + self.jacket_drop
        self.waist_y, self.hem_y, self.bust_y = waist_y, hem_y, bust_y
        self.bust_point = fb.bust_point
        w_side = usx - fb.side_supp
        hip_x = max(w_side + 2.0, (p.cadera + 6.0) / 4.0)
        break_y = waist_y - 6.0
        self.break_y = break_y

        side = smooth_curve([(usx, bust_y), (w_side + 0.5, (bust_y + waist_y) / 2),
                             (w_side, waist_y), (hip_x - 0.4, (waist_y + hem_y) / 2),
                             (hip_x, hem_y)], samples_per_span=6)

        # ---- delantero con solapa ----
        LP = (-ext - lapw, break_y - (break_y - fnd) * 0.5)     # punta de solapa
        NT = (-ext - lapw + 2.6, LP[1] - 3.2)                    # pico del notch
        gorge = (fnw * 0.5, fnd * 0.32)
        snp = (fnw, 0.0)
        front = [(-ext, hem_y), (-ext, break_y), LP, NT, gorge, snp]
        front += [d.points["D-SP"].as_tuple()]
        front += list(d.front_armhole[1:])
        front += side[1:]
        front += [(-ext, hem_y)]
        self.front = _dedup(front)

        # pinzas interiores: busto (del costado al BP) y cintura (ojo de pez)
        BP = fb.bust_point
        self.front_darts = []
        b_base = (usx, bust_y + 1.5)
        self.front_darts.append((b_base, BP, (usx - 1.5, bust_y + 3.5)))
        fwx = BP[0]
        intake = fb.spec.front_waist_dart
        wl1, wl2 = (fwx + intake / 2, waist_y), (fwx - intake / 2, waist_y)
        self.front_darts.append((wl1, (fwx, BP[1] + 2.0), wl2))          # sube al busto
        self.front_darts.append((wl1, (fwx, waist_y + 13.0), wl2))       # baja a la cadera
        self.roll_line = (LP, (snp[0] - 1.0, snp[1] + 1.0))
        nbut = 2
        self.buttons = [(-ext + 0.4, break_y + i * 6.5) for i in range(nbut)]

        # ---- espalda (CB al doblez) ----
        cbn = d.points["E-CBn"].as_tuple()
        spB = d.points["E-SP"].as_tuple()
        usxB = d.points["E-US"].x
        w_sideB = usxB - fb.side_supp
        hip_xB = max(w_sideB + 2.0, (p.cadera + 6.0) / 4.0)
        sideB = smooth_curve([(usxB, bust_y), (w_sideB + 0.5, (bust_y + waist_y) / 2),
                              (w_sideB, waist_y), (hip_xB - 0.4, (waist_y + hem_y) / 2),
                              (hip_xB, hem_y)], samples_per_span=6)
        back = [cbn] + list(d.back_neck[1:]) + [spB] + list(d.back_armhole[1:])
        back += sideB[1:] + [(0.0, hem_y)]
        self.back = _dedup(back)
        bwx = w_sideB * 0.42
        self.back_darts = [((bwx + 1.6, waist_y), (bwx, waist_y - 12.0), (bwx - 1.6, waist_y)),
                           ((bwx + 1.6, waist_y), (bwx, waist_y + 12.0), (bwx - 1.6, waist_y))]

        # ---- vista (facing): sigue la solapa y el borde delantero ----
        fw = 8.0
        self.facing = _dedup([(-ext, hem_y), (-ext, break_y), LP, NT, gorge, snp,
                              (snp[0] - fw + 2, fnd), (-ext + fw, break_y),
                              (-ext + fw, hem_y)])

        # ---- forro delantero = delantero menos la vista ----
        self.lining_front = _clip_right(self.front, -ext + fw)
        # ---- forro espalda = espalda + pliegue de holgura en el CB ----
        pleat = 2.5
        self.lining_back = _dedup([(0.0, cbn[1])] + [(x + pleat, y) for x, y in self.back]
                                  + [(0.0, hem_y)])

        # ---- cuello sastre ----
        neck_len = polyline_length(d.back_neck) + polyline_length(d.front_neck)
        self.collar = _collar(neck_len, lapw)
        return self


def _collar(neck_len: float, lapw: float) -> list:
    """Cuello sastre (medio): banda curva con caída, casa con el escote + gorge."""
    L = neck_len + lapw * 0.4
    hgt = 7.0
    bottom = []
    n = 28
    for i in range(n + 1):
        t = i / n
        x = t * L
        y = -(2.2 * (t - 0.5) ** 2) + 0.6            # ligera curva de montaje
        bottom.append((x, y))
    top = [(x, y + hgt) for x, y in bottom]
    # pico exterior en el extremo (lado de la solapa)
    top[-1] = (top[-1][0] + 2.0, top[-1][1] + 1.5)
    return _dedup(bottom + list(reversed(top)))


def _clip_right(contour, x_line):
    """Parte del contorno a la derecha de ``x_line`` (para el forro sin la vista)."""
    from shapely.geometry import Polygon, box
    poly = Polygon(contour)
    if not poly.is_valid:
        poly = poly.buffer(0)
    minx, miny, maxx, maxy = poly.bounds
    r = poly.intersection(box(x_line, miny - 5, maxx + 5, maxy + 5))
    if r.geom_type == "MultiPolygon":
        r = max(r.geoms, key=lambda g: g.area)
    return _dedup([(float(x), float(y)) for x, y in r.exterior.coords])


def _dedup(poly, tol=1e-6):
    out = []
    for pt in poly:
        pt = (float(pt[0]), float(pt[1]))
        if not out or math.hypot(pt[0] - out[-1][0], pt[1] - out[-1][1]) > tol:
            out.append(pt)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= tol:
        out.pop()
    return out


def build_jacket_body(method, p: Parameters, lapel_w: float = 8.0,
                      jacket_drop: float = 24.0) -> JacketBody:
    return JacketBody(p=p, method=method, lapel_w=lapel_w, jacket_drop=jacket_drop).build()
