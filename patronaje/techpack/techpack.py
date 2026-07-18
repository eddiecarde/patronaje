"""Ensamblado del Tech Pack (ficha técnica completa) en HTML autocontenido.

Reúne todas las secciones exigidas por el prompt: ficha técnica, plano
delantero y trasero, detalles (cuello, manga, puño, bolsillo), tabla de medidas,
BOM, consumo, secuencia de confección, control de calidad y tolerancias. Se
genera como **HTML autocontenido** (SVG inline, sin recursos externos), listo
para abrir en el navegador e imprimir a PDF A4.
"""
from __future__ import annotations

import datetime
import html

from .flats import garment_flat_svg, piece_detail_svg
from .bom import build_bom
from .consumption import consumption
from .sequence import (SEWING_SEQUENCE, QC_CHECKLIST, TOLERANCES,
                       finished_measurements)


_CSS = """
:root{--ink:#1f2d3d;--line:#c9d4e0;--accent:#22405e;--soft:#eef4fb;}
*{box-sizing:border-box;} body{font-family:'Segoe UI',Arial,sans-serif;color:var(--ink);
  margin:0;padding:0;background:#fff;font-size:12px;line-height:1.4;}
.page{max-width:1000px;margin:0 auto;padding:22px 26px;}
h1{font-size:20px;margin:0 0 2px;} h2{font-size:14px;margin:22px 0 8px;
  border-bottom:2px solid var(--accent);padding-bottom:3px;color:var(--accent);}
.head{display:flex;justify-content:space-between;align-items:flex-start;
  border:1px solid var(--line);border-radius:8px;padding:12px 16px;background:var(--soft);}
.head .meta div{margin:1px 0;}
.badge{background:var(--accent);color:#fff;border-radius:6px;padding:6px 10px;font-weight:600;}
table{border-collapse:collapse;width:100%;margin:6px 0 4px;}
th,td{border:1px solid var(--line);padding:4px 7px;text-align:left;}
th{background:var(--soft);} td.num,th.num{text-align:right;}
.flats{display:flex;gap:16px;flex-wrap:wrap;justify-content:center;}
.flats > div{flex:1 1 340px;text-align:center;}
.details{display:flex;gap:12px;flex-wrap:wrap;}
.details > div{flex:1 1 180px;border:1px solid var(--line);border-radius:6px;padding:6px;text-align:center;}
.flats svg,.details svg{max-width:100%;height:auto;}
ol,ul{margin:4px 0 4px 18px;padding:0;} li{margin:2px 0;}
.small{color:#6b8199;font-size:11px;} .grid2{display:flex;gap:20px;flex-wrap:wrap;}
.grid2>div{flex:1 1 380px;}
@media print{.page{max-width:none;} h2{page-break-after:avoid;}}
"""


