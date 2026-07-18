"""Tests del motor geométrico y de curvas."""
from patronaje.core.geometry import (
    line_intersection, tangent_arc, offset_polyline, polygon_area, distance,
)
from patronaje.core.curves import (
    CubicBezier, NaturalCubicSpline, smooth_curve, chord_error,
)


def test_line_intersection():
    assert line_intersection((0, 0), (10, 0), (5, -5), (5, 5)) == (5.0, 0.0)
    assert line_intersection((0, 0), (1, 0), (0, 1), (1, 1)) is None  # paralelas


def test_polygon_area_square():
    assert abs(polygon_area([(0, 0), (4, 0), (4, 4), (0, 4)]) - 16.0) < 1e-9


def test_tangent_arc_is_tangent():
    arc = tangent_arc((0, 10), (0, 0), (10, 0), 2.0, segments=16)
    # el primer punto de tangencia está sobre el segmento vertical entrante
    assert abs(arc[0][0]) < 1e-6
    # el último sobre el segmento horizontal
    assert abs(arc[-1][1]) < 1e-6


def test_offset_distance():
    off = offset_polyline([(0, 0), (10, 0)], 1.0, ccw=True)
    # una recta desplazada 1 cm mantiene la distancia
    assert abs(distance(off[0], (0, 1)) ) < 1e-9


def test_spline_g2_low_chord_error():
    pts = [(0, 0), (1, 0.6), (2, 1.6), (2.6, 2.8), (3, 4)]
    sp = NaturalCubicSpline(pts)
    err = chord_error(sp, sp.sample(60))
    assert err < 0.01  # apta para CNC


def test_bezier_curvature_symmetry():
    b = CubicBezier((0, 0), (1, 0), (1, 1), (0, 1))
    assert b.length(64) > 0
    assert abs(b.curvature(0.5)) > 0


def test_smooth_curve_interpolates_endpoints():
    pts = [(0, 0), (2, 1), (4, 0)]
    curve = smooth_curve(pts, samples_per_span=8)
    assert distance(curve[0], (0, 0)) < 1e-9
    assert distance(curve[-1], (4, 0)) < 1e-9
