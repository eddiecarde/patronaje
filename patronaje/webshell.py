"""Cáscara web compartida: barra de navegación + 'handoff' de la plataforma.

`inject_shell(html)` inserta en cualquier visor generado:
  1. una **barra de navegación** común (Inicio · Patrón 2D · Maniquí 3D), para que
     los tres visores se sientan como una sola app;
  2. un **lector de query-string** genérico: si la página se abre con
     `?busto=90&cadera=98&garment=falda&sexo=F...`, aplica esas medidas/selección
     sobre el visor y vuelve a renderizar. Funciona con ambos visores por
     detección de funciones (`build/draw` en el 2D, `buildSliders/rebuild` en el 3D).

Todo es inline (sin recursos externos): la app sigue siendo autocontenida/offline.
"""

_NAV = (
    '<nav style="display:flex;gap:2px;align-items:center;background:#101722;'
    'padding:8px 14px;font:600 13px system-ui,-apple-system,sans-serif;'
    'position:sticky;top:0;z-index:50;border-bottom:1px solid #1f2937">'
    '<a href="index.html" style="color:#e9dcc6;font-weight:800;margin-right:14px;'
    'text-decoration:none">✂ Patronaje</a>'
    '<a href="index.html" style="color:#cdd6e0;text-decoration:none;padding:5px 10px;'
    'border-radius:7px">Inicio</a>'
    '<a href="viewer_live.html" style="color:#cdd6e0;text-decoration:none;padding:5px 10px;'
    'border-radius:7px">Patrón 2D</a>'
    '<a href="viewer_3d.html" style="color:#cdd6e0;text-decoration:none;padding:5px 10px;'
    'border-radius:7px">Maniquí 3D</a>'
    '</nav>'
)

_HANDOFF = (
    "(function(){try{var q=new URLSearchParams(location.search);"
    "var sx=document.getElementById('sexo');"
    "if(sx&&q.has('sexo')){sx.value=q.get('sexo');sx.dispatchEvent(new Event('change'));}"
    "var gs=document.getElementById('garment');"
    "if(gs&&q.has('garment')){gs.value=q.get('garment');gs.dispatchEvent(new Event('change'));}"
    "var ov=false;if(typeof P==='object'&&P){for(var k in P){if(q.has(k)){"
    "var v=parseFloat(q.get(k));if(isFinite(v)){P[k]=v;ov=true;}}}}"
    "if(ov){if(typeof camReady!=='undefined')camReady=false;"
    "if(typeof buildSliders==='function')buildSliders();"
    "if(typeof build==='function')build();"
    "if(typeof rebuild==='function')rebuild();"
    "if(typeof draw==='function')draw();}"
    "}catch(e){}})();"
)


def inject_shell(html: str) -> str:
    """Inserta la barra de navegación y el lector de query-string en un visor."""
    html = html.replace('<body>', '<body>' + _NAV, 1)
    i = html.rfind('</body>')
    if i != -1:
        html = html[:i] + '<script>' + _HANDOFF + '</script>' + html[i:]
    return html
