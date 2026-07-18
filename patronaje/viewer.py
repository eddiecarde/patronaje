"""Generador de un visor/configurador HTML autocontenido.

Produce un único archivo HTML (SVG inline, sin recursos externos) donde se puede
elegir **método** y **estilo** y ver el patrón al instante, junto con el número
de piezas y el consumo de tela. Es una capa de presentación sobre el motor: los
SVG se generan con `export_svg` y las estadísticas con `marker_report`.

Uso:
    python -m patronaje.viewer --output output   # genera output/viewer.html
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile

from .garment.shirt import build_shirt
from .transform.styles import apply_style
from .export.svg import export_svg
from .marker.layout import marker_report

METHODS = [("aldrich", "Aldrich"), ("mueller", "Müller & Sohn"), ("bunka", "Bunka"),
           ("esmod", "ESMOD"), ("marti", "Sistema Martí"), ("armstrong", "Joseph-Armstrong")]
STYLES = ["flare", "puff", "bell", "princess", "empire", "peplum", "dolman", "raglan",
          "v_neck", "boat_neck", "dress", "oversized", "wrap", "godet"]


def _svg_of(shirt) -> str:
    fd, path = tempfile.mkstemp(suffix=".svg")
    os.close(fd)
    export_svg(shirt, path)
    with open(path, encoding="utf-8") as f:
        s = f.read()
    os.remove(path)
    # quita la declaración XML para inlinar
    if s.lstrip().startswith("<?xml"):
        s = s[s.index("?>") + 2:]
    return s.strip()


def _stats(shirt) -> dict:
    rep = marker_report(shirt, widths=(150.0,))
    d = rep["por_ancho"][150.0]
    return {"piezas": len(shirt.pieces), "largo_m": d["largo_m"],
            "eficiencia": round(d["eficiencia"] * 100, 1)}


def build_variants(size: str = "S") -> dict:
    variants = {}
    for key, label in METHODS:
        sh = build_shirt(size, method=key).layout()
        variants[f"m:{key}"] = {"cat": "Método", "label": label,
                                "svg": _svg_of(sh), "stats": _stats(sh)}
    for st in STYLES:
        sh = build_shirt(size, method="aldrich")
        sh = apply_style(sh, st)
        variants[f"s:{st}"] = {"cat": "Estilo", "label": st,
                               "svg": _svg_of(sh), "stats": _stats(sh)}
    return variants


_PAGE = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Patronaje — visor de patrones</title>
<style>
:root{--ink:#1f2d3d;--line:#c9d4e0;--accent:#22405e;--soft:#eef4fb;}
*{box-sizing:border-box} body{font-family:'Segoe UI',Arial,sans-serif;color:var(--ink);
 margin:0;background:#f4f7fb} .wrap{max-width:1100px;margin:0 auto;padding:18px}
h1{font-size:20px;margin:4px 0} .sub{color:#6b8199;font-size:13px;margin-bottom:12px}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;background:#fff;
 border:1px solid var(--line);border-radius:10px;padding:12px}
select,button{font-size:14px;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:#fff}
.stage{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px}
.svgbox{flex:1 1 620px;background:#fff;border:1px solid var(--line);border-radius:10px;
 padding:12px;min-height:300px;overflow:auto} .svgbox svg{width:100%;height:auto;max-height:75vh}
.panel{flex:1 1 220px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.badge{display:inline-block;background:var(--accent);color:#fff;border-radius:6px;padding:3px 8px;font-size:12px}
.kv{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:6px 0}
.legend span{display:inline-block;margin-right:10px;font-size:12px}
.dot{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:middle}
@media(prefers-color-scheme:dark){body{background:#0f1720;color:#dfe8f2}
 .controls,.svgbox,.panel{background:#16212e;border-color:#2a3a4d} .svgbox{background:#f4f7fb}}
:root[data-theme="dark"] body{background:#0f1720;color:#dfe8f2}
:root[data-theme="dark"] .controls,:root[data-theme="dark"] .panel{background:#16212e;border-color:#2a3a4d}
:root[data-theme="light"] body{background:#f4f7fb;color:#1f2d3d}
:root[data-theme="light"] .controls,:root[data-theme="light"] .panel{background:#fff}
</style></head><body><div class="wrap">
<h1>Sistema de patronaje — visor de patrones</h1>
<div class="sub">Camisa básica femenina ML · Talla S · elige método y estilo para ver el patrón</div>
<div class="controls">
 <label>Categoría <select id="cat"></select></label>
 <label>Variante <select id="var"></select></label>
 <span class="legend"><span><i class="dot" style="background:#d00"></i>corte</span>
 <span><i class="dot" style="background:#0a0"></i>costura</span>
 <span><i class="dot" style="background:#ca0"></i>hilo</span>
 <span><i class="dot" style="background:#0bb"></i>piquetes</span>
 <span><i class="dot" style="background:#c0c"></i>doblez</span></span>
</div>
<div class="stage">
 <div class="svgbox" id="svg"></div>
 <div class="panel">
  <div class="badge" id="catlabel">—</div>
  <h2 id="label" style="margin:8px 0">—</h2>
  <div class="kv"><span>Piezas</span><b id="piezas">—</b></div>
  <div class="kv"><span>Consumo (150 cm)</span><b id="largo">—</b></div>
  <div class="kv"><span>Eficiencia tela</span><b id="ef">—</b></div>
  <p class="sub" style="margin-top:12px">Generado por el motor paramétrico
   (6 métodos · 25 estilos · 6 tallas). Exportable a DXF/SVG/PDF/AI/JSON/CSV/SCR.</p>
 </div>
</div></div>
<script>
const DATA = {data};
const cats = [...new Set(Object.values(DATA).map(v=>v.cat))];
const catSel=document.getElementById('cat'), varSel=document.getElementById('var');
cats.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;catSel.appendChild(o)});
function fillVars(){varSel.innerHTML='';const c=catSel.value;
 Object.entries(DATA).filter(([k,v])=>v.cat===c).forEach(([k,v])=>{
  const o=document.createElement('option');o.value=k;o.textContent=v.label;varSel.appendChild(o)});show()}
function show(){const v=DATA[varSel.value];if(!v)return;
 document.getElementById('svg').innerHTML=v.svg;
 document.getElementById('catlabel').textContent=v.cat;
 document.getElementById('label').textContent=v.label;
 document.getElementById('piezas').textContent=v.stats.piezas;
 document.getElementById('largo').textContent=v.stats.largo_m.toFixed(2)+' m';
 document.getElementById('ef').textContent=v.stats.eficiencia+' %';}
catSel.onchange=fillVars; varSel.onchange=show; fillVars();
</script></body></html>"""


def build_viewer(outdir: str = "output", size: str = "S") -> str:
    os.makedirs(outdir, exist_ok=True)
    variants = build_variants(size)
    page = _PAGE.replace("{data}", json.dumps(variants, ensure_ascii=False))
    path = os.path.join(outdir, "viewer.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Genera el visor HTML de patrones")
    ap.add_argument("--output", default="output")
    ap.add_argument("--size", default="S")
    args = ap.parse_args(argv)
    path = build_viewer(args.output, args.size)
    print(f"Visor generado: {path} ({os.path.getsize(path)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
