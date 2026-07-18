"""Estilos derivados por manipulación de bloque.

A partir del ensamble base (:class:`~patronaje.garment.shirt.Shirt`) se generan
variantes de estilo modificando las piezas con las operaciones geométricas de
`operations.py`. Cada estilo reemplaza los contornos afectados y deja el resto
del sistema (validación geométrica, exportadores, tech pack, marker) intacto.

Estilos incluidos:
* **flare** — camisa acampanada / túnica A-line (vuelo en delantero y espalda).
* **puff** — manga abullonada (volumen + copa levantada; la cabeza se frunce).

Nota: algunos estilos rompen a propósito el casado ``sisa = copa`` (p. ej. la
manga abullonada se **frunce** en la sisa), por lo que se validan sólo las
comprobaciones **geométricas** (polígono cerrado, simple, sin duplicados).
"""
from __future__ import annotations

from ..garment.shirt import Shirt
from . import operations as ops


def _find(shirt, name):
    # coincidencia exacta primero; si no, por prefijo (p. ej. "DELANTERO (base entallada)")
    exact = next((p for p in shirt.pieces if p.name == name), None)
    if exact is not None:
        return exact
    return next((p for p in shirt.pieces if p.name.startswith(name)), None)


def _side_x_at(contour, y):
    """x del costado (máximo) donde el contorno cruza la altura ``y``."""
    xs = []
    pts = list(contour)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        lo, hi = min(y0, y1), max(y0, y1)
        if lo - 1e-9 <= y <= hi + 1e-9 and abs(y1 - y0) > 1e-12:
            t = (y - y0) / (y1 - y0)
            xs.append(x0 + t * (x1 - x0))
    return max(xs) if xs else 0.0


def flare_shirt(shirt: Shirt, added_hem: float = 10.0) -> Shirt:
    """Convierte la camisa en acampanada/túnica añadiendo ``added_hem`` cm de
    vuelo por costado en delantero y espalda (A-line por slash-and-spread)."""
    p = shirt.p
    top_y = p.prof_sisa
    bot_y = p.largo_camisa
    quarter = (p.busto + p.holgura_busto) / 4.0
    ratio = added_hem / quarter
    for name in ("DELANTERO", "ESPALDA"):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.flare(pc.net_contour, 0.0, top_y, bot_y, ratio, side=+1)
            pc.name = name + " (acampanado)"
    return shirt


def puff_sleeve(shirt: Shirt, width_factor: float = 1.30, cap_lift: float = 3.5) -> Shirt:
    """Manga abullonada: ensancha la manga y levanta la copa (se frunce en la
    cabeza). Rompe intencionalmente el casado sisa=copa."""
    pc = _find(shirt, "MANGA")
    if pc:
        cap_h = shirt.sleeve.cap_height
        pts = ops.widen(pc.net_contour, 0.0, width_factor)
        pts = ops.lift(pts, cap_lift, cap_h, above=True)
        pc.net_contour = pts
        pc.name = "MANGA (abullonada)"
        pc.reference_texts = list(pc.reference_texts) + [((0.0, cap_h * 0.5), "fruncir cabeza")]
    return shirt


def bell_sleeve(shirt: Shirt, added: float = 16.0) -> Shirt:
    """Manga campana: vuelo simétrico desde el codo hasta la boca de manga."""
    pc = _find(shirt, "MANGA")
    if pc:
        s = shirt.sleeve
        top_y = s.cap_height + (shirt.p.largo_manga - s.cap_height) * 0.45
        ratio = added / 24.0
        pc.net_contour = ops.flare_symmetric(pc.net_contour, 0.0, top_y,
                                             shirt.p.largo_manga, ratio)
        pc.name = "MANGA (campana)"
    return shirt


def mandarin_collar(shirt: Shirt) -> Shirt:
    """Cuello mao: elimina la hoja de cuello y deja sólo la banda (más alta)."""
    shirt.pieces = [p for p in shirt.pieces if p.name != "CUELLO"]
    stand = _find(shirt, "PIE DE CUELLO")
    if stand:
        ys = [q[1] for q in stand.net_contour]
        y0 = min(ys)
        stand.net_contour = [(x, y0 + (y - y0) * 1.6) for x, y in stand.net_contour]
        stand.name = "CUELLO MAO"
    return shirt


