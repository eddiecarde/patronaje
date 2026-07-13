"""Tests de la capa de abstracción de métodos de patronaje."""
import pytest

from patronaje.blocks.registry import list_methods, get_method
from patronaje.blocks.base import DraftingMethod
from patronaje.garment.shirt import build_shirt
from patronaje.validation.validators import validate_all


ALL_METHODS = ["aldrich", "mueller", "bunka", "esmod"]


def test_registry_lists_methods():
    names = {m["name"] for m in list_methods()}
    for m in ALL_METHODS:
        assert m in names


@pytest.mark.parametrize("method", ALL_METHODS)
def test_every_method_valid_all_sizes(method):
    for size in ["XS", "S", "M", "L", "XL", "XXL"]:
        sh = build_shirt(size, method=method)
        assert len(sh.pieces) == 10
        assert validate_all(sh, tol=0.6).ok, f"{method} {size} inválido"


def test_methods_produce_distinct_blocks():
    necks = {m: build_shirt("S", method=m).bodice.neckline_length()
             for m in ALL_METHODS}
    # al menos 3 valores de escote distintos entre los 4 métodos
    assert len(set(round(v, 1) for v in necks.values())) >= 3, necks


def test_aldrich_is_available_and_valid():
    m = get_method("aldrich")
    assert isinstance(m, DraftingMethod) and m.available
    sh = build_shirt("S", method="aldrich")
    assert validate_all(sh).ok


def test_default_method_is_aldrich():
    sh_default = build_shirt("S")
    sh_aldrich = build_shirt("S", method="aldrich")
    assert sh_default.method == "aldrich"
    assert len(sh_default.pieces) == len(sh_aldrich.pieces) == 10


def test_mueller_available_and_valid():
    m = get_method("mueller")
    assert m.available
    for size in ["XS", "S", "M", "L", "XL", "XXL"]:
        sh = build_shirt(size, method="mueller")
        assert len(sh.pieces) == 10
        assert validate_all(sh, tol=0.6).ok, f"Müller {size} inválido"


def test_mueller_differs_from_aldrich():
    a = build_shirt("S", method="aldrich").bodice
    m = build_shirt("S", method="mueller").bodice
    # bloques distintos: escote y sisa no coinciden
    assert abs(a.neckline_length() - m.neckline_length()) > 0.5
    assert abs(a.armhole_length() - m.armhole_length()) > 0.3


def test_unknown_method_raises():
    with pytest.raises(KeyError):
        get_method("noexiste")


def test_required_measurements_present_for_aldrich():
    from patronaje.parametric.measurements import build_parameters
    p = build_parameters("S")
    assert get_method("aldrich").check_measurements(p) == []
