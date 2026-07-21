"""Visor 3D del maniquí a medida (Opción B — WebGL/PBR con Three.js).

Genera un HTML **autocontenido y sin red** (la librería Three.js va *incrustada*,
no se descarga de ningún CDN) con un maniquí de sastre (dress form) paramétrico
renderizado con **WebGL**: materiales **PBR** (lino/lona para el cuerpo, metal
para el poste, negro satinado para el pomo y el pedestal), **iluminación de
estudio** (luz clave + relleno + contra) y **sombras suaves** proyectadas sobre
el suelo. La prenda se muestra como cáscara coloreada por el **mapa de ajuste**
(holgura por zona) o, activando *«Caída (sim)»*, como **malla de tela** que cae
por gravedad (solver PBD) y colisiona con el maniquí.

El cuerpo se construye por *loft* de anillos elípticos cuyo perímetro reproduce
cada medida (busto, cintura, cadera…) — el mismo motor paramétrico de antes —
pero ahora se convierte en mallas suaves de Three.js (normales promediadas) en
lugar de dibujarse con un renderizador por software. Hay maniquí de **Mujer** y
de **Hombre** con siluetas y medidas propias.

Uso:
    python -m patronaje.viewer3d --output output   # genera output/viewer_3d.html
"""
from __future__ import annotations

import argparse
import os

_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")


def _three_js() -> str:
    """Devuelve el código de Three.js vendorizado (para incrustar, sin red)."""
    with open(os.path.join(_ASSET_DIR, "three.min.js"), "r", encoding="utf-8") as f:
        return f.read()


_PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Patronaje — maniquí 3D a medida</title>
<style>
:root{--ink:#1f2d3d;--line:#c9d4e0;}
*{box-sizing:border-box}body{font-family:'Segoe UI',Arial,sans-serif;color:var(--ink);margin:0;background:#f4f7fb}
.wrap{max-width:1150px;margin:0 auto;padding:18px}h1{font-size:20px;margin:4px 0}
.sub{color:#6b8199;font-size:13px;margin-bottom:12px}
.stage{display:flex;gap:16px;flex-wrap:wrap}
.controls{flex:1 1 280px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}
.view{flex:2 1 600px;background:#0e141c;border:1px solid var(--line);border-radius:10px;padding:10px}
canvas{width:100%;height:auto;touch-action:none;cursor:grab;border-radius:6px;display:block}
.row{display:flex;align-items:center;gap:8px;margin:7px 0;font-size:13px}
.row label{flex:0 0 120px}.row input[type=range]{flex:1}.row b{flex:0 0 50px;text-align:right;font-variant-numeric:tabular-nums}
select{width:100%;font-size:14px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:#fff}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;margin-top:8px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:4px;vertical-align:middle}
.kv{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:4px 0;font-size:13px}
@media(prefers-color-scheme:dark){body{background:#0f1720;color:#dfe8f2}.controls{background:#16212e;border-color:#2a3a4d}}
</style></head><body><div class="wrap">
<h1>Patronaje — maniquí 3D a medida (WebGL)</h1>
<div class="sub">Maniquí de sastre paramétrico desde tus medidas, renderizado con
 <b>WebGL</b>: materiales PBR (lino/metal), iluminación de estudio y sombras. La prenda
 se ve como cáscara con <b>mapa de ajuste</b> o cae como tela (PBD). Arrastra para girar,
 rueda para acercar. Librería <b>incrustada</b>: funciona sin red ni descargas.</div>
<div class="stage">
 <div class="controls">
  <div class="row"><label>Cuerpo</label><select id="sexo"><option value="F">Mujer</option><option value="M">Hombre</option></select></div>
  <div class="row"><label>Prenda</label><select id="garment"></select></div>
  <div class="row"><label>Ver prenda</label>
   <span style="flex:1"><input type="checkbox" id="showg" checked> <span style="font-size:12px;color:#6b8199">muestra/oculta la prenda</span></span></div>
  <div class="row"><label>Caída (sim)</label>
   <span style="flex:1"><input type="checkbox" id="sim"> <span style="font-size:12px;color:#6b8199">simula la caída de la tela (PBD)</span></span>
   <button id="redrape" style="font-size:12px;padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer">Re-drapear</button></div>
  <div class="row"><label>Tejido</label>
   <select id="fabric" style="flex:1;font-size:13px;padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:#fff"></select></div>
  <div class="row"><label>Ver tensión</label>
   <span style="flex:1"><input type="checkbox" id="tension"> <span style="font-size:12px;color:#6b8199">mapa de estiramiento de la tela</span></span></div>
  <div id="tlegend" class="legend" style="display:none">
   <span><i style="background:#2f7fd0"></i>flojo</span>
   <span><i style="background:#3aa85a"></i>reposo</span>
   <span><i style="background:#d84a3a"></i>estirado</span></div>
  <div id="sliders"></div>
  <div class="legend">
   <span><i style="background:#c0392b"></i>tira (&lt;0)</span>
   <span><i style="background:#e67e22"></i>ajustado</span>
   <span><i style="background:#27ae60"></i>cómodo</span>
   <span><i style="background:#2980b9"></i>holgado</span></div>
  <div id="fit" style="margin-top:8px"></div>
 </div>
 <div class="view"><canvas id="cv" width="640" height="760"></canvas></div>
</div></div>
<script>/*__THREE__*/</script>
<script>/*__ENGINE__*/</script>
<script>
// ================= parámetros =================
const DEFS={
 busto:["Busto/Pecho",76,124,88],holgura_busto:["Holgura busto",-2,20,8],
 cintura:["Cintura",55,115,70],cadera:["Cadera",78,135,94],
 contorno_cuello:["Contorno cuello",32,46,37],ancho_espalda:["Ancho espalda",30,48,37],
 contorno_brazo:["Contorno brazo",22,44,30],muneca:["Muñeca",13,24,18],
 altura_cadera:["Altura cadera",16,26,20],talle:["Talle (nuca-cint.)",34,52,41],
 estatura:["Estatura",150,190,168],largo:["Largo prenda",30,130,68]};
const P={};for(const k in DEFS)P[k]=DEFS[k][3];
let SEX='F';
const PRESETS={
 F:{busto:88,cintura:70,cadera:94,contorno_cuello:37,ancho_espalda:37,contorno_brazo:30,muneca:18,altura_cadera:20,talle:41,estatura:168,largo:68},
 M:{busto:100,cintura:87,cadera:100,contorno_cuello:40,ancho_espalda:45,contorno_brazo:34,muneca:19,altura_cadera:22,talle:47,estatura:178,largo:74}};

// ================= geometría paramétrica =================
const N=64;                                     // segmentos por anillo (alta resolución = suave)
function ringC(y,C,ratio){ // anillo por circunferencia (Ramanujan) y ratio ancho/fondo
 const r=ratio,P1=Math.PI*(3*(r+1)-Math.sqrt((3*r+1)*(r+3))),d=C/P1,a=r*d;
 return ringAD(y,a,d);}
function ringAD(y,a,d){const p=[];for(let k=0;k<N;k++){const t=2*Math.PI*k/N;
 p.push([a*Math.cos(t),y,d*Math.sin(t)]);}return p;}

function easeColor(e){ // holgura cm -> color de ajuste
 if(e<0)return [192,57,43]; if(e<3)return [230,126,34]; if(e<11)return [39,174,96]; return [41,128,185];}

// niveles del cuerpo (y en cm, cadera arriba del suelo por la estatura)
function bodyLevels(){
 const H=P.estatura;
 const ankleY=H*0.045, kneeY=H*0.28, hipY=H*0.52, waistY=hipY+P.altura_cadera,
  bustY=waistY+P.talle*0.44, chestY=bustY+H*0.03, shY=bustY+P.talle*0.34,
  neckY=shY+H*0.02, headB=neckY+H*0.03, headT=headB+H*0.135;
 return {ankleY,kneeY,hipY,waistY,bustY,chestY,shY,neckY,headB,headT};}

function ellip(c,rx,ry,rz){const out=[];  // elipsoide (rings) para mano/pie/pomo
 for(let i=0;i<=8;i++){const ph=(-Math.PI/2)+Math.PI*i/8,rr=Math.cos(ph);
  const ring=[];for(let k=0;k<N;k++){const th=2*Math.PI*k/N;
   ring.push([c[0]+rx*rr*Math.cos(th),c[1]+ry*Math.sin(ph),c[2]+rz*rr*Math.sin(th)]);}out.push(ring);}
 return out;}

function tube(p0,p1,r0,r1,segs){ // cilindro entre dos puntos (para mangas/piernas/poste)
 const ax=[p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2]];const L=Math.hypot(ax[0],ax[1],ax[2])||1;
 const dir=[ax[0]/L,ax[1]/L,ax[2]/L];
 let up=[0,1,0]; if(Math.abs(dir[1])>0.9)up=[1,0,0];
 const u=norm(cross(up,dir)),v=norm(cross(dir,u));const rings=[];
 for(let s=0;s<=segs;s++){const t=s/segs,c=[p0[0]+ax[0]*t,p0[1]+ax[1]*t,p0[2]+ax[2]*t],r=r0+(r1-r0)*t,ring=[];
  for(let k=0;k<N;k++){const th=2*Math.PI*k/N,cx=Math.cos(th)*r,cz=Math.sin(th)*r;
   ring.push([c[0]+u[0]*cx+v[0]*cz,c[1]+u[1]*cx+v[1]*cz,c[2]+u[2]*cx+v[2]*cz]);}rings.push(ring);}
 return rings;}
function cross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
function norm(a){const l=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/l,a[1]/l,a[2]/l];}

// interpola 'steps' anillos entre rA y rB (exclusivos), con suavizado coseno
// (pendiente 0 en ambos extremos) para redondear crestas al loftear
function blendRings(rA,rB,steps){const out=[];
 for(let i=1;i<=steps;i++){const t=i/(steps+1),s=0.5-0.5*Math.cos(Math.PI*t),ring=[];
  for(let k=0;k<N;k++)ring.push([rA[k][0]+(rB[k][0]-rA[k][0])*s,
   rA[k][1]+(rB[k][1]-rA[k][1])*s,rA[k][2]+(rB[k][2]-rA[k][2])*s]);
  out.push(ring);}return out;}

// dome de cierre hacia el CENTROIDE del anillo (sirve para extremos fuera del eje:
// manos, pies). Encoge el anillo hacia su centro y lo desplaza en Y.
function capEnd(ring,dyv,steps){
 let cx=0,cz=0;const n=ring.length;for(const p of ring){cx+=p[0];cz+=p[2];}cx/=n;cz/=n;
 const out=[];for(let i=1;i<=steps;i++){const t=i/steps,s=Math.cos(t*Math.PI/2),yo=dyv*Math.sin(t*Math.PI/2);
  out.push(ring.map(p=>[cx+(p[0]-cx)*s,p[1]+yo,cz+(p[2]-cz)*s]));}
 return out;}

// dome de cierre desde un anillo hacia un punto central (para tapar la malla)
function capFrom(ring,dy,steps){
 let a=0,d=0,y=ring[0][1];for(const p of ring){a=Math.max(a,Math.abs(p[0]));d=Math.max(d,Math.abs(p[2]));}
 const out=[];for(let i=1;i<=steps;i++){const t=i/steps,s=Math.cos(t*Math.PI/2);
  out.push(ringAD(y+dy*Math.sin(t*Math.PI/2),Math.max(a*s,1e-3),Math.max(d*s,1e-3)));}
 return out;}

// perfil (a,d) del torso por circunferencia y ratio a esa altura
function adC(C,r){const P1=Math.PI*(3*(r+1)-Math.sqrt((3*r+1)*(r+3)));const d=C/P1;return {a:r*d,d};}

function buildBody(L,drape){  // maniquí de sastre como CAMPO IMPLÍCITO (torso + cápsulas fundidas)
 const male=SEX==='M';
 const waistC=male?P.cintura+(P.busto-P.cintura)*0.28:P.cintura;
 const hipC=male?P.cadera*0.93:P.cadera;
 const bRat=male?1.32:1.24, wRat=male?1.30:1.35, hRat=male?1.30:1.42, shW=P.ancho_espalda*(male?0.44:0.39);
 // ---- perfil del torso (a,d) por altura: cadera baja -> cuello ----
 const prof=[],pAD=(y,a,d)=>prof.push({y,a,d});let t;
 t=adC(hipC*0.93,hRat-0.03); pAD(L.hipY-6,t.a,t.d);        // pelvis baja
 t=adC(hipC,hRat);           pAD(L.hipY,t.a,t.d);
 t=adC((hipC+waistC)/2,(hRat+wRat)/2); pAD((L.hipY+L.waistY)/2,t.a,t.d);
 t=adC(waistC,wRat);         pAD(L.waistY,t.a,t.d);
 t=adC((waistC+P.busto)/2,(wRat+bRat)/2); pAD((L.waistY+L.bustY)/2,t.a,t.d);
 t=adC(P.busto,bRat);        pAD(L.bustY,t.a,t.d);
 t=adC(P.busto*(male?0.95:0.90),bRat-0.05); pAD(L.chestY,t.a,t.d);
 pAD(L.shY, shW*0.66, P.busto*(male?0.135:0.125));         // hombro: torso estrecho (el deltoides da la anchura)
 pAD((L.shY+L.neckY)/2, shW*0.46, P.busto*0.085);          // trapecio (cuello baja en pendiente al hombro)
 t=adC(P.contorno_cuello*(male?1.05:1.0),1.06); pAD(L.neckY,t.a,t.d); // cuello
 prof.sort((u,v)=>u.y-v.y);
 let maxA=0;for(const q of prof)maxA=Math.max(maxA,q.a);  // punto más ancho del torso (cadera)
 const yTop=L.neckY, yBot=L.hipY-6;
 // ---- primitivas (round cones) que se FUNDEN con el torso: brazos, piernas ----
 const aR=P.contorno_brazo/(2*Math.PI)*0.82, wR=P.muneca/(2*Math.PI)*0.86, eaR=aR*0.74;
 const armX=maxA+aR*0.35;                                 // brazos cuelgan por FUERA del punto más ancho
 const thR=P.cadera*(male?0.115:0.12), knR=thR*0.56, caR=thR*0.62, ankR=thR*0.34, cx=thR*(male?0.78:0.72);
 const limbs=[],legs=[],blobs=[],armCaps=[],armAxis=[],legAxis=[];
 [1,-1].forEach(s=>{
  const sh=[s*shW*0.94,L.shY-3.5,0.4], el=[s*armX,(L.shY+L.hipY)/2,2.0], wr=[s*armX,L.hipY-4,4.5];
  if(!drape){                                            // al drapear: horma SIN brazos (como en atelier)
   limbs.push({a:sh,b:el,r1:aR,r2:eaR,k:3.5});           // brazo alto (funde en el hombro)
   limbs.push({a:el,b:wr,r1:eaR,r2:wR,k:1.7});           // antebrazo
   blobs.push({c:[wr[0],wr[1]-wR*1.9,wr[2]+0.4],r:[wR*0.62,wR*2.3,wR*1.35],k:1.3}); // mano
   armAxis.push([sh,wr,s]);
   armCaps.push({a:el,b:wr,r0:eaR*1.05,r1:wR*1.05});
  }
  const hip=[s*cx,L.hipY+1,0], kn=[s*cx*0.96,L.kneeY,0.5],
        ca=[s*cx*0.95,(L.kneeY+L.ankleY)/2,0.8], an=[s*cx*0.93,L.ankleY,0.5];
  limbs.push({a:hip,b:kn,r1:thR,r2:knR,k:5.5});           // muslo (funde en la pelvis)
  limbs.push({a:kn,b:ca,r1:knR,r2:caR,k:2.2});            // pantorrilla
  limbs.push({a:ca,b:an,r1:caR,r2:ankR,k:1.6});           // tobillo
  legAxis.push([hip,an]);
  legs.push({a:hip,b:kn,r0:thR*0.9,r1:knR},{a:kn,b:an,r0:knR,r1:ankR}); // colisionadores sim
 });
 // ---- pecho/busto y glúteos: elipsoides que se funden con el torso ----
 const bAD=adC(P.busto,bRat), hAD=adC(hipC,hRat), colBlobs=[];
 [1,-1].forEach(s=>{
  // busto (mujer, marcado) / pectoral (hombre, plano y alto)
  const bust=male
   ?{c:[s*P.busto*0.075,L.chestY,bAD.d*0.6], r:[P.busto*0.095,P.busto*0.055,P.busto*0.05], k:5.5}
   :{c:[s*P.busto*0.052,L.bustY-1,bAD.d*0.62], r:[P.busto*0.075,P.busto*0.08,P.busto*0.062], k:3.5};
  // glúteos (atrás, en el asiento, bajo la línea de cadera)
  const glute=male
   ?{c:[s*P.cadera*0.055,L.hipY-4,-hAD.d*0.58], r:[P.cadera*0.075,P.cadera*0.075,P.cadera*0.055], k:5.5}
   :{c:[s*P.cadera*0.06,L.hipY-4,-hAD.d*0.55], r:[P.cadera*0.092,P.cadera*0.088,P.cadera*0.075], k:5.0};
  blobs.push(bust,glute);colBlobs.push(bust,glute);   // colBlobs: colisión de la tela
 });
 return {prof,yTop,yBot,limbs,legs,blobs,colBlobs,armCaps,armAxis,legAxis,shW,levels:L};}

// ---- SDF del cuerpo y poligonización por Surface Nets ----
function smin(a,b,k){const h=Math.max(0,Math.min(1,0.5+0.5*(b-a)/k));return b+h*(a-b)-k*h*(1-h);}
function sdRoundCone(p,a,b,r1,r2){ // cono con extremos esféricos (iq)
 const bax=b[0]-a[0],bay=b[1]-a[1],baz=b[2]-a[2];
 const l2=bax*bax+bay*bay+baz*baz,rr=r1-r2,a2=l2-rr*rr,il2=1/l2;
 const pax=p[0]-a[0],pay=p[1]-a[1],paz=p[2]-a[2];
 const y=pax*bax+pay*bay+paz*baz,z=y-l2;
 const wx=pax*l2-bax*y,wy=pay*l2-bay*y,wz=paz*l2-baz*y,x2=wx*wx+wy*wy+wz*wz;
 const y2=y*y*l2,z2=z*z*l2;
 const kk=(rr<0?-1:1)*rr*rr*x2;                     // sign(rr) sólo en k
 if((z<0?-1:1)*a2*z2>kk)return Math.sqrt(x2+z2)*il2-r2;  // sign(z)
 if((y<0?-1:1)*a2*y2<kk)return Math.sqrt(x2+y2)*il2-r1;  // sign(y)
 return (Math.sqrt(x2*a2*il2)+y*rr)*il2-r1;}
function sdEllipsoid(p,c,r){ // elipsoide (iq, aprox.) — para pecho/busto y glúteos
 const qx=(p[0]-c[0]),qy=(p[1]-c[1]),qz=(p[2]-c[2]);
 const k0=Math.hypot(qx/r[0],qy/r[1],qz/r[2]);
 const k1=Math.hypot(qx/(r[0]*r[0]),qy/(r[1]*r[1]),qz/(r[2]*r[2]));
 return k0*(k0-1.0)/(k1||1e-9);}
function torsoAD(prof,y){ // (a,d) interpolado del torso
 if(y<=prof[0].y)return prof[0];
 const n=prof.length;if(y>=prof[n-1].y)return prof[n-1];
 for(let i=0;i<n-1;i++)if(y>=prof[i].y&&y<=prof[i+1].y){
  const tt=(y-prof[i].y)/(prof[i+1].y-prof[i].y||1);
  return {a:prof[i].a+(prof[i+1].a-prof[i].a)*tt,d:prof[i].d+(prof[i+1].d-prof[i].d)*tt};}
 return prof[0];}
function sdTorso(p,B){ // cilindro generalizado de sección elíptica, con tapas redondeadas
 const yc=Math.max(B.yBot,Math.min(B.yTop,p[1])),ad=torsoAD(B.prof,yc),a=ad.a,d=ad.d;
 const ql=Math.hypot(p[0]/a,p[2]/d),radial=(ql-1)*Math.min(a,d);
 const dyv=(p[1]>B.yTop)?p[1]-B.yTop:(p[1]<B.yBot?B.yBot-p[1]:0);
 return dyv>0?Math.hypot(Math.max(radial,0),dyv):radial;}
function bodyField(p,B){let d=sdTorso(p,B);
 for(let i=0;i<B.limbs.length;i++){const s=B.limbs[i];d=smin(d,sdRoundCone(p,s.a,s.b,s.r1,s.r2),s.k);}
 if(B.blobs)for(let i=0;i<B.blobs.length;i++){const b=B.blobs[i];d=smin(d,sdEllipsoid(p,b.c,b.r),b.k);}
 return d;}
function fieldNormal(B,x,y,z){const e=0.35;
 const nx=bodyField([x+e,y,z],B)-bodyField([x-e,y,z],B),
       ny=bodyField([x,y+e,z],B)-bodyField([x,y-e,z],B),
       nz=bodyField([x,y,z+e],B)-bodyField([x,y,z-e],B),l=Math.hypot(nx,ny,nz)||1;
 return [nx/l,ny/l,nz/l];}
const _CORN=[[0,0,0],[1,0,0],[0,1,0],[1,1,0],[0,0,1],[1,0,1],[0,1,1],[1,1,1]];
const _EDG=[[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,6],[3,7],[4,5],[4,6],[5,7],[6,7]];
function bodyGeomImplicit(B){ // Surface Nets sobre el campo -> BufferGeometry suave
 let maxA=0,maxD=0;for(const q of B.prof){maxA=Math.max(maxA,q.a);maxD=Math.max(maxD,q.d);}
 const aR=P.contorno_brazo/(2*Math.PI);
 const xh=Math.max(maxA,B.shW*0.9+aR)+4, zh=Math.max(maxD,6)+5, cs=1.05;
 const x0=-xh,y0=B.levels.ankleY-2,z0=-zh;
 const nx=Math.ceil(2*xh/cs),ny=Math.ceil((B.yTop+2-y0)/cs),nz=Math.ceil(2*zh/cs);
 const NX=nx+1,NY=ny+1,NZ=nz+1,gi=(i,j,k)=>(i*NY+j)*NZ+k;
 const F=new Float32Array(NX*NY*NZ);
 for(let i=0;i<NX;i++)for(let j=0;j<NY;j++)for(let k=0;k<NZ;k++)
  F[gi(i,j,k)]=bodyField([x0+i*cs,y0+j*cs,z0+k*cs],B);
 const ci=(i,j,k)=>(i*ny+j)*nz+k,cellV=new Int32Array(nx*ny*nz).fill(-1);
 const pos=[],nor=[],uv=[],ao=[];
 for(let i=0;i<nx;i++)for(let j=0;j<ny;j++)for(let k=0;k<nz;k++){
  const v=[];let mask=0;
  for(let c=0;c<8;c++){const o=_CORN[c],val=F[gi(i+o[0],j+o[1],k+o[2])];v.push(val);if(val<0)mask|=1<<c;}
  if(mask===0||mask===255)continue;
  let sx=0,sy=0,sz=0,cnt=0;
  for(const e of _EDG){const c0=e[0],c1=e[1];if((v[c0]<0)!==(v[c1]<0)){
   const tt=v[c0]/(v[c0]-v[c1]),o0=_CORN[c0],o1=_CORN[c1];
   sx+=o0[0]+(o1[0]-o0[0])*tt;sy+=o0[1]+(o1[1]-o0[1])*tt;sz+=o0[2]+(o1[2]-o0[2])*tt;cnt++;}}
  const px=x0+(i+sx/cnt)*cs,py=y0+(j+sy/cnt)*cs,pz=z0+(k+sz/cnt)*cs;
  cellV[ci(i,j,k)]=pos.length/3;pos.push(px,py,pz);
  const nn=fieldNormal(B,px,py,pz);nor.push(nn[0],nn[1],nn[2]);
  // oclusión ambiental por el propio campo (iq): en cavidades (axila, cintura,
  // cuello, entrepierna) el campo sube más lento que el paso -> se oscurece.
  let occ=0,sca=1;
  for(let s=1;s<=5;s++){const h=s*1.5,
   dd=bodyField([px+nn[0]*h,py+nn[1]*h,pz+nn[2]*h],B);
   occ+=Math.max(0,h-dd)*sca;sca*=0.78;}
  ao.push(Math.max(0.35,Math.min(1,1-0.16*occ)));
  uv.push(Math.atan2(px,pz)/(2*Math.PI)+0.5,py*0.5);}  // costura UV atrás (oculta)
 const idx=[];
 // quad con winding coherente (flip): normal saliente consistente en toda la malla
 const quad=(a,b,c,d,flip)=>{if(a<0||b<0||c<0||d<0)return;
  if(flip)idx.push(a,c,b,a,d,c);else idx.push(a,b,c,a,c,d);};
 const S=(i,j,k)=>F[gi(i,j,k)]<0;
 for(let i=0;i<nx;i++)for(let j=1;j<ny;j++)for(let k=1;k<nz;k++)
  if(S(i,j,k)!==S(i+1,j,k))quad(cellV[ci(i,j,k)],cellV[ci(i,j-1,k)],cellV[ci(i,j-1,k-1)],cellV[ci(i,j,k-1)],S(i,j,k));
 for(let i=1;i<nx;i++)for(let j=0;j<ny;j++)for(let k=1;k<nz;k++)
  if(S(i,j,k)!==S(i,j+1,k))quad(cellV[ci(i,j,k)],cellV[ci(i,j,k-1)],cellV[ci(i-1,j,k-1)],cellV[ci(i-1,j,k)],S(i,j,k));
 for(let i=1;i<nx;i++)for(let j=1;j<ny;j++)for(let k=0;k<nz;k++)
  if(S(i,j,k)!==S(i,j,k+1))quad(cellV[ci(i,j,k)],cellV[ci(i-1,j,k)],cellV[ci(i-1,j-1,k)],cellV[ci(i,j-1,k)],S(i,j,k));
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
 g.setAttribute('normal',new THREE.Float32BufferAttribute(nor,3));
 g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
 g.setAttribute('ao',new THREE.Float32BufferAttribute(ao,1));
 g.setIndex(idx);g.__tris=idx.length/3;return g;}

// prenda: cáscara a offset del cuerpo, en grupos de anillos con holgura por anillo
function fillEase(rings,v){return rings.map(()=>v);}
function capEndGroup(g,dy){ // tapa el extremo abierto (último anillo) de una manga/pernera
 const last=g.rings[g.rings.length-1],caps=capFrom(last,dy,3),ev=g.ease[g.ease.length-1];
 for(const c of caps)g.ease.push(ev);
 g.rings=g.rings.concat(caps);return g;}
function buildGarment(L,g){
 const groups=[],fit=[];
 const eB=P.holgura_busto, eW=Math.max(0,eB*0.7), eH=4;
 if(g==="falda"){
  const hem=L.waistY-(P.largo);
  const rings=[ringC(L.waistY,P.cintura+2,1.34),ringC(L.hipY,P.cadera+4,1.42),ringC(hem,P.cadera+4+18,1.4)];
  groups.push({rings,ease:[2,4,4],alpha:0.68});
  fit.push(["Cintura",2],["Cadera",4]);
 }else if(g==="pantalon"){
  const rings=[ringC(L.waistY,P.cintura+2,1.34),ringC(L.hipY,P.cadera+5,1.42)];
  groups.push({rings,ease:[2,5],alpha:0.68});
  const legTop=L.hipY-2, ankle=L.ankleY+3, cx=P.cadera/9.5, tR=P.cadera*0.16+2.5;
  [1,-1].forEach(s=>{
   const t1=tube([s*cx,legTop,0],[s*cx*0.92,L.kneeY,0.3],tR,tR*0.62,6);
   const t2=tube([s*cx*0.92,L.kneeY,0.3],[s*cx*0.9,ankle,0.3],tR*0.62,tR*0.5,5);
   groups.push({rings:t1,ease:fillEase(t1,5),alpha:0.68});
   groups.push(capEndGroup({rings:t2,ease:fillEase(t2,5),alpha:0.68},-4));});
  fit.push(["Cintura",2],["Cadera",5]);
 }else{ // camisa / vestido / blazer — cáscara de torso sobre el dress form (sin mangas)
  const botY=(g==="vestido")?L.waistY-(P.largo-P.talle*0.44):L.hipY-2;
  const botC=(g==="vestido")?P.cadera+6+ ((P.largo>90)?14:2):P.cadera+eH;
  const rings=[ringC(L.chestY,P.busto*0.9+eB*0.6,1.22),ringC(L.bustY,P.busto+eB,1.26),
   ringC(L.waistY,P.cintura+eW,1.34),ringC(botY,botC,1.42)];
  groups.push({rings,ease:[eB*0.6,eB,eW,eH],alpha:0.62});
  fit.push(["Busto",eB],["Cintura",eW],["Cadera",eH]);
 }
 return {groups,fit};}

// ================= perfil del cuerpo (para colisión) =================
function perim(a,d){return Math.PI*(3*(a+d)-Math.sqrt((3*a+d)*(a+3*d)));}
function bodyProfileFrom(rings){
 return rings.map(r=>{let a=0,d=0;for(const p of r){a=Math.max(a,Math.abs(p[0]));d=Math.max(d,Math.abs(p[2]));}
  return {y:r[0][1],a,d};}).sort((u,v)=>u.y-v.y);}
function bodyAD(prof,y){
 if(y<=prof[0].y)return [prof[0].a,prof[0].d];
 if(y>=prof[prof.length-1].y)return [prof[prof.length-1].a,prof[prof.length-1].d];
 for(let i=0;i<prof.length-1;i++){if(y>=prof[i].y&&y<=prof[i+1].y){
  const t=(y-prof[i].y)/(prof[i+1].y-prof[i].y||1);
  return [prof[i].a+(prof[i+1].a-prof[i].a)*t,prof[i].d+(prof[i+1].d-prof[i].d)*t];}}
 return [prof[0].a,prof[0].d];}

// mallas de tela (rings x N) para simular; ring 0 se fija (cuelga de ahí)
function garmentGrids(L,g,prof){
 const grids=[]; const M=13;
 const shellRing=(y,ease,flare)=>{let a,d;
  if(y>=prof[0].y-40){[a,d]=bodyAD(prof,Math.max(y,prof[0].y));}else{[a,d]=[prof[0].a,prof[0].d];}
  const bc=perim(a,d),sc=(bc+ease)/bc,fl=1+(flare||0);return ringAD(y,a*sc*fl,d*sc*fl);};
 if(g==="falda"){
  const topY=L.waistY,hemY=L.waistY-P.largo,rings=[];
  for(let i=0;i<=M;i++){const t=i/M,y=topY+(hemY-topY)*t;
   const flare=Math.max(0,(y<L.hipY)?(L.hipY-y)/(L.hipY-hemY)*0.5:0);
   rings.push(shellRing(y,3,flare));}
  grids.push(rings);
 }else if(g==="pantalon"){
  const topY=L.hipY-2,ankle=L.ankleY+3,cx=P.cadera/9.5,tR=P.cadera*0.16+2.5;
  [1,-1].forEach(s=>{const rings=[];for(let i=0;i<=M;i++){const t=i/M,y=topY+(ankle-topY)*t,ring=[];
   const cxx=s*cx*(1-0.08*t),rr=tR*(1-0.42*t);for(let k=0;k<N;k++){const th=2*Math.PI*k/N;
    ring.push([cxx+Math.cos(th)*rr,y,Math.sin(th)*rr]);}rings.push(ring);}grids.push(rings);});
 }else{
  const topY=L.shY-1,hemY=(g==="vestido")?L.waistY-(P.largo-P.talle*0.44):L.hipY-2,rings=[];
  for(let i=0;i<=M;i++){const t=i/M,y=topY+(hemY-topY)*t;
   const flare=(g==="vestido"&&y<L.hipY)?(L.hipY-y)/(L.hipY-hemY)*0.35:0;
   rings.push(shellRing(y,(y>=L.bustY?P.holgura_busto:P.holgura_busto*0.8),flare));}
  grids.push(rings);
 }
 return grids;}

// ================= solver PBD =================
function capsulePush(p,seg){  // empuja la partícula fuera de una cápsula (segmento+radio)
 const a=seg.a,b=seg.b,abx=b[0]-a[0],aby=b[1]-a[1],abz=b[2]-a[2];
 const L2=abx*abx+aby*aby+abz*abz||1;
 let t=((p[0]-a[0])*abx+(p[1]-a[1])*aby+(p[2]-a[2])*abz)/L2;t=Math.max(0,Math.min(1,t));
 const cx=a[0]+abx*t,cy=a[1]+aby*t,cz=a[2]+abz*t;
 let dx=p[0]-cx,dy=p[1]-cy,dz=p[2]-cz,dl=Math.hypot(dx,dy,dz),r=(seg.r0+(seg.r1-seg.r0)*t)+0.8;
 if(dl<r&&dl>1e-6){const s=r/dl;p[0]=cx+dx*s;p[1]=cy+dy*s;p[2]=cz+dz*s;}}
function ellipsoidPush(p,c,r){  // empuja la partícula fuera de un elipsoide (busto/glúteo)
 const gap=1.0,qx=(p[0]-c[0])/(r[0]+gap),qy=(p[1]-c[1])/(r[1]+gap),qz=(p[2]-c[2])/(r[2]+gap);
 const e=qx*qx+qy*qy+qz*qz;
 if(e<1&&e>1e-6){const s=1/Math.sqrt(e);
  p[0]=c[0]+(p[0]-c[0])*s;p[1]=c[1]+(p[1]-c[1])*s;p[2]=c[2]+(p[2]-c[2])*s;}}
function buildCloth(grids,prof,legs,hipY,B){
 const pos=[],prev=[],pin=[],cons=[],faces=[],gridInfo=[];
 for(const rings of grids){
  const R=rings.length,base=pos.length,idx=(r,k)=>base+r*N+k;
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){pos.push(rings[r][k].slice());prev.push(rings[r][k].slice());pin.push(r===0?1:0);}
  const add=(a,b,t)=>{const dx=pos[a][0]-pos[b][0],dy=pos[a][1]-pos[b][1],dz=pos[a][2]-pos[b][2];
   cons.push([a,b,Math.hypot(dx,dy,dz),t||0]);};             // t=1 -> flexión (rigidez de tejido)
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   add(idx(r,k),idx(r,k2));                                   // anillo
   if(r<R-1){add(idx(r,k),idx(r+1,k));add(idx(r,k),idx(r+1,k2));}  // columna + cizalla
   if(r<R-2)add(idx(r,k),idx(r+2,k),1);}                      // flexión
  for(let r=0;r<R-1;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   faces.push([idx(r,k),idx(r,k2),idx(r+1,k2),idx(r+1,k)]);}
  gridInfo.push({base,R});}
 return {pos,prev,pin,cons,faces,prof,legs:legs||[],hipY:hipY||0,B:B||null};}

// biblioteca de tejidos: parámetros físicos (rigidez de flexión, amortiguación,
// peso) + acabado de superficie (rugosidad, brillo). Un "material digital" ligero
// y reutilizable, en la línea de un U3M sin archivos externos.
const FABRICS={
 algodon:{label:"Algodón",bendK:0.55,damp:0.985,gmul:1.0,rough:0.86,sheen:0.5},
 lino:   {label:"Lino",   bendK:0.72,damp:0.985,gmul:1.05,rough:0.92,sheen:0.32},
 lana:   {label:"Lana",   bendK:0.5, damp:0.980,gmul:1.15,rough:0.95,sheen:0.28},
 seda:   {label:"Seda",   bendK:0.28,damp:0.972,gmul:0.9, rough:0.42,sheen:1.1},
 denim:  {label:"Mezclilla",bendK:0.9,damp:0.990,gmul:1.2,rough:0.80,sheen:0.45},
 gasa:   {label:"Gasa",   bendK:0.16,damp:0.965,gmul:0.8, rough:0.55,sheen:0.95}};
let FAB=FABRICS.algodon, showTension=false;

// mapa de tensión: color por vértice según el estiramiento medio de sus aristas
// (azul = flojo, verde = reposo, rojo = estirado) — diagnóstico de ajuste.
function clothTension(cl){
 const n=cl.pos.length,ratio=new Float32Array(n),cnt=new Float32Array(n);
 for(const c of cl.cons){const a=cl.pos[c[0]],b=cl.pos[c[1]];
  const d=Math.hypot(b[0]-a[0],b[1]-a[1],b[2]-a[2]),r=d/(c[2]||1e-6);
  ratio[c[0]]+=r;cnt[c[0]]++;ratio[c[1]]+=r;cnt[c[1]]++;}
 let mean=0,m=0;
 for(let i=0;i<n;i++){if(cnt[i]){ratio[i]/=cnt[i];mean+=ratio[i];m++;}else ratio[i]=1;}
 mean=m?mean/m:1;                        // tensión RELATIVA a la media: resalta focos
 const col=new Float32Array(n*3);
 for(let i=0;i<n;i++){const t=Math.max(-1,Math.min(1,(ratio[i]-mean)*16));let r,g,bl;
  if(t>=0){r=0.16+0.74*t;g=0.66-0.42*t;bl=0.30*(1-t);}      // media -> estirado (rojo)
  else{const s=-t;r=0.16*(1-s);g=0.66-0.30*s;bl=0.30+0.55*s;} // media -> flojo (azul)
  col[i*3]=r;col[i*3+1]=g;col[i*3+2]=bl;}
 return col;}

function stepCloth(cl,dt){
 const g=-160*dt*dt*FAB.gmul, damp=FAB.damp;
 for(let i=0;i<cl.pos.length;i++){if(cl.pin[i])continue;const p=cl.pos[i],q=cl.prev[i];
  const vx=(p[0]-q[0])*damp,vy=(p[1]-q[1])*damp,vz=(p[2]-q[2])*damp;
  q[0]=p[0];q[1]=p[1];q[2]=p[2];p[0]+=vx;p[1]+=vy+g;p[2]+=vz;}
 for(let it=0;it<8;it++){
  for(const c of cl.cons){const a=cl.pos[c[0]],b=cl.pos[c[1]];
   let dx=b[0]-a[0],dy=b[1]-a[1],dz=b[2]-a[2],d=Math.hypot(dx,dy,dz)||1e-6;
   const st=c[3]?FAB.bendK:1.0;                              // flexión suave según tejido
   const diff=(d-c[2])/d*0.5*st,wa=cl.pin[c[0]]?0:1,wb=cl.pin[c[1]]?0:1,ws=wa+wb||1;
   dx*=diff;dy*=diff;dz*=diff;
   if(wa){a[0]+=dx*wa/ws;a[1]+=dy*wa/ws;a[2]+=dz*wa/ws;}
   if(wb){b[0]-=dx*wb/ws;b[1]-=dy*wb/ws;b[2]-=dz*wb/ws;}}
  if(!cl.B)for(let i=0;i<cl.pos.length;i++){if(cl.pin[i])continue;const p=cl.pos[i];
   if(p[1]>cl.hipY-2){let [a,d]=bodyAD(cl.prof,p[1]);a+=1.6;d+=1.6;   // colisión aproximada (falda/pantalón)
    const e=(p[0]*p[0])/(a*a)+(p[2]*p[2])/(d*d);
    if(e<1&&e>1e-6){const s=1/Math.sqrt(e);p[0]*=s;p[2]*=s;}}
   for(let j=0;j<cl.legs.length;j++)capsulePush(p,cl.legs[j]);
   if(cl.blobs)for(let j=0;j<cl.blobs.length;j++)ellipsoidPush(p,cl.blobs[j].c,cl.blobs[j].r);}}
 // prendas de torso: colisión EXACTA contra el campo del cuerpo (una vez por paso).
 // También se empujan los puntos FIJADOS del borde superior (escote/sisa) para que
 // se apoyen por delante del busto en vez de que éste asome.
 if(cl.B){const mg=1.4;for(let i=0;i<cl.pos.length;i++){const p=cl.pos[i];
  const f=bodyField(p,cl.B);if(f<mg){const n=fieldNormal(cl.B,p[0],p[1],p[2]),d=mg-f;
   p[0]+=n[0]*d;p[1]+=n[1]*d;p[2]+=n[2]*d;}}}
}

// ===== TRY-ON completo: prenda REAL cosida (tubo con escote/sisa/hombro del bloque)
// que se sujeta por los HOMBROS y CAE por gravedad (PBD), colisionando con el maniquí.
function topEdgeArr(L,g){                 // altura del borde superior por azimut k
 const gsh=L.shY-1.5, fnd=P.contorno_cuello/5+1.0, bnd=2.0, arm=L.shY-7.5;
 const cK=[0,8,16,24,32,40,48,56], cV=[arm,gsh,gsh-fnd,gsh,arm,gsh,gsh-bnd,gsh];
 const arr=new Array(N);
 for(let k=0;k<N;k++){let i=0;while(i<cK.length-1&&k>=cK[i+1])i++;
  const a=cK[i],b=(i+1<cK.length)?cK[i+1]:cK[0]+N,va=cV[i],vb=cV[(i+1)%cK.length];
  const t=(k-a)/(b-a),s=0.5-0.5*Math.cos(Math.PI*t);arr[k]=va+(vb-va)*s;}
 return arr;}
function clothFromRings(grids,prof,legs,hipY,pinTop,blobs,B){  // como buildCloth, pin selectivo en r=0
 const pos=[],prev=[],pin=[],cons=[],faces=[];
 for(const rings of grids){const R=rings.length,base=pos.length,idx=(r,k)=>base+r*N+k;
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){pos.push(rings[r][k].slice());prev.push(rings[r][k].slice());
   pin.push((r===0&&(!pinTop||pinTop[k]))?1:0);}
  const add=(a,b,t)=>{const dx=pos[a][0]-pos[b][0],dy=pos[a][1]-pos[b][1],dz=pos[a][2]-pos[b][2];
   cons.push([a,b,Math.hypot(dx,dy,dz),t||0]);};
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   add(idx(r,k),idx(r,k2));if(r<R-1){add(idx(r,k),idx(r+1,k));add(idx(r,k),idx(r+1,k2));}
   if(r<R-2)add(idx(r,k),idx(r+2,k),1);}
  for(let r=0;r<R-1;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   faces.push([idx(r,k),idx(r,k2),idx(r+1,k2),idx(r+1,k)]);}}
 return {pos,prev,pin,cons,faces,prof,legs:legs||[],hipY:hipY||0,blobs:blobs||[],B:B||null};}
function buildGarmentCloth(L,g,prof,legs,blobs,B){  // prenda de torso real (escote/sisa) cosida
 const top=topEdgeArr(L,g),M=15,eB=P.holgura_busto;
 const hemY=(g==='vestido')?L.waistY-(P.largo-P.talle*0.44):L.hipY-2;
 const rad=y=>{const yy=Math.max(prof[0].y,Math.min(prof[prof.length-1].y,y));
  let ad=bodyAD(prof,yy);const bc=perim(ad[0],ad[1]),ease=(y>=L.bustY?eB+4:eB*0.85+9),sc=(bc+ease)/bc;
  return [ad[0]*sc,ad[1]*sc];};
 const rings=[];
 for(let r=0;r<=M;r++){const t=r/M,ring=[];
  for(let k=0;k<N;k++){const th=2*Math.PI*k/N,yTop=top[k],y=yTop+(hemY-yTop)*t,ad=rad(y);
   ring.push([ad[0]*Math.cos(th),y,ad[1]*Math.sin(th)]);}
  rings.push(ring);}
 // sujeta TODO el borde superior (escote/sisa/hombro): la prenda cuelga de ahí y cae
 return clothFromRings([rings],prof,legs||[],L.hipY,null,blobs,B);}

// ================= escena Three.js =================
const cv=document.getElementById('cv');
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x0d131b);
const camera=new THREE.PerspectiveCamera(36,cv.width/cv.height,1,3000);
const renderer=new THREE.WebGLRenderer({canvas:cv,antialias:true});
renderer.setSize(cv.width,cv.height,false);
renderer.setPixelRatio(Math.min(2,window.devicePixelRatio||1));
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
renderer.outputColorSpace=THREE.SRGBColorSpace;

