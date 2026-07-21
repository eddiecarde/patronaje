"""Plataforma web: página de inicio unificada (`index.html`) que ata los visores.

Un único punto de entrada, autocontenido y offline, con:
  - configurador de **talla / cuerpo / prenda** y **medidas editables** (prefijadas
    por talla, con opción de **cargar JSON**);
  - botones que abren el **patrón 2D en vivo** y el **maniquí 3D** pasando la
    configuración por query-string (la lee `webshell._HANDOFF`);
  - sección de **descargas** (CAD) y enlaces a la documentación.

Es la capa de presentación: la fuente de verdad sigue siendo el motor Python.
"""
from __future__ import annotations

import json
import os

from .parametric.measurements import SIZE_CHART

# medidas que ofrece el formulario (clave, etiqueta) — las que entienden los visores
_FIELDS = [
    ("busto", "Busto / Pecho"),
    ("cintura", "Cintura"),
    ("cadera", "Cadera"),
    ("contorno_cuello", "Contorno cuello"),
    ("ancho_espalda", "Ancho espalda"),
    ("hombro", "Hombro"),
    ("contorno_brazo", "Contorno brazo"),
    ("muneca", "Muñeca"),
    ("altura_cadera", "Altura cadera"),
    ("talle", "Talle (nuca-cint.)"),
    ("estatura", "Estatura"),
]
_ESTATURA = {"XS": 162, "S": 168, "M": 170, "L": 174, "XL": 178, "XXL": 182}


def _sizes_json() -> str:
    """Tabla talla -> medidas (desde SIZE_CHART, fuente de verdad del motor)."""
    out = {}
    for size, ch in SIZE_CHART.items():
        d = {}
        for k, _ in _FIELDS:
            if k == "talle":
                d[k] = ch.get("talle_espalda", 41)
            elif k == "estatura":
                d[k] = _ESTATURA.get(size, 168)
            elif k in ch:
                d[k] = ch[k]
        out[size] = d
    return json.dumps(out, ensure_ascii=False)


_PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Patronaje — plataforma</title>
<style>
:root{--bg:#0e141c;--panel:#fff;--ink:#1a2230;--mut:#5b6675;--line:#e2e6ec;
 --brand:#2a6df4;--accent:#c9a24b;--dark:#101722}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:#f4f6f9}
nav{display:flex;gap:2px;align-items:center;background:var(--dark);padding:8px 14px;
 font-weight:600;font-size:13px;position:sticky;top:0;z-index:50;border-bottom:1px solid #1f2937}
nav a{color:#cdd6e0;text-decoration:none;padding:5px 10px;border-radius:7px}
nav a.brand{color:#e9dcc6;font-weight:800;margin-right:14px}
nav a.active{background:#1f2b3a;color:#fff}
.hero{background:linear-gradient(135deg,#101722,#1c2a3e);color:#eaf0f7;padding:34px 20px 40px}
.hero .in{max-width:1040px;margin:0 auto}
.hero h1{margin:0 0 8px;font-size:26px;letter-spacing:-.2px}
.hero p{margin:0;color:#aebbcb;max-width:680px;line-height:1.5}
.wrap{max-width:1040px;margin:-22px auto 40px;padding:0 20px}
.grid{display:grid;grid-template-columns:1.4fr 1fr;gap:18px}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 18px 20px;
 box-shadow:0 6px 24px rgba(20,30,50,.06)}
.card h2{margin:0 0 4px;font-size:16px}
.card .hint{color:var(--mut);font-size:13px;margin:0 0 14px}
label{display:block;font-size:12px;color:var(--mut);margin:0 0 4px}
select,input[type=number]{width:100%;font-size:14px;padding:8px 9px;border:1px solid var(--line);
 border-radius:9px;background:#fff;color:var(--ink)}
.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px}
@media(max-width:520px){.row3{grid-template-columns:1fr 1fr}}
.meas{display:grid;grid-template-columns:1fr 1fr;gap:10px 12px}
.meas .f{margin-bottom:2px}
.btns{display:flex;flex-direction:column;gap:10px;margin-top:6px}
.btn{display:flex;align-items:center;justify-content:center;gap:8px;padding:13px 14px;border-radius:11px;
 font-size:15px;font-weight:700;text-decoration:none;cursor:pointer;border:0}
.btn.p{background:var(--brand);color:#fff}
.btn.s{background:#111a27;color:#fff}
.btn.g{background:#fff;color:var(--ink);border:1px solid var(--line);font-weight:600}
.filerow{margin-top:12px;font-size:13px;color:var(--mut)}
.filerow input{font-size:12px}
.kpis{display:flex;gap:14px;flex-wrap:wrap;margin:2px 0 12px}
.kpi{background:#f6f8fb;border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:13px}
.kpi b{display:block;font-size:18px;color:var(--ink)}
.dl{font-size:13px;line-height:1.7;color:var(--ink)}
.dl code{background:#0e141c;color:#e9edf3;padding:2px 7px;border-radius:6px;font-size:12px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.tag{background:#eef2f8;border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:12px;color:var(--mut)}
footer{max-width:1040px;margin:0 auto;padding:20px;color:var(--mut);font-size:12px;line-height:1.6}
a.link{color:var(--brand);text-decoration:none}
</style></head><body>
<nav><a href="index.html" class="brand">✂ Patronaje</a>
 <a href="index.html" class="active">Inicio</a>
 <a href="viewer_live.html">Patrón 2D</a>
 <a href="viewer_3d.html">Maniquí 3D</a></nav>

<div class="hero"><div class="in">
 <h1>Patronaje industrial paramétrico</h1>
 <p>Configura tu prenda por talla o por medidas, ve el <b>patrón 2D</b> recalcularse
  al instante y pruébalo en el <b>maniquí 3D</b> a medida. El núcleo (método Aldrich,
  splines G2, curvas listas para CNC) genera patrones de producción y exportación CAD.</p>
</div></div>

<div class="wrap"><div class="grid">
 <div class="card">
  <h2>Configura tu patrón</h2>
  <p class="hint">Elige una talla base y ajusta las medidas si lo necesitas.</p>
  <div class="row3">
   <div><label>Talla</label><select id="size"></select></div>
   <div><label>Cuerpo (3D)</label><select id="sexo">
     <option value="F">Mujer</option><option value="M">Hombre</option></select></div>
   <div><label>Prenda</label><select id="garment">
     <option value="camisa">Camisa</option><option value="falda">Falda</option>
     <option value="pantalon">Pantalón</option><option value="vestido">Vestido</option>
     <option value="blazer">Blazer</option></select></div>
  </div>
  <div class="meas" id="meas"></div>
  <div class="filerow">Cargar medidas (JSON):
   <input type="file" id="file" accept="application/json,.json"></div>
 </div>

 <div class="card">
  <h2>Ver el patrón</h2>
  <p class="hint">Se abre con tu configuración aplicada.</p>
  <div class="btns">
   <a class="btn p" id="go2d">📐 Abrir patrón 2D (en vivo)</a>
   <a class="btn s" id="go3d">🧍 Abrir maniquí 3D</a>
   <a class="btn g" href="viewer.html">Ver variantes por método/estilo</a>
  </div>
  <div style="margin-top:16px">
   <h2>Producción / CAD</h2>
   <p class="hint" style="margin-bottom:8px">Genera los archivos de corte con el CLI:</p>
   <div class="dl"><code>python -m patronaje.cli --size S --output output</code><br>
    DXF R2013 · AAMA/ASTM · SVG · PDF 1:1 · AI · JSON · CSV · SCR · tech pack · marker.</div>
   <div class="tags">
    <span class="tag">Aldrich</span><span class="tag">Müller</span><span class="tag">Bunka</span>
    <span class="tag">Esmod</span><span class="tag">grading XS–XXL</span><span class="tag">a medida</span></div>
  </div>
 </div>
</div></div>

<footer>
 Autocontenido y offline — sin CDN. Motor paramétrico en Python; los visores portan el
 núcleo a JavaScript. Licencia <b>MIT</b>; el maniquí 3D incrusta <b>three.js</b> (MIT, ver NOTICE).
 Documentación en <span style="color:#334">docs/</span>.
</footer>

<script>
const SIZES=/*__SIZES__*/;
const FIELDS=/*__FIELDS__*/;
const meas=document.getElementById('meas');
const inputs={};
FIELDS.forEach(f=>{const k=f[0];
 const w=document.createElement('div');w.className='f';
 w.innerHTML='<label>'+f[1]+' (cm)</label><input type="number" step="0.5" id="m_'+k+'">';
 meas.appendChild(w);inputs[k]=w.querySelector('input');});
const sizeSel=document.getElementById('size');
Object.keys(SIZES).forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent='Talla '+s;sizeSel.appendChild(o);});
sizeSel.value='S';
function fillFromSize(){const d=SIZES[sizeSel.value]||{};FIELDS.forEach(f=>{const k=f[0];
 if(d[k]!=null)inputs[k].value=d[k];});}
fillFromSize();
sizeSel.onchange=fillFromSize;
function qs(extra){const q=new URLSearchParams();
 q.set('garment',document.getElementById('garment').value);
 FIELDS.forEach(f=>{const v=parseFloat(inputs[f[0]].value);if(isFinite(v))q.set(f[0],v);});
 if(extra)for(const k in extra)q.set(k,extra[k]);
 return q.toString();}
document.getElementById('go2d').addEventListener('click',()=>{location.href='viewer_live.html?'+qs();});
document.getElementById('go3d').addEventListener('click',()=>{
 location.href='viewer_3d.html?'+qs({sexo:document.getElementById('sexo').value});});
document.getElementById('file').addEventListener('change',ev=>{
 const f=ev.target.files[0];if(!f)return;const r=new FileReader();
 r.onload=()=>{try{const j=JSON.parse(r.result);const m=j.measurements||j.medidas||j;
  FIELDS.forEach(ff=>{const k=ff[0];if(m[k]!=null)inputs[k].value=m[k];});
 }catch(e){alert('JSON no válido');}};r.readAsText(f);});
</script></body></html>"""


def build_web_app(outdir: str = "output") -> str:
    """Genera `output/index.html`, la página de inicio unificada de la plataforma."""
    os.makedirs(outdir, exist_ok=True)
    html = (_PAGE
            .replace("/*__SIZES__*/", _sizes_json())
            .replace("/*__FIELDS__*/", json.dumps(_FIELDS, ensure_ascii=False)))
    path = os.path.join(outdir, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


if __name__ == "__main__":
    import sys
    out = sys.argv[sys.argv.index("--output") + 1] if "--output" in sys.argv else "output"
    p = build_web_app(out)
    print(f"Plataforma: {p} ({os.path.getsize(p)/1024:.0f} KB)")
