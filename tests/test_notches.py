"""Tests del casado automático de piquetes entre costuras."""
from patronaje.garment.shirt import build_shirt
from patronaje.garment.skirt import build_skirt
from patronaje.garment.notches import seam_subpath, match_seam, _polylen
from patronaje.validation.validators import ValidationReport, validate_notch_matching


def test_seam_subpath_picks_shorter_side():
    # cuadrado unidad; de (0,0) a (1,0): camino corto es el borde directo
    sq = [(0, 0), (1, 0), (1, 1), (0, 1)]
    short = seam_subpath(sq, (0, 0), (1, 0), prefer="short")
    long = seam_subpath(sq, (0, 0), (1, 0), prefer="long")
    assert abs(_polylen(short) - 1.0) < 1e-9
    assert _polylen(long) > _polylen(short)


def test_shirt_side_seam_matches_exactly():
    sh = build_shirt("S")
    seams = dict((n, (a, b)) for n, a, b in sh.seam_matching)
    la, lb = seams["costado del/esp"]
    assert abs(la - lb) < 0.5           # costado delantero == trasero


def test_shirt_shoulder_matches_yoke():
    sh = build_shirt("S")
    seams = dict((n, (a, b)) for n, a, b in sh.seam_matching)
    la, lb = seams["hombro del/canesú"]
    assert abs(la - lb) < 0.5


def test_matched_notches_added_to_both_pieces():
    sh = build_shirt("S")
    front = next(p for p in sh.pieces if p.name == "DELANTERO")
    back = next(p for p in sh.pieces if p.name == "ESPALDA")
    # el costado añade 2 piquetes casados a cada pieza (además de los propios)
    assert len(front.notches) >= 2 and len(back.notches) >= 2


def test_notch_lands_on_the_seam_subpath():
    from shapely.geometry import LineString, Point
    sh = build_shirt("S")
    b = sh.bodice
    front = next(p for p in sh.pieces if p.name == "DELANTERO")
    sub = LineString(seam_subpath(front.net_contour, b.points["D-US"].as_tuple(),
                                  b.points["D-Hs"].as_tuple()))
    # cada piquete casado del costado cae sobre el tramo de costura (dist ~0)
    on_seam = [n for n in front.notches if sub.distance(Point(n)) < 1e-6]
    assert len(on_seam) >= 2


def test_skirt_side_seam_matches_and_validates():
    sk = build_skirt("S")
    seams = dict((n, (a, b)) for n, a, b in sk.seam_matching)
    la, lb = seams["costado falda"]
    assert abs(la - lb) < 0.5
    rep = ValidationReport()
    validate_notch_matching(sk, rep)
    assert rep.ok


def test_match_seam_returns_segment_lengths():
    sh = build_shirt("S")
    b = sh.bodice
    front = next(p for p in sh.pieces if p.name == "DELANTERO")
    back = next(p for p in sh.pieces if p.name == "ESPALDA")
    la, lb = match_seam(front, b.points["D-US"].as_tuple(), b.points["D-Hs"].as_tuple(),
                        back, b.points["E-US"].as_tuple(), b.points["E-Hs"].as_tuple())
    assert la > 0 and lb > 0