def sleeveless(shirt: Shirt) -> Shirt:
    """Sin mangas: elimina manga, puño y tapeta (sisa acabada con vista/bies)."""
    drop = {"PUNO", "TAPETA MANGA"}
    shirt.pieces = [p for p in shirt.pieces
                    if p.name not in drop and not p.name.startswith("MANGA")]
    return shirt


def crop_top(shirt: Shirt, at: float = 0.45) -> Shirt:
    """Crop: recorta el largo de delantero, espalda y vista."""
    p = shirt.p
    cut_y = p.prof_sisa + (p.largo_camisa - p.prof_sisa) * at
    for name in ("DELANTERO", "ESPALDA", "VISTA DELANTERA"):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.clip_below(pc.net_contour, cut_y)
            pc.name = name + " (crop)"
    return shirt


def princess_front(shirt: Shirt) -> Shirt:
    """Costura princesa: divide el delantero en panel centro + panel costado."""
    from ..piece import Piece
    p = shirt.p
    b = shirt.bodice
    pc = _find(shirt, "DELANTERO")
    if pc is None:
        return shirt
    ytar = p.prof_sisa * 0.5
    top = min(b.front_armhole, key=lambda q: abs(q[1] - ytar))
    princess_x = p.busto / 8.0
    bottom = (princess_x, p.largo_camisa)
    c1, c2 = ops.split_panel(pc.net_contour, top, bottom, princess_x - 1.0)
    center_c, side_c = (c1, c2) if min(q[0] for q in c1) < min(q[0] for q in c2) else (c2, c1)
    center = Piece(name="DELANTERO CENTRO", number=1, size=pc.size, quantity=2,
                   cut_type="par: izq + der", net_contour=center_c,
                   seam_allowance=p.margen_costura,
                   grain=((2.0, p.escote_del_prof + 4), (2.0, p.largo_camisa - 4)),
                   buttons=pc.buttons, buttonholes=pc.buttonholes)
    side = Piece(name="DELANTERO COSTADO", number=11, size=pc.size, quantity=2,
                 cut_type="par: izq + der", net_contour=side_c,
                 seam_allowance=p.margen_costura,
                 grain=((p.cuarto_busto * 0.7, p.prof_sisa + 4),
                        (p.cuarto_busto * 0.7, p.largo_camisa - 4)))
    idx = shirt.pieces.index(pc)
    shirt.pieces[idx:idx + 1] = [center, side]
    return shirt


def short_sleeve(shirt: Shirt, at: float = 0.42, name: str = "MANGA CORTA") -> Shirt:
    """Manga corta: recorta la manga y elimina puño y tapeta."""
    pc = _find(shirt, "MANGA")
    if pc:
        s = shirt.sleeve
        cut = s.cap_height + (shirt.p.largo_manga - s.cap_height) * at
        pc.net_contour = ops.clip_below(pc.net_contour, cut)
        pc.hem_allowance = shirt.p.margen_dobladillo  # boca de manga acabada con dobladillo
        pc.name = name
    shirt.pieces = [p for p in shirt.pieces if p.name not in ("PUNO", "TAPETA MANGA")]
    return shirt


def cap_sleeve(shirt: Shirt) -> Shirt:
    """Manga cap (muy corta, sobre el hombro)."""
    return short_sleeve(shirt, at=0.13, name="MANGA CAP")


def dress(shirt: Shirt, extra_len: float = 28.0, flare_add: float = 12.0) -> Shirt:
    """Camisa-vestido: alarga el cuerpo y le da vuelo A-line."""
    p = shirt.p
    hinge = p.prof_sisa
    orig = p.largo_camisa
    factor = (orig - hinge + extra_len) / (orig - hinge)
    newbot = hinge + (orig - hinge) * factor
    ratio = flare_add / ((p.busto + p.holgura_busto) / 4.0)
    for name in ("DELANTERO", "ESPALDA", "VISTA DELANTERA"):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.lengthen(pc.net_contour, hinge, factor)
            pc.net_contour = ops.flare(pc.net_contour, 0.0, hinge, newbot, ratio, side=+1)
            pc.name = name + " (vestido)"
    return shirt


def oversized(shirt: Shirt, factor: float = 1.12) -> Shirt:
    """Corte holgado/oversize: ensancha cuerpo, canesú y manga."""
    for name in ("DELANTERO", "ESPALDA", "CANESU", "MANGA"):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.widen(pc.net_contour, 0.0, factor)
            pc.name = pc.name + " (oversize)"
    return shirt