def _table(headers, rows, num_cols=()):
    th = "".join(f"<th class='{'num' if i in num_cols else ''}'>{html.escape(str(h))}</th>"
                 for i, h in enumerate(headers))
    trs = []
    for r in rows:
        tds = "".join(f"<td class='{'num' if i in num_cols else ''}'>{html.escape(str(c))}</td>"
                      for i, c in enumerate(r))
        trs.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def build_techpack_html(shirt) -> str:
    p = shirt.p
    size = shirt.p._base["talla_nombre"].descripcion.replace("talla ", "")
    today = datetime.date.today().isoformat()

    front = garment_flat_svg(p, "front")
    back = garment_flat_svg(p, "back")

    # detalles
    detail_names = ["CUELLO", "PIE DE CUELLO", "MANGA", "PUNO", "BOLSILLO"]
    details_html = ""
    for name in detail_names:
        pc = next((x for x in shirt.pieces if x.name == name), None)
        if pc:
            details_html += f"<div>{piece_detail_svg(pc)}</div>"

    # tabla de medidas del cuerpo
    body_rows = [(k, f"{p[k]:.1f}") for k in
                 ["busto", "cintura", "cadera", "largo_camisa", "largo_manga",
                  "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo", "muneca"]]
    # medidas terminadas + tolerancia
    fin = finished_measurements(shirt)
    fin_rows = [(r["pom"], f"{r['valor_cm']:.1f}", f"± {r['tol_cm']:.1f}") for r in fin]

    # piezas
    piece_rows = [(pc.number, pc.name, pc.quantity, pc.cut_type,
                   "Sí" if pc.on_fold else "No") for pc in shirt.pieces]

    # BOM
    bom = build_bom(shirt)
    bom_rows = [(it["item"], it["unidad"], it["cantidad"], it["obs"]) for it in bom["items"]]

    # consumo
    cons = consumption(shirt)
    cons_rows = []
    for W, d in cons["por_ancho"].items():
        cons_rows.append((f"{d['ancho_cm']:.0f} cm", f"{d['largo_m']:.2f} m",
                          f"{d['compra_recomendada_m']:.2f} m",
                          f"{d['eficiencia']*100:.1f} %", f"{d['desperdicio']*100:.1f} %"))

    tol_rows = [(a, b) for a, b in TOLERANCES]

    parts = []
    parts.append(f"<style>{_CSS}</style>")
    parts.append("<div class='page'>")
    parts.append(f"""
      <div class='head'>
        <div class='meta'>
          <h1>Camisa básica femenina · Manga larga</h1>
          <div><b>Método:</b> Aldrich (Metric Pattern Cutting for Women's Wear)</div>
          <div><b>Estilo:</b> CAM-BAS-001 &nbsp; <b>Temporada:</b> —</div>
          <div class='small'>Ficha técnica generada por el motor paramétrico · {today}</div>
        </div>
        <div class='badge'>TALLA {size}</div>
      </div>
    """)

    parts.append("<h2>1. Planos técnicos</h2>")
    parts.append(f"<div class='flats'><div>{front}</div><div>{back}</div></div>")

    parts.append("<h2>2. Detalles de pieza</h2>")
    parts.append(f"<div class='details'>{details_html}</div>")

    parts.append("<div class='grid2'>")
    parts.append("<div><h2>3. Tabla de medidas (cuerpo)</h2>"
                 + _table(["Medida", "cm"], body_rows, num_cols=(1,)) + "</div>")
    parts.append("<div><h2>4. Medidas terminadas + tolerancia</h2>"
                 + _table(["Punto de medida (POM)", "cm", "Tol."], fin_rows, num_cols=(1, 2))
                 + "</div>")
    parts.append("</div>")

    parts.append("<h2>5. Piezas del patrón</h2>")
    parts.append(_table(["#", "Pieza", "Cant.", "Tipo de corte", "Al doblez"],
                        piece_rows, num_cols=(0, 2)))

    parts.append("<h2>6. Lista de materiales (BOM)</h2>")
    parts.append(_table(["Material", "Ud.", "Cant.", "Observaciones"], bom_rows, num_cols=(2,)))

    parts.append("<h2>7. Consumo de tela y desperdicio</h2>")
    parts.append(_table(["Ancho de tela", "Largo marker", "Compra (c/ merma)",
                         "Eficiencia", "Desperdicio"], cons_rows))
    parts.append("<div class='small'>Consumo por prenda con nesting por skyline de "
                 "contorno (encaje real, rotación 180°); combinar varias prendas/tallas "
                 "en el mismo trazo reduce aún más el desperdicio.</div>")

    parts.append("<div class='grid2'>")
    seq = "".join(f"<li>{html.escape(s)}</li>" for s in SEWING_SEQUENCE)
    parts.append(f"<div><h2>8. Secuencia de confección</h2><ol>{seq}</ol></div>")
    qc = "".join(f"<li>{html.escape(s)}</li>" for s in QC_CHECKLIST)
    parts.append(f"<div><h2>9. Control de calidad</h2><ul>{qc}</ul>"
                 "<h2>10. Tolerancias</h2>"
                 + _table(["Concepto", "Tolerancia"], tol_rows) + "</div>")
    parts.append("</div>")

    parts.append("<div class='small' style='margin-top:18px'>Documento generado "
                 "automáticamente. Verificar prototipo antes de producción.</div>")
    parts.append("</div>")
    return "".join(parts)


def export_techpack(shirt, path: str) -> str:
    html_doc = "<!doctype html><html lang='es'><head><meta charset='utf-8'>" \
               "<title>Tech Pack — Camisa básica femenina</title></head><body>" \
               + build_techpack_html(shirt) + "</body></html>"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return path
