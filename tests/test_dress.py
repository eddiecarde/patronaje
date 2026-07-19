"""Tests del vestido (cuerpo entallado + falda con costura de talle)."""
import os
import tempfile

import pytest

from patronaje.garment.dress import build_dress
from patronaje.transform.styles import apply_style
from patronaje.transform.dress_styles import DRESS_STYLES
from patronaje.validation.validators import (
    ValidationReport, validate_piece_geometry, validate_notch_matching)

METHODS = ["aldrich", "mueller", "bunka", "esmod", "marti", "armstrong"]


def _geom_ok(g):
    rep = ValidationReport()
    for pc in g.pieces:
        validate_piece_geometry(pc, rep)
    return rep.ok


def _skirt_front(g):
    return next(p for p in g.pieces if p.name.startswith("VESTIDO FALDA DELANTERA"))


def _hem_width(g):
    pc = _skirt_front(g)
    ymax = max(q[1] for q in pc.net_contour)
    xs = [x for x, y in pc.net_contour if abs(y - ymax) < 0.6]
    return max(xs) - min(xs)


def _length(g):
    return max(q[1] for q in _skirt_front(g).net_contour)


@pytest.mark.parametrize("method", METHODS)
def test_dress_valid_each_method(method):
    d = build_dress("S", method=method).layout()
    assert len(d.pieces) == 5     # talle del/esp + falda del/tra + manga
    assert _geom_ok(d)


def test_dress_waist_seam_matches_within_ease():
    d = build_dress("S", method="aldrich")
    rep = ValidationReport()
    validate_notch_matching(d, rep, tol=2.0)
    assert rep.ok
    # el talle casa con la falda dentro de una holgura de montaje razonable
    for name, bw, sw in d.seam_matching:
        assert abs(bw - sw) < 2.0, name


def test_dress_pieces_carry_darts():
    d = build_dress("S")
    bod = next(p for p in d.pieces if p.name.startswith("VESTIDO DELANTERO"))
    sk = _skirt_front(d)
    assert len(bod.darts) >= 1 and len(sk.darts) == 1


@pytest.mark.parametrize("style", list(DRESS_STYLES))
def test_every_dress_style_valid(style):
    d = apply_style(build_dress("S"), style)
    assert _geom_ok(d)


def test_sin_mangas_drops_sleeve():
    d = apply_style(build_dress("S"), "sin_mangas")
    assert not any(p.name.startswith("MANGA") for p in d.pieces)
    assert len(d.pieces) == 4


def test_flare_widens_and_length_changes():
    base = _hem_width(build_dress("S").layout())
    assert _hem_width(apply_style(build_dress("S"), "evase")) > base + 4
    baseL = _length(build_dress("S"))
    assert _length(apply_style(build_dress("S"), "maxi")) > baseL
    assert _length(apply_style(build_dress("S"), "mini")) < baseL


def test_godet_adds_piece_and_unknown_style_raises():
    assert len(apply_style(build_dress("S"), "godet").pieces) == 6
    with pytest.raises(KeyError):
        apply_style(build_dress("S"), "no_existe")


def test_dress_cli_export_with_method_and_style():
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d, garment="dress", method="bunka", style="evase", quiet=True)
    assert os.path.basename(outs["dxf_r2013"]).startswith("vestido_S_bunka_evase")
    assert "techpack" not in outs
    for k in ["svg", "json", "csv", "marker_150"]:
        assert os.path.exists(outs[k]) and os.path.getsize(outs[k]) > 0
