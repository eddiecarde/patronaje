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
    return next((p for p in shirt.pieces if p.name == name), None)


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
                    grain=((2.0, waist + 2), (2.0, waist + peplum_len - 2)))
        shirt.pieces.insert(idx + 1, pep)
    return shirt


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
}


def apply_style(shirt: Shirt, style: str, **kw) -> Shirt:
    if style in (None, "", "none"):
        return shirt
    if style not in STYLES:
        raise KeyError(f"Estilo desconocido: '{style}'. Opciones: {list(STYLES)}")
    shirt = STYLES[style](shirt, **kw)
    shirt.layout()
    return shirt
