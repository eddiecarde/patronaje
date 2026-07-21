"""Tests de Fase 2: AAMA/ASTM DXF, AI, grading XS–XXL y nido."""
import os
import tempfile

import ezdxf

from patronaje.garment.shirt import build_shirt
from patronaje.export.dxf_aama import export_dxf_aama, validate_aama_dxf
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
    for req in ["1", "2", "3", "4", "5", "6", "7", "8", "11", "13", "15"]:
        assert req in layers
    # hilo en la 11 (no la 7) y taladros en la 13 (no la 6): asignación ASTM correcta
    blk = doc.blocks.get(blocks[0])
    by_layer = {}
    for e in blk:
        by_layer.setdefault(e.dxf.layer, []).append(e.dxftype())
    assert any(t == "LINE" for t in by_layer.get("11", [])), "hilo debe ir en la capa 11"
    assert "POINT" in by_layer.get("2", []) or "POINT" in by_layer.get("3", [])


def test_aama_conformance_roundtrip():
    """Certificación por round-trip: cada prenda exporta un DXF AAMA/ASTM que se
    reabre, pasa la auditoría estructural de ezdxf y casa con la fuente."""
    from patronaje.garment.skirt import build_skirt
    from patronaje.garment.trouser import build_trouser
    from patronaje.garment.dress import build_dress
    from patronaje.garment.blazer import build_blazer
    d = tempfile.mkdtemp()
    garments = {"camisa": build_shirt("S"), "falda": build_skirt("S"),
                "pantalon": build_trouser("S"), "vestido": build_dress("S"),
                "blazer": build_blazer("S")}
    for name, g in garments.items():
        sh = g.layout()
        p = export_dxf_aama(sh, os.path.join(d, f"{name}.dxf"))
        rep = validate_aama_dxf(p, sh)
        assert rep["ok"], f"{name}: {rep['issues']}"
        assert rep["audit_errors"] == 0
        assert rep["blocks"] == len(sh.pieces)
        # cada pieza: contorno cerrado + anotación
        for bn, r in rep["per_piece"].items():
            assert r["closed"] and r["boundary_pts"] >= 3, (name, bn, r)
            assert r["text"] >= 1, (name, bn, r)


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
