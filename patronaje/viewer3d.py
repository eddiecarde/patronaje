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

// dome de cierre desde un anillo hacia un punto central (para tapar la malla)
function capFrom(ring,dy,steps){
 let a=0,d=0,y=ring[0][1];for(const p of ring){a=Math.max(a,Math.abs(p[0]));d=Math.max(d,Math.abs(p[2]));}
 const out=[];for(let i=1;i<=steps;i++){const t=i/steps,s=Math.cos(t*Math.PI/2);
  out.push(ringAD(y+dy*Math.sin(t*Math.PI/2),Math.max(a*s,1e-3),Math.max(d*s,1e-3)));}
 return out;}

function buildBody(L){  // maniquí de sastre (dress form): torso cerrado (cuello→cadera)
 const H=P.estatura, male=SEX==='M';
 const waistC=male?P.cintura+(P.busto-P.cintura)*0.28:P.cintura;
 const hipC=male?P.cadera*0.93:P.cadera;
 const bRat=male?1.32:1.24, wRat=male?1.30:1.35, hRat=male?1.30:1.42, shW=P.ancho_espalda*(male?0.52:0.45);
 // anillos del torso, de arriba (cuello) hacia abajo (cadera baja)
 const neck=ringC(L.neckY,P.contorno_cuello*(male?1.05:1.0),1.08);
 const T=[];
 T.push(ringAD((L.shY+L.neckY)/2,shW*0.56,P.busto*0.085)); // trapecio bajo el cuello
 T.push(ringAD(L.shY,shW,P.busto*(male?0.125:0.11)));       // línea de hombro
 T.push(ringC(L.chestY,P.busto*(male?0.95:0.90),bRat-0.05));
 T.push(ringC(L.bustY,P.busto,bRat));
 T.push(ringC((L.waistY+L.bustY)/2,(waistC+P.busto)/2,(wRat+bRat)/2));
 T.push(ringC(L.waistY,waistC,wRat));
 T.push(ringC((L.hipY+L.waistY)/2,(hipC+waistC)/2,(hRat+wRat)/2));
 T.push(ringC(L.hipY,hipC,hRat));
 const hipLow=ringC(L.hipY-4,hipC*0.965,hRat-0.02);
 // malla cerrada: tapa de cuello + trapecio + cuerpo + cadera + fondo redondeado
 const topCap=capFrom(neck,H*0.03,4).reverse();     // cúpula sobre el cuello (redondea hombros)
 const botCap=capFrom(hipLow,-H*0.07,5);            // fondo redondeado del maniquí
 const torso=topCap.concat([neck],T,[hipLow],botCap);
 // colisionadores de pierna (cápsula) para que el pantalón caiga sobre ellas en la sim
 const tR=P.cadera*(male?0.108:0.10), kR=tR*0.70, aR=tR*0.5, lx=P.cadera/10, legs=[];
 [1,-1].forEach(s=>{
  const hip=[s*lx,L.hipY-2,0], kn=[s*lx*0.95,L.kneeY,0.3], an=[s*lx*0.92,L.ankleY,0.3];
  legs.push({a:hip,b:kn,r0:tR,r1:kR},{a:kn,b:an,r0:kR,r1:aR});
 });
 return {torso,legs,levels:L};}

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
function buildCloth(grids,prof,legs,hipY){
 const pos=[],prev=[],pin=[],cons=[],faces=[],gridInfo=[];
 for(const rings of grids){
  const R=rings.length,base=pos.length,idx=(r,k)=>base+r*N+k;
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){pos.push(rings[r][k].slice());prev.push(rings[r][k].slice());pin.push(r===0?1:0);}
  const add=(a,b)=>{const dx=pos[a][0]-pos[b][0],dy=pos[a][1]-pos[b][1],dz=pos[a][2]-pos[b][2];
   cons.push([a,b,Math.hypot(dx,dy,dz)]);};
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   add(idx(r,k),idx(r,k2));                                   // anillo
   if(r<R-1){add(idx(r,k),idx(r+1,k));add(idx(r,k),idx(r+1,k2));}  // columna + cizalla
   if(r<R-2)add(idx(r,k),idx(r+2,k));}                        // flexión
  for(let r=0;r<R-1;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   faces.push([idx(r,k),idx(r,k2),idx(r+1,k2),idx(r+1,k)]);}
  gridInfo.push({base,R});}
 return {pos,prev,pin,cons,faces,prof,legs:legs||[],hipY:hipY||0};}

