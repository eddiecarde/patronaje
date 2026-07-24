"""Aplicación web (FastAPI) sobre el motor de patronaje.

Expone el **motor real de Python** (el que produce los archivos listos para
producción) detrás de una API REST y una interfaz web: eliges prenda, talla o
medidas a medida, método y estilo, generas el patrón y **descargas los archivos
reales** (DXF R2013, DXF AAMA/ASTM, PDF 1:1/A4, SVG, AI, JSON, CSV, SCR, tech
pack y markers). Integra los visores 2D en vivo y el maniquí 3D.

    python -m patronaje.app                 # arranca en http://127.0.0.1:8000
    uvicorn patronaje.app:app --reload      # desarrollo

A diferencia de los visores (que portan el motor a JS para el navegador), aquí la
**fuente de verdad es Python**: los archivos descargables salen del mismo motor
que la CLI (`patronaje.cli.generate`).
"""
from __future__ import annotations

import io
import os
import re
import shutil
import tempfile
import uuid
import zipfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

from .cli import generate
from .parametric.measurements import SIZE_CHART
from .webapp import _FIELDS, _ESTATURA
from .viewer import METHODS

# --------------------------------------------------------------------------
# Configuración: prendas (id ES -> motor EN) + estilos por prenda
# --------------------------------------------------------------------------
def _styles():
    from .transform.styles import STYLES
    from .transform.skirt_styles import SKIRT_STYLES
    from .transform.trouser_styles import TROUSER_STYLES
    from .transform.dress_styles import DRESS_STYLES
    from .transform.blazer_styles import BLAZER_STYLES
    return {"camisa": list(STYLES), "falda": list(SKIRT_STYLES),
            "pantalon": list(TROUSER_STYLES), "vestido": list(DRESS_STYLES),
            "blazer": list(BLAZER_STYLES)}


GARMENTS = {
    "camisa":   {"label": "Camisa", "garment": "shirt", "fit": "shirt"},
    "falda":    {"label": "Falda", "garment": "skirt", "fit": "shirt"},
    "pantalon": {"label": "Pantalón", "garment": "trouser", "fit": "shirt"},
    "vestido":  {"label": "Vestido", "garment": "dress", "fit": "shirt"},
    "blazer":   {"label": "Blazer", "garment": "blazer", "fit": "shirt"},
}

# largos de prenda ajustables por prenda (además de las medidas del cuerpo), para
# el modo a medida
_LENGTHS = {
    "camisa":   [("largo_camisa", "Largo camisa"), ("largo_manga", "Largo manga")],
    "falda":    [("largo_falda", "Largo falda")],
    "pantalon": [("largo_pantalon", "Largo pantalón")],
    "vestido":  [("largo_falda", "Largo de la falda")],
    "blazer":   [("largo_manga", "Largo manga")],
}
_LEN_KEYS = ("largo_camisa", "largo_manga", "largo_falda", "largo_pantalon")
_LEN_DEFAULT = {"largo_falda": 60.0, "largo_pantalon": 100.0}

# etiqueta legible por tipo de archivo generado
_FILE_LABELS = {
    "dxf_r2013": "DXF R2013 (CAD por capas)",
    "dxf_aama": "DXF AAMA/ASTM D6673",
    "svg": "SVG vectorial",
    "pdf_1a1": "PDF 1:1 (mosaico para imprimir)",
    "pdf_a4": "PDF A4",
    "ai": "Adobe Illustrator (.ai)",
    "json": "Geometría JSON",
    "csv": "CSV de puntos",
    "scr": "Script AutoCAD (.scr)",
    "techpack": "Tech pack (ficha técnica HTML)",
    "marker_110": "Marker · tela 110 cm",
    "marker_150": "Marker · tela 150 cm",
    "marker_160": "Marker · tela 160 cm",
}
_MIME = {".svg": "image/svg+xml", ".html": "text/html; charset=utf-8",
         ".pdf": "application/pdf", ".json": "application/json",
         ".csv": "text/csv", ".dxf": "image/vnd.dxf", ".ai": "application/pdf",
         ".scr": "text/plain"}