def empire(shirt: Shirt, at: float = 0.28, flare_add: float = 16.0) -> Shirt:
    """Corte imperio: separa talle (arriba) y falda (abajo, con vuelo)."""
    from ..piece import Piece
    p = shirt.p
    hinge = p.prof_sisa
    emp = hinge + (p.largo_camisa - hinge) * at
    ratio = flare_add / ((p.busto + p.holgura_busto) / 4.0)
    for name in ("DELANTERO", "ESPALDA"):
        pc = _find(shirt, name)
        if pc is None:
            continue
        upper = ops.clip_below(pc.net_contour, emp)
        lower = ops.clip_above(pc.net_contour, emp)
        lower = ops.flare(lower, 0.0, emp, p.largo_camisa, ratio, side=+1)
        pc.net_contour = upper
        pc.name = name + " TALLE"
        idx = shirt.pieces.index(pc)
        skirt = Piece(name=name + " FALDA", number=pc.number + 20, size=pc.size,
                      quantity=pc.quantity, cut_type=pc.cut_type,
                      on_fold=pc.on_fold, fold_x=pc.fold_x,
                      net_contour=lower, seam_allowance=p.margen_costura,
                      hem_allowance=p.margen_dobladillo,
                      grain=((2.0, emp + 2), (2.0, p.largo_camisa - 2)))
        shirt.pieces.insert(idx + 1, skirt)
    return shirt


def _reshape_neck(shirt: Shirt, drop: float, widen_neck: float,
                  kind: str, drop_collar: bool, label: str) -> Shirt:
    """Remodela el escote del delantero (V o barco) y opcionalmente quita cuello."""
    import math
    from ..core.curves import smooth_curve
    p = shirt.p
    b = shirt.bodice
    pc = _find(shirt, "DELANTERO")
    if pc is None:
        return shirt
    ext = p.extension_boton
    fnd = p.escote_del_prof
    deeper = fnd + drop
    snp = b.points["D-SNP"].as_tuple()
    snp_new = (snp[0] + widen_neck, snp[1])
    c = pc.net_contour
    isn = min(range(len(c)), key=lambda i: math.hypot(c[i][0] - snp[0], c[i][1] - snp[1]))
    head = [(-ext, deeper), (0.0, deeper)]
    if kind == "v":
        head += [snp_new]
    else:  # barco / scoop
        head += smooth_curve([(0.0, deeper), (snp_new[0] * 0.5, deeper * 0.9), snp_new],
                             samples_per_span=8)[1:]
    pc.net_contour = head + list(c[isn + 1:])
    pc.buttons = [(bx, by) for (bx, by) in pc.buttons if by >= deeper]
    pc.buttonholes = [t for t in pc.buttonholes if t[1] >= deeper]
    pc.name = "DELANTERO " + label
    if drop_collar:
        shirt.pieces = [x for x in shirt.pieces if x.name not in ("CUELLO", "PIE DE CUELLO")]
    return shirt


def v_neck(shirt: Shirt) -> Shirt:
    """Escote en V (sin cuello)."""
    return _reshape_neck(shirt, drop=8.0, widen_neck=0.0, kind="v",
                         drop_collar=True, label="(escote V)")


def boat_neck(shirt: Shirt) -> Shirt:
    """Escote barco (ancho y poco profundo, sin cuello)."""
    return _reshape_neck(shirt, drop=-3.0, widen_neck=5.0, kind="scoop",
                         drop_collar=True, label="(escote barco)")


def hi_lo(shirt: Shirt, front_at: float = 0.62) -> Shirt:
    """Dobladillo asimétrico: delantero más corto, espalda largo."""
    p = shirt.p
    cut = p.prof_sisa + (p.largo_camisa - p.prof_sisa) * front_at
    for name in ("DELANTERO", "VISTA DELANTERA"):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.clip_below(pc.net_contour, cut)
            pc.name = name + " (hi-lo)"
    return shirt


