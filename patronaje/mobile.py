"""App móvil **offline** (para empaquetar como APK Android con WebView).

Genera un sitio autocontenido (`index.html` + `patterns/*.svg` + los visores 2D/3D)
que funciona **sin servidor ni red**: el usuario elige **prenda, talla y estilo** y
ve al instante el patrón trazado por el **motor real de Python** (los SVG se
pre-generan en tiempo de compilación y se incrustan como recursos). El modo
**a medida** se delega al visor 2D en vivo (motor portado a JS), que recalcula el
patrón base con las medidas de la persona.

    python -m patronaje.mobile --output app_offline

Lo consume el proyecto Android (`android/`) que copia esta carpeta a
`app/src/main/assets/www/` y compila el APK. Ver `docs/apk.md`.
"""
from __future__ import annotations

import json
import os
import tempfile

from .export.svg import export_svg
from .viewer import _stats, build_live_viewer
from .viewer3d import build_body_viewer
from .parametric.measurements import SIZE_CHART

# prendas (id ES -> builder) y sus registros de estilos
GARMENTS = [
    ("camisa", "Camisa", "shirt"),
    ("falda", "Falda", "skirt"),
    ("pantalon", "Pantalón", "trouser"),
    ("vestido", "Vestido", "dress"),
    ("blazer", "Blazer", "blazer"),
]


def _builder(gid):
    if gid == "camisa":
        from .garment.shirt import build_shirt as b
    elif gid == "falda":
        from .garment.skirt import build_skirt as b
    elif gid == "pantalon":
        from .garment.trouser import build_trouser as b
    elif gid == "vestido":
        from .garment.dress import build_dress as b
    else:
        from .garment.blazer import build_blazer as b
    return b


def _styles_for(gid):
    from .transform.styles import STYLES
    from .transform.skirt_styles import SKIRT_STYLES
    from .transform.trouser_styles import TROUSER_STYLES
    from .transform.dress_styles import DRESS_STYLES
    from .transform.blazer_styles import BLAZER_STYLES
    return {"camisa": list(STYLES), "falda": list(SKIRT_STYLES),
            "pantalon": list(TROUSER_STYLES), "vestido": list(DRESS_STYLES),
            "blazer": list(BLAZER_STYLES)}[gid]


def _svg_string(shirt) -> str:
    fd, path = tempfile.mkstemp(suffix=".svg")
    os.close(fd)
    try:
        export_svg(shirt, path)
        with open(path, encoding="utf-8") as f:
            s = f.read()
    finally:
        os.remove(path)
    if s.lstrip().startswith("<?xml"):
        s = s[s.index("?>") + 2:]
    return s.strip()


def _build_one(gid, size, style, method="aldrich"):
    """Construye prenda+estilo y devuelve (svg, stats) o (None, None) si falla."""
    from .transform.styles import apply_style
    try:
        sh = _builder(gid)(size, method=method)
        if style == "base":
            sh = sh.layout()
        else:
            sh = apply_style(sh, style)
        return _svg_string(sh), _stats(sh)
    except Exception:
        return None, None


