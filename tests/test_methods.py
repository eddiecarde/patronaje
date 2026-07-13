"""Tests de la capa de abstracción de métodos de patronaje."""
import pytest

from patronaje.blocks.registry import list_methods, get_method
from patronaje.blocks.base import DraftingMethod
from patronaje.garment.shirt import build_shirt
from patronaje.validation.validators import validate_all


def test_registry_lists_methods():
    names = {m["name"] for m in list_methods()}
    assert "aldrich" in names and "mueller" in names


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


def test_planned_method_raises():
    with pytest.raises(NotImplementedError):
        get_method("mueller")
    with pytest.raises(NotImplementedError):
        build_shirt("S", method="mueller")


def test_unknown_method_raises():
    with pytest.raises(KeyError):
        get_method("noexiste")


def test_required_measurements_present_for_aldrich():
    from patronaje.parametric.measurements import build_parameters
    p = build_parameters("S")
    assert get_method("aldrich").check_measurements(p) == []
