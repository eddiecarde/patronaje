"""Lista de materiales (BOM — Bill of Materials).

Deriva del ensamble de la camisa: cuenta botones y ojales de las piezas,
estima entretela por las piezas con entretela, e incorpora el consumo de tela
principal (del módulo de consumo). Devuelve una estructura lista para tabular en
el tech pack.
"""
from __future__ import annotations

from .consumption import consumption


def build_bom(shirt, width_ref: float = 150.0) -> dict:
    # botones y ojales
    n_botones = sum(len(pc.buttons) for pc in shirt.pieces)
    n_ojales = sum(len(pc.buttonholes) for pc in shirt.pieces)
    # piezas con entretela
    entretela_piezas = [pc.name for pc in shirt.pieces if "entretela" in pc.cut_type.lower()]
    # área de entretela aprox (cuello + pie + puños)
    area_entretela = sum(pc.area() for pc in shirt.pieces
                         if "entretela" in pc.cut_type.lower())

    cons = consumption(shirt, widths=(width_ref,))
    largo_m = cons["por_ancho"][width_ref]["compra_recomendada_m"]

    items = [
        {"item": "Tela principal (popelín/algodón)", "unidad": "m",
         "cantidad": largo_m, "obs": f"ancho {width_ref:.0f} cm, incl. margen de mermas"},
        {"item": "Entretela fusionable", "unidad": "m",
         "cantidad": round(max(0.25, area_entretela / (90.0 * 100.0)), 2),
         "obs": f"para {', '.join(entretela_piezas) or 'cuello/puños'} (ancho 90 cm)"},
        {"item": "Botones", "unidad": "u", "cantidad": n_botones,
         "obs": "delantero + puños + pie de cuello (Ø 11 mm)"},
        {"item": "Ojales", "unidad": "u", "cantidad": n_ojales, "obs": "confección"},
        {"item": "Hilo de coser", "unidad": "cono",
         "cantidad": 1, "obs": "≈150 m por prenda (tex 30)"},
        {"item": "Etiqueta de marca", "unidad": "u", "cantidad": 1, "obs": "cuello interior"},
        {"item": "Etiqueta de composición/talla", "unidad": "u", "cantidad": 1,
         "obs": "costado interior"},
    ]
    return {
        "talla": pc_size(shirt),
        "resumen": {"botones": n_botones, "ojales": n_ojales,
                    "piezas_totales": len(shirt.pieces)},
        "items": items,
    }


def pc_size(shirt) -> str:
    return shirt.p._base["talla_nombre"].descripcion.replace("talla ", "")
