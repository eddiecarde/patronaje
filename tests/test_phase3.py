"""Tests de Fase 3: marker/consumo, BOM y tech pack."""
import os
import tempfile

from patronaje.garment.shirt import build_shirt
from patronaje.marker.layout import nest, marker_report, export_marker_svg
from patronaje.techpack.bom import build_bom
from patronaje.techpack.consumption import consumption
from patronaje.techpack.techpack import export_techpack, build_techpack_html
from patronaje.techpack.sequence import finished_measurements, SEWING_SEQUENCE, QC_CHECKLIST


def test_marker_no_overlap_and_within_width():
    sh = build_shirt("S").layout()
    W = 150.0
    placements, length = nest(sh, W)
    assert length > 0
    # cada instancia cabe en el ancho
    for pl in placements:
        assert pl.x + pl.w <= W + 1e-6
    # sin solapamiento (bounding boxes)
    for i in range(len(placements)):
        a = placements[i]
        for j in range(i + 1, len(placements)):
            b = placements[j]
            sep = (a.x + a.w <= b.x + 1e-9 or b.x + b.w <= a.x + 1e-9 or
                   a.y + a.h <= b.y + 1e-9 or b.y + b.h <= a.y + 1e-9)
            assert sep, f"solapan {a.piece.name} y {b.piece.name}"


def test_wider_fabric_uses_less_length():
    sh = build_shirt("S").layout()
    rep = marker_report(sh)
    l110 = rep["por_ancho"][110.0]["largo_cm"]
    l160 = rep["por_ancho"][160.0]["largo_cm"]
    assert l160 < l110


def test_consumption_has_purchase_margin():
    sh = build_shirt("S").layout()
    cons = consumption(sh, widths=(150.0,))
    d = cons["por_ancho"][150.0]
    assert d["compra_recomendada_m"] > d["largo_m"]


def test_bom_counts_buttons_and_holes():
    sh = build_shirt("S").layout()
    bom = build_bom(sh)
    assert bom["resumen"]["botones"] >= 7
    assert bom["resumen"]["ojales"] >= 7
    assert any("Tela principal" in it["item"] for it in bom["items"])


def test_finished_measurements_and_sequence():
    sh = build_shirt("S")
    fin = finished_measurements(sh)
    poms = {r["pom"] for r in fin}
    assert "Largo total (desde nuca)" in poms
    assert len(SEWING_SEQUENCE) >= 8 and len(QC_CHECKLIST) >= 6


def test_techpack_html_sections():
    sh = build_shirt("S").layout()
    doc = build_techpack_html(sh)
    for section in ["Planos técnicos", "Lista de materiales (BOM)",
                    "Consumo de tela", "Secuencia de confección",
                    "Control de calidad", "Tolerancias"]:
        assert section in doc
    # dos SVG de planos + detalles
    assert doc.count("<svg") >= 5


def test_techpack_export_and_marker_svg():
    sh = build_shirt("S").layout()
    d = tempfile.mkdtemp()
    tp = export_techpack(sh, os.path.join(d, "tp.html"))
    mk = export_marker_svg(sh, 150.0, os.path.join(d, "m.svg"))
    assert os.path.getsize(tp) > 0 and os.path.getsize(mk) > 0
