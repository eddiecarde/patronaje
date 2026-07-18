"""Tests del bloque base entallado (sloper) con pinzas y equilibrio."""
import os
import tempfile

import pytest
from shapely.geometry import Polygon

from patronaje.parametric.measurements import build_parameters
from patronaje.blocks.registry import get_method
from patronaje.blocks.fitted import build_fitted
from patronaje.garment.sloper import build_sloper
from patronaje.validation.validators import ValidationReport, validate_piece_geometry

METHODS = ["aldrich", "mueller", "bunka", "esmod", "marti", "armstrong"]
DART_POS = ["side", "shoulder", "neck", "armhole", "french", "waist"]


def _geom_ok(sl):
    rep = ValidationReport()
    for pc in sl.pieces:
        validate_piece_geometry(pc, rep)
    return rep.ok


@pytest.mark.parametrize("method", METHODS)
def test_sloper_valid_each_method(method):
    sl = build_sloper("S", method=method)
    assert len(sl.pieces) == 3
    assert _geom_ok(sl)
    # 4 pinzas: busto + cintura delantera + cintura trasera + hombro
    ndarts = sum(len(pc.darts) for pc in sl.pieces)
    assert ndarts == 4


@pytest.mark.parametrize("pos", DART_POS)
def test_bust_dart_positions_valid(pos):
    p = build_parameters("S")
    fb = build_fitted(get_method("aldrich"), p, bust_dart_pos=pos)
    assert Polygon(fb.front).is_valid and Polygon(fb.front).is_simple


def test_waist_suppression_matches_bust_waist_difference():
    p = build_parameters("S")
    fb = build_fitted(get_method("aldrich"), p)
    quarter_bust = (p.busto + p.holgura_busto) / 4.0
    quarter_waist = (p.cintura + fb.spec.waist_ease) / 4.0
    assert abs(fb.waist_suppression - (quarter_bust - quarter_waist)) < 1e-6


def test_bust_point_and_dart_present():
    fb = build_fitted(get_method("bunka"), build_parameters("S"))
    assert fb.bust_point is not None
    # la pinza de busto apunta cerca del punto de busto
    b1, apex, b2 = fb.front_darts[0]
    assert abs(apex[0] - fb.bust_point[0]) < 6 and abs(apex[1] - fb.bust_point[1]) < 6


def test_sloper_grades_all_sizes():
    for size in ["XS", "S", "M", "L", "XL", "XXL"]:
        assert _geom_ok(build_sloper(size, method="mueller"))


def test_fitted_princess_absorbs_darts():
    from patronaje.transform.styles import apply_style
    sl = build_sloper("S", method="aldrich")
    assert sum(len(pc.darts) for pc in sl.pieces) == 4
    sl = apply_style(sl, "princess")
    # el delantero se parte en dos y sus pinzas quedan absorbidas en la costura
    front_panels = [pc for pc in sl.pieces if "DELANTERO" in pc.name]
    assert len(front_panels) == 2
    assert sum(len(pc.darts) for pc in front_panels) == 0
    assert _geom_ok(sl)


def test_fitted_empire_releases_waist_dart_and_keeps_bust():
    from patronaje.transform.styles import apply_style
    sl = apply_style(build_sloper("S", method="aldrich"), "empire")
    assert _geom_ok(sl)
    front_talle = next(p for p in sl.pieces if p.name.startswith("DELANTERO TALLE"))
    front_falda = next(p for p in sl.pieces if p.name.startswith("DELANTERO FALDA"))
    # el talle conserva la pinza de busto; la falda no tiene pinzas
    assert len(front_talle.darts) == 1
    assert len(front_falda.darts) == 0
    # la falda es una pieza con dobladillo real
    assert front_falda.hem_allowance is not None
    # la falda vuela: su bajo es más ancho que su cintura
    ys = [q[1] for q in front_falda.net_contour]
    top_x = max(x for x, y in front_falda.net_contour if abs(y - min(ys)) < 0.5)
    bot_x = max(x for x, y in front_falda.net_contour if abs(y - max(ys)) < 0.5)
    assert bot_x > top_x + 5


def test_fitted_peplum_keeps_bodice_darts_flounce_dartless():
    from patronaje.transform.styles import apply_style
    sl = apply_style(build_sloper("S", method="aldrich"), "peplum")
    assert _geom_ok(sl)
    talle = next(p for p in sl.pieces if p.name.startswith("DELANTERO TALLE"))
    volante = next(p for p in sl.pieces if p.name.startswith("DELANTERO VOLANTE"))
    assert len(talle.darts) == 2          # busto + cintura
    assert len(volante.darts) == 0
    assert volante.hem_allowance is not None


def test_hem_allowance_propagated_to_hemmed_pieces():
    from patronaje.transform.styles import apply_style
    from patronaje.garment.shirt import build_shirt
    p = build_parameters("S")
    hem = p.margen_dobladillo
    # vista delantera: dobla con el bajo del delantero
    facing = next(x for x in build_shirt("S").pieces if x.name == "VISTA DELANTERA")
    assert facing.hem_allowance == hem
    # manga del sloper: muñeca con dobladillo simple
    sleeve = next(x for x in build_sloper("S").pieces if x.name == "MANGA")
    assert sleeve.hem_allowance == hem
    # manga recortada: la nueva boca lleva dobladillo
    short = next(x for x in apply_style(build_shirt("S"), "short_sleeve").pieces
                 if x.name.startswith("MANGA"))
    assert short.hem_allowance == hem


def test_fitted_cli_exports():
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d, fit="fitted", bust_dart="french", quiet=True)
    for k in ["dxf_r2013", "svg", "json", "csv"]:
        assert os.path.exists(outs[k]) and os.path.getsize(outs[k]) > 0
