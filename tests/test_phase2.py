"""Tests de Fase 2: AAMA/ASTM DXF, AI, grading XS–XXL y nido."""
import os
import tempfile

import ezdxf

from patronaje.garment.shirt import build_shirt
from patronaje.export.dxf_aama import export_dxf_aama
from patronaje.export.ai import export_ai
from patronaje.grading.rules import increments, delta_from_base, SIZE_ORDER
from patronaje.grading.grader import grade_all, export_grade_nest


def test_aama_dxf_blocks_and_layers():
    sh = build_shirt("S").layout()
    d = tempfile.mkdtemp()
    p = export_dxf_aama(sh, os.path.join(d, "aama.dxf"))
    doc = ezdxf.readfile(p)
    assert doc.dxfversion == "AC1027"
    assert len(doc.audit().errors) == 0
    # un bloque por pieza + 10 INSERT
    blocks = [b.name for b in doc.blocks if b.name.startswith("P")]
    assert len(blocks) == 10
    inserts = [e for e in doc.modelspace() if e.dxftype() == "INSERT"]
    assert len(inserts) == 10
    layers = {l.dxf.name for l in doc.layers}
    for req in ["1", "4", "6", "7", "8"]:
        assert req in layers


def test_ai_is_pdf_compatible():
    sh = build_shirt("S").layout()
    d = tempfile.mkdtemp()
    p = export_ai(sh, os.path.join(d, "camisa.ai"))
    with open(p, "rb") as f:
        assert f.read(5) == b"%PDF-"


def test_grading_increments_consistent():
    inc = increments()
    # busto crece 4 cm por talla en toda la escala
    for pair in inc:
        assert abs(inc[pair]["busto"] - 4.0) < 1e-6
    # delta acumulado XXL respecto de S
    assert abs(delta_from_base("XXL")["busto"] - 16.0) < 1e-6


def test_grade_all_sizes_bigger_than_previous():
    shirts = grade_all()
    areas = []
    for s in SIZE_ORDER:
        front = next(p for p in shirts[s].pieces if p.name == "DELANTERO")
        areas.append(front.area())
    # el área del delantero crece monótonamente con la talla
    assert all(b > a for a, b in zip(areas, areas[1:])), areas


def test_grade_nest_export():
    d = tempfile.mkdtemp()
    p = export_grade_nest("DELANTERO", os.path.join(d, "nest.svg"))
    assert os.path.exists(p) and os.path.getsize(p) > 0
