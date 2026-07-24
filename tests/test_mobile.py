"""Tests de la app móvil offline (motor -> SVG pre-generados para el APK)."""
from patronaje import mobile


def test_build_one_produces_svg_and_stats_for_each_garment():
    # base de cada prenda: trazo real del motor -> SVG + estadísticas
    for gid, _label, _eng in mobile.GARMENTS:
        svg, st = mobile._build_one(gid, "S", "base")
        assert svg and svg.lstrip().startswith("<svg"), gid
        assert st["piezas"] >= 2, gid
        assert st["largo_m"] > 0, gid


def test_build_one_applies_style():
    svg_base, _ = mobile._build_one("falda", "M", "base")
    svg_styled, st = mobile._build_one("falda", "M", "circular")
    assert svg_styled and svg_styled.startswith("<svg")
    assert svg_styled != svg_base           # el estilo cambia el trazo
    assert st["piezas"] >= 2


def test_styles_registry_matches_engine():
    # cada prenda expone al menos un estilo propio
    for gid, _l, _e in mobile.GARMENTS:
        assert len(mobile._styles_for(gid)) >= 1, gid


def test_app_html_has_pickers_and_offline_bridge():
    html = mobile._APP_HTML
    for needle in ["id=\"garment\"", "id=\"style\"", "id=\"size\"",
                   "Android.shareSvg", "viewer_live.html", "viewer_3d.html",
                   "index.json"]:
        assert needle in html, needle