// iluminación de estudio: hemisférica + clave (con sombra) + relleno + contra
scene.add(new THREE.HemisphereLight(0xf3f6ff,0x2a3340,0.5));   // el resto de ambiente lo da la IBL
const key=new THREE.DirectionalLight(0xffffff,2.4);
key.position.set(90,230,150);key.castShadow=true;
key.shadow.mapSize.set(2048,2048);key.shadow.bias=-0.0009;key.shadow.normalBias=1.6;
const sc=key.shadow.camera;sc.left=-100;sc.right=100;sc.top=240;sc.bottom=-30;sc.near=1;sc.far=700;
scene.add(key);
const fill=new THREE.DirectionalLight(0xdfe8ff,0.6);fill.position.set(-110,90,60);scene.add(fill);
const rim=new THREE.DirectionalLight(0xffffff,0.9);rim.position.set(-40,150,-160);scene.add(rim);

// IBL (image-based lighting): entorno de estudio PROCEDURAL (sin HDRI externo),
// filtrado por PMREM -> irradiancia difusa realista + brillo especular suave en la
// lona y la tela. Es lo que da el aspecto "de foto" al maniquí, no un cambio de motor.
function makeEnv(){
 const w=512,h=256,c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');
 const g=x.createLinearGradient(0,0,0,h);            // cenit -> horizonte -> suelo
 g.addColorStop(0.0,'#eef2f7');g.addColorStop(0.42,'#c9d2de');g.addColorStop(0.5,'#aeb8c6');
 g.addColorStop(0.5,'#39414e');g.addColorStop(1.0,'#20262f');
 x.fillStyle=g;x.fillRect(0,0,w,h);
 const rg=x.createRadialGradient(w*0.66,h*0.26,4,w*0.66,h*0.26,h*0.46);   // ventana/luz clave
 rg.addColorStop(0,'rgba(255,255,255,0.92)');rg.addColorStop(1,'rgba(255,255,255,0)');
 x.fillStyle=rg;x.fillRect(0,0,w,h);return c;}
