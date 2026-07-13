"""Interfaz de línea de comandos del sistema de patronaje.

Uso:
    python -m patronaje.cli --size S --output output
    python -m patronaje.cli --all-sizes --output output   # grada XS..XXL

Flujo:
    1. Construye los parámetros y ensambla la camisa (motor paramétrico Aldrich).
    2. Ejecuta el layout (posiciona las piezas sin solaparse).
    3. Valida geometría y casado; si hay errores, aborta salvo ``--force``.
    4. Exporta los formatos: DXF R2013, DXF AAMA/ASTM, SVG, PDF 1:1, PDF A4,
       AI, JSON de geometría, CSV de puntos y SCR de AutoCAD.
    5. Con --all-sizes: grada todas las tallas y genera el nido de grading.
"""
from __future__ import annotations

import argparse
import os
import sys

from .garment.shirt import build_shirt
from .validation.validators import validate_all
from .export.dxf_r2013 import export_dxf
from .export.dxf_aama import export_dxf_aama
from .export.svg import export_svg
from .export.pdf import export_pdf_1to1, export_pdf_a4
from .export.ai import export_ai
from .export.json_geom import export_json
from .export.csv_points import export_csv
from .export.scr import export_scr
from .grading.rules import SIZE_ORDER, grading_table_text
from .grading.grader import export_grade_nest
from .techpack.techpack import export_techpack
from .marker.layout import export_marker_svg, marker_report


def generate(size: str = "S", outdir: str = "output", *,
             include_seam: bool = True, force: bool = False,
             tol: float = 0.5, quiet: bool = False) -> dict:
    os.makedirs(outdir, exist_ok=True)
    shirt = build_shirt(size).layout()

    report = validate_all(shirt, tol=tol)
    if not quiet:
        print(report.text())
    if not report.ok and not force:
        print("\n[ABORTADO] Hay errores de validación. Use --force para exportar de todos modos.")
        sys.exit(2)

    base = os.path.join(outdir, f"camisa_{size}")
    outputs = {}
    outputs["dxf_r2013"] = export_dxf(shirt, f"{base}.dxf", include_seam=include_seam)
    outputs["dxf_aama"] = export_dxf_aama(shirt, f"{base}_AAMA_ASTM.dxf")
    outputs["svg"] = export_svg(shirt, f"{base}.svg", include_seam=include_seam)
    outputs["pdf_1a1"] = export_pdf_1to1(shirt, f"{base}_1a1.pdf", include_seam=include_seam)
    outputs["pdf_a4"] = export_pdf_a4(shirt, f"{base}_A4.pdf", include_seam=include_seam)
    outputs["ai"] = export_ai(shirt, f"{base}.ai", include_seam=include_seam)
    outputs["json"] = export_json(shirt, f"{base}.json")
    outputs["csv"] = export_csv(shirt, f"{base}_puntos.csv")
    outputs["scr"] = export_scr(shirt, f"{base}.scr", include_seam=include_seam)
    # Fase 3: tech pack + planos de corte
    outputs["techpack"] = export_techpack(shirt, f"{base}_tech_pack.html")
    for W in (110, 150, 160):
        outputs[f"marker_{W}"] = export_marker_svg(shirt, float(W), f"{base}_marker_{W}.svg")

    if not quiet:
        rep = marker_report(shirt)
        print("\n=== CONSUMO DE TELA (marker) ===")
        for W, dd in rep["por_ancho"].items():
            print(f"  ancho {dd['ancho_cm']:.0f} cm -> {dd['largo_m']:.2f} m  "
                  f"(desperdicio {dd['desperdicio']*100:.1f} %)")
    if not quiet:
        print(f"\n=== ARCHIVOS GENERADOS (talla {size}) ===")
        for k, v in outputs.items():
            print(f"  {k:10s} -> {v}  ({os.path.getsize(v)/1024:.1f} KB)")
    return outputs


def generate_all_sizes(outdir: str = "output", *, include_seam: bool = True,
                       force: bool = False, tol: float = 0.6) -> dict:
    """Grada todas las tallas (regeneración paramétrica) y el nido de grading."""
    print(grading_table_text())
    print()
    all_out = {}
    for s in SIZE_ORDER:
        sub = os.path.join(outdir, s)
        all_out[s] = generate(s, sub, include_seam=include_seam, force=force,
                              tol=tol, quiet=True)
        print(f"  [OK] talla {s}: {len(all_out[s])} archivos -> {sub}/")
    # nidos de grading de piezas clave
    nests = {}
    for pieza in ["DELANTERO", "ESPALDA", "MANGA"]:
        p = os.path.join(outdir, f"nido_grading_{pieza}.svg")
        nests[pieza] = export_grade_nest(pieza, p)
        print(f"  [OK] nido de grading {pieza} -> {p}")
    all_out["_nidos"] = nests
    return all_out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generador de patrones industriales (Aldrich)")
    ap.add_argument("--size", default="S", help="Talla (XS,S,M,L,XL,XXL)")
    ap.add_argument("--output", default="output", help="Carpeta de salida")
    ap.add_argument("--all-sizes", action="store_true", help="Gradar todas las tallas XS..XXL")
    ap.add_argument("--no-seam", action="store_true", help="No dibujar línea de costura")
    ap.add_argument("--force", action="store_true", help="Exportar aunque falle la validación")
    ap.add_argument("--tol", type=float, default=0.5, help="Tolerancia de casado (cm)")
    args = ap.parse_args(argv)
    if args.all_sizes:
        generate_all_sizes(args.output, include_seam=not args.no_seam,
                           force=args.force, tol=max(args.tol, 0.6))
    else:
        generate(args.size, args.output, include_seam=not args.no_seam,
                 force=args.force, tol=args.tol)


if __name__ == "__main__":
    main()