JOBS_DIR = os.path.join(tempfile.gettempdir(), "patronaje_jobs")
VIEWERS_DIR = os.path.join(JOBS_DIR, "_viewers")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _job_dir(job_id: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{8,40}", job_id or ""):
        raise HTTPException(status_code=404, detail="job no encontrado")
    d = os.path.join(JOBS_DIR, job_id)
    if not os.path.isdir(d):
        raise HTTPException(status_code=404, detail="job no encontrado")
    return d


def _build_garment(gid, size, method, style, p=None):
    """Construye la prenda (para estadísticas), mismo motor que la CLI."""
    if gid == "camisa":
        from .garment.shirt import build_shirt as bld
    elif gid == "falda":
        from .garment.skirt import build_skirt as bld
    elif gid == "pantalon":
        from .garment.trouser import build_trouser as bld
    elif gid == "vestido":
        from .garment.dress import build_dress as bld
    else:
        from .garment.blazer import build_blazer as bld
    sh = bld(size, method=method, p=p)
    if style and style not in ("none", ""):
        from .transform.styles import apply_style
        sh = apply_style(sh, style)
    return sh.layout()


def _stats(gid, size, method, style, p=None):
    try:
        sh = _build_garment(gid, size, method, style, p)
        from .marker.layout import marker_report
        rep = marker_report(sh, widths=(150.0,))
        d = rep["por_ancho"][150.0]
        return {"piezas": len(sh.pieces), "consumo_m": round(d["largo_m"], 2),
                "eficiencia": round(d["eficiencia"] * 100, 1)}
    except Exception:
        return None


def _list_files(job_id, outputs):
    files = []
    for key, path in outputs.items():
        if not path or not os.path.isfile(path):
            continue
        name = os.path.basename(path)
        files.append({"key": key, "label": _FILE_LABELS.get(key, key),
                      "name": name, "url": f"/api/file/{job_id}/{name}",
                      "kb": round(os.path.getsize(path) / 1024, 1)})
    order = list(_FILE_LABELS)
    files.sort(key=lambda f: order.index(f["key"]) if f["key"] in order else 99)
    return files


def _sizes_table():
    out = {}
    for size, ch in SIZE_CHART.items():
        d = {}
        for k, _ in _FIELDS:
            d[k] = ch.get(k, _ESTATURA.get(size, 168) if k == "estatura" else 0)
        for lk in _LEN_KEYS:                       # largos de prenda (para prefijar)
            d[lk] = ch.get(lk, _LEN_DEFAULT.get(lk, 0))
        out[size] = d
    return out


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
class GenReq(BaseModel):
    garment: str = "camisa"
    mode: str = "size"            # "size" | "custom"
    size: str = "S"
    method: str = "aldrich"
    style: str = "none"
    include_seam: bool = True
    measurements: dict | None = None


def _prepare_viewers():
    """Genera los visores 2D/3D (estáticos) una vez para servirlos."""
    try:
        from .viewer import build_live_viewer
        from .viewer3d import build_body_viewer
        build_live_viewer(VIEWERS_DIR)
        build_body_viewer(VIEWERS_DIR)
    except Exception:
        pass


def create_app() -> FastAPI:
    os.makedirs(VIEWERS_DIR, exist_ok=True)

    @asynccontextmanager
    async def _lifespan(_app):
        _prepare_viewers()
        yield

    app = FastAPI(title="Patronaje — app web", version="1.0", lifespan=_lifespan)

    @app.get("/", response_class=HTMLResponse)
    @app.get("/index.html", response_class=HTMLResponse)
    def home():
        return HTMLResponse(_APP_UI)

    @app.get("/api/config")
    def config():
        st = _styles()
        return {
            "garments": [{"id": gid, "label": g["label"], "styles": st[gid]}
                         for gid, g in GARMENTS.items()],
            "methods": [{"id": m, "label": lab} for m, lab in METHODS],
            "sizes": _sizes_table(),
            "size_order": list(SIZE_CHART),
            "fields": _FIELDS,
            "lengths": _LENGTHS,
        }

    @app.post("/api/generate")
    def api_generate(req: GenReq):
        if req.garment not in GARMENTS:
            raise HTTPException(status_code=400, detail="prenda desconocida")
        g = GARMENTS[req.garment]
        p, size = None, req.size
        if req.mode == "custom":
            # base = tabla de la talla de referencia (aporta los largos de prenda
            # requeridos: largo_camisa/largo_manga/talle) + medidas del cuerpo del usuario
            ref = req.size if req.size in SIZE_CHART else "S"
            meas = dict(SIZE_CHART[ref])
            meas.update({k: v for k, v in (req.measurements or {}).items() if v is not None})
            from .parametric.validation import validate_measurements, has_errors, format_issues
            issues = validate_measurements(meas)
            if has_errors(issues):
                raise HTTPException(status_code=422,
                                    detail={"error": "medidas no válidas",
                                            "issues": format_issues(issues)})
            from .parametric.measurements import build_parameters_from_measurements
            try:
                p = build_parameters_from_measurements(meas, name="custom")
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            # largos de prenda a medida (el usuario los fija; sobrescriben el default)
            for lk in _LEN_KEYS:
                v = (req.measurements or {}).get(lk)
                if v is not None:
                    try:
                        p.set(lk, float(v), descripcion="largo de prenda (a medida)")
                    except Exception:
                        pass
            size = "custom"

        job_id = uuid.uuid4().hex
        outdir = os.path.join(JOBS_DIR, job_id)
        os.makedirs(outdir, exist_ok=True)
        style = req.style or "none"
        try:
            outputs = generate(size, outdir, quiet=True, method=req.method,
                               style=style, garment=g["garment"], fit=g["fit"],
                               include_seam=req.include_seam, force=True, p=p)
        except Exception as e:
            shutil.rmtree(outdir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"No se pudo generar: {e}")

        files = _list_files(job_id, outputs)
        preview = next((f["url"] for f in files if f["key"] == "svg"), None)
        return {"job_id": job_id, "garment": req.garment, "size": size,
                "method": req.method, "style": style,
                "stats": _stats(req.garment, size, req.method, style, p),
                "preview": preview, "files": files,
                "zip": f"/api/zip/{job_id}"}

    @app.get("/api/file/{job_id}/{name}")
    def api_file(job_id: str, name: str):
        if "/" in name or ".." in name:
            raise HTTPException(status_code=400, detail="nombre no válido")
        fp = os.path.join(_job_dir(job_id), name)
        if not os.path.isfile(fp):
            raise HTTPException(status_code=404, detail="archivo no encontrado")
        mime = _MIME.get(os.path.splitext(name)[1].lower())
        return FileResponse(fp, media_type=mime, filename=name)

    @app.get("/api/zip/{job_id}")
    def api_zip(job_id: str):
        d = _job_dir(job_id)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name in sorted(os.listdir(d)):
                fp = os.path.join(d, name)
                if os.path.isfile(fp):
                    z.write(fp, name)
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="application/zip",
            headers={"Content-Disposition":
                     f'attachment; filename="patronaje_{job_id[:8]}.zip"'})

    def _viewer(name):
        fp = os.path.join(VIEWERS_DIR, name)
        if not os.path.isfile(fp):     # generación perezosa si el startup falló
            _prepare_viewers()
        if not os.path.isfile(fp):
            raise HTTPException(status_code=404, detail="visor no disponible")
        return FileResponse(fp, media_type="text/html")

    @app.get("/viewer_live.html")
    def viewer_2d():
        return _viewer("viewer_live.html")

    @app.get("/viewer_3d.html")
    def viewer_3d():
        return _viewer("viewer_3d.html")

    return app


