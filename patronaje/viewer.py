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


_LIVE_PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Patronaje — visor en vivo</title>
<style>
:root{--ink:#1f2d3d;--line:#c9d4e0;--accent:#22405e;}
*{box-sizing:border-box} body{font-family:'Segoe UI',Arial,sans-serif;color:var(--ink);
 margin:0;background:#f4f7fb} .wrap{max-width:1150px;margin:0 auto;padding:18px}
h1{font-size:20px;margin:4px 0} .sub{color:#6b8199;font-size:13px;margin-bottom:12px}
.stage{display:flex;gap:16px;flex-wrap:wrap;margin-top:8px}
.controls{flex:1 1 300px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.svgbox{flex:2 1 620px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px;min-height:320px}
.svgbox svg{width:100%;height:auto;max-height:78vh}
.row{display:flex;align-items:center;gap:8px;margin:7px 0;font-size:13px}
.row label{flex:0 0 118px} .row input[type=range]{flex:1} .row b{flex:0 0 54px;text-align:right;font-variant-numeric:tabular-nums}
.kv{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:5px 0;font-size:13px}
.ok{color:#0a7a2f;font-weight:600} .bad{color:#c0392b;font-weight:600}
.legend span{display:inline-block;margin-right:10px;font-size:12px}
.dot{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:middle}
button{font-size:13px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer}
@media(prefers-color-scheme:dark){body{background:#0f1720;color:#dfe8f2}
 .controls,.svgbox{background:#16212e;border-color:#2a3a4d} .svgbox{background:#f4f7fb}}
:root[data-theme="dark"] body{background:#0f1720;color:#dfe8f2}
:root[data-theme="dark"] .controls{background:#16212e;border-color:#2a3a4d}
:root[data-theme="light"] body{background:#f4f7fb;color:#1f2d3d}
:root[data-theme="light"] .controls{background:#fff}
</style></head><body><div class="wrap">
<h1>Patronaje — visor en vivo (motor paramétrico en el navegador)</h1>
<div class="sub">Elige la prenda, mueve las medidas y el patrón se recalcula al instante
 (camisa, falda, pantalón). Sin dependencias: el núcleo (spline G2 + fórmulas de bloque) corre en JS.</div>
<div class="stage">
 <div class="controls">
  <div class="row"><label>Prenda</label>
   <select id="garment" style="flex:1;font-size:14px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:#fff"></select></div>
  <div id="ctrls"></div>
 </div>
 <div class="svgbox">
  <div id="svg"></div>
  <div style="margin-top:10px" class="legend">
   <span><i class="dot" style="background:#22405e"></i>línea de costura</span>
   <span><i class="dot" style="background:#111"></i>pinza</span></div>
  <div id="metrics"></div>
  <div style="margin-top:10px"><button id="reset">Restablecer medidas</button></div>
 </div>
</div></div>
<script>
// ====== núcleo paramétrico portado (fiel a patronaje.core.curves + blocks Aldrich) ======
function solveM(t,y){const n=t.length,M=new Array(n).fill(0);if(n<3)return M;
 const h=[];for(let i=0;i<n-1;i++)h.push(t[i+1]-t[i]);
 const lo=new Array(n).fill(0),di=new Array(n).fill(1),up=new Array(n).fill(0),r=new Array(n).fill(0);
 for(let i=1;i<n-1;i++){lo[i]=h[i-1];di[i]=2*(h[i-1]+h[i]);up[i]=h[i];
  r[i]=6*((y[i+1]-y[i])/h[i]-(y[i]-y[i-1])/h[i-1]);}
 for(let i=1;i<n;i++){const w=lo[i]/di[i-1];di[i]-=w*up[i-1];r[i]-=w*r[i-1];}
 M[n-1]=0;for(let i=n-2;i>=0;i--)M[i]=(r[i]-up[i]*M[i+1])/di[i];M[0]=0;M[n-1]=0;return M;}
class Spline{constructor(pts){this.pts=pts;this.xs=pts.map(p=>p[0]);this.ys=pts.map(p=>p[1]);
  const t=[0];for(let i=1;i<pts.length;i++)t.push(t[i-1]+Math.hypot(this.xs[i]-this.xs[i-1],this.ys[i]-this.ys[i-1]));
  this.t=t;this.total=t[t.length-1];this.Mx=solveM(t,this.xs);this.My=solveM(t,this.ys);}
 ev(tv,y,M){const t=this.t;let lo=0,hi=t.length;while(lo<hi){const m=(lo+hi)>>1;if(t[m]<tv)lo=m+1;else hi=m;}
  let i=Math.min(Math.max(lo-1,0),t.length-2);const h=t[i+1]-t[i];if(h<=0)return y[i];
  const A=(t[i+1]-tv)/h,B=(tv-t[i])/h;
  return A*y[i]+B*y[i+1]+((A**3-A)*M[i]+(B**3-B)*M[i+1])*(h*h)/6;}
 pt(tv){return [this.ev(tv,this.xs,this.Mx),this.ev(tv,this.ys,this.My)];}
 sample(n){if(this.total<=0)return this.pts.slice();const o=[];for(let i=0;i<=n;i++)o.push(this.pt(this.total*i/n));return o;}}
function smooth(pts,span){span=span||12;if(pts.length<=2)return pts.map(p=>[p[0],p[1]]);
 return new Spline(pts.map(p=>[p[0],p[1]])).sample(span*(pts.length-1));}
function plen(p){let s=0;for(let i=0;i<p.length-1;i++)s+=Math.hypot(p[i+1][0]-p[i][0],p[i+1][1]-p[i][1]);return s;}
function xAtY(poly,y){for(let i=0;i<poly.length-1;i++){const [x0,y0]=poly[i],[x1,y1]=poly[i+1];
  const lo=Math.min(y0,y1),hi=Math.max(y0,y1);if(lo-1e-9<=y&&y<=hi+1e-9&&Math.abs(y1-y0)>1e-12){
   const t=(y-y0)/(y1-y0);return x0+t*(x1-x0);}}return Math.abs(poly[0][1]-y)<Math.abs(poly[poly.length-1][1]-y)?poly[0][0]:poly[poly.length-1][0];}

function bodice(P){
 const cc=P.contorno_cuello,bnw=cc/5-0.3,fnw=cc/5-0.5,fnd=cc/5+2.0;
 const scye=P.busto/8+10.5+0.5,med=P.ancho_espalda/2,cuarto=(P.busto+P.holgura_busto)/4,largo=P.largo_camisa,H=P.hombro;
 const sub=2.0,dropB=4.5,dropF=5.0,yl=10.0;
 const cbn=[0,sub],snpB=[bnw,0],dxB=Math.sqrt(Math.max(0,H*H-dropB*dropB)),spB=[bnw+dxB,dropB];
 const bLine=scye*0.55,ab=[med,bLine],usB=[cuarto,scye];
 const backNeck=smooth([cbn,[bnw*0.45,sub*0.9],[bnw*0.8,sub*0.45],snpB],10);
 const midB=[med+(cuarto-med)*0.55,bLine+(scye-bLine)*0.62];
 const backArm=smooth([spB,ab,midB,usB],12);
 const snpF=[fnw,0],cfn=[0,fnd],dxF=Math.sqrt(Math.max(0,H*H-dropF*dropF)),spF=[fnw+dxF,dropF];
 const fLine=scye*0.60,fc=[med-1.5,fLine],usF=[cuarto,scye];
 const frontNeck=smooth([snpF,[fnw*0.62,fnd*0.40],[fnw*0.28,fnd*0.80],cfn],12);
 const midF=[fc[0]+(cuarto-fc[0])*0.55,fLine+(scye-fLine)*0.60];
 const frontArm=smooth([spF,fc,midF,usF],12);
 const rev=a=>a.slice().reverse();
 const front=[cfn].concat(rev(frontNeck).slice(1),[spF],frontArm.slice(1),[[cuarto,largo]],[[0,largo]]);
 const armXb=xAtY(backArm,yl);
 const yoke=[cbn].concat(backNeck.slice(1),[spB],backArm.filter(p=>p[1]<=yl),[[armXb,yl]],[[0,yl]]);
 const lower=[[0,yl],[armXb,yl]].concat(backArm.filter(p=>p[1]>=yl),[[cuarto,largo]],[[0,largo]]);
 return {front,yoke,lower,backNeck,frontNeck,backArm,frontArm,scye};}

function sleeve(P,targetArm){
 const capFor=(h,bh)=>{const sh=[0,0],br=[bh,h],bl=[-bh,h];
  const f=smooth([sh,[bh*0.30,h*0.10],[bh*0.62,h*0.42],[bh*0.90,h*0.82],br],8);
  const b=smooth([sh,[-bh*0.32,h*0.08],[-bh*0.66,h*0.40],[-bh*0.92,h*0.80],bl],8);
  return b.slice().reverse().concat(f.slice(1));};
 const solveB=(h)=>{const tg=targetArm+1.0;let lo=3,hi=P.contorno_brazo;
  for(let i=0;i<60;i++){const m=(lo+hi)/2;if(plen(capFor(h,m))>tg)hi=m;else lo=m;}return (lo+hi)/2;};
 const scye=P.busto/8+10.5+0.5,minHalf=(P.contorno_brazo+2.0)/2;let h=scye*0.45,bh=0;
 for(let i=0;i<40;i++){bh=solveB(h);if(bh>=minHalf||h<=3)break;h*=0.92;}
 const cap=capFor(h,bh),bocaHalf=(P.muneca+6.0)/2;
 const outline=cap.concat([[bocaHalf,P.largo_manga],[-bocaHalf,P.largo_manga]]);
 return {outline,capLen:plen(cap)};}

// pinza en un borde (fiel a blocks.fitted._insert_dart)
function insertDart(edge,frac,intake,apex){
 const pts=edge.map(p=>[p[0],p[1]]),seg=[];
 for(let i=0;i<pts.length-1;i++)seg.push(Math.hypot(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]));
 const tot=seg.reduce((a,b)=>a+b,0)||1;
 const at=(dist)=>{let acc=0;for(let i=0;i<pts.length-1;i++){if(acc+seg[i]>=dist){const t=seg[i]?(dist-acc)/seg[i]:0;
   return [pts[i][0]+t*(pts[i+1][0]-pts[i][0]),pts[i][1]+t*(pts[i+1][1]-pts[i][1])];}acc+=seg[i];}return pts[pts.length-1];};
 const c=tot*frac,d1=c-intake/2,d2=c+intake/2,leg1=at(d1),leg2=at(d2),ap=[apex[0],apex[1]];
 const cum=[0];for(const L of seg)cum.push(cum[cum.length-1]+L);
 const out=[],e=1e-9;
 for(let i=0;i<pts.length;i++){
  if(cum[i]<=d1+e||cum[i]>=d2-e)out.push(pts[i]);
  if(cum[i]<=d1+e&&(i+1===pts.length||cum[i+1]>d1))out.push(leg1,ap,leg2);}
 return {out,dart:[leg1,ap,leg2]};}
function dedup(poly){const out=[],tol=1e-6;
 for(let p of poly){p=[p[0],p[1]];if(!out.length||Math.hypot(p[0]-out[out.length-1][0],p[1]-out[out.length-1][1])>tol)out.push(p);}
 if(out.length>1&&Math.hypot(out[0][0]-out[out.length-1][0],out[0][1]-out[out.length-1][1])<=tol)out.pop();return out;}

// ---- camisa ----
function shirtPieces(P){
 const b=bodice(P),s=sleeve(P,plen(b.backArm)+plen(b.frontArm));
 const esc=plen(b.backNeck)+plen(b.frontNeck),sisa=plen(b.backArm)+plen(b.frontArm),copa=s.capLen;
 const d=Math.abs(sisa-copa);
 return {list:[["Delantero",b.front],["Espalda",b.lower],["Canesú",b.yoke],["Manga",s.outline]],
  metrics:[["Escote (medio)",esc.toFixed(1)+" cm"],["Sisa",sisa.toFixed(1)+" cm"],["Copa de manga",copa.toFixed(1)+" cm"],
           ["Casado |sisa − copa|",d.toFixed(2)+" cm",d<=1.5]],
  match:{escote:esc,sisa:sisa,copa:copa}};}

// ---- falda (fiel a blocks.skirt) ----
function skirtPanel(P,dartIn,dartLen,dartFrac){
 const qh=(P.cadera+4)/4,qw=(P.cintura+1)/4,supp=Math.max(0,qh-qw),dart=Math.min(dartIn,supp),side=supp-dart,sw=qh-side;
 const hipY=P.altura_cadera,hemY=P.largo_falda,cx=sw*dartFrac;
 const r=insertDart([[0,0],[sw,0]],sw?cx/sw:0,dart,[cx,dartLen]);
 const s=smooth([[sw,0],[qh-0.3,hipY*0.55],[qh,hipY]],8);
 return {contour:r.out.concat(s.slice(1),[[qh,hemY]],[[0,hemY]]),dart:r.dart};}
function skirtPieces(P){
 const f=skirtPanel(P,2.5,10,0.45),b=skirtPanel(P,3.5,14,0.50),qh=(P.cadera+4)/4,qw=(P.cintura+1)/4;
 return {list:[["Falda delantera",f.contour,[f.dart]],["Falda trasera",b.contour,[b.dart]]],
  metrics:[["Cintura (total)",(4*qw).toFixed(1)+" cm"],["Cadera (total)",(4*qh).toFixed(1)+" cm"],["Largo",P.largo_falda.toFixed(0)+" cm"]]};}

// ---- pantalón (fiel a blocks.trouser) ----
function trouserPanel(P,back){
 const hq=(P.cadera+5)/4,wq=(P.cintura+2)/4,rise=P.cadera/4+4,hipY=P.altura_cadera,hemY=P.largo_pantalon;
 const kneeY=rise+(hemY-rise)*0.47,fork=hq*(back?0.45:0.20);
 const knH=(44/4)*(back?1.05:0.92),hmH=(42/4)*(back?1.05:0.92);
 const dIn=back?3:2,dLen=back?13:10,tilt=back?2:0;
 const supp=Math.max(0,hq-wq),dart=Math.min(dIn,supp),side=supp-dart,sw=hq-side;
 const lc=(hq-fork)/2,kin=lc-knH,kout=lc+knH,hin=lc-hmH,hout=lc+hmH;
 const cf=smooth([[tilt,0],[0,hipY*0.7],[0,hipY],[-fork*0.45,rise-2.5],[-fork,rise]],8);
 const ins=smooth([[-fork,rise],[kin,kneeY],[hin,hemY]],8);
 const out=smooth([[hout,hemY],[kout,kneeY],[hq,hipY],[sw,0]],8);
 const cx=sw*(back?0.42:0.45),frac=(sw-cx)/Math.max(1e-6,sw-tilt);
 const r=insertDart([[sw,0],[tilt,0]],frac,dart,[cx,dLen]);
 const contour=dedup(cf.concat(ins.slice(1),[[hout,hemY]],out.slice(1),r.out.slice(1)));
 return {contour,dart:r.dart,inseam:ins};}
function trouserPieces(P){
 const f=trouserPanel(P,false),b=trouserPanel(P,true);
 return {list:[["Pantalón delantero",f.contour,[f.dart]],["Pantalón trasero",b.contour,[b.dart]]],
  metrics:[["Entrepierna del.",plen(f.inseam).toFixed(1)+" cm"],["Entrepierna tra.",plen(b.inseam).toFixed(1)+" cm"],["Largo",P.largo_pantalon.toFixed(0)+" cm"]]};}

const DEFS={
 busto:["Busto",76,120,88],holgura_busto:["Holgura busto",2,16,8],
 contorno_cuello:["Contorno cuello",32,46,37],ancho_espalda:["Ancho espalda",32,46,37],
 hombro:["Hombro",10,16,12.5],contorno_brazo:["Contorno brazo",24,42,30],muneca:["Muñeca",14,24,18],
 largo_camisa:["Largo camisa",50,90,68],largo_manga:["Largo manga",45,74,60],
 cintura:["Cintura",55,115,70],cadera:["Cadera",78,135,94],altura_cadera:["Altura cadera",16,26,20],
 largo_falda:["Largo falda",35,95,60],largo_pantalon:["Largo pantalón",70,115,100]};
const GARMENTS={
 camisa:{label:"Camisa",keys:["busto","holgura_busto","contorno_cuello","ancho_espalda","hombro","contorno_brazo","muneca","largo_camisa","largo_manga"],fn:shirtPieces},
 falda:{label:"Falda",keys:["cintura","cadera","altura_cadera","largo_falda"],fn:skirtPieces},
 pantalon:{label:"Pantalón",keys:["cintura","cadera","altura_cadera","largo_pantalon"],fn:trouserPieces}};
const P={};for(const k in DEFS)P[k]=DEFS[k][3];
let current="camisa";

function draw(){
 const R=GARMENTS[current].fn(P);let ox=0,gap=6,parts=[],minY=1e9,maxY=-1e9;
 R.list.forEach(([name,poly,darts])=>{
  let mnx=1e9,mxx=-1e9,mny=1e9,mxy=-1e9;
  poly.forEach(p=>{mnx=Math.min(mnx,p[0]);mxx=Math.max(mxx,p[0]);mny=Math.min(mny,p[1]);mxy=Math.max(mxy,p[1]);});
  const dx=ox-mnx;
  parts.push({name,pts:poly.map(p=>[p[0]+dx,p[1]]),cx:(mnx+mxx)/2+dx,top:mny,
   darts:(darts||[]).map(dt=>dt.map(p=>[p[0]+dx,p[1]]))});
  minY=Math.min(minY,mny);maxY=Math.max(maxY,mxy);ox+=(mxx-mnx)+gap;});
 const pad=6,vb=[-pad,minY-pad-4,ox+2*pad,(maxY-minY)+2*pad+4];
 let svg='<svg viewBox="'+vb.join(' ')+'" xmlns="http://www.w3.org/2000/svg">';
 parts.forEach(pt=>{const d=pt.pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(2)+' '+p[1].toFixed(2)).join(' ')+' Z';
  svg+='<path d="'+d+'" fill="none" stroke="#22405e" stroke-width="0.5"/>';
  pt.darts.forEach(dt=>{svg+='<path d="M'+dt[0][0].toFixed(2)+' '+dt[0][1].toFixed(2)+'L'+dt[1][0].toFixed(2)+' '+dt[1][1].toFixed(2)
   +'L'+dt[2][0].toFixed(2)+' '+dt[2][1].toFixed(2)+'" fill="none" stroke="#111" stroke-width="0.35"/>';});
  svg+='<text x="'+pt.cx.toFixed(1)+'" y="'+(pt.top-1).toFixed(1)+'" font-size="3" text-anchor="middle" fill="#6b8199">'+pt.name+'</text>';});
 svg+='</svg>';
 document.getElementById('svg').innerHTML=svg;
 document.getElementById('metrics').innerHTML=R.metrics.map(m=>
  '<div class="kv"><span>'+m[0]+'</span><b'+(m.length>2?' class="'+(m[2]?'ok':'bad')+'"':'')+'>'+m[1]+'</b></div>').join('');
 if(R.match)window.__lengths=R.match;}

function build(){const c=document.getElementById('ctrls');c.innerHTML='';
 GARMENTS[current].keys.forEach(k=>{const [lab,mn,mx]=DEFS[k];
  const row=document.createElement('div');row.className='row';
  row.innerHTML='<label>'+lab+'</label><input type="range" min="'+mn+'" max="'+mx+'" step="0.5" value="'+P[k]+'"><b>'+P[k]+'</b>';
  const inp=row.querySelector('input'),val=row.querySelector('b');
  inp.addEventListener('input',()=>{P[k]=parseFloat(inp.value);val.textContent=P[k];draw();});
  c.appendChild(row);});}
const gsel=document.getElementById('garment');
for(const g in GARMENTS){const o=document.createElement('option');o.value=g;o.textContent=GARMENTS[g].label;gsel.appendChild(o);}
gsel.addEventListener('change',()=>{current=gsel.value;build();draw();});
document.getElementById('reset').addEventListener('click',()=>{GARMENTS[current].keys.forEach(k=>P[k]=DEFS[k][3]);build();draw();});
build();draw();
</script></body></html>"""


def build_live_viewer(outdir: str = "output") -> str:
    """Genera un visor **en vivo**: el motor (spline G2 + fórmulas Aldrich) corre en
    JavaScript, así que mover una medida recalcula el patrón al instante, sin
    servidor ni dependencias. Es una reimplementación de presentación del núcleo;
    la fuente de verdad sigue siendo el motor Python."""
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "viewer_live.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(_LIVE_PAGE)
    return path


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
    live = build_live_viewer(args.output)
    print(f"Visor en vivo:  {live} ({os.path.getsize(live)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
