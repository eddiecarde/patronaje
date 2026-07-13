"""Planos técnicos (fashion flats) de la camisa: delantero y trasero.

Dibujos esquemáticos y **paramétricos** de la prenda terminada (no del patrón),
como los que encabezan una ficha técnica. Se construyen desde las medidas del
motor, de modo que también escalan con la talla. Devuelven SVG inline (string)
para incrustar en el tech pack, y detalles de cuello/manga/puño/bolsillo.
"""
from __future__ import annotations

import svgwrite

from ..parametric.parameters import Parameters


def _dims(p: Parameters):
    HB = (p.busto + p.holgura_busto) / 4.0          # medio ancho de pecho (flat)
    waist = (p.cintura + 10) / 4.0
    hem = (p.cadera + 8) / 4.0
    L = p.largo_camisa
    AD = p.prof_sisa
    nw = p.escote_del_ancho + 0.5
    nd = p.escote_del_prof
    sh = p.ancho_espalda / 2.0 + 1.0
    SL = p.largo_manga
    cuffw = (p.muneca + 3) / 2.0
    return dict(HB=HB, waist=waist, hem=hem, L=L, AD=AD, nw=nw, nd=nd, sh=sh,
                SL=SL, cuffw=cuffw)


def garment_flat_svg(p: Parameters, view: str = "front") -> str:
    d = _dims(p)
    HB, waist, hem, L, AD = d["HB"], d["waist"], d["hem"], d["L"], d["AD"]
    nw, nd, sh, SL, cuffw = d["nw"], d["nd"], d["sh"], d["SL"], d["cuffw"]
    back = view == "back"
    neck_depth = 2.0 if back else nd

    W = 2 * (sh + SL * 0.62) + 20
    H = L + 14
    dwg = svgwrite.Drawing(size=(f"{W}cm", f"{H}cm"), viewBox=f"{-W/2} -6 {W} {H}")
    body = dwg.g(fill="#eef4fb", stroke="#22405e", stroke_width=0.25)
    line = dwg.g(fill="none", stroke="#22405e", stroke_width=0.2)
    thin = dwg.g(fill="none", stroke="#6b8199", stroke_width=0.15)

    # ---- mangas (laid-flat, salen del hombro) ----
    for s in (-1, 1):
        x_sh = s * sh
        sleeve = [
            (x_sh, 2.0),
            (s * (sh + SL * 0.60), AD * 0.55),
            (s * (sh + SL * 0.60), AD * 0.55 + SL * 0.62),
            (s * (sh + SL * 0.60 - (SL * 0.60 - cuffw)), AD * 0.55 + SL * 0.62 + 3),
            (s * (HB - 0.5), AD + 1.0),
        ]
        body.add(dwg.polygon(points=sleeve))
        # puño
        cw0 = s * (sh + SL * 0.60)
        cw1 = s * (sh + SL * 0.60 - (SL * 0.60 - cuffw))
        yb = AD * 0.55 + SL * 0.62
        body.add(dwg.polygon(points=[(cw0, yb), (cw0, yb + 4.0),
                                     (cw1, yb + 7.0), (cw1, yb + 3.0)],
                             fill="#dbe7f4"))

    # ---- cuerpo ----
    bodypts = [
        (-nw, neck_depth),
        (-sh, 2.0),
        (-HB, AD),
        (-waist, AD + (L - AD) * 0.5),
        (-hem, L),
        (hem, L),
        (waist, AD + (L - AD) * 0.5),
        (HB, AD),
        (sh, 2.0),
        (nw, neck_depth),
    ]
    body.add(dwg.polygon(points=bodypts))

    # ---- escote / cuello ----
    if back:
        line.add(dwg.path(d=f"M {-nw},{neck_depth} Q 0,{neck_depth+1.5} {nw},{neck_depth}"))
        # línea de canesú
        thin.add(dwg.line((-sh + 1, p.linea_canesu), (sh - 1, p.linea_canesu)))
    else:
        line.add(dwg.path(d=f"M {-nw},{neck_depth} Q 0,{neck_depth+2.5} {nw},{neck_depth}"))
    # banda de cuello (pie) y cuello
    band_h = 2.2
    line.add(dwg.rect(insert=(-nw - 0.5, neck_depth - band_h), size=(2 * nw + 1, band_h),
                      rx=0.4, fill="#dbe7f4"))
    collar = [(-nw - 2.5, neck_depth - band_h - 3.0), (-nw - 0.5, neck_depth - band_h),
              (nw + 0.5, neck_depth - band_h), (nw + 2.5, neck_depth - band_h - 3.0),
              (nw, neck_depth - band_h - 4.5), (-nw, neck_depth - band_h - 4.5)]
    body.add(dwg.polygon(points=collar, fill="#dbe7f4"))

    if not back:
        # tapeta y botones
        line.add(dwg.line((0, neck_depth), (0, L)))
        line.add(dwg.line((1.6, neck_depth), (1.6, L)))
        ny = 8
        for i in range(ny):
            by = neck_depth + 3 + (L - neck_depth - 8) * i / (ny - 1)
            body.add(dwg.circle(center=(0.8, by), r=0.45, fill="#22405e"))
        # bolsillo de parche (lado izq de quien mira -> derecho de la prenda)
        px, py, pw, ph = -HB * 0.55, AD + 2.0, 12.0, 13.5
        body.add(dwg.polygon(points=[(px, py), (px + pw, py), (px + pw, py + ph * 0.72),
                                     (px + pw / 2, py + ph), (px, py + ph * 0.72)],
                             fill="none"))

    dwg.add(body); dwg.add(line); dwg.add(thin)
    title = "TRASERO" if back else "DELANTERO"
    dwg.add(dwg.text(f"PLANO {title}", insert=(-W / 2 + 2, H - 8),
                     font_size=2.2, font_family="sans-serif", fill="#22405e"))
    return dwg.tostring()


def piece_detail_svg(piece, title: str = "") -> str:
    """SVG inline de una pieza (línea de corte + costura + hilo) para detalles."""
    cut = piece.cut_contour()
    xs = [q[0] for q in cut]; ys = [q[1] for q in cut]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    w = (maxx - minx) + 4; h = (maxy - miny) + 6
    dwg = svgwrite.Drawing(size=(f"{w}cm", f"{h}cm"),
                           viewBox=f"{minx-2} {miny-4} {w} {h}")
    dwg.add(dwg.polygon(points=cut, fill="#eef4fb", stroke="#d00", stroke_width=0.12))
    dwg.add(dwg.polygon(points=list(piece.net_contour), fill="none",
                        stroke="#0a0", stroke_width=0.08))
    if piece.grain:
        (x1, y1), (x2, y2) = piece.grain
        dwg.add(dwg.line((x1, y1), (x2, y2), stroke="#c0a000", stroke_width=0.12))
    dwg.add(dwg.text(title or piece.name, insert=(minx, miny - 1.2),
                     font_size=1.4, font_family="sans-serif", fill="#000"))
    return dwg.tostring()
