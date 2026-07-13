"""Interfaz de línea de comandos del sistema de patronaje.

Uso:
    python -m patronaje.cli --size S --output output

Flujo:
    1. Construye los parámetros y ensambla la camisa (motor paramétrico Aldrich).
    2. Ejecuta el layout (posiciona las piezas sin solaparse).
    3. Valida geometría y casado; si hay errores, aborta salvo ``--force``.
    4. Exporta todos los formatos de Fase 1: DXF R2013, SVG, PDF 1:1, PDF A4,
       JSON de geometría, CSV de puntos y SCR de AutoCAD.
"""
from __future__ import annotations

import argparse
import os
import sys

from .garment.shirt import build_shirt
from .validation.validators import validate_all
from .export.dxf_r2013 import export_dxf
from .export.svg import export_svg
from .export.pdf import export_pdf_1to1, export_pdf_a4
from .export.json_geom import export_json
from .export.csv_points import export_csv
from .export.scr import export_scr


def generate(size: str = "S", outdir: str = "output", *,
             include_seam: bool = True, force: bool = False,
             tol: float = 0.5) -> dict:
    os.makedirs(outdir, exist_ok=True)
    shirt = build_shirt(size).layout()

    report = validate_all(shirt, tol=tol)
    print(report.text())
    if not report.ok and not force:
        print("\n[ABORTADO] Hay errores de validación. Use --force para exportar de todos modos.")
        sys.exit(2)

    base = os.path.join(outdir, f"camisa_{size}")
    outputs = {}
    outputs["dxf"] = export_dxf(shirt, f"{base}.dxf", include_seam=include_seam)
    outputs["svg"] = export_svg(shirt, f"{base}.svg", include_seam=include_seam)
    outputs["pdf_1a1"] = export_pdf_1to1(shirt, f"{base}_1a1.pdf", include_seam=include_seam)
    outputs["pdf_a4"] = export_pdf_a4(shirt, f"{base}_A4.pdf", include_seam=include_seam)
    outputs["json"] = export_json(shirt, f"{base}.json")
    outputs["csv"] = export_csv(shirt, f"{base}_puntos.csv")
    outputs["scr"] = export_scr(shirt, f"{base}.scr", include_seam=include_seam)

    print("\n=== ARCHIVOS GENERADOS ===")
    for k, v in outputs.items():
        size_kb = os.path.getsize(v) / 1024
        print(f"  {k:8s} -> {v}  ({size_kb:.1f} KB)")
    return outputs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generador de patrones industriales (Aldrich)")
    ap.add_argument("--size", default="S", help="Talla (XS,S,M,L,XL,XXL)")
    ap.add_argument("--output", default="output", help="Carpeta de salida")
    ap.add_argument("--no-seam", action="store_true", help="No dibujar línea de costura")
    ap.add_argument("--force", action="store_true", help="Exportar aunque falle la validación")
    ap.add_argument("--tol", type=float, default=0.5, help="Tolerancia de casado (cm)")
    args = ap.parse_args(argv)
    generate(args.size, args.output, include_seam=not args.no_seam,
             force=args.force, tol=args.tol)


if __name__ == "__main__":
    main()
