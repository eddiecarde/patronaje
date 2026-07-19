"""Tests del visor en vivo (motor paramétrico portado a JS)."""
import glob
import os
import pathlib
import tempfile

import pytest

from patronaje.viewer import build_live_viewer
from patronaje.garment.shirt import build_shirt


def test_live_viewer_generates_self_contained():
    d = tempfile.mkdtemp()
    path = build_live_viewer(d)
    assert os.path.exists(path) and os.path.getsize(path) > 0
    html = pathlib.Path(path).read_text(encoding="utf-8")
    # núcleo portado presente
    for marker in ("class Spline", "function bodice", "function sleeve", "window.__lengths"):
        assert marker in html
    # autocontenido: sin recursos externos (el xmlns del SVG no es una carga de red)
    assert "src=" not in html          # ningún <script src>/<img src> remoto
    assert 'href="http' not in html    # ninguna hoja de estilos externa
    assert "fetch(" not in html and "cdn" not in html.lower()
    assert "<script" in html


def _chromium():
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium-*/chrome-linux/headless_shell"):
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


@pytest.mark.skipif(_chromium() is None, reason="Chromium no disponible (CI sin navegador)")
def test_live_viewer_matches_python_engine():
    """El motor JS debe reproducir las longitudes del motor Python (fidelidad)."""
    playwright = pytest.importorskip("playwright.sync_api")
    d = tempfile.mkdtemp()
    url = pathlib.Path(build_live_viewer(d)).resolve().as_uri()
    sh = build_shirt("S")
    ref = {"escote": sh.bodice.neckline_length(),
           "sisa": sh.bodice.armhole_length(),
           "copa": sh.sleeve.cap_length()}
    with playwright.sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=_chromium())
        pg = b.new_page()
        pg.goto(url)
        pg.wait_for_function("window.__lengths !== undefined")
        js = pg.evaluate("window.__lengths")
        b.close()
    for k, v in ref.items():
        assert abs(js[k] - v) < 0.05, f"{k}: JS {js[k]:.4f} vs PY {v:.4f}"