const _envTex=new THREE.CanvasTexture(makeEnv());_envTex.mapping=THREE.EquirectangularReflectionMapping;
const _pmrem=new THREE.PMREMGenerator(renderer);_pmrem.compileEquirectangularShader();
scene.environment=_pmrem.fromEquirectangular(_envTex).texture;
_envTex.dispose();_pmrem.dispose();

// suelo de estudio (recibe sombra)
const floorMat=new THREE.MeshStandardMaterial({color:0x141c26,roughness:0.95,metalness:0.0});
const floor=new THREE.Mesh(new THREE.CircleGeometry(170,72),floorMat);
floor.rotation.x=-Math.PI/2;floor.position.y=0.0;floor.receiveShadow=true;scene.add(floor);

// textura de lona/lino PROCEDURAL (tejido plano): sin imágenes externas, se dibuja
// en un <canvas> -> mapa de color + bump de trama, para el relieve bajo luz PBR.
function makeLinen(){
 const px=128,thread=4;                              // 32 hilos por baldosa (mosaico continuo)
 const bc=document.createElement('canvas');bc.width=bc.height=px;const bx=bc.getContext('2d');
 const cc=document.createElement('canvas');cc.width=cc.height=px;const cx=cc.getContext('2d');
 const bi=bx.createImageData(px,px),ci=cx.createImageData(px,px);
 for(let j=0;j<px;j++)for(let i=0;i<px;i++){
  const over=((Math.floor(i/thread)+Math.floor(j/thread))&1)===0; // trama por encima/por debajo
  const u=(i%thread)/thread,v=(j%thread)/thread;
  const crest=over?Math.sin(Math.PI*u):Math.sin(Math.PI*v);       // cresta del hilo (0..1)
  const noise=(Math.random()-0.5)*0.13;                            // fibras/slubs del lino
  const h=Math.max(0,Math.min(1,0.34+crest*0.6+noise));
  const o=(j*px+i)*4,g=Math.round(h*255);
  bi.data[o]=bi.data[o+1]=bi.data[o+2]=g;bi.data[o+3]=255;         // bump (altura)
  const sh=(0.8+h*0.22)*(over?1.0:0.95);                           // color beige con variación de hilo
  ci.data[o]=Math.round(233*sh);ci.data[o+1]=Math.round(220*sh);ci.data[o+2]=Math.round(198*sh);ci.data[o+3]=255;
 }
 bx.putImageData(bi,0,0);cx.putImageData(ci,0,0);return {bump:bc,color:cc};}
