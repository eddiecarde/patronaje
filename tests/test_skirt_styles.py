"""Tests de los estilos de falda (manipulación del bloque de falda)."""
import os
import tempfile

import pytest

from patronaje.garment.skirt import build_skirt
from patronaje.transform.styles import apply_style
from patronaje.transform.skirt_styles import SKIRT_STYLES
from patronaje.validation.validators import ValidationReport, validate_piece_geometry


def _geom_ok(g):
    rep = ValidationReport()
    for pc in g.pieces:
        validate_piece_geometry(pc, rep)
    return rep.ok


def _front(g):
    return next(p for p in g.pieces if p.name.startswith("FALDA DELANTERA"))


def _hem_width(g):
    pc = _front(g)
    ys = [q[1] for q in pc.net_contour]
    ymax = max(ys)
    xs = [x for x, y in pc.net_contour if abs(y - ymax) < 0.5]
    return max(xs) - min(xs)


def _length(g):
    pc = _front(g)
    return max(q[1] for q in pc.net_contour)


@pytest.mark.parametrize("style", list(SKIRT_STYLES))
def test_every_skirt_style_geometry_valid(style):
    g = apply_style(build_skirt("S"), style)
    assert len(g.pieces) >= 3
    assert _geom_ok(g), f"estilo de falda {style} inválido"


def test_flared_styles_widen_hem():
    base = _hem_width(build_skirt("S").layout())
    assert _hem_width(apply_style(build_skirt("S"), "evase")) > base + 5
    assert _hem_width(apply_style(build_skirt("S"), "circular")) > \
        _hem_width(apply_style(build_skirt("S"), "evase"))


def test_full_waist_styles_drop_darts():
    for st in ("fruncida", "tableada"):
        g = apply_style(build_skirt("S"), st)
        assert all(len(pc.darts) == 0 for pc in g.pieces)


def test_mini_shorter_and_maxi_longer():
    base = _length(build_skirt("S"))
    assert _length(apply_style(build_skirt("S"), "mini")) < base
    assert _length(apply_style(build_skirt("S"), "maxi")) > base


def test_yoke_and_godet_add_pieces():
    assert len(apply_style(build_skirt("S"), "yoke").pieces) == 5   # 2 canesú + 2 inferior + pretina
    assert len(apply_style(build_skirt("S"), "godet").pieces) == 4  # + godet


def test_tubo_narrows_hem():
    base = _hem_width(build_skirt("S").layout())
    assert _hem_width(apply_style(build_skirt("S"), "tubo")) < base


def test_unknown_skirt_style_raises():
    with pytest.raises(KeyError):
        apply_style(build_skirt("S"), "no_existe")


def test_skirt_style_cli_export():
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d, garment="skirt", style="evase", quiet=True)
    assert os.path.basename(outs["dxf_r2013"]).startswith("falda_S_evase")
    assert os.path.getsize(outs["svg"]) > 0
