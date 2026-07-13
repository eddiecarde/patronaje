"""Exportador CSV de puntos.

Vuelca todos los puntos de contorno (línea de costura y de corte) de cada pieza
a un CSV plano, apto para hojas de cálculo o para verificación punto a punto.
Columnas: pieza, numero, talla, tipo_linea, indice, x_cm, y_cm.
"""
from __future__ import annotations

import csv


def export_csv(shirt, path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pieza", "numero", "talla", "tipo_linea", "indice", "x_cm", "y_cm"])
        for pc in shirt.pieces:
            for i, (x, y) in enumerate(pc.net_contour):
                w.writerow([pc.name, pc.number, pc.size, "costura", i,
                            f"{x:.4f}", f"{y:.4f}"])
            for i, (x, y) in enumerate(pc.cut_contour()):
                w.writerow([pc.name, pc.number, pc.size, "corte", i,
                            f"{x:.4f}", f"{y:.4f}"])
    return path
