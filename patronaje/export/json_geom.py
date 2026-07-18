"""Exportador de geometría a JSON.

Serializa el patrón completo con todos los puntos, contornos, curvas y metadata
por pieza, más los parámetros del motor. Es el formato de intercambio del
sistema y la base para reimportar/depurar o alimentar otros procesos.
"""
from __future__ import annotations

import json


def shirt_to_dict(shirt) -> dict:
    p = shirt.p
    b = getattr(shirt, "bodice", None)
    s = getattr(shirt, "sleeve", None)
    data = {
        "prenda": getattr(shirt, "prenda", "camisa_basica_femenina_ML"),
        "metodo": getattr(shirt, "method", "aldrich").capitalize(),
        "talla": p._base["talla_nombre"].descripcion.replace("talla ", ""),
        "parametros": p.as_dict(),
        "piezas": [],
    }
    # medidas de casado (sólo prendas con cuerpo/manga)
    if b is not None and hasattr(b, "neckline_length"):
        data["medidas_clave"] = {
            "escote_medio": b.neckline_length(),
            "sisa": b.armhole_length(),
        }
        if s is not None:
            data["medidas_clave"].update({
                "copa_manga": s.cap_length(),
                "altura_copa": s.cap_height,
                "biceps": 2 * s.biceps_half,
            })
    for pc in shirt.pieces:
        data["piezas"].append({
            "nombre": pc.name,
            "numero": pc.number,
            "talla": pc.size,
            "cantidad": pc.quantity,
            "tipo_corte": pc.cut_type,
            "al_doblez": pc.on_fold,
            "margen_costura": pc.seam_allowance,
            "area_cm2": round(pc.area(), 2),
            "perimetro_cm": round(pc.perimeter(), 2),
            "bbox": [round(v, 3) for v in pc.bbox()],
            "linea_costura": [[round(x, 4), round(y, 4)] for x, y in pc.net_contour],
            "linea_corte": [[round(x, 4), round(y, 4)] for x, y in pc.cut_contour()],
            "linea_hilo": [list(pc.grain[0]), list(pc.grain[1])] if pc.grain else None,
            "piquetes": [[round(x, 4), round(y, 4)] for x, y in pc.notches],
            "perforaciones": [[round(x, 4), round(y, 4)] for x, y in pc.drills],
            "botones": [[round(x, 4), round(y, 4)] for x, y in pc.buttons],
        })
    return data


def export_json(shirt, path: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(shirt_to_dict(shirt), f, ensure_ascii=False, indent=2)
    return path
