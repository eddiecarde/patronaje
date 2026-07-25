"""Tests de la copa de manga por Bézier cúbica (camisa de mujer)."""
import math

from patronaje.blocks.sleeve_cap import (
    curva_copa_manga, curvaCopaManga, bezier_cap_curve, bezier_cap_guides,
    GUIA2_FRAC_X, GUIA2_FRAC_Y, GUIA1_FRAC_X, GUIA1_FRAC_Y, DELANTERO_DIP,
)
from patronaje.garment.shirt import build_shirt
from patronaje.export._common import gather_entities


def test_control_points_follow_spec():
    ancho, alt = 30.0, 9.0
    W, H = ancho / 2, alt
    r = curva_copa_manga(ancho, alt, "espalda")
    assert r["p0"] == (0.0, 0.0)
    assert r["p3"] == (W, H)
    assert r["guia2"] == (GUIA2_FRAC_X * W, GUIA2_FRAC_Y * H)   # cerca de la base
    assert r["guia1"] == (GUIA1_FRAC_X * W, GUIA1_FRAC_Y * H)   # cerca de la cima


def test_front_dips_second_guide():
    """El delantero baja la 2ª guía DELANTERO_DIP cm (concavidad de la base)."""
    esp = curva_copa_manga(30.0, 9.0, "espalda")
    det = curva_copa_manga(30.0, 9.0, "delantero")
    assert det["guia2"][0] == esp["guia2"][0]                  # misma x
    assert abs(det["guia2"][1] - (esp["guia2"][1] - DELANTERO_DIP)) < 1e-9


def test_camelcase_alias_is_same():
    assert curvaCopaManga is curva_copa_manga


def test_curve_endpoints_and_bezier_pass_through_controls():
    r = curva_copa_manga(28.0, 8.0, "espalda", samples=40)
    curve = r["curve"]
    assert curve[0] == (0.0, 0.0)                              # P0
    assert abs(curve[-1][0] - r["W"]) < 1e-9 and abs(curve[-1][1] - r["H"]) < 1e-9  # P3


def test_full_cap_placement_in_block_frame():
    """Copa completa: cima en SH=(0,0) y bíceps en (±bh, h)."""
    bh, h = 15.0, 9.0
    cap = bezier_cap_curve(bh, h)
    assert abs(cap[0][0] + bh) < 1e-6 and abs(cap[0][1] - h) < 1e-6   # BL
    assert abs(cap[-1][0] - bh) < 1e-6 and abs(cap[-1][1] - h) < 1e-6  # BR
    ys = [y for _, y in cap]
    assert min(ys) < 1e-6                                             # toca la cima (y=0)


def test_shirt_uses_bezier_and_matches_armhole():
    sh = build_shirt("S")
    assert sh.sleeve.cap_style == "bezier"
    diff = sh.sleeve.cap_length() - (sh.bodice.armhole_length() + sh.sleeve_ease)
    assert abs(diff) < 0.5                                            # sigue casando


def test_guides_only_in_debug_never_in_print():
    sh = build_shirt("S")
    manga = next(p for p in sh.pieces if p.name == "MANGA")
    assert manga.debug_guides                                        # tiene guías
    printed = [e for e in gather_entities(sh, debug=False) if getattr(e, "layer", "") == "GUIA"]
    debugged = [e for e in gather_entities(sh, debug=True) if getattr(e, "layer", "") == "GUIA"]
    assert printed == []                                             # NUNCA en el PDF
    assert len(debugged) >= 4                                        # control + bisectriz ×2
