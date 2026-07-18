"""Tests de márgenes de costura por borde y piquetes de dobladillo."""
from patronaje.garment.shirt import build_shirt
from patronaje.piece import ENotch, Layer


def _piece(sh, name):
    return next(p for p in sh.pieces if p.name == name)


def test_hem_margin_larger_than_seam():
    sh = build_shirt("S")
    front = _piece(sh, "DELANTERO")
    net = front.net_contour
    cut = front.cut_contour()
    net_maxy = max(q[1] for q in net)
    cut_maxy = max(q[1] for q in cut)
    net_maxx = max(q[0] for q in net)
    cut_maxx = max(q[0] for q in cut)
    # el dobladillo (borde inferior) crece ~hem_allowance (2.5)
    assert abs((cut_maxy - net_maxy) - front.hem_allowance) < 0.4
    # el costado crece ~seam_allowance (1.0)
    assert abs((cut_maxx - net_maxx) - front.seam_allowance) < 0.4
    assert front.hem_allowance > front.seam_allowance


def test_fold_edge_has_no_margin():
    sh = build_shirt("S")
    back = _piece(sh, "ESPALDA")   # al doblez en CB (x=0)
    cut = back.cut_contour()
    # el borde de doblez sigue en x≈0 (sin margen)
    assert min(q[0] for q in cut) > -0.2


def test_hem_notches_present():
    sh = build_shirt("S")
    front = _piece(sh, "DELANTERO")
    assert len(front.hem_corners()) == 2
    notches = [e for e in front.get_entities()
               if isinstance(e, ENotch) and e.layer == Layer.PIQUETES]
    assert len(notches) >= 2   # incluye los piquetes de dobladillo


def test_cut_line_still_valid():
    from shapely.geometry import Polygon
    sh = build_shirt("S")
    for name in ("DELANTERO", "ESPALDA"):
        cut = _piece(sh, name).cut_contour()
        assert Polygon(cut).is_valid and Polygon(cut).is_simple
