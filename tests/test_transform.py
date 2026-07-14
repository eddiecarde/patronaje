"""Tests de la capa de manipulación de bloque (estilos)."""
from patronaje.garment.shirt import build_shirt
from patronaje.transform.styles import flare_shirt, puff_sleeve, apply_style
from patronaje.transform import operations as ops
from patronaje.validation.validators import ValidationReport, validate_piece_geometry


def _hem_width(shirt, name):
    pc = next(p for p in shirt.pieces if p.name.startswith(name))
    ys = [q[1] for q in pc.net_contour]
    ymax = max(ys)
    xs = [q[0] for q in pc.net_contour if abs(q[1] - ymax) < 0.5]
    return max(xs) - min(xs)


def _geom_ok(shirt):
    rep = ValidationReport()
    for pc in shirt.pieces:
        validate_piece_geometry(pc, rep)
    return rep.ok


def test_flare_widens_hem_and_stays_valid():
    base_w = _hem_width(build_shirt("S"), "DELANTERO")
    fl = flare_shirt(build_shirt("S"), added_hem=12).layout()
    assert _hem_width(fl, "DELANTERO") > base_w + 8
    assert _geom_ok(fl)


def test_puff_widens_sleeve_and_stays_valid():
    base = build_shirt("S")
    base_area = next(p for p in base.pieces if p.name == "MANGA").area()
    pf = puff_sleeve(build_shirt("S")).layout()
    assert next(p for p in pf.pieces if p.name.startswith("MANGA")).area() > base_area
    assert _geom_ok(pf)


def test_apply_style_dispatch_and_noop():
    sh = apply_style(build_shirt("S"), "none")
    assert len(sh.pieces) == 10
    fl = apply_style(build_shirt("S"), "flare")
    assert any("acampanado" in p.name for p in fl.pieces)


def test_flare_keeps_center_front_straight():
    fl = flare_shirt(build_shirt("S"), added_hem=12)
    pc = next(p for p in fl.pieces if p.name.startswith("DELANTERO"))
    # el centro (x<=0, banda/CF) no se abre: no aparecen x negativos grandes nuevos
    assert min(q[0] for q in pc.net_contour) > -3.0


def test_pivot_operation():
    import math
    pts = [(0, 0), (10, 0)]
    out = ops.pivot(pts, (0, 0), math.pi / 2, moving=lambda p: p[0] > 5)
    # (10,0) rota 90° alrededor del origen -> (0,10)
    assert abs(out[1][0]) < 1e-9 and abs(out[1][1] - 10) < 1e-9