const _lin=makeLinen();
const LIN_BUMP=new THREE.CanvasTexture(_lin.bump);
LIN_BUMP.wrapS=LIN_BUMP.wrapT=THREE.RepeatWrapping;LIN_BUMP.repeat.set(7,1);
const LIN_COLOR=new THREE.CanvasTexture(_lin.color);
LIN_COLOR.wrapS=LIN_COLOR.wrapT=THREE.RepeatWrapping;LIN_COLOR.repeat.set(7,1);
LIN_COLOR.colorSpace=THREE.SRGBColorSpace;LIN_COLOR.anisotropy=4;

// materiales PBR
const MAT_BODY=new THREE.MeshStandardMaterial({color:0xe9dcc6,map:LIN_COLOR,
 roughness:0.9,metalness:0.02,side:THREE.DoubleSide,envMapIntensity:0.4});
// relieve de tejido por TRIPLANAR en el shader (sin depender de UVs): perturba la
// normal con el gradiente de la trama muestreada por posición mundial. Reutilizable
// en el cuerpo (lona) y en la prenda (tela).
function applyLinen(mat,sc,amt,useAo){
 mat.onBeforeCompile=sh=>{
  sh.uniforms.uLin={value:LIN_BUMP};sh.uniforms.uLinSc={value:sc};sh.uniforms.uLinAmt={value:amt};
  const vHead='varying vec3 vWP;\n'+(useAo?'attribute float ao;varying float vAo;\n':'');
  sh.vertexShader=vHead+sh.vertexShader.replace('#include <worldpos_vertex>',
   '#include <worldpos_vertex>\n vWP=(modelMatrix*vec4(transformed,1.0)).xyz;'+(useAo?'\n vAo=ao;':''));
  sh.fragmentShader='uniform sampler2D uLin;uniform float uLinSc;uniform float uLinAmt;varying vec3 vWP;\n'
   +(useAo?'varying float vAo;\n':'')
   +sh.fragmentShader.replace('#include <normal_fragment_maps>',
   ['#include <normal_fragment_maps>','{',
    ' vec3 an=abs(normal);an/=(an.x+an.y+an.z+1e-5);',
    ' float h =an.x*texture2D(uLin,vWP.zy*uLinSc).r+an.y*texture2D(uLin,vWP.xz*uLinSc).r+an.z*texture2D(uLin,vWP.xy*uLinSc).r;',
    ' vec2 dHdxy=vec2(dFdx(h),dFdy(h))*uLinAmt;',   // perturbNormalArb (bump por derivadas de pantalla)
    ' vec3 sp=-vViewPosition, sx=dFdx(sp), sy=dFdy(sp);',
    ' vec3 R1=cross(sy,normal), R2=cross(normal,sx); float fDet=dot(sx,R1);',
    ' vec3 vGrad=sign(fDet)*(dHdxy.x*R1+dHdxy.y*R2);',
    ' normal=normalize(abs(fDet)*normal - vGrad);',
    '}'].join('\n'));
  if(useAo)  // oclusión de contacto: oscurece el difuso e indirecto en cavidades
   sh.fragmentShader=sh.fragmentShader.replace('#include <color_fragment>',
    '#include <color_fragment>\n diffuseColor.rgb*=vAo;');};
 mat.needsUpdate=true;}