function stepCloth(cl,dt){
 const g=-160*dt*dt, damp=0.985;
 for(let i=0;i<cl.pos.length;i++){if(cl.pin[i])continue;const p=cl.pos[i],q=cl.prev[i];
  const vx=(p[0]-q[0])*damp,vy=(p[1]-q[1])*damp,vz=(p[2]-q[2])*damp;
  q[0]=p[0];q[1]=p[1];q[2]=p[2];p[0]+=vx;p[1]+=vy+g;p[2]+=vz;}
 for(let it=0;it<6;it++){
  for(const c of cl.cons){const a=cl.pos[c[0]],b=cl.pos[c[1]];
   let dx=b[0]-a[0],dy=b[1]-a[1],dz=b[2]-a[2],d=Math.hypot(dx,dy,dz)||1e-6;
   const diff=(d-c[2])/d*0.5,wa=cl.pin[c[0]]?0:1,wb=cl.pin[c[1]]?0:1,ws=wa+wb||1;
   dx*=diff;dy*=diff;dz*=diff;
   if(wa){a[0]+=dx*wa/ws;a[1]+=dy*wa/ws;a[2]+=dz*wa/ws;}
   if(wb){b[0]-=dx*wb/ws;b[1]-=dy*wb/ws;b[2]-=dz*wb/ws;}}
  for(let i=0;i<cl.pos.length;i++){if(cl.pin[i])continue;const p=cl.pos[i];
   if(p[1]>cl.hipY-2){let [a,d]=bodyAD(cl.prof,p[1]);a+=0.8;d+=0.8;
    const e=(p[0]*p[0])/(a*a)+(p[2]*p[2])/(d*d);
    if(e<1&&e>1e-6){const s=1/Math.sqrt(e);p[0]*=s;p[2]*=s;}}
   for(let j=0;j<cl.legs.length;j++)capsulePush(p,cl.legs[j]);}}
}

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
scene.add(new THREE.HemisphereLight(0xf3f6ff,0x2a3340,0.85));
const key=new THREE.DirectionalLight(0xffffff,2.4);
key.position.set(90,230,150);key.castShadow=true;
key.shadow.mapSize.set(2048,2048);key.shadow.bias=-0.0006;
const sc=key.shadow.camera;sc.left=-100;sc.right=100;sc.top=240;sc.bottom=-30;sc.near=1;sc.far=700;
scene.add(key);
const fill=new THREE.DirectionalLight(0xdfe8ff,0.6);fill.position.set(-110,90,60);scene.add(fill);
const rim=new THREE.DirectionalLight(0xffffff,0.9);rim.position.set(-40,150,-160);scene.add(rim);

// suelo de estudio (recibe sombra)
const floorMat=new THREE.MeshStandardMaterial({color:0x141c26,roughness:0.95,metalness:0.0});
const floor=new THREE.Mesh(new THREE.CircleGeometry(170,72),floorMat);
floor.rotation.x=-Math.PI/2;floor.position.y=0.0;floor.receiveShadow=true;scene.add(floor);

