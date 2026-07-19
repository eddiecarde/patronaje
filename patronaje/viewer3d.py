"""Visor 3D del maniquí a medida (Opción A).

Genera un HTML **autocontenido** con un maniquí paramétrico (dress form)
construido desde las medidas, y la prenda como **cáscara** a offset del cuerpo,
coloreada por un **mapa de ajuste** (holgura por zona: verde cómodo, ámbar
ajustado, rojo tira, azul holgado). Se rota con el ratón y se recalcula al mover
las medidas — sin dependencias: un pequeño renderizador 3D por software
(proyección + painter's algorithm) dibuja sobre un Canvas.

No es simulación de caída (Fase 2): la prenda es una superficie ajustada al
cuerpo con su silueta y holgura reales, suficiente para "verla puesta" y evaluar
la horma.

Uso:
    python -m patronaje.viewer3d --output output   # genera output/viewer_3d.html
"""
from __future__ import annotations

import argparse
import os

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
.view{flex:2 1 600px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px}
canvas{width:100%;height:auto;touch-action:none;cursor:grab;background:linear-gradient(#eef4fb,#dfe8f2)}
.row{display:flex;align-items:center;gap:8px;margin:7px 0;font-size:13px}
.row label{flex:0 0 120px}.row input[type=range]{flex:1}.row b{flex:0 0 50px;text-align:right;font-variant-numeric:tabular-nums}
select{width:100%;font-size:14px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:#fff}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;margin-top:8px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:4px;vertical-align:middle}
.kv{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:4px 0;font-size:13px}
@media(prefers-color-scheme:dark){body{background:#0f1720;color:#dfe8f2}.controls,.view{background:#16212e;border-color:#2a3a4d}}
</style></head><body><div class="wrap">
<h1>Patronaje — maniquí 3D a medida</h1>
<div class="sub">Maniquí paramétrico desde tus medidas + la prenda como cáscara con
 <b>mapa de ajuste</b> (holgura por zona). Arrastra para girar. Sin dependencias:
 renderizador 3D por software. No es simulación de caída (eso es la Fase 2).</div>
<div class="stage">
 <div class="controls">
  <div class="row"><label>Prenda</label><select id="garment"></select></div>
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
 <div class="view"><canvas id="cv" width="620" height="720"></canvas></div>
</div></div>
<script>
// ================= parámetros =================
const DEFS={
 busto:["Busto",76,120,88],holgura_busto:["Holgura busto",-2,20,8],
 cintura:["Cintura",55,115,70],cadera:["Cadera",78,135,94],
 contorno_cuello:["Contorno cuello",32,46,37],ancho_espalda:["Ancho espalda",30,48,37],
 altura_cadera:["Altura cadera",16,26,20],talle:["Talle (nuca-cint.)",34,52,41],
 estatura:["Estatura",150,190,168],largo:["Largo prenda",30,130,68]};
const P={};for(const k in DEFS)P[k]=DEFS[k][3];

// ================= geometría paramétrica =================
const N=36;
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

function ellip(c,rx,ry,rz){const out=[];  // elipsoide (rings) para mano/pie
 for(let i=0;i<=6;i++){const ph=(-Math.PI/2)+Math.PI*i/6,rr=Math.cos(ph);
  const ring=[];for(let k=0;k<N;k++){const th=2*Math.PI*k/N;
   ring.push([c[0]+rx*rr*Math.cos(th),c[1]+ry*Math.sin(ph),c[2]+rz*rr*Math.sin(th)]);}out.push(ring);}
 return out;}

function buildBody(L){  // figura humana: torso + brazos + piernas
 const H=P.estatura;
 const T=[];
 T.push(ringC(L.hipY-7,P.cadera*0.94,1.38));            // unión a las piernas
 T.push(ringC(L.hipY,P.cadera,1.40));
 T.push(ringC((L.hipY+L.waistY)/2,(P.cadera+P.cintura)/2,1.37));
 T.push(ringC(L.waistY,P.cintura,1.34));
 T.push(ringC((L.waistY+L.bustY)/2,(P.cintura+P.busto)/2,1.30));
 T.push(ringC(L.bustY,P.busto,1.26));
 T.push(ringC(L.chestY,P.busto*0.88,1.20));
 T.push(ringAD(L.shY,P.ancho_espalda*0.52,P.busto*0.115));   // hombros
 T.push(ringC(L.neckY,P.contorno_cuello*1.02,1.10));
 const limbs=[];
 // brazos (cuelgan a los lados, ligera separación)
 const shX=P.ancho_espalda*0.50, armLen=H*0.44,
  uR=P.contorno_brazo/6.0, fR=P.muneca/5.0, wR=P.muneca/7.5;
 [1,-1].forEach(s=>{
  const sh=[s*shX,L.shY-3,0.4], el=[s*(shX+1.5),L.shY-armLen*0.46,1.6], wr=[s*(shX+2.6),L.shY-armLen,2.6];
  limbs.push(tube(sh,el,uR,fR,4));
  limbs.push(tube(el,wr,fR,wR,4));
  limbs.push(ellip(wr,wR*1.3,wR*1.7,wR*1.1));            // mano
 });
 // piernas
 const tR=P.cadera*0.16, kR=tR*0.55, aR=tR*0.36, lx=P.cadera/9.5;
 [1,-1].forEach(s=>{
  const hip=[s*lx,L.hipY-6,0], kn=[s*lx*0.92,L.kneeY,0.3], an=[s*lx*0.9,L.ankleY,0.3];
  limbs.push(tube(hip,kn,tR,kR,5));
  limbs.push(tube(kn,an,kR,aR,4));
  limbs.push(ellip([s*lx*0.9,L.ankleY-1,aR*1.4],aR*1.0,aR*0.85,aR*2.4)); // pie
 });
 return {torso:T,limbs,levels:L};}

function headRings(L){ // cabeza elipsoide
 const cy=(L.headB+L.headT)/2, ry=(L.headT-L.headB)/2, rx=ry*0.70, rz=ry*0.80, out=[];
 for(let i=0;i<=8;i++){const ph=(-Math.PI/2)+Math.PI*i/8, y=cy+ry*Math.sin(ph), rr=Math.cos(ph);
  out.push(ringAD(y,rx*rr,rz*rr));}
 return out;}

function tube(p0,p1,r0,r1,segs){ // cilindro entre dos puntos (para mangas/piernas)
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

// prenda: cáscara a offset del cuerpo, coloreada por holgura
function buildGarment(L,g){
 const faces=[],fit=[];const push=(rings,cf,alpha)=>ringsToFaces(rings,cf,alpha,faces);
 const eB=P.holgura_busto, eW=Math.max(0,eB*0.7), eH=4, hemY=L.waistY-(P.largo-P.talle*0.44);
 function shellRings(topY,botY,botC,botR){
  return [ringC(L.shY-1,P.contorno_cuello+6,1.15),
   ringC(L.bustY,P.busto+eB,1.26),ringC(L.waistY,P.cintura+eW,1.34),
   ringC(Math.min(botY,L.hipY),P.cadera+eH,1.42),ringC(botY,botC,botR)];}
 if(g==="falda"){
  const hem=L.waistY-(P.largo);
  const rings=[ringC(L.waistY,P.cintura+2,1.34),ringC(L.hipY,P.cadera+4,1.42),ringC(hem,P.cadera+4+18,1.4)];
  push(rings,(i)=>easeColor([2,4,4][i]||4),0.62);
  fit.push(["Cintura",2],["Cadera",4]);
 }else if(g==="pantalon"){
  const rings=[ringC(L.waistY,P.cintura+2,1.34),ringC(L.hipY,P.cadera+5,1.42)];
  push(rings,(i)=>easeColor([2,5][i]||5),0.62);
  // dos perneras (siguen las piernas del maniquí, con holgura)
  const legTop=L.hipY-2, ankle=L.ankleY+3, cx=P.cadera/9.5, tR=P.cadera*0.16+2.5;
  [1,-1].forEach(s=>{
   const t1=tube([s*cx,legTop,0],[s*cx*0.92,L.kneeY,0.3],tR,tR*0.62,5);
   const t2=tube([s*cx*0.92,L.kneeY,0.3],[s*cx*0.9,ankle,0.3],tR*0.62,tR*0.5,4);
   ringsToFaces(t1,()=>easeColor(5),0.62,faces);ringsToFaces(t2,()=>easeColor(5),0.62,faces);});
  fit.push(["Cintura",2],["Cadera",5]);
 }else{ // camisa / vestido / blazer (torso + mangas)
  const botY=(g==="vestido")?L.waistY-(P.largo-P.talle*0.44):L.hipY-2;
  const botC=(g==="vestido")?P.cadera+6+ ((P.largo>90)?14:2):P.cadera+eH;
  const rings=[ringC(L.shY-1,P.contorno_cuello+8,1.15),ringC(L.bustY,P.busto+eB,1.26),
   ringC(L.waistY,P.cintura+eW,1.34),ringC(botY,botC,1.42)];
  const cols=[eB*0.6,eB,eW,eH];
  push(rings,(i)=>easeColor(cols[i]),0.6);
  // mangas (cuelgan sobre los brazos)
  const sh=P.ancho_espalda*0.50, sy=L.shY-2, armLen=P.estatura*0.44;
  const slLen=(g==="blazer")?armLen*0.62:(g==="vestido"?armLen*0.42:armLen*0.55);
  [1,-1].forEach(s=>{const t=tube([s*sh,sy,0.3],[s*(sh+1.5),sy-slLen,1.6],P.contorno_brazo/5.2,P.contorno_brazo/6.0,6);
   ringsToFaces(t,()=>easeColor(eB*0.8),0.72,faces);});
  fit.push(["Busto",eB],["Cintura",eW],["Cadera",eH]);
 }
 return {faces,fit};}

function ringsToFaces(rings,colorFn,alpha,out){
 for(let r=0;r<rings.length-1;r++){const A=rings[r],B=rings[r+1],col=colorFn(r);
  for(let k=0;k<N;k++){const k2=(k+1)%N;
   out.push({v:[A[k],A[k2],B[k2],B[k]],col,alpha});}}}

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
function easeAtY(L,y){const pts=[[L.bustY,P.holgura_busto],[L.waistY,Math.max(1,P.holgura_busto*0.7)],[L.hipY,4]];
 if(y>=pts[0][0])return pts[0][1]; if(y<=pts[2][0])return pts[2][1];
 for(let i=0;i<2;i++){if(y<=pts[i][0]&&y>=pts[i+1][0]){const t=(pts[i][0]-y)/(pts[i][0]-pts[i+1][0]);
  return pts[i][1]+(pts[i+1][1]-pts[i][1])*t;}}return 4;}

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
function buildCloth(grids,prof){
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
 return {pos,prev,pin,cons,faces,prof};}

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
  // colisión con el maniquí (elipse por altura + margen)
  for(let i=0;i<cl.pos.length;i++){if(cl.pin[i])continue;const p=cl.pos[i];
   let [a,d]=bodyAD(cl.prof,p[1]);a+=0.8;d+=0.8;
   const e=(p[0]*p[0])/(a*a)+(p[2]*p[2])/(d*d);
   if(e<1&&e>1e-6){const s=1/Math.sqrt(e);p[0]*=s;p[2]*=s;}}}
}
function clothFaces(cl,col){const out=[];
 for(const q of cl.faces)out.push({v:[cl.pos[q[0]],cl.pos[q[1]],cl.pos[q[2]],cl.pos[q[3]]],col,alpha:0.9});
 return out;}

// ================= render =================
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
let yaw=0.5,pitch=0.05,drag=null,MESH=null,CLOTH=null,simMode=false,raf=null;

function rebuild(){
 const L=bodyLevels(),body=buildBody(L),head=headRings(L),g=document.getElementById('garment').value;
 const SKIN=[228,199,178];
 const bfaces=[];
 ringsToFaces(body.torso,()=>SKIN,1.0,bfaces);
 for(const limb of body.limbs)ringsToFaces(limb,()=>SKIN,1.0,bfaces);
 ringsToFaces(tube([0,L.neckY,0],[0,L.headB+1,0],P.contorno_cuello/6.8,P.contorno_cuello/7.5,2),()=>SKIN,1.0,bfaces);
 ringsToFaces(head,()=>SKIN,1.0,bfaces);
 const prof=bodyProfileFrom(body.torso);
 const gm=buildGarment(L,g);
 const all=bfaces.concat(gm.faces);
 let yMin=1e9,yMax=-1e9;for(const fa of all)for(const v of fa.v){if(v[1]<yMin)yMin=v[1];if(v[1]>yMax)yMax=v[1];}
 MESH={body:bfaces,garment:gm.faces,cy:(yMin+yMax)/2,hh:Math.max(1,yMax-yMin),prof,L,g};
 document.getElementById('fit').innerHTML='<b>Holgura (ajuste)</b>'+gm.fit.map(f=>
  '<div class="kv"><span>'+f[0]+'</span><b style="color:rgb('+easeColor(f[1]).join(',')+')">'+f[1].toFixed(1)+' cm</b></div>').join('');
 if(simMode){startSim();}else{if(raf)cancelAnimationFrame(raf),raf=null;draw();}}

function startSim(){
 const grids=garmentGrids(MESH.L,MESH.g,MESH.prof);
 CLOTH=buildCloth(grids,MESH.prof);
 if(raf)cancelAnimationFrame(raf);
 let n=0;const loop=()=>{for(let s=0;s<2;s++)stepCloth(CLOTH,0.12);n++;
  draw();if(n<220&&simMode)raf=requestAnimationFrame(loop);};loop();}

function render(faces){
 const w=cv.width,h=cv.height;ctx.clearRect(0,0,w,h);
 const cyaw=Math.cos(yaw),syaw=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 const rot=p=>{let x=p[0]*cyaw-p[2]*syaw,z=p[0]*syaw+p[2]*cyaw,y=p[1];
  return [x,y*cp-z*sp,y*sp+z*cp];};
 const cy=MESH.cy,dist=260,f=760,sc=0.72*h*dist/(f*MESH.hh);
 const proj=p=>{const zc=p[2]+dist,k=f/(zc||1e-3)*sc;return [w/2+p[0]*k,h*0.52-(p[1]-cy)*k,zc];};
 const light=norm([0.35,0.55,0.75]),draws=[];
 for(const fa of faces){const rv=fa.v.map(rot);
  const n=norm(cross([rv[1][0]-rv[0][0],rv[1][1]-rv[0][1],rv[1][2]-rv[0][2]],
                     [rv[2][0]-rv[0][0],rv[2][1]-rv[0][1],rv[2][2]-rv[0][2]]));
  const lamb=Math.abs(n[0]*light[0]+n[1]*light[1]+n[2]*light[2]);
  const pv=rv.map(proj),zc=(pv[0][2]+pv[1][2]+pv[2][2]+pv[3][2])/4;
  draws.push({pv,zc,col:fa.col,sh:Math.min(1,0.35+0.75*lamb),alpha:fa.alpha});}
 draws.sort((a,b)=>b.zc-a.zc);
 for(const d of draws){const c=d.col;ctx.beginPath();ctx.moveTo(d.pv[0][0],d.pv[0][1]);
  for(let i=1;i<4;i++)ctx.lineTo(d.pv[i][0],d.pv[i][1]);ctx.closePath();
  ctx.fillStyle='rgba('+Math.round(c[0]*d.sh)+','+Math.round(c[1]*d.sh)+','+Math.round(c[2]*d.sh)+','+d.alpha+')';ctx.fill();}
 window.__rendered=draws.length;}

function draw(){
 let faces=MESH.body.slice();
 if(simMode&&CLOTH)faces=faces.concat(clothFaces(CLOTH,[57,110,158]));
 else faces=faces.concat(MESH.garment);
 render(faces);}

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
document.getElementById('sim').onchange=e=>{simMode=e.target.checked;rebuild();};
document.getElementById('redrape').onclick=()=>{if(simMode)startSim();};
cv.onpointerdown=e=>{drag=[e.clientX,e.clientY];cv.setPointerCapture(e.pointerId);cv.style.cursor='grabbing';};
cv.onpointermove=e=>{if(!drag)return;yaw+=(e.clientX-drag[0])*0.01;pitch+=(e.clientY-drag[1])*0.01;
 pitch=Math.max(-0.9,Math.min(0.9,pitch));drag=[e.clientX,e.clientY];draw();};
cv.onpointerup=()=>{drag=null;cv.style.cursor='grab';};
buildSliders();rebuild();
</script></body></html>"""


def build_body_viewer(outdir: str = "output") -> str:
    """Genera el visor 3D del maniquí a medida (HTML autocontenido)."""
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "viewer_3d.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(_PAGE)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Genera el visor 3D del maniquí a medida")
    ap.add_argument("--output", default="output")
    args = ap.parse_args(argv)
    path = build_body_viewer(args.output)
    print(f"Visor 3D generado: {path} ({os.path.getsize(path)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
