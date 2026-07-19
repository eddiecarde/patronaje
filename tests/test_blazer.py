"""Tests de la chaqueta/blazer (manga 2 piezas, solapa, cuello, vista, forro)."""
import os
import tempfile

import pytest

from patronaje.blocks.blazer import build_two_piece_sleeve
from patronaje.garment.blazer import build_blazer
from patronaje.transform.styles import apply_style
from patronaje.transform.blazer_styles import BLAZER_STYLES
from patronaje.parametric.measurements import build_parameters
from patronaje.validation.validators import (
    ValidationReport, validate_piece_geometry, validate_notch_matching)

METHODS = ["aldrich", "mueller", "bunka", "esmod", "marti", "armstrong"]


def _report(z, tol=1.0):
    rep = ValidationReport()
    for pc in z.pieces:
        validate_piece_geometry(pc, rep)
    validate_notch_matching(z, rep, tol=tol)
    return rep


def _front(z):
    return next(p for p in z.pieces if p.name.startswith("CHAQUETA DELANTERO"))


@pytest.mark.parametrize("method", METHODS)
def test_blazer_valid_each_method(method):
    z = build_blazer("S", method=method).layout()
    assert len(z.pieces) == 8
    assert _report(z).ok


def test_two_piece_sleeve_seams_equal_length():
    s = build_two_piece_sleeve(build_parameters("S"), 40.0)
    # mangón y soplillo comparten longitud de costura -> casan
    assert abs(s.seam_len_front - s.seam_len_back) < 1e-6
    from shapely.geometry import Polygon
    assert Polygon(s.top).is_valid and Polygon(s.under).is_valid


def test_blazer_seam_matching_exact():
    z = build_blazer("S")
    names = [n for n, _, _ in z.seam_matching]
    assert "costado del/esp" in names
    assert any("manga" in n for n in names)
    for n, a, b in z.seam_matching:
        assert abs(a - b) < 1.0, n


def test_front_has_lapel_and_interior_darts():
    z = build_blazer("S")
    f = _front(z)
    # la solapa sale más allá de la extensión de botonadura (x muy negativo)
    assert min(x for x, y in f.net_contour) < -5.0
    # pinza de busto + ojo de pez de cintura (2) = 3 pinzas interiores
    assert len(f.darts) == 3
    assert len(f.buttons) >= 1


def test_pieces_present():
    names = {p.name for p in build_blazer("S").pieces}
    for expected in ["MANGA SUPERIOR", "MANGA INFERIOR", "CUELLO SASTRE",
                     "VISTA DELANTERA", "FORRO DELANTERO", "FORRO ESPALDA"]:
        assert any(n.startswith(expected) for n in names), expected


@pytest.mark.parametrize("style", list(BLAZER_STYLES))
def test_every_blazer_style_valid(style):
    z = apply_style(build_blazer("S"), style)
    assert _report(z).ok


def test_sin_forro_drops_lining_and_length_styles():
    assert len(apply_style(build_blazer("S"), "sin_forro").pieces) == 6
    baseL = max(q[1] for q in _front(build_blazer("S")).net_contour)
    crop = max(q[1] for q in _front(apply_style(build_blazer("S"), "crop")).net_contour)
    lon = max(q[1] for q in _front(apply_style(build_blazer("S"), "longline")).net_contour)
    assert crop < baseL < lon


def test_cruzada_widens_front_and_adds_buttons():
    base = _front(build_blazer("S"))
    cru = _front(apply_style(build_blazer("S"), "cruzada"))
    assert min(x for x, y in cru.net_contour) < min(x for x, y in base.net_contour)
    assert len(cru.buttons) > len(base.buttons)


def test_blazer_cli_export():
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d, garment="blazer", method="bunka", style="longline", quiet=True)
    assert os.path.basename(outs["dxf_r2013"]).startswith("blazer_S_bunka_longline")
    assert "techpack" not in outs
    for k in ["svg", "json", "csv", "marker_150"]:
        assert os.path.exists(outs[k]) and os.path.getsize(outs[k]) > 0
