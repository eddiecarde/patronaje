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
    for marker in ("class Spline", "function bodice", "function sleeve", "window.__lengths",
                   "skirtPieces", "trouserPieces", "insertDart",
                   "fittedBodice", "dressPieces", "twoPieceSleeve", "blazerPieces"):
        assert marker in html
    # autocontenido: sin recursos externos (el xmlns del SVG no es una carga de red)
    assert "src=" not in html          # ningún <script src>/<img src> remoto
    assert 'href="http' not in html    # ninguna hoja de estilos externa
    assert "fetch(" not in html and "cdn" not in html.lower()
    assert "<script" in html


def test_body_viewer_3d_generates_self_contained():
    from patronaje.viewer3d import build_body_viewer
    d = tempfile.mkdtemp()
    path = build_body_viewer(d)
    assert os.path.exists(path) and os.path.getsize(path) > 0
    html = pathlib.Path(path).read_text(encoding="utf-8")
    for marker in ("buildBody", "buildGarment", "easeColor", "getContext", "window.__rendered"):
        assert marker in html
    assert "src=" not in html and 'href="http' not in html and "cdn" not in html.lower()


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
    from patronaje.blocks.skirt import build_skirt_block
    from patronaje.blocks.trouser import build_trouser_block
    from patronaje.parametric.measurements import build_parameters
    sk = build_skirt_block(build_parameters("S"))
    tr = build_trouser_block(build_parameters("S"))
    with playwright.sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=_chromium())
        pg = b.new_page()
        pg.goto(url)
        pg.wait_for_function("window.__lengths !== undefined")
        js = pg.evaluate("window.__lengths")               # camisa (por defecto)
        sk_js = pg.evaluate("(()=>{const R=skirtPieces(P);"
                            "return [parseFloat(R.metrics[0][1]),parseFloat(R.metrics[1][1])];})()")
        tr_js = pg.evaluate("(()=>{const R=trouserPieces(P);"
                            "return [plen(trouserPanel(P,false).inseam),plen(trouserPanel(P,true).inseam)];})()")
        # vestido y blazer: nº de piezas y que no lancen excepción
        dz_js = pg.evaluate("(()=>dressPieces(P).list.length)()")
        bz_js = pg.evaluate("(()=>blazerPieces(P).list.length)()")
        b.close()
    for k, v in ref.items():
        assert abs(js[k] - v) < 0.05, f"{k}: JS {js[k]:.4f} vs PY {v:.4f}"
    assert abs(sk_js[0] - sk.waist_length()) < 0.1
    assert abs(sk_js[1] - sk.hip_length()) < 0.1
    assert abs(tr_js[0] - tr.inseam_length()) < 0.1
    assert abs(tr_js[1] - tr.inseam_length(True)) < 0.1
    assert dz_js == 4 and bz_js == 4     # vestido: talle+falda; blazer: cuerpo+manga 2 piezas


@pytest.mark.skipif(_chromium() is None, reason="Chromium no disponible (CI sin navegador)")
def test_body_viewer_3d_renders_each_garment():
    """El maniquí 3D dibuja caras para cada prenda sin errores de consola."""
    playwright = pytest.importorskip("playwright.sync_api")
    from patronaje.viewer3d import build_body_viewer
    d = tempfile.mkdtemp()
    url = pathlib.Path(build_body_viewer(d)).resolve().as_uri()
    errs = []
    with playwright.sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=_chromium())
        pg = b.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url)
        pg.wait_for_function("window.__rendered !== undefined")
        counts = {}
        for g in ["camisa", "falda", "pantalon", "vestido", "blazer"]:
            pg.select_option("#garment", g)
            pg.wait_for_timeout(30)
            counts[g] = pg.evaluate("window.__rendered")
        b.close()
    assert not errs, errs
    assert all(v > 100 for v in counts.values()), counts
