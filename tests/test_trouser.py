"""Tests del bloque y prenda de pantalón base."""
import os
import tempfile

import pytest

from patronaje.parametric.measurements import build_parameters
from patronaje.blocks.trouser import build_trouser_block
from patronaje.garment.trouser import build_trouser
from patronaje.validation.validators import (
    ValidationReport, validate_piece_geometry, validate_notch_matching)

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]


def _report(g):
    rep = ValidationReport()
    for pc in g.pieces:
        validate_piece_geometry(pc, rep)
    validate_notch_matching(g, rep)
    return rep


@pytest.mark.parametrize("size", SIZES)
def test_trouser_valid_geometry_each_size(size):
    t = build_trouser(size).layout()
    assert len(t.pieces) == 3
    assert _report(t).ok


def test_trouser_piece_roles_and_darts():
    t = build_trouser("S")
    names = [pc.name for pc in t.pieces]
    assert names == ["PANTALON DELANTERO", "PANTALON TRASERO", "PRETINA"]
    front, back, band = t.pieces
    assert len(front.darts) == 1 and len(back.darts) == 1 and len(band.darts) == 0
    assert front.hem_allowance == build_parameters("S").margen_dobladillo


def test_back_fork_deeper_than_front():
    blk = build_trouser_block(build_parameters("S"))
    front_min_x = min(x for x, y in blk.front)
    back_min_x = min(x for x, y in blk.back)
    assert back_min_x < front_min_x       # el gancho trasero es más profundo


def test_inseam_front_back_match():
    blk = build_trouser_block(build_parameters("S"))
    assert abs(blk.inseam_length() - blk.inseam_length(True)) < 0.8


def test_seam_matching_within_tolerance():
    t = build_trouser("S")
    for name, la, lb in t.seam_matching:
        assert abs(la - lb) < 0.8, name


def test_trouser_regenerates_parametrically():
    small = build_trouser_block(build_parameters("XS")).waist_length()
    big = build_trouser_block(build_parameters("XXL")).waist_length()
    assert big > small + 10


def test_trouser_cli_exports_without_techpack():
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d, garment="trouser", quiet=True)
    for k in ["dxf_r2013", "svg", "json", "csv", "scr", "marker_150"]:
        assert os.path.exists(outs[k]) and os.path.getsize(outs[k]) > 0
    assert "techpack" not in outs
    assert os.path.basename(outs["dxf_r2013"]).startswith("pantalon_S")