def cocoon(shirt: Shirt, reduce: float = 8.0) -> Shirt:
    """Dobladillo entallado (cocoon): estrecha la base respecto de la cadera."""
    p = shirt.p
    ratio = -reduce / ((p.busto + p.holgura_busto) / 4.0)
    for name in ("DELANTERO", "ESPALDA"):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.flare(pc.net_contour, 0.0, p.prof_sisa,
                                       p.largo_camisa, ratio, side=+1)
            pc.name = name + " (cocoon)"
    return shirt


def peplum(shirt: Shirt, waist_at: float = 0.30, peplum_len: float = 16.0,
           flare_add: float = 22.0) -> Shirt:
    """Peplum: talle hasta la cintura + volante acampanado corto."""
    from ..piece import Piece
    p = shirt.p
    hinge = p.prof_sisa
    waist = hinge + (p.largo_camisa - hinge) * waist_at
    ratio = flare_add / ((p.busto + p.holgura_busto) / 4.0)
    for name in ("DELANTERO", "ESPALDA"):
        pc = _find(shirt, name)
        if pc is None:
            continue
        upper = ops.clip_below(pc.net_contour, waist)
        lower = ops.clip_above(pc.net_contour, waist)
        lower = ops.flare(lower, 0.0, waist, p.largo_camisa, ratio, side=+1)
        lower = ops.clip_below(lower, waist + peplum_len)
        pc.net_contour = upper
        pc.name = name + " TALLE"
        idx = shirt.pieces.index(pc)
        pep = Piece(name=name + " PEPLUM", number=pc.number + 30, size=pc.size,
                    quantity=pc.quantity, cut_type=pc.cut_type,
                    on_fold=pc.on_fold, fold_x=pc.fold_x,
                    net_contour=lower, seam_allowance=p.margen_costura,
                    hem_allowance=p.margen_dobladillo,
                    grain=((2.0, waist + 2), (2.0, waist + peplum_len - 2)))
        shirt.pieces.insert(idx + 1, pep)
    return shirt


# ==========================================================================
# Estilos avanzados (reconstruyen la relación cuerpo/manga)
# ==========================================================================
def _grown_on(shirt: Shirt, sleeve_len_frac: float, wrist_extra: float,
              batwing: float, label: str) -> Shirt:
    """Manga cortada de una pieza con el cuerpo (dolman/kimono). Se construyen
    contornos frescos desde los landmarks del bloque y se une el canesú a la
    espalda (sin manga separada)."""
    from ..core.curves import smooth_curve
    p = shirt.p
    b = shirt.bodice
    ext = p.extension_boton
    fnd = p.escote_del_prof
    largo = p.largo_camisa
    SL = p.largo_manga * sleeve_len_frac
    WR = p.muneca + wrist_extra

    def wing(sp, us):
        wt = (sp[0] + SL, sp[1] + SL * 0.12)
        ww = (sp[0] + SL, sp[1] + SL * 0.12 + WR)
        under = smooth_curve([ww, (us[0] + batwing, us[1] + SL * 0.42),
                              (us[0] + 3, us[1] + 4), us], samples_per_span=8)
        return [sp, wt, ww] + under[1:]

    fpc = _find(shirt, "DELANTERO")
    if fpc:
        spF = b.points["D-SP"].as_tuple(); usF = b.points["D-US"].as_tuple()
        fc = [(-ext, fnd), (0.0, fnd)] + list(reversed(b.front_neck))[1:]
        fc += wing(spF, usF)
        fc += [b.points["D-Hs"].as_tuple(), (-ext, largo)]
        fpc.net_contour = ops.dedup(fc)
        fpc.name = "DELANTERO " + label

    bpc = _find(shirt, "ESPALDA")
    if bpc:
        spB = b.points["E-SP"].as_tuple(); usB = b.points["E-US"].as_tuple()
        bc = [b.points["E-CBn"].as_tuple()] + b.back_neck[1:]
        bc += wing(spB, usB)
        bc += [b.points["E-Hs"].as_tuple(), b.points["E-Hc"].as_tuple()]
        bpc.net_contour = ops.dedup(bc)
        bpc.name = "ESPALDA " + label

    shirt.pieces = [x for x in shirt.pieces if x.name != "CANESU"
                    and not x.name.startswith("MANGA")
                    and x.name not in ("PUNO", "TAPETA MANGA")]
    return shirt


def dolman(shirt: Shirt) -> Shirt:
    """Manga dolman/murciélago (grown-on con axila profunda)."""
    return _grown_on(shirt, sleeve_len_frac=0.68, wrist_extra=12.0,
                     batwing=13.0, label="DOLMAN")


