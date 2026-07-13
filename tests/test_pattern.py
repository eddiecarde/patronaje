"""Tests del ensamble paramétrico, validaciones y regeneración."""
import os
import tempfile

from patronaje.garment.shirt import build_shirt
from patronaje.parametric.measurements import build_parameters
from patronaje.validation.validators import validate_all


def test_ten_pieces():
    sh = build_shirt("S")
    assert len(sh.pieces) == 10
    names = {p.name for p in sh.pieces}
    for req in ["DELANTERO", "ESPALDA", "CANESU", "MANGA", "PUNO", "TAPETA MANGA",
                "CUELLO", "PIE DE CUELLO", "VISTA DELANTERA", "BOLSILLO"]:
        assert req in names


def test_all_validations_pass_S():
    sh = build_shirt("S")
    report = validate_all(sh, tol=0.5)
    assert report.ok, report.text()


def test_cap_matches_armhole():
    sh = build_shirt("S")
    diff = sh.sleeve.cap_length() - (sh.bodice.armhole_length() + sh.sleeve_ease)
    assert abs(diff) < 0.5


def test_parametric_regeneration_all_sizes():
    for size in ["XS", "S", "M", "L", "XL", "XXL"]:
        sh = build_shirt(size)
        report = validate_all(sh, tol=0.6)
        assert report.ok, f"talla {size}:\n{report.text()}"


def test_measurement_change_regenerates():
    p = build_parameters("S")
    a1 = build_shirt("S").bodice.armhole_length()
    # aumentar el busto debe agrandar la sisa al regenerar
    p.update(busto=100)
    from patronaje.garment.shirt import Shirt
    sh2 = Shirt(p=p).build()
    assert sh2.bodice.armhole_length() != a1


def test_pieces_are_closed_polygons():
    sh = build_shirt("S")
    for pc in sh.pieces:
        poly = pc.net_polygon()
        assert poly.is_valid and poly.is_simple
        assert pc.area() > 0


def test_export_all_formats(tmp_path=None):
    from patronaje.cli import generate
    d = tempfile.mkdtemp()
    outs = generate("S", d)
    for k in ["dxf_r2013", "dxf_aama", "svg", "pdf_1a1", "pdf_a4", "ai", "json", "csv", "scr"]:
        assert os.path.exists(outs[k]) and os.path.getsize(outs[k]) > 0


def test_dxf_opens_and_has_layers():
    import ezdxf
    d = tempfile.mkdtemp()
    from patronaje.cli import generate
    outs = generate("S", d)
    doc = ezdxf.readfile(outs["dxf_r2013"])
    assert doc.dxfversion == "AC1027"  # R2013
    layers = {l.dxf.name for l in doc.layers}
    for req in ["CORTE", "COSTURA", "PIQUETES", "HILO", "DOBLEZ", "TEXTOS"]:
        assert req in layers
    audit = doc.audit()
    assert len(audit.errors) == 0
