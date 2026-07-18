"""Tests del bloque y prenda de falda base (recta / lápiz)."""
import os
import tempfile

import pytest

from patronaje.parametric.measurements import build_parameters
from patronaje.blocks.skirt import build_skirt_block
from patronaje.garment.skirt import build_skirt
from patronaje.validation.validators import ValidationReport, validate_piece_geometry

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]


def _geom_ok(g):
    rep = ValidationReport()
    for pc in g.pieces:
        validate_piece_geometry(pc, rep)
    return rep.ok


@pytest.mark.parametrize("size", SIZES)
def test_skirt_valid_geometry_each_size(size):
    sk = build_skirt(size).layout()
    assert len(sk.pieces) == 3
    assert _geom_ok(sk)


def test_skirt_piece_roles_and_darts():
    sk = build_skirt("S")
    names = [pc.name for pc in sk.pieces]
    assert names == ["FALDA DELANTERA", "FALDA TRASERA", "PRETINA"]
    front, back, band = sk.pieces
    assert len(front.darts) == 1 and len(back.darts) == 1 and len(band.darts) == 0
    # ambos paneles al doblez y con dobladillo real
    assert front.on_fold and back.on_fold
    assert front.hem_allowance == build_parameters("S").margen_dobladillo


def test_skirt_waist_and_hip_match_measurements():
    p = build_parameters("S")
    blk = build_skirt_block(p)
    assert abs(blk.waist_length() - (p.cintura + p.holgura_cintura_falda)) < 1e-6
    assert abs(blk.hip_length() - (p.cadera + p.holgura_cadera)) < 1e-6


def test_back_dart_longer_than_front():
    blk = build_skirt_block(build_parameters("S"))
    (fb1, fapex, fb2) = blk.front_darts[0]
    (bb1, bapex, bb2) = blk.back_darts[0]
    assert bapex[1] > fapex[1]      # la pinza trasera apunta más abajo


def test_skirt_regenerates_parametrically():
    small = build_skirt_block(build_parameters("XS")).hip_length()
    big = build_skirt_block(build_parameters("XXL")).hip_length()
    assert big > small + 10


def test_skirt_cli_exports_without_techpack():
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d, garment="skirt", quiet=True)
    for k in ["dxf_r2013", "svg", "json", "csv", "scr", "marker_150"]:
        assert os.path.exists(outs[k]) and os.path.getsize(outs[k]) > 0
    assert "techpack" not in outs           # el tech pack es específico de camisa
    assert os.path.basename(outs["dxf_r2013"]).startswith("falda_S")
