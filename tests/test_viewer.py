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
    for marker in ("buildBody", "buildGarment", "easeColor", "getContext", "window.__rendered",
                   "buildCloth", "stepCloth", "garmentGrids"):
        assert marker in html
    # WebGL/PBR con Three.js **incrustado** (offline, sin red): la librería va inline,
    # no se carga de ningún recurso remoto. (Los strings de URL que trae la propia
    # librería —licencia, aviso de deprecación— no son cargas de red.)
    assert "THREE" in html and "WebGLRenderer" in html
    assert "<script src" not in html          # ningún <script> remoto
    assert 'href="http' not in html           # ninguna hoja de estilos externa
    assert 'src="http' not in html            # ningún recurso remoto (CDN)


def test_web_app_hub_self_contained():
    from patronaje.webapp import build_web_app
    from patronaje.parametric.measurements import SIZE_CHART
    d = tempfile.mkdtemp()
    html = pathlib.Path(build_web_app(d)).read_text(encoding="utf-8")
    for marker in ("Patronaje", "viewer_live.html", "viewer_3d.html", "SIZES", "go2d", "go3d"):
        assert marker in html
    # autocontenido (sin recursos remotos) y tabla de tallas inyectada desde el motor
    assert 'src="http' not in html and 'href="http' not in html
    for s in SIZE_CHART:
        assert '"' + s + '"' in html


def test_viewers_carry_shell_and_handoff():
    from patronaje.viewer3d import build_body_viewer
    d = tempfile.mkdtemp()
    live = pathlib.Path(build_live_viewer(d)).read_text(encoding="utf-8")
    v3 = pathlib.Path(build_body_viewer(d)).read_text(encoding="utf-8")
    for h in (live, v3):
        assert 'href="index.html"' in h          # barra de navegación común
        assert "URLSearchParams" in h            # handoff de la plataforma


def _chromium():
    """Ruta a un Chromium preinstalado (este entorno). Si no hay, devuelve None y
    Playwright usa su navegador gestionado (p. ej. en CI tras `playwright install`)."""
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium-*/chrome-linux/headless_shell"):
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


def _launch(pw):
    """Lanza Chromium: usa el binario preinstalado si existe; si no, el gestionado."""
    exe = _chromium()
    return pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()


def _browser_available():
    import importlib.util
    if importlib.util.find_spec("playwright") is None:
        return False
    if _chromium():
        return True
    # Playwright instalado: ¿hay navegador gestionado? (CI tras `playwright install`)
    import glob as _g
    import os as _os
    home = _os.path.expanduser("~")
    for base in (_os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
                 _os.path.join(home, ".cache", "ms-playwright")):
        if base and _g.glob(_os.path.join(base, "chromium-*")):
            return True
    return False


@pytest.mark.skipif(not _browser_available(), reason="Playwright/Chromium no disponible")
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
        b = _launch(pw)
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


@pytest.mark.skipif(not _browser_available(), reason="Playwright/Chromium no disponible")
def test_body_viewer_3d_renders_each_garment():
    """El maniquí 3D dibuja caras para cada prenda sin errores de consola."""
    playwright = pytest.importorskip("playwright.sync_api")
    from patronaje.viewer3d import build_body_viewer
    d = tempfile.mkdtemp()
    url = pathlib.Path(build_body_viewer(d)).resolve().as_uri()
    errs = []
    with playwright.sync_playwright() as pw:
        b = _launch(pw)
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


@pytest.mark.skipif(not _browser_available(), reason="Playwright/Chromium no disponible")
def test_cloth_simulation_is_stable():
    """La simulación de caída (PBD) converge sin explotar (sin NaN, acotada)."""
    playwright = pytest.importorskip("playwright.sync_api")
    from patronaje.viewer3d import build_body_viewer
    d = tempfile.mkdtemp()
    url = pathlib.Path(build_body_viewer(d)).resolve().as_uri()
    with playwright.sync_playwright() as pw:
        b = _launch(pw)
        pg = b.new_page()
        pg.goto(url)
        pg.wait_for_function("window.__rendered !== undefined")
        stats = {}
        for g in ["falda", "vestido", "camisa", "pantalon"]:
            pg.select_option("#garment", g)
            stats[g] = pg.evaluate(
                "(()=>{simMode=true;rebuild();if(raf)cancelAnimationFrame(raf);"
                "for(let i=0;i<400;i++)stepCloth(CLOTH,0.12);"
                "let bad=0,ymin=1e9,ymax=-1e9;for(const p of CLOTH.pos){"
                "if(!isFinite(p[0])||!isFinite(p[1])||!isFinite(p[2]))bad++;"
                "ymin=Math.min(ymin,p[1]);ymax=Math.max(ymax,p[1]);}"
                "return {bad,span:ymax-ymin,n:CLOTH.pos.length};})()")
        b.close()
    for g, s in stats.items():
        assert s["bad"] == 0, f"{g}: NaN en la malla"
        assert 5 < s["span"] < 250, f"{g}: la tela explotó/colapsó ({s['span']})"
        assert s["n"] > 100