def kimono(shirt: Shirt) -> Shirt:
    """Manga kimono (grown-on más recta y corta)."""
    return _grown_on(shirt, sleeve_len_frac=0.42, wrist_extra=8.0,
                     batwing=7.0, label="KIMONO")


def raglan(shirt: Shirt) -> Shirt:
    """Manga raglán: costura del escote a la axila; el cuerpo pierde el hombro."""
    from ..core.curves import smooth_curve
    p = shirt.p
    b = shirt.bodice
    ext = p.extension_boton
    fnd = p.escote_del_prof
    largo = p.largo_camisa

    # ---- delantero ----
    fpc = _find(shirt, "DELANTERO")
    if fpc:
        fn_rev = list(reversed(b.front_neck))            # CFn -> SNP
        rneck = ops.arclen_point(fn_rev, 0.5)
        rarm = ops.arclen_point(b.front_armhole, 0.45)   # SP -> US
        neck_part = ops.slice_curve(fn_rev, 0.0, 0.5)
        arm_part = ops.slice_curve(b.front_armhole, 0.45, 1.0)
        raglan_seam = smooth_curve([rneck, ((rneck[0] + rarm[0]) / 2 - 1,
                                            (rneck[1] + rarm[1]) / 2), rarm], samples_per_span=6)
        fc = [(-ext, fnd), (0.0, fnd)] + neck_part[1:] + raglan_seam[1:] + arm_part[1:]
        fc += [b.points["D-Hs"].as_tuple(), (-ext, largo)]
        fpc.net_contour = ops.dedup(fc)
        fpc.name = "DELANTERO RAGLAN"

    # ---- espalda (completa, sin canesú) ----
    bpc = _find(shirt, "ESPALDA")
    if bpc:
        rneck = ops.arclen_point(b.back_neck, 0.5)       # CBn -> SNP
        rarm = ops.arclen_point(b.back_armhole, 0.45)
        neck_part = ops.slice_curve(b.back_neck, 0.0, 0.5)
        arm_part = ops.slice_curve(b.back_armhole, 0.45, 1.0)
        raglan_seam = smooth_curve([rneck, ((rneck[0] + rarm[0]) / 2 - 1,
                                            (rneck[1] + rarm[1]) / 2), rarm], samples_per_span=6)
        bc = neck_part + raglan_seam[1:] + arm_part[1:]
        bc += [b.points["E-Hs"].as_tuple(), b.points["E-Hc"].as_tuple()]
        bpc.net_contour = ops.dedup(bc)
        bpc.name = "ESPALDA RAGLAN"

    # ---- manga raglán: cabeza con pico de hombro ----
    mpc = _find(shirt, "MANGA")
    if mpc:
        cap_h = shirt.sleeve.cap_height
        mpc.net_contour = ops.lift(mpc.net_contour, cap_h * 0.9, cap_h, above=True)
        mpc.name = "MANGA RAGLAN"

    shirt.pieces = [x for x in shirt.pieces if x.name != "CANESU"]
    return shirt


def godet(shirt: Shirt, godet_width: float = 20.0, from_frac: float = 0.55) -> Shirt:
    """Godets: piezas triangulares insertadas en los costados para dar vuelo."""
    from ..piece import Piece
    p = shirt.p
    top_y = p.prof_sisa + (p.largo_camisa - p.prof_sisa) * from_frac
    h = p.largo_camisa - top_y
    size = shirt.pieces[0].size if shirt.pieces else "S"
    contour = [(0.0, 0.0), (godet_width / 2, h), (-godet_width / 2, h)]
    god = Piece(name="GODET", number=40, size=size, quantity=4,
                cut_type="4 (en costados)", net_contour=contour,
                seam_allowance=p.margen_costura, hem_allowance=p.margen_dobladillo,
                grain=((0.0, 1.0), (0.0, h - 1)),
                reference_texts=[((0.0, h * 0.4), "godet")])
    shirt.pieces.append(god)
    # marca de abertura de godet en delantero y espalda (referencia)
    for name in ("DELANTERO", "ESPALDA"):
        pc = _find(shirt, name)
        if pc:
            xside = p.cuarto_busto
            pc.construction_lines = list(pc.construction_lines) + [
                ((xside, top_y), (xside, p.largo_camisa))]
    return shirt


