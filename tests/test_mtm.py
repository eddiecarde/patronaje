"""Tests del modo a medida (made-to-measure) y validación de medidas."""
import json
import os
import tempfile

import pytest

from patronaje.parametric.measurements import (
    SIZE_CHART, build_parameters, build_parameters_from_measurements)
from patronaje.parametric.validation import validate_measurements, has_errors
from patronaje.garment.shirt import build_shirt
from patronaje.garment.sloper import build_sloper
from patronaje.validation.validators import ValidationReport, validate_piece_geometry


def _geom_ok(g):
    rep = ValidationReport()
    for pc in g.pieces:
        validate_piece_geometry(pc, rep)
    return rep.ok


def _base():
    return dict(busto=90, cintura=68, cadera=96, largo_camisa=66, largo_manga=59,
                contorno_cuello=37, ancho_espalda=36.5, hombro=12.5,
                contorno_brazo=29, muneca=17)


def test_standard_sizes_have_no_errors():
    for size, m in SIZE_CHART.items():
        assert not has_errors(validate_measurements(m)), size


def test_missing_measurement_is_error():
    m = _base()
    del m["busto"]
    issues = validate_measurements(m)
    assert has_errors(issues)
    assert any(i.field == "busto" for i in issues)


def test_incoherent_proportions_flagged():
    m = _base()
    m["muneca"] = 40          # muñeca > brazo
    assert has_errors(validate_measurements(m))
    m = _base()
    m["contorno_cuello"] = 200  # escote más ancho que la espalda
    assert has_errors(validate_measurements(m))


def test_unknown_key_is_warning_not_error():
    m = _base()
    m["altura_total"] = 168
    issues = validate_measurements(m)
    assert not has_errors(issues)
    assert any(i.field == "altura_total" and i.level == "warn" for i in issues)


def test_mtm_builder_fills_secondary_measurements():
    p = build_parameters_from_measurements(_base(), name="ana")
    # se estiman talle_espalda y altura_cadera aunque no se aporten
    assert p.talle_espalda > 0 and p.altura_cadera > 0
    assert "ana" in p._base["talla_nombre"].descripcion


def test_mtm_builder_requires_core_measurements():
    m = _base()
    del m["cadera"]
    with pytest.raises(ValueError):
        build_parameters_from_measurements(m)


def test_mtm_matches_standard_size_when_fed_same_numbers():
    p_std = build_parameters("S")
    p_mtm = build_parameters_from_measurements(SIZE_CHART["S"], name="S")
    for key in ["cuarto_busto", "prof_sisa", "escote_del_prof", "boca_manga"]:
        assert abs(p_std[key] - p_mtm[key]) < 1e-9


def test_mtm_shirt_and_sloper_build_valid():
    p = build_parameters_from_measurements(_base(), name="ana")
    assert _geom_ok(build_shirt("ana", p=p).layout())
    assert _geom_ok(build_sloper("ana", p=p).layout())


def test_cli_measurements_flow(tmp_path=None):
    from patronaje.cli import _load_measurements
    d = tempfile.mkdtemp()
    path = os.path.join(d, "cliente.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"nombre": "cliente", "medidas": _base()}, f)
    p, name = _load_measurements(path)
    assert name == "cliente"
    assert p.busto == 90