// materiales PBR
const MAT_BODY=new THREE.MeshStandardMaterial({color:0xe9dcc6,roughness:0.86,metalness:0.03});
const MAT_POST=new THREE.MeshStandardMaterial({color:0xc2c7cf,roughness:0.32,metalness:0.9});
const MAT_KNOB=new THREE.MeshStandardMaterial({color:0x1b1b22,roughness:0.35,metalness:0.15});
const MAT_BLACK=new THREE.MeshStandardMaterial({color:0x181820,roughness:0.5,metalness:0.35});
const MAT_WHEEL=new THREE.MeshStandardMaterial({color:0x0d0d12,roughness:0.6,metalness:0.2});
function garmentMat(alpha){return new THREE.MeshStandardMaterial({
 vertexColors:true,roughness:0.72,metalness:0.02,transparent:alpha<0.99,opacity:alpha,
 side:THREE.DoubleSide});}
const MAT_CLOTH=new THREE.MeshStandardMaterial({color:0x3f6fa0,roughness:0.85,metalness:0.02,side:THREE.DoubleSide});

// helpers: convertir listas de anillos en BufferGeometry indexada (normales suaves)
function ringGroupsGeom(groups){
 const pos=[],idx=[];let off=0,tris=0;
 for(const rings of groups){const R=rings.length;
  for(let r=0;r<R;r++)for(let k=0;k<N;k++){const p=rings[r][k];pos.push(p[0],p[1],p[2]);}
  for(let r=0;r<R-1;r++)for(let k=0;k<N;k++){const k2=(k+1)%N;
   const a=off+r*N+k,b=off+r*N+k2,c=off+(r+1)*N+k2,d=off+(r+1)*N+k;
   idx.push(a,b,c,a,c,d);tris+=2;}
  off+=R*N;}
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
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
 const L=bodyLevels(),body=buildBody(L),g=document.getElementById('garment').value;
 const H=P.estatura;
 clearRoot();
 let tris=0;
 // cuerpo: torso cerrado (dress form) — lino/lona
 const bodyGeom=ringGroupsGeom([body.torso]);
 addMesh(bodyGeom,MAT_BODY,true);tris+=bodyGeom.__tris;
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
 const prof=bodyProfileFrom(body.torso);
 const gm=buildGarment(L,g);
 let garMesh=null;
 if(showG&&!simMode){const gg=coloredGarmentGeom(gm.groups);
  garMesh=addMesh(gg,garmentMat(0.9),false);tris+=gg.__tris;}
 MESH={body:body,cy:0,prof,legs:body.legs,L,g,groups:gm.groups};
 // encuadre (una vez / al cambiar de sexo)
 const yTop=L.neckY+H*0.11,yBot=0;
 target.set(0,(yTop+yBot)/2,0);
 if(!camReady){radius=(yTop-yBot)*1.35;camReady=true;}
 document.getElementById('fit').innerHTML='<b>Holgura (ajuste)</b>'+gm.fit.map(f=>
  '<div class="kv"><span>'+f[0]+'</span><b style="color:rgb('+easeColor(f[1]).join(',')+')">'+f[1].toFixed(1)+' cm</b></div>').join('');
 CLOTH=null;
 if(simMode){startSim();}else{if(raf){cancelAnimationFrame(raf);raf=null;}window.__rendered=tris;draw();}}

function startSim(){
 const grids=garmentGrids(MESH.L,MESH.g,MESH.prof);
 CLOTH=buildCloth(grids,MESH.prof,MESH.legs,MESH.L.hipY);
 const cg=clothGeom(CLOTH);
 const clothMesh=new THREE.Mesh(cg,MAT_CLOTH);clothMesh.castShadow=true;
 clothMesh.name='__cloth';ROOT.add(clothMesh);
 if(raf)cancelAnimationFrame(raf);
 let n=0;const loop=()=>{for(let s=0;s<2;s++)stepCloth(CLOTH,0.12);
  const pa=cg.attributes.position.array;
  for(let i=0;i<CLOTH.pos.length;i++){pa[i*3]=CLOTH.pos[i][0];pa[i*3+1]=CLOTH.pos[i][1];pa[i*3+2]=CLOTH.pos[i][2];}
  cg.attributes.position.needsUpdate=true;cg.computeVertexNormals();
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
    html = _PAGE.replace("/*__THREE__*/", _three_js())
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