def wrap_front(shirt: Shirt, wrap_x: float = 16.0) -> Shirt:
    """Delantero cruzado (wrap): borde interior diagonal que cruza al costado
    opuesto; sin botonadura (se ata al costado)."""
    p = shirt.p
    b = shirt.bodice
    fnd = p.escote_del_prof
    largo = p.largo_camisa
    pc = _find(shirt, "DELANTERO")
    if pc:
        fc = [(-wrap_x, largo), (0.0, fnd)] + list(reversed(b.front_neck))[1:]
        fc += [b.points["D-SP"].as_tuple()] + list(b.front_armhole[1:])
        fc += [b.points["D-Hs"].as_tuple()]
        pc.net_contour = ops.dedup(fc)
        pc.buttons = []
        pc.buttonholes = []
        pc.name = "DELANTERO WRAP"
        pc.reference_texts = list(pc.reference_texts) + [((-wrap_x * 0.5, largo - 4), "cruce")]
    return shirt


def back_pleat(shirt: Shirt, pleat: float = 6.0) -> Shirt:
    """Pliegue de tabla (box pleat) en el centro de la espalda."""
    pc = _find(shirt, "ESPALDA")
    if pc:
        ys = [q[1] for q in pc.net_contour]
        y_top, y_bot = min(ys), max(ys)
        shifted = [(x + pleat, y) for x, y in pc.net_contour]
        pc.net_contour = ops.dedup([(0.0, y_top)] + shifted + [(0.0, y_bot)])
        pc.construction_lines = list(pc.construction_lines) + [
            ((pleat, y_top), (pleat, y_bot)), ((0.0, y_top), (0.0, y_bot))]
        pc.reference_texts = list(pc.reference_texts) + [((pleat * 0.5, y_top + 3), "tabla")]
        pc.name = "ESPALDA (pliegue tabla)"
    return shirt


def off_shoulder(shirt: Shirt) -> Shirt:
    """Hombros descubiertos (bardot): escote ancho y bajo + manga corta."""
    _reshape_neck(shirt, drop=1.0, widen_neck=8.0, kind="scoop",
                  drop_collar=True, label="(bardot)")
    short_sleeve(shirt, at=0.30, name="MANGA (bardot)")
    return shirt


def tie_front(shirt: Shirt, waist_at: float = 0.45) -> Shirt:
    """Nudo delantero: recorta a la cintura (delantero corto, espalda algo más
    larga) y estrecha el bajo delantero hacia el centro (efecto de nudo)."""
    p = shirt.p
    hinge = p.prof_sisa
    cut_f = hinge + (p.largo_camisa - hinge) * waist_at
    cut_b = hinge + (p.largo_camisa - hinge) * (waist_at + 0.12)
    for name, cut in (("DELANTERO", cut_f), ("VISTA DELANTERA", cut_f),
                      ("ESPALDA", cut_b)):
        pc = _find(shirt, name)
        if pc:
            pc.net_contour = ops.clip_below(pc.net_contour, cut)
            pc.name = name + " (nudo)"
    f = _find(shirt, "DELANTERO")
    if f:
        ratio = -6.0 / ((p.busto + p.holgura_busto) / 4.0)
        f.net_contour = ops.flare(f.net_contour, 0.0, hinge, cut_f, ratio, side=+1)
    return shirt


