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
             tol: float = 0.5, quiet: bool = False, method: str = "aldrich",
             style: str = "none", fit: str = "shirt", bust_dart: str = "side",
             garment: str = "shirt", p=None) -> dict:
    os.makedirs(outdir, exist_ok=True)
    fitted = fit == "fitted"
    is_skirt = garment == "skirt"
    is_trouser = garment == "trouser"
    is_dress = garment == "dress"
    is_blazer = garment == "blazer"
    other = is_skirt or is_trouser or is_dress or is_blazer
    from .validation.validators import ValidationReport, validate_piece_geometry

    if other:
        # prendas propias (falda / pantalón / vestido): validación geométrica + casado
        from .validation.validators import validate_notch_matching
        if is_skirt:
            from .garment.skirt import build_skirt
            shirt = build_skirt(size, method=method, p=p)
            label = "falda base"
        elif is_trouser:
            from .garment.trouser import build_trouser
            shirt = build_trouser(size, method=method, p=p)
            label = "pantalón base"
        elif is_dress:
            from .garment.dress import build_dress
            shirt = build_dress(size, method=method, bust_dart_pos=bust_dart, p=p)
            label = "vestido base"
        else:
            from .garment.blazer import build_blazer
            shirt = build_blazer(size, method=method, p=p)
            label = "chaqueta/blazer"
        styled = style not in (None, "", "none")
        if styled:
            from .transform.styles import apply_style
            shirt = apply_style(shirt, style)
        else:
            shirt = shirt.layout()
        report = ValidationReport()
        for pc in shirt.pieces:
            validate_piece_geometry(pc, report)
        validate_notch_matching(shirt, report, tol=2.0 if is_dress else 0.8)
        if not quiet:
            extra = f" | pinza busto: {bust_dart}" if is_dress else ""
            print(f"[{label} | método: {method}{extra}" + (f" | estilo: {style}]" if styled else "]"))
            print(report.text())
    elif fitted:
        # bloque base entallado (sloper) con pinzas y equilibrio
        from .garment.sloper import build_sloper
        shirt = build_sloper(size, method=method, bust_dart_pos=bust_dart, p=p).layout()
        if style not in (None, "", "none"):
            from .transform.styles import apply_style
            shirt = apply_style(shirt, style)
        report = ValidationReport()
        for pc in shirt.pieces:
            validate_piece_geometry(pc, report)
        if not quiet:
            print(f"[base entallada | método: {method} | pinza busto: {bust_dart}]")
            print(report.text())
            fb = shirt.fitted
            print(f"  supresión de cintura/panel: {fb.waist_suppression:.1f} cm  "
                  f"(costado {fb.side_supp:.1f} + pinzas)")
    else:
        shirt = build_shirt(size, method=method, p=p).layout()
        styled = style not in (None, "", "none")
        if styled:
            from .transform.styles import apply_style
            shirt = apply_style(shirt, style)
            report = ValidationReport()
            for pc in shirt.pieces:
                validate_piece_geometry(pc, report)
        else:
            report = validate_all(shirt, tol=tol)
        if not quiet:
            print(f"[método: {method}" + (f" | estilo: {style}]" if styled else "]"))
            print(report.text())

    if not report.ok and not force:
        print("\n[ABORTADO] Hay errores de validación. Use --force para exportar de todos modos.")
        sys.exit(2)

    suffix = "" if method == "aldrich" else f"_{method}"
    if other:
        if style not in (None, "", "none"):
            suffix += f"_{style}"
    elif fitted:
        suffix += f"_base_{bust_dart}"
        if style not in (None, "", "none"):
            suffix += f"_{style}"
    elif style not in (None, "", "none"):
        suffix += f"_{style}"
    prefix = {"skirt": "falda", "trouser": "pantalon", "dress": "vestido",
              "blazer": "blazer"}.get(garment, "camisa")
    base = os.path.join(outdir, f"{prefix}_{size}{suffix}")
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
    # Fase 3: tech pack (específico de camisa) + planos de corte
    if not other:
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
                       force: bool = False, tol: float = 0.6,
                       method: str = "aldrich") -> dict:
    """Grada todas las tallas (regeneración paramétrica) y el nido de grading."""
    print(grading_table_text())
    print()
    all_out = {}
    for s in SIZE_ORDER:
        sub = os.path.join(outdir, s)
        all_out[s] = generate(s, sub, include_seam=include_seam, force=force,
                              tol=tol, quiet=True, method=method)
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
    ap.add_argument("--method", default="aldrich",
                    help="Método (aldrich, mueller, bunka, esmod, marti, armstrong)")
    ap.add_argument("--style", default="none",
                    help="Estilo: none, flare, puff, bell, mandarin, sleeveless, crop, "
                         "princess, short_sleeve, cap_sleeve, dress, oversized, empire, "
                         "v_neck, boat_neck, hi_lo, cocoon, peplum, "
                         "dolman, kimono, raglan, godet, wrap, back_pleat, "
                         "off_shoulder, tie_front. "
                         "Falda (--garment skirt): evase, acampanada, circular, tubo, "
                         "mini, maxi, fruncida, tableada, yoke, godet. "
                         "Pantalón (--garment trouser): recto, pitillo, wide, palazzo, "
                         "campana, capri, short, culotte, jogger. "
                         "Vestido (--garment dress): recto, evase, acampanada, sin_mangas, "
                         "mini, maxi, godet. "
                         "Blazer (--garment blazer): clasica, crop, longline, cruzada, "
                         "un_boton, sin_forro")
    ap.add_argument("--garment", default="shirt",
                    choices=["shirt", "skirt", "trouser", "dress", "blazer"],
                    help="Prenda: shirt = camisa; skirt = falda base recta; "
                         "trouser = pantalón base; dress = vestido (talle+falda, por método); "
                         "blazer = chaqueta sastre (manga 2 piezas, solapa, forro, por método)")
    ap.add_argument("--fit", default="shirt", choices=["shirt", "fitted"],
                    help="shirt = camisa holgada; fitted = bloque base entallado con pinzas "
                         "(sólo con --garment shirt)")
    ap.add_argument("--bust-dart", default="side",
                    help="Posición de la pinza de busto (side, shoulder, neck, armhole, "
                         "french, waist) — sólo con --fit fitted")
    ap.add_argument("--measurements", default=None, metavar="FILE.json",
                    help="Modo a medida: JSON con las medidas del cuerpo (cm). "
                         "Sustituye a --size; el nombre de talla sale del archivo.")
    args = ap.parse_args(argv)

    custom_p = None
    size = args.size
    if args.measurements:
        custom_p, size = _load_measurements(args.measurements, force=args.force)

    if args.all_sizes:
        generate_all_sizes(args.output, include_seam=not args.no_seam,
                           force=args.force, tol=max(args.tol, 0.6), method=args.method)
    else:
        generate(size, args.output, include_seam=not args.no_seam,
                 force=args.force, tol=args.tol, method=args.method, style=args.style,
                 fit=args.fit, bust_dart=args.bust_dart, garment=args.garment, p=custom_p)


def _load_measurements(path: str, *, force: bool = False):
    """Carga un JSON de medidas, lo valida y devuelve (Parameters, nombre)."""
    import json
    from .parametric.validation import (
        validate_measurements, format_issues, has_errors)
    from .parametric.measurements import build_parameters_from_measurements

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # admite {"nombre": ..., "medidas": {...}} o directamente {medida: valor}
    name = data.pop("nombre", None) if isinstance(data, dict) else None
    measurements = data.get("medidas", data) if isinstance(data, dict) else data
    if name is None:
        name = os.path.splitext(os.path.basename(path))[0]

    issues = validate_measurements(measurements)
    print(format_issues(issues))
    if has_errors(issues) and not force:
        print("\n[ABORTADO] Medidas incoherentes. Corrija el JSON o use --force.")
        sys.exit(2)
    p = build_parameters_from_measurements(measurements, name=name)
    print(f"[modo a medida | {name}]")
    return p, name


if __name__ == "__main__":
    main()