def build_offline_app(outdir: str = "app_offline", method: str = "aldrich",
                      quiet: bool = False) -> dict:
    """Genera la app offline completa. Devuelve el índice {piezas, consumo…}."""
    www = outdir
    patterns = os.path.join(www, "patterns")
    os.makedirs(patterns, exist_ok=True)

    sizes = list(SIZE_CHART)
    index = {"method": method, "sizes": sizes, "garments": [], "stats": {}}

    for gid, label, _eng in GARMENTS:
        styles = ["base"] + _styles_for(gid)
        ok_styles = []
        for style in styles:
            any_ok = False
            for size in sizes:
                svg, st = _build_one(gid, size, style, method)
                if svg is None:
                    continue
                any_ok = True
                key = f"{gid}_{size}_{style}"
                with open(os.path.join(patterns, key + ".svg"), "w",
                          encoding="utf-8") as f:
                    f.write(svg)
                index["stats"][key] = {"piezas": st["piezas"],
                                       "consumo_m": round(st["largo_m"], 2),
                                       "eficiencia": st["eficiencia"]}
            if any_ok:
                ok_styles.append(style)
            if not quiet:
                print(f"  {gid} · {style}: {'ok' if any_ok else 'omitido'}")
        index["garments"].append({"id": gid, "label": label, "styles": ok_styles})

    with open(os.path.join(www, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    with open(os.path.join(www, "index.html"), "w", encoding="utf-8") as f:
        f.write(_APP_HTML)
    with open(os.path.join(www, "manifest.webmanifest"), "w", encoding="utf-8") as f:
        f.write(_MANIFEST)

    # visores interactivos (motor JS, offline) para el modo a medida y el 3D
    build_live_viewer(www)
    build_body_viewer(www)

    n = len(index["stats"])
    if not quiet:
        print(f"App offline en {www}/  ({n} patrones, {len(sizes)} tallas)")
    return index


_MANIFEST = json.dumps({
    "name": "Patronaje", "short_name": "Patronaje", "start_url": "./index.html",
    "display": "standalone", "background_color": "#0f1620", "theme_color": "#0f1620",
    "icons": [],
}, ensure_ascii=False)


_APP_HTML = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Patronaje</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='13'>%E2%9C%82</text></svg>">
<style>
:root{--bg:#0f1620;--card:#17212e;--ink:#dce6f0;--soft:#8ea1b5;--line:#293849;
 --accent:#5aa2d8;--ok:#2e7d46;--wash:#16344c;
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5;
 padding-bottom:env(safe-area-inset-bottom)}
.top{background:#0b1219;color:#e9dcc6;padding:12px 16px;display:flex;gap:12px;align-items:center;
 font-weight:800;position:sticky;top:0;z-index:20;border-bottom:1px solid #1f2937}
.top .sp{flex:1}.top a{color:#cdd6e0;text-decoration:none;font-size:13px;font-weight:600}
.wrap{max-width:900px;margin:0 auto;padding:14px 16px 40px}
label.f{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.05em;
 color:var(--soft);margin:14px 0 5px;font-weight:700}
select{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:10px;
 background:var(--card);color:var(--ink);font-size:16px;appearance:none;
 background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' stroke='%238ea1b5' stroke-width='1.6' fill='none'/%3E%3C/svg%3E");
 background-repeat:no-repeat;background-position:right 12px center}
.seg{display:flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-top:5px}
.seg button{flex:1;padding:11px;border:0;background:var(--card);color:var(--ink);font-size:14px;font-weight:600}
.seg button.on{background:var(--accent);color:#04121e}
.stats{display:flex;gap:8px;margin:14px 0 6px;flex-wrap:wrap}
.stat{background:var(--wash);border:1px solid var(--line);border-radius:10px;padding:8px 12px;flex:1;min-width:88px}
.stat .n{font-size:18px;font-weight:800;font-variant-numeric:tabular-nums}
.stat .l{font-size:10px;color:var(--soft);text-transform:uppercase;letter-spacing:.04em}
.svgbox{border:1px solid var(--line);border-radius:12px;background:#f4f7fb;padding:10px;
 min-height:280px;display:flex;align-items:center;justify-content:center;overflow:auto}
.svgbox svg{max-width:100%;height:auto;max-height:64vh}
.rowbtns{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.btn{flex:1;min-width:130px;padding:12px;border-radius:10px;border:1px solid var(--line);
 background:var(--card);color:var(--ink);text-decoration:none;font-size:14px;font-weight:600;
 text-align:center;cursor:pointer}
.btn.primary{background:var(--ok);color:#fff;border-color:transparent}
.note{color:var(--soft);font-size:12px;margin-top:10px}
.hidden{display:none}
</style></head><body>
<div class="top"><span>&#9986; Patronaje</span><span class="sp"></span>
 <a href="viewer_live.html">2D</a><a href="viewer_3d.html">3D</a></div>
<div class="wrap">
 <label class="f">Prenda</label><select id="garment"></select>
 <label class="f">Estilo</label><select id="style"></select>
 <div class="seg"><button id="mSize" class="on">Por talla</button>
  <button id="mCustom">A medida</button></div>
 <div id="sizeBox"><label class="f">Talla</label><select id="size"></select></div>
 <div id="stats" class="stats hidden"></div>
 <div class="svgbox" id="svg">Cargando…</div>
 <div class="rowbtns">
  <a class="btn primary" id="dl">&#8681; Guardar/compartir SVG</a>
  <a class="btn" id="edit2d" href="viewer_live.html">Editar a medida (2D)</a>
  <a class="btn" id="view3d" href="viewer_3d.html">Maniquí 3D</a></div>
 <div class="note" id="note"></div>
</div>
<script>
let IDX=null, MODE='size';
const $=id=>document.getElementById(id);
async function boot(){
 IDX=await (await fetch('index.json')).json();
 const gs=$('garment');IDX.garments.forEach(g=>gs.add(new Option(g.label,g.id)));
 const ss=$('size');IDX.sizes.forEach(s=>ss.add(new Option(s,s)));
 ss.value=IDX.sizes.includes('S')?'S':IDX.sizes[0];
 gs.onchange=()=>{fillStyles();load();};
 $('style').onchange=load; ss.onchange=load;
 $('mSize').onclick=()=>setMode('size'); $('mCustom').onclick=()=>setMode('custom');
 fillStyles();load();
}
function garment(){return IDX.garments.find(g=>g.id===$('garment').value);}
function styleLabel(s){return s==='base'?'Base (sin estilo)':s;}
function fillStyles(){const st=$('style');st.innerHTML='';
 garment().styles.forEach(s=>st.add(new Option(styleLabel(s),s)));}
function setMode(m){MODE=m;$('mSize').classList.toggle('on',m==='size');
 $('mCustom').classList.toggle('on',m==='custom');
 $('sizeBox').style.display=m==='size'?'':'none';
 if(m==='custom'){
  $('note').textContent='A medida: abre el editor 2D en vivo, mueve tus medidas y el patrón se recalcula al instante (motor en el dispositivo). Los estilos se aplican en el modo Por talla.';
  $('svg').innerHTML=''; $('stats').classList.add('hidden');
 }else{$('note').textContent='';load();}
}
async function load(){
 if(MODE==='custom')return;
 const gid=$('garment').value,sz=$('size').value,style=$('style').value;
 const key=gid+'_'+sz+'_'+style;
 const st=IDX.stats[key];
 // enlaces a los visores con la prenda seleccionada
 $('edit2d').href='viewer_live.html?garment='+gid;
 $('view3d').href='viewer_3d.html?garment='+gid;
 if(!st){$('svg').innerHTML='No disponible';$('stats').classList.add('hidden');return;}
 $('stats').classList.remove('hidden');
 $('stats').innerHTML=
  '<div class="stat"><div class="n">'+st.piezas+'</div><div class="l">Piezas</div></div>'+
  '<div class="stat"><div class="n">'+st.consumo_m.toFixed(2)+' m</div><div class="l">Consumo 150cm</div></div>'+
  '<div class="stat"><div class="n">'+st.eficiencia+' %</div><div class="l">Eficiencia</div></div>';
 try{
  const svg=await (await fetch('patterns/'+key+'.svg')).text();
  $('svg').innerHTML=svg;
  const a=$('dl');
  if(window.Android&&Android.shareSvg){       // APK: comparte por el diálogo nativo
   a.removeAttribute('href');a.onclick=()=>{Android.shareSvg(key+'.svg',svg);return false;};
  }else{                                       // navegador/PWA: descarga por blob
   const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
   a.href=url;a.download=key+'.svg';a.onclick=null;
  }
 }catch(e){$('svg').innerHTML='No disponible';}
 $('note').textContent='Método '+IDX.method.charAt(0).toUpperCase()+IDX.method.slice(1)+
  ' · patrón trazado por el motor paramétrico. Para tus medidas exactas usa «Editar a medida (2D)».';
}
boot();
</script></body></html>"""


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Genera la app móvil offline (para el APK)")
    ap.add_argument("--output", default="app_offline")
    ap.add_argument("--method", default="aldrich")
    args = ap.parse_args(argv)
    build_offline_app(args.output, method=args.method)


if __name__ == "__main__":
    main()