def fitted_princess(sloper) -> "object":
    """Costura princesa sobre el bloque entallado: parte el delantero en panel
    centro + costado, **absorbiendo la pinza de busto y la de cintura** en la
    costura (línea princesa que pasa por el punto de busto). Requiere un sloper
    (`--fit fitted`)."""
    from ..core.curves import smooth_curve
    from ..piece import Piece
    fb = getattr(sloper, "fitted", None)
    if fb is None:
        raise ValueError("fitted_princess requiere un sloper (--fit fitted)")
    p = sloper.p
    d = fb.draft
    BP = fb.bust_point
    bust_y = d.points["D-US"].y
    quarter = d.points["D-US"].x
    waist_y = bust_y + fb.spec.bust_to_waist
    fwaist_y = waist_y + fb.spec.bust_dart
    side_supp = fb.side_supp
    w_side = quarter - side_supp
    fwd = fb.spec.front_waist_dart
    princess_x = BP[0] - 1.0

    cfn = d.points["D-CFn"].as_tuple()
    sp = d.points["D-SP"].as_tuple()
    arm = list(d.front_armhole)                       # SP..US
    ias = int(len(arm) * 0.5)
    AS = arm[ias]

    side_curve = smooth_curve([(quarter, bust_y),
                               (w_side + 0.6, (bust_y + fwaist_y) / 2),
                               (w_side, fwaist_y)], samples_per_span=6)
    pc_center = smooth_curve([AS, (BP[0] + 1.5, BP[1]), (princess_x, fwaist_y)],
                             samples_per_span=8)
    pc_side = smooth_curve([(princess_x + fwd, fwaist_y), (BP[0] - 1.0, BP[1]), AS],
                           samples_per_span=8)

    center = [cfn] + list(reversed(d.front_neck))[1:] + [sp] + arm[1:ias + 1]
    center += pc_center[1:] + [(0.0, fwaist_y)]
    side = list(arm[ias:]) + side_curve[1:] + [(princess_x + fwd, fwaist_y)] + pc_side[1:]

    from ..transform import operations as ops
    center_pc = Piece(name="DELANTERO CENTRO (princesa)", number=1, size=_sz(sloper),
                      quantity=2, cut_type="par: izq + der",
                      net_contour=ops.dedup(center), seam_allowance=p.margen_costura,
                      grain=((1.5, d.points["D-CFn"].y + 4), (1.5, fwaist_y - 3)),
                      drills=[BP])
    side_pc = Piece(name="DELANTERO COSTADO (princesa)", number=11, size=_sz(sloper),
                    quantity=2, cut_type="par: izq + der",
                    net_contour=ops.dedup(side), seam_allowance=p.margen_costura,
                    grain=((w_side * 0.6, bust_y + 3), (w_side * 0.6, fwaist_y - 3)))
    # reemplaza el delantero por los dos paneles (sin pinzas: absorbidas)
    front = _find(sloper, "DELANTERO")
    idx = sloper.pieces.index(front)
    sloper.pieces[idx:idx + 1] = [center_pc, side_pc]
    return sloper


def fitted_empire(sloper, at: float = 0.55, flare_add: float = 16.0,
                  skirt_len: float = 52.0) -> "object":
    """Corte imperio **dart-aware** sobre el sloper: la costura imperio pasa por
    debajo del busto; el **talle conserva la pinza de busto** (y la de hombro/
    omóplato) mientras que la **falda libera la supresión de cintura** en su vuelo
    (panel acampanado sin pinzas). Requiere un sloper (`--fit fitted`)."""
    from ..piece import Piece
    fb = getattr(sloper, "fitted", None)
    if fb is None:
        raise ValueError("fitted_empire requiere un sloper (--fit fitted)")
    p = sloper.p
    d = fb.draft
    bust_y = d.points["D-US"].y
    waist_y = bust_y + fb.spec.bust_to_waist
    empire_y = bust_y + (waist_y - bust_y) * at
    for name, released in (("DELANTERO", fb.spec.front_waist_dart),
                           ("ESPALDA", fb.spec.back_waist_dart)):
        pc = _find(sloper, name)
        if pc is None:
            continue
        w_top = _side_x_at(pc.net_contour, empire_y)
        pc.net_contour = ops.clip_below(pc.net_contour, empire_y)
        # conserva sólo las pinzas cuyas bases quedan enteras en el talle
        pc.darts = [dt for dt in pc.darts if max(dt[0][1], dt[2][1]) < empire_y - 1e-6]
        pc.hem_allowance = None
        pc.name = name + " TALLE (imperio)"
        half = w_top + flare_add + released      # supresión de cintura -> vuelo
        hem_y = empire_y + skirt_len
        skirt_c = [(0.0, empire_y), (w_top, empire_y), (half, hem_y), (0.0, hem_y)]
        skirt = Piece(name=name + " FALDA (imperio)", number=pc.number + 20,
                      size=pc.size, quantity=1, cut_type="al doblez",
                      on_fold=True, fold_x=0.0, net_contour=skirt_c,
                      seam_allowance=p.margen_costura, hem_allowance=p.margen_dobladillo,
                      grain=((w_top * 0.5, empire_y + 2), (w_top * 0.5, hem_y - 2)),
                      reference_texts=[((half * 0.4, (empire_y + hem_y) / 2), "vuelo")])
        sloper.pieces.insert(sloper.pieces.index(pc) + 1, skirt)
    return sloper


