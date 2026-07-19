"""Tests de los estilos de pantalón (manipulación del bloque)."""
import os
import tempfile

import pytest

from patronaje.garment.trouser import build_trouser
from patronaje.transform.styles import apply_style
from patronaje.transform.trouser_styles import TROUSER_STYLES
from patronaje.validation.validators import ValidationReport, validate_piece_geometry


def _geom_ok(g):
    rep = ValidationReport()
    for pc in g.pieces:
        validate_piece_geometry(pc, rep)
    return rep.ok


def _front(g):
    return next(p for p in g.pieces if p.name.startswith("PANTALON DELANTERO"))


def _hem_width(g):
    pc = _front(g)
    ymax = max(q[1] for q in pc.net_contour)
    xs = [x for x, y in pc.net_contour if abs(y - ymax) < 0.6]
    return max(xs) - min(xs)


def _length(g):
    return max(q[1] for q in _front(g).net_contour)


@pytest.mark.parametrize("style", list(TROUSER_STYLES))
def test_every_trouser_style_geometry_valid(style):
    g = apply_style(build_trouser("S"), style)
    assert len(g.pieces) == 3
    assert _geom_ok(g), f"estilo de pantalón {style} inválido"


def test_pitillo_narrows_and_wide_widens():
    base = _hem_width(build_trouser("S").layout())
    assert _hem_width(apply_style(build_trouser("S"), "pitillo")) < base
    assert _hem_width(apply_style(build_trouser("S"), "wide")) > base
    assert _hem_width(apply_style(build_trouser("S"), "palazzo")) > \
        _hem_width(apply_style(build_trouser("S"), "wide"))


def test_cropped_styles_are_shorter():
    base = _length(build_trouser("S"))
    for st in ("capri", "short", "culotte"):
        assert _length(apply_style(build_trouser("S"), st)) < base


def test_jogger_marks_elastic_cuff():
    g = apply_style(build_trouser("S"), "jogger")
    txt = [t for pc in g.pieces for _, t in pc.reference_texts]
    assert any("elástico" in t for t in txt)


def test_darts_preserved_in_leg_styles():
    # los estilos de pierna no tocan la cintura: la pinza se conserva
    g = apply_style(build_trouser("S"), "wide")
    assert len(_front(g).darts) == 1


def test_unknown_trouser_style_raises():
    with pytest.raises(KeyError):
        apply_style(build_trouser("S"), "no_existe")


def test_trouser_style_cli_export():
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d, garment="trouser", style="palazzo", quiet=True)
    assert os.path.basename(outs["dxf_r2013"]).startswith("pantalon_S_palazzo")
    assert os.path.getsize(outs["svg"]) > 0