applyLinen(MAT_BODY,0.42,0.9,true);
const MAT_POST=new THREE.MeshStandardMaterial({color:0xc2c7cf,roughness:0.32,metalness:0.9});
const MAT_KNOB=new THREE.MeshStandardMaterial({color:0x1b1b22,roughness:0.35,metalness:0.15});
const MAT_BLACK=new THREE.MeshStandardMaterial({color:0x181820,roughness:0.5,metalness:0.35});
const MAT_WHEEL=new THREE.MeshStandardMaterial({color:0x0d0d12,roughness:0.6,metalness:0.2});
function garmentMat(alpha){return new THREE.MeshStandardMaterial({
 vertexColors:true,roughness:0.72,metalness:0.02,transparent:alpha<0.99,opacity:alpha,
 side:THREE.DoubleSide});}
const MAT_CLOTH=new THREE.MeshStandardMaterial({color:0x3f6fa0,roughness:0.86,metalness:0.02,side:THREE.DoubleSide,envMapIntensity:0.55});
applyLinen(MAT_CLOTH,0.9,0.5);                 // la prenda también con relieve de tela (más fino)
// material del mapa de tensión (color por vértice, sin relieve para leer bien el color)
const MAT_TENSION=new THREE.MeshStandardMaterial({vertexColors:true,roughness:0.8,metalness:0.02,side:THREE.DoubleSide});
// color de tela por prenda
const GCOL={camisa:0xdfe3ea,falda:0x7d5a86,pantalon:0x36435c,vestido:0xa8455a,blazer:0x3a4150};
const MAT_SEAM=new THREE.LineDashedMaterial({color:0x5b5140,transparent:true,opacity:0.72,dashSize:1.4,gapSize:0.9});