def fitted_peplum(sloper, peplum_len: float = 18.0, flare_add: float = 24.0) -> "object":
    """Peplum **dart-aware** sobre el sloper: el **talle conserva todas las pinzas**
    (busto + cintura) hasta la cintura natural; el **volante** arranca en la cintura
    como pieza acampanada sin pinzas (la supresión se suelta en el vuelo). Requiere
    un sloper (`--fit fitted`)."""
    from ..piece import Piece
    fb = getattr(sloper, "fitted", None)
    if fb is None:
        raise ValueError("fitted_peplum requiere un sloper (--fit fitted)")
    p = sloper.p
    d = fb.draft
    bust_y = d.points["D-US"].y
    waist_y = bust_y + fb.spec.bust_to_waist
    for name, released in (("DELANTERO", fb.spec.front_waist_dart),
                           ("ESPALDA", fb.spec.back_waist_dart)):
        pc = _find(sloper, name)
        if pc is None:
            continue
        w_top = _side_x_at(pc.net_contour, waist_y)
        pc.name = name + " TALLE (peplum)"       # mantiene todas sus pinzas
        half = w_top + flare_add + released
        hem_y = waist_y + peplum_len
        pep_c = [(0.0, waist_y), (w_top, waist_y), (half, hem_y), (0.0, hem_y)]
        pep = Piece(name=name + " VOLANTE (peplum)", number=pc.number + 30,
                    size=pc.size, quantity=1, cut_type="al doblez",
                    on_fold=True, fold_x=0.0, net_contour=pep_c,
                    seam_allowance=p.margen_costura, hem_allowance=p.margen_dobladillo,
                    grain=((w_top * 0.5, waist_y + 2), (w_top * 0.5, hem_y - 2)),
                    reference_texts=[((half * 0.4, (waist_y + hem_y) / 2), "vuelo")])
        sloper.pieces.insert(sloper.pieces.index(pc) + 1, pep)
    return sloper


def _sz(garment):
    return garment.p._base["talla_nombre"].descripcion.replace("talla ", "")


# estilos que requieren/aprovechan el bloque entallado (sloper)
FITTED_STYLES = {
    "princess": fitted_princess,
    "empire": fitted_empire,
    "peplum": fitted_peplum,
}


STYLES = {
    "flare": flare_shirt,
    "puff": puff_sleeve,
    "bell": bell_sleeve,
    "mandarin": mandarin_collar,
    "sleeveless": sleeveless,
    "crop": crop_top,
    "princess": princess_front,
    "short_sleeve": short_sleeve,
    "cap_sleeve": cap_sleeve,
    "dress": dress,
    "oversized": oversized,
    "empire": empire,
    "v_neck": v_neck,
    "boat_neck": boat_neck,
    "hi_lo": hi_lo,
    "cocoon": cocoon,
    "peplum": peplum,
    "dolman": dolman,
    "kimono": kimono,
    "raglan": raglan,
    "godet": godet,
    "wrap": wrap_front,
    "back_pleat": back_pleat,
    "off_shoulder": off_shoulder,
    "tie_front": tie_front,
}


def apply_style(shirt: Shirt, style: str, **kw) -> Shirt:
    if style in (None, "", "none"):
        return shirt
    # falda: registro de estilos propio
    if getattr(shirt, "prenda", "").startswith("falda"):
        from .skirt_styles import SKIRT_STYLES
        if style not in SKIRT_STYLES:
            raise KeyError(f"Estilo de falda desconocido: '{style}'. "
                           f"Opciones: {list(SKIRT_STYLES)}")
        shirt = SKIRT_STYLES[style](shirt, **kw)
        shirt.layout()
        return shirt
    # sobre el sloper (bloque entallado) hay versiones dart-aware
    is_sloper = hasattr(shirt, "fitted")
    if is_sloper and style in FITTED_STYLES:
        shirt = FITTED_STYLES[style](shirt, **kw)
    elif style in STYLES:
        shirt = STYLES[style](shirt, **kw)
    else:
        raise KeyError(f"Estilo desconocido: '{style}'. Opciones: {list(STYLES)}")
    shirt.layout()
    return shirt