app = create_app()


_APP_UI = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Patronaje — aplicación</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='13'>%E2%9C%82</text></svg>">

<style>
:root{--bg:#eef1f5;--card:#fff;--ink:#1d2733;--soft:#5f6f80;--line:#d3dbe4;
 --accent:#245b86;--accent2:#2f7fb0;--ok:#2e7d46;--wash:#e4edf4;
 --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;}
@media(prefers-color-scheme:dark){:root{--bg:#0f1620;--card:#17212e;--ink:#dce6f0;
 --soft:#8ea1b5;--line:#293849;--accent:#5aa2d8;--accent2:#74b4e2;--wash:#16344c;}}
:root[data-theme=light]{--bg:#eef1f5;--card:#fff;--ink:#1d2733;--soft:#5f6f80;--line:#d3dbe4;--accent:#245b86;--wash:#e4edf4;}
:root[data-theme=dark]{--bg:#0f1620;--card:#17212e;--ink:#dce6f0;--soft:#8ea1b5;--line:#293849;--accent:#5aa2d8;--wash:#16344c;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5}
.top{background:#0f1620;color:#e9dcc6;padding:12px 20px;display:flex;gap:18px;align-items:center;font-weight:600}
.top b{color:#e9dcc6}.top a{color:#cdd6e0;text-decoration:none;font-size:14px}.top a:hover{color:#fff}
.wrap{max-width:1180px;margin:0 auto;padding:22px 20px 60px}
h1{font-size:23px;margin:.2em 0}.sub{color:var(--soft);font-size:14px;margin-bottom:18px;max-width:70ch}
.stage{display:grid;grid-template-columns:340px 1fr;gap:20px}
@media(max-width:840px){.stage{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
label.f{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--soft);margin:12px 0 4px;font-weight:700}
select,input[type=number]{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);font-size:14px}
.seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{flex:1;padding:8px;border:0;background:var(--card);color:var(--ink);cursor:pointer;font-size:13px}
.seg button.on{background:var(--accent);color:#fff}
.meas{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.meas .m label{font-size:11px;color:var(--soft)}.meas .m input{padding:6px 8px}
.gen{margin-top:16px;width:100%;padding:12px;border:0;border-radius:9px;background:var(--accent);color:#fff;font-size:15px;font-weight:700;cursor:pointer}
.gen:disabled{opacity:.6;cursor:default}
.chk{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:13px;color:var(--soft)}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.stat{background:var(--wash);border:1px solid var(--line);border-radius:9px;padding:8px 14px;min-width:96px}
.stat .n{font-size:20px;font-weight:800;font-variant-numeric:tabular-nums}.stat .l{font-size:11px;color:var(--soft);text-transform:uppercase;letter-spacing:.04em}
.preview{border:1px solid var(--line);border-radius:10px;background:#fff;padding:10px;text-align:center;min-height:220px}
.preview img{max-width:100%;max-height:60vh}
.files{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}
@media(max-width:560px){.files{grid-template-columns:1fr}.meas{grid-template-columns:1fr}}
.file{display:flex;justify-content:space-between;align-items:center;gap:8px;border:1px solid var(--line);border-radius:8px;padding:9px 11px;text-decoration:none;color:var(--ink);background:var(--card)}
.file:hover{border-color:var(--accent)}.file .fl{font-size:13px;font-weight:600}.file .fk{font-size:11px;color:var(--soft);font-family:var(--mono)}
.rowbtns{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
.btn{padding:9px 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);text-decoration:none;font-size:13px;font-weight:600;cursor:pointer}
.btn.primary{background:var(--ok);color:#fff;border-color:transparent}
.empty{color:var(--soft);text-align:center;padding:50px 10px}
.err{color:#c0392b;background:#fdecea;border:1px solid #f5c6cb;border-radius:8px;padding:10px 12px;font-size:13px;margin-top:12px}
@media(prefers-color-scheme:dark){.err{background:#3a1c1c;border-color:#5a2a2a;color:#f0a8a0}.preview{background:#f4f7fb}}
.spin{display:inline-block;width:16px;height:16px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:sp .7s linear infinite;vertical-align:-3px;margin-right:8px}
@keyframes sp{to{transform:rotate(360deg)}}
.share{width:100%;margin-top:8px}
#toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#1d2733;color:#fff;padding:10px 16px;border-radius:8px;font-size:13px;opacity:0;transition:opacity .3s;pointer-events:none;z-index:50;max-width:90vw;overflow:hidden;text-overflow:ellipsis}
.subhead{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--soft);font-weight:700;grid-column:1/-1;margin-top:6px}
</style></head><body>
<div class="top"><b>&#9986; Patronaje</b>
 <a href="/">Inicio</a><a href="/viewer_live.html">Patrón 2D</a><a href="/viewer_3d.html">Maniquí 3D</a></div>
<div class="wrap">
 <h1>Genera tu patrón industrial</h1>
 <div class="sub">Elige la prenda y las medidas; el <b>motor paramétrico</b> traza el
  patrón con curvas CAD reales y validación de casado, y genera los archivos listos
  para producción para que los <b>descargues</b> — el mismo motor que la línea de comandos.</div>
 <div id="toast"></div>
 <div class="stage">
  <div class="card" id="panel">
   <label class="f">Prenda</label><select id="garment"></select>
   <label class="f">Medidas</label>
   <div class="seg"><button id="mSize" class="on" onclick="setMode('size')">Por talla</button>
    <button id="mCustom" onclick="setMode('custom')">A medida</button></div>
   <div id="sizeBox"><label class="f">Talla</label><select id="size"></select></div>
   <div id="customBox" style="display:none"><div class="meas" id="meas"></div></div>
   <label class="f">Método de trazado</label><select id="method"></select>
   <label class="f">Estilo</label><select id="style"></select>
   <label class="chk"><input type="checkbox" id="seam" checked> Incluir margen de costura</label>
   <button class="gen" id="gen" onclick="doGenerate()">Generar patrón</button>
   <button class="btn share" id="share" onclick="shareLink()">&#128279; Copiar enlace del proyecto</button>
   <div id="err"></div>
  </div>
  <div class="card" id="result"><div class="empty">Configura a la izquierda y pulsa
   <b>Generar patrón</b>. Aquí verás la vista previa, las métricas y las descargas.</div></div>
 </div>
</div>
<script>
let CFG=null, MODE='size';
const $=id=>document.getElementById(id);
async function boot(){
 CFG=await (await fetch('/api/config')).json();
 const gs=$('garment');CFG.garments.forEach(g=>gs.add(new Option(g.label,g.id)));
 const ms=$('method');CFG.methods.forEach(m=>ms.add(new Option(m.label,m.id)));
 const ss=$('size');CFG.size_order.forEach(s=>ss.add(new Option(s,s)));ss.value='S';
 gs.onchange=()=>{fillStyles();if(MODE==='custom')buildMeas();};
 ss.onchange=()=>{if(MODE==='custom')buildMeas();};
 fillStyles();buildMeas();
 if(restore())doGenerate();     // proyecto compartido por enlace -> restaura y genera
}
function garment(){return CFG.garments.find(g=>g.id===$('garment').value);}
function fillStyles(){const st=$('style');st.innerHTML='';st.add(new Option('Base (sin estilo)','none'));
 garment().styles.forEach(s=>st.add(new Option(s,s)));}
function meaInput(k,lab,v){return '<div class="m"><label>'+lab+'</label><input type="number" step="0.5" id="fx-'+k+'" value="'+v+'"></div>';}
function buildMeas(){const box=$('meas');box.innerHTML='';const sz=CFG.sizes[$('size').value]||{};
 CFG.fields.forEach(([k,lab])=>box.insertAdjacentHTML('beforeend',meaInput(k,lab,sz[k]||0)));
 const lens=CFG.lengths[$('garment').value]||[];
 if(lens.length){box.insertAdjacentHTML('beforeend','<div class="subhead">Largos de prenda</div>');
  lens.forEach(([k,lab])=>box.insertAdjacentHTML('beforeend',meaInput(k,lab,sz[k]||0)));}}
function setMode(m){MODE=m;$('mSize').classList.toggle('on',m==='size');$('mCustom').classList.toggle('on',m==='custom');
 $('sizeBox').style.display=m==='size'?'':'none';$('customBox').style.display=m==='custom'?'':'none';
 if(m==='custom')buildMeas();}
function customMeas(){const m={};document.querySelectorAll('#meas [id^=fx-]').forEach(el=>{m[el.id.slice(3)]=parseFloat(el.value);});return m;}
// --- guardar / compartir el proyecto por enlace (estado en la URL, sin backend) ---
function projState(){const s={garment:$('garment').value,mode:MODE,size:$('size').value,
 method:$('method').value,style:$('style').value,seam:$('seam').checked};
 if(MODE==='custom')s.measurements=customMeas();return s;}
function toast(msg){const t=$('toast');t.textContent=msg;t.style.opacity=1;clearTimeout(t._t);t._t=setTimeout(()=>t.style.opacity=0,2600);}
function shareLink(){const code=btoa(unescape(encodeURIComponent(JSON.stringify(projState()))));
 const url=location.origin+location.pathname+'?p='+encodeURIComponent(code);
 if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(url).then(()=>toast('Enlace del proyecto copiado')).catch(()=>toast(url));
 else toast(url);}
function restore(){const q=new URLSearchParams(location.search).get('p');if(!q)return false;
 try{const s=JSON.parse(decodeURIComponent(escape(atob(q))));
  $('garment').value=s.garment||'camisa';fillStyles();
  $('method').value=s.method||'aldrich';$('style').value=s.style||'none';
  $('seam').checked=s.seam!==false;$('size').value=s.size||'S';
  setMode(s.mode||'size');
  if(s.mode==='custom'&&s.measurements){buildMeas();for(const k in s.measurements){const el=$('fx-'+k);if(el)el.value=s.measurements[k];}}
  return true;}catch(e){return false;}}
async function doGenerate(){
 $('err').innerHTML='';const btn=$('gen');btn.disabled=true;btn.innerHTML='<span class="spin"></span>Generando…';
 const body={garment:$('garment').value,mode:MODE,size:$('size').value,method:$('method').value,
  style:$('style').value,include_seam:$('seam').checked};
 if(MODE==='custom')body.measurements=customMeas();
 try{
  const r=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data=await r.json();
  if(!r.ok){const d=data.detail;const msg=(d&&d.issues)?d.issues.join(' · '):(typeof d==='string'?d:'Error al generar');
   $('err').innerHTML='<div class="err">'+msg+'</div>';return;}
  render(data);
 }catch(e){$('err').innerHTML='<div class="err">Error de red: '+e+'</div>';}
 finally{btn.disabled=false;btn.textContent='Generar patrón';}
}
function render(d){
 const s=d.stats;let h='';
 if(s)h+='<div class="stats">'
  +'<div class="stat"><div class="n">'+s.piezas+'</div><div class="l">Piezas</div></div>'
  +'<div class="stat"><div class="n">'+s.consumo_m.toFixed(2)+' m</div><div class="l">Consumo 150cm</div></div>'
  +'<div class="stat"><div class="n">'+s.eficiencia+' %</div><div class="l">Eficiencia</div></div></div>';
 h+='<div class="rowbtns"><a class="btn primary" href="'+d.zip+'">&#8681; Descargar todo (ZIP)</a>'
  +'<a class="btn" href="/viewer_live.html" target="_blank">Abrir patrón 2D en vivo</a>'
  +'<a class="btn" href="/viewer_3d.html" target="_blank">Abrir maniquí 3D</a></div>';
 if(d.preview)h+='<div class="preview"><img src="'+d.preview+'" alt="vista previa del patrón"></div>';
 h+='<div class="files">'+d.files.map(f=>'<a class="file" href="'+f.url+'" download>'
  +'<span><span class="fl">'+f.label+'</span><br><span class="fk">'+f.name+'</span></span>'
  +'<span class="fk">'+f.kb+' KB</span></a>').join('')+'</div>';
 $('result').innerHTML=h;
}
boot();
</script></body></html>"""


def main(argv=None):
    import argparse
    import uvicorn
    ap = argparse.ArgumentParser(description="Servidor web de patronaje (FastAPI)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args(argv)
    print(f"Patronaje app -> http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