// helpers: convertir listas de anillos en BufferGeometry indexada (normales suaves)
function ringGroupsGeom(groups){
 const pos=[],uv=[],idx=[];let off=0,tris=0;
 for(const rings of groups){const R=rings.length;
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){const p=rings[r][k];pos.push(p[0],p[1],p[2]);
   uv.push(k/N, r*0.5);}                       // UV: k alrededor, anillo hacia abajo (para la lona)
  for(let r=0;r<R-1;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   const a=off+r*N+k,b=off+r*N+k2,c=off+(r+1)*N+k2,d=off+(r+1)*N+k;
   idx.push(a,b,c,a,c,d);tris+=2;}
  off+=R*N;}
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
 g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
 g.setIndex(idx);g.computeVertexNormals();g.__tris=tris;return g;}

function coloredGarmentGeom(groups){ // groups: [{rings,ease}]
 const pos=[],col=[],idx=[];let off=0,tris=0;
 for(const grp of groups){const rings=grp.rings,R=rings.length;
  for(let r=0;r<R;r++){const c=easeColor(grp.ease[r]);
   for(let k=0;k<N;k++){const p=rings[r][k];pos.push(p[0],p[1],p[2]);
    col.push((c[0]/255)**2.2,(c[1]/255)**2.2,(c[2]/255)**2.2);}}
  for(let r=0;r<R-1;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   const a=off+r*N+k,b=off+r*N+k2,c=off+(r+1)*N+k2,d=off+(r+1)*N+k;
   idx.push(a,b,c,a,c,d);tris+=2;}
  off+=R*N;}
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
 g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
 g.setIndex(idx);g.computeVertexNormals();g.__tris=tris;return g;}

function clothGeom(cl){
 const pos=new Float32Array(cl.pos.length*3),idx=[];
 for(let i=0;i<cl.pos.length;i++){pos[i*3]=cl.pos[i][0];pos[i*3+1]=cl.pos[i][1];pos[i*3+2]=cl.pos[i][2];}
 for(const q of cl.faces)idx.push(q[0],q[1],q[2],q[0],q[2],q[3]);
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.BufferAttribute(pos,3));
 g.setIndex(idx);g.computeVertexNormals();g.__tris=idx.length/3;return g;}

// costuras marcadas del maniquí (centro, princesa, costados, línea de busto/cintura,
// hombro, brazo, pierna) como líneas discontinuas, al estilo de una horma de atelier
function seamLines(B,L){
 const seg=[],push=(a,b)=>seg.push(a[0],a[1],a[2],b[0],b[1],b[2]);
 // marcha desde un punto interior 'o' en dirección 'd' hasta la superficie del campo
 const surfFrom=(o,d)=>{const dl=Math.hypot(d[0],d[1],d[2])||1,u=[d[0]/dl,d[1]/dl,d[2]/dl];
  let tt=0;for(let it=0;it<64;it++){const x=o[0]+u[0]*tt,y=o[1]+u[1]*tt,z=o[2]+u[2]*tt;
   const f=bodyField([x,y,z],B);if(f>-0.35)return [x+u[0]*0.3,y+u[1]*0.3,z+u[2]*0.3];
   tt+=Math.max(0.4,-f*0.9);}return [o[0]+u[0]*tt,o[1]+u[1]*tt,o[2]+u[2]*tt];};
 const surf=(y,dx,dz)=>surfFrom([0,y,0],[dx,0,dz]);
 const polyY=(dx,dz,yA,yB,n)=>{let prev=null;for(let i=0;i<=n;i++){const p=surf(yA+(yB-yA)*i/n,dx,dz);
  if(prev)push(prev,p);prev=p;}};
 // verticales del torso: centro delantero/trasero, costados, princesa delantera ±
 const yA=L.hipY-3,yB=L.shY-2,ang=0.62;
 polyY(0,1,yA,yB,18); polyY(0,-1,yA,yB,18); polyY(1,0,yA,yB,18); polyY(-1,0,yA,yB,18);
 polyY(Math.sin(ang),Math.cos(ang),yA,yB,18); polyY(-Math.sin(ang),Math.cos(ang),yA,yB,18);
 // horizontales: busto/pecho y cintura (marcha radial alrededor)
 [L.bustY,L.waistY].forEach(y=>{let prev=null;for(let k=0;k<=N;k++){const th=2*Math.PI*k/N;
  const p=surf(y,Math.cos(th),Math.sin(th));if(prev)push(prev,p);prev=p;}});
 // costura exterior de cada brazo y delantera de cada pierna (marcha desde el eje del miembro)
 B.armAxis.forEach(ax=>{const p0=ax[0],p1=ax[1],s=ax[2];let prev=null;
  for(let i=0;i<=12;i++){const tt=i/12,c=[p0[0]+(p1[0]-p0[0])*tt,p0[1]+(p1[1]-p0[1])*tt,p0[2]+(p1[2]-p0[2])*tt];
   const p=surfFrom(c,[s,0,0.25]);if(prev)push(prev,p);prev=p;}});
 B.legAxis.forEach(ax=>{const p0=ax[0],p1=ax[1];let prev=null;
  for(let i=0;i<=14;i++){const tt=i/14,c=[p0[0]+(p1[0]-p0[0])*tt,p0[1]+(p1[1]-p0[1])*tt,p0[2]+(p1[2]-p0[2])*tt];
   const p=surfFrom(c,[0,0,1]);if(prev)push(prev,p);prev=p;}});
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute(seg,3));
 const line=new THREE.LineSegments(g,MAT_SEAM);line.computeLineDistances();return line;}

// ================= estado / rebuild =================
const ROOT=new THREE.Group();scene.add(ROOT);
let MESH=null,CLOTH=null,simMode=false,showG=true,raf=null;
let theta=0.62,phi=1.28,radius=380,target=new THREE.Vector3(0,90,0),camReady=false;

function clearRoot(){
 for(const c of ROOT.children.slice()){ROOT.remove(c);if(c.geometry)c.geometry.dispose();}}

function addMesh(geom,mat,shadow){
 const m=new THREE.Mesh(geom,mat);m.castShadow=!!shadow;m.receiveShadow=false;ROOT.add(m);return m;}

function updateCamera(){
 const rp=Math.sin(phi);
 camera.position.set(target.x+radius*rp*Math.sin(theta),target.y+radius*Math.cos(phi),
  target.z+radius*rp*Math.cos(theta));
 camera.lookAt(target);}

function rebuild(){
 const g=document.getElementById('garment').value;
 const torsoG=(g==='camisa'||g==='vestido'||g==='blazer');   // solo el torso se drapea sin brazos
 const L=bodyLevels(),body=buildBody(L,simMode&&torsoG);
 const H=P.estatura;
 clearRoot();
 let tris=0;
 // cuerpo: superficie implícita (torso + brazos + piernas FUNDIDOS) — lino/lona
 const bodyGeom=bodyGeomImplicit(body);
 addMesh(bodyGeom,MAT_BODY,true);tris+=bodyGeom.__tris;
 // costuras marcadas (centro, princesa, costados, busto/cintura, hombro, brazo, pierna)
 ROOT.add(seamLines(body,L));
 // pomo negro sobre poste metálico (remate del dress form)
 const postGeom=ringGroupsGeom([tube([0,L.neckY-1,0],[0,L.neckY+H*0.045,0],P.contorno_cuello/10,P.contorno_cuello/13,3)]);
 addMesh(postGeom,MAT_POST,true);tris+=postGeom.__tris;
 const knobGeom=ringGroupsGeom([ellip([0,L.neckY+H*0.075,0],H*0.019,H*0.032,H*0.019)]);
 addMesh(knobGeom,MAT_KNOB,true);tris+=knobGeom.__tris;
 // pedestal: poste central + base de 5 patas con ruedas
 const pedGeom=ringGroupsGeom([tube([0,2,0],[0,L.hipY-4,0],2.3,2.3,3)]);
 addMesh(pedGeom,MAT_BLACK,true);tris+=pedGeom.__tris;
 const arms=[],wheels=[];
 for(let i=0;i<5;i++){const a=2*Math.PI*i/5+0.35,R=H*0.12;
  arms.push(tube([0,2.5,0],[Math.cos(a)*R,1.0,Math.sin(a)*R],1.7,1.0,2));
  wheels.push(ellip([Math.cos(a)*R,1.2,Math.sin(a)*R],1.5,1.3,1.5));}
 const armGeom=ringGroupsGeom(arms);addMesh(armGeom,MAT_BLACK,true);tris+=armGeom.__tris;
 const whGeom=ringGroupsGeom(wheels);addMesh(whGeom,MAT_WHEEL,true);tris+=whGeom.__tris;
 // prenda
 const prof=body.prof;
 const gm=buildGarment(L,g);
 let garMesh=null;
 if(showG&&!simMode){const gg=coloredGarmentGeom(gm.groups);
  garMesh=addMesh(gg,garmentMat(0.9),false);tris+=gg.__tris;}
 MESH={body:body,cy:0,prof,legs:body.legs,colBlobs:body.colBlobs,armCaps:body.armCaps,L,g,groups:gm.groups};
 // encuadre (una vez / al cambiar de sexo)
 const yTop=L.neckY+H*0.11,yBot=0;
 target.set(0,(yTop+yBot)/2,0);
 if(!camReady){radius=(yTop-yBot)*1.35;camReady=true;}
 document.getElementById('fit').innerHTML='<b>Holgura (ajuste)</b>'+gm.fit.map(f=>
  '<div class="kv"><span>'+f[0]+'</span><b style="color:rgb('+easeColor(f[1]).join(',')+')">'+f[1].toFixed(1)+' cm</b></div>').join('');
 CLOTH=null;
 if(simMode){startSim();}else{if(raf){cancelAnimationFrame(raf);raf=null;}window.__rendered=tris;draw();}}

function startSim(){
 MAT_CLOTH.color.setHex(GCOL[MESH.g]||0x3f6fa0);
 MAT_CLOTH.roughness=FAB.rough;MAT_CLOTH.envMapIntensity=FAB.sheen;MAT_CLOTH.needsUpdate=true;
 const torso=(MESH.g==='camisa'||MESH.g==='vestido'||MESH.g==='blazer');
 CLOTH=torso?buildGarmentCloth(MESH.L,MESH.g,MESH.prof,MESH.legs.concat(MESH.armCaps||[]),MESH.colBlobs,MESH.body)
            :buildCloth(garmentGrids(MESH.L,MESH.g,MESH.prof),MESH.prof,MESH.legs,MESH.L.hipY,MESH.body);
 const cg=clothGeom(CLOTH);
 if(showTension)cg.setAttribute('color',new THREE.BufferAttribute(clothTension(CLOTH),3));
 const clothMesh=new THREE.Mesh(cg,showTension?MAT_TENSION:MAT_CLOTH);clothMesh.castShadow=true;
 clothMesh.name='__cloth';ROOT.add(clothMesh);
 if(raf)cancelAnimationFrame(raf);
 let n=0;const loop=()=>{for(let s=0;s<2;s++)stepCloth(CLOTH,0.12);
  const pa=cg.attributes.position.array;
  for(let i=0;i<CLOTH.pos.length;i++){pa[i*3]=CLOTH.pos[i][0];pa[i*3+1]=CLOTH.pos[i][1];pa[i*3+2]=CLOTH.pos[i][2];}
  cg.attributes.position.needsUpdate=true;
  if(showTension){const cc=clothTension(CLOTH),ca=cg.attributes.color.array;ca.set(cc);cg.attributes.color.needsUpdate=true;}
  cg.computeVertexNormals();
  window.__rendered=cg.__tris+200;n++;draw();
  if(n<220&&simMode)raf=requestAnimationFrame(loop);};loop();}

function draw(){updateCamera();renderer.render(scene,camera);}

// ================= UI =================
function buildSliders(){const c=document.getElementById('sliders');c.innerHTML='';
 for(const k in DEFS){const[lab,mn,mx]=DEFS[k];const row=document.createElement('div');row.className='row';
  row.innerHTML='<label>'+lab+'</label><input type="range" min="'+mn+'" max="'+mx+'" step="0.5" value="'+P[k]+'"><b>'+P[k]+'</b>';
  const inp=row.querySelector('input'),val=row.querySelector('b');
  inp.oninput=()=>{P[k]=parseFloat(inp.value);val.textContent=P[k];rebuild();};c.appendChild(row);}}
const gsel=document.getElementById('garment');
[["camisa","Camisa"],["falda","Falda"],["pantalon","Pantalón"],["vestido","Vestido"],["blazer","Blazer"]]
 .forEach(([v,l])=>{const o=document.createElement('option');o.value=v;o.textContent=l;gsel.appendChild(o);});
gsel.onchange=rebuild;
document.getElementById('sexo').onchange=e=>{SEX=e.target.value;
 for(const k in PRESETS[SEX])P[k]=PRESETS[SEX][k];camReady=false;buildSliders();rebuild();};
document.getElementById('showg').onchange=e=>{showG=e.target.checked;rebuild();};
document.getElementById('sim').onchange=e=>{simMode=e.target.checked;rebuild();};
document.getElementById('redrape').onclick=()=>{if(simMode)startSim();};
const fabsel=document.getElementById('fabric');
for(const k in FABRICS){const o=document.createElement('option');o.value=k;o.textContent=FABRICS[k].label;fabsel.appendChild(o);}
fabsel.onchange=e=>{FAB=FABRICS[e.target.value];if(simMode)startSim();};
document.getElementById('tension').onchange=e=>{showTension=e.target.checked;
 document.getElementById('tlegend').style.display=showTension?'flex':'none';if(simMode)startSim();};
cv.onpointerdown=e=>{cv.__drag=[e.clientX,e.clientY];cv.setPointerCapture(e.pointerId);cv.style.cursor='grabbing';};
cv.onpointermove=e=>{if(!cv.__drag)return;theta-=(e.clientX-cv.__drag[0])*0.01;phi-=(e.clientY-cv.__drag[1])*0.01;
 phi=Math.max(0.25,Math.min(2.7,phi));cv.__drag=[e.clientX,e.clientY];draw();};
cv.onpointerup=()=>{cv.__drag=null;cv.style.cursor='grab';};
cv.onwheel=e=>{e.preventDefault();radius*=(1+Math.sign(e.deltaY)*0.08);
 radius=Math.max(120,Math.min(900,radius));draw();};
buildSliders();rebuild();
</script></body></html>"""


def build_body_viewer(outdir: str = "output") -> str:
    """Genera el visor 3D del maniquí a medida (HTML autocontenido, Three.js incrustado)."""
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "viewer_3d.html")
    from .webshell import inject_shell
    from .viewer import engine_js
    html = _PAGE.replace("/*__THREE__*/", _three_js()).replace("/*__ENGINE__*/", engine_js())
    html = inject_shell(html)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Genera el visor 3D del maniquí a medida")
    ap.add_argument("--output", default="output")
    args = ap.parse_args(argv)
    path = build_body_viewer(args.output)
    print(f"Visor 3D generado: {path} ({os.path.getsize(path)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
