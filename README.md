# Patronaje — Sistema de patrones industriales paramétricos

Motor **paramétrico** en Python para generar patrones industriales de ropa
**listos para producción** (no ilustraciones), con geometría CAD real, curvas
G2 aptas para corte CNC, validaciones de casado y exportación multiformato.

**Primer producto:** camisa básica femenina de manga larga, método **Aldrich**,
talla S internacional. El mismo motor es la base para futuras prendas (blusas,
vestidos, chaquetas, pantalones, faldas).

> Estado: **Fases 1, 2 y 3 completas** — motor geométrico, bloques Aldrich, 10
> piezas, validaciones, exportadores DXF R2013 / **DXF AAMA/ASTM** / SVG /
> PDF 1:1 / PDF A4 / **AI** / JSON / CSV / SCR, **grading XS–XXL** con nido,
> **tech pack** HTML completo y **plano de corte** (marker) con consumo y
> desperdicio para telas 110/150/160 cm.

## Instalación

```bash
pip install -r requirements.txt      # numpy, ezdxf, shapely, reportlab, svgwrite
```

## Uso

```bash
python -m patronaje.cli --size S --output output              # una talla (Aldrich)
python -m patronaje.cli --size S --method mueller --output output  # método Müller & Sohn
python -m patronaje.cli --all-sizes --output output           # grada XS..XXL + nido
```

**Métodos de patronaje**: `aldrich` (por defecto) y `mueller` (Müller & Sohn).
El motor de geometría y todo lo demás se reutiliza entre métodos — ver
`docs/motor_metodos.md`, `docs/metodo_mueller.md`.

Genera en `output/` (por talla):

| Archivo                    | Formato                                            |
|----------------------------|----------------------------------------------------|
| `camisa_S.dxf`             | DXF **AutoCAD R2013** con 11 capas independientes  |
| `camisa_S_AAMA_ASTM.dxf`   | DXF **AAMA/ASTM D6673** (bloques + capas numéricas) |
| `camisa_S.svg`             | SVG vectorial por capas                            |
| `camisa_S_1a1.pdf`         | PDF **escala real 1:1** en mosaico A4              |
| `camisa_S_A4.pdf`          | PDF de conjunto ajustado a A4                       |
| `camisa_S.ai`              | **AI** compatible con PDF (Illustrator), 1:1        |
| `camisa_S.json`            | Geometría completa + parámetros                    |
| `camisa_S_puntos.csv`      | Todos los puntos (costura y corte)                 |
| `camisa_S.scr`             | Script de AutoCAD que reconstruye el patrón        |
| `camisa_S_tech_pack.html`  | **Tech pack** completo (ficha, BOM, consumo, QC…)  |
| `camisa_S_marker_150.svg`  | **Plano de corte** (marker) por ancho de tela      |

Con `--all-sizes`: subcarpeta por talla + `output/nido_grading_*.svg`.

Tallas disponibles: `XS S M L XL XXL` (medidas base en
`patronaje/parametric/measurements.py`). Grading: ver `docs/grading.md`;
formatos industriales: `docs/aama_astm.md`.

## Piezas generadas

Delantero · Espalda · Canesú · Manga · Puño · Tapeta · Cuello · Pie de cuello ·
Vista · Bolsillo (opcional).

Cada pieza incluye: línea de corte, línea de costura, línea de hilo, centro,
piquetes, perforaciones, puntos de control, nombre, número, talla, cantidad,
tipo de corte e indicación "AL DOBLEZ".

## Arquitectura (modular)

```
patronaje/
  core/        motor geométrico + matemático (puntos, geometría, curvas Bézier/spline G2)
  parametric/  registro de parámetros y medidas por talla
  blocks/      trazos Aldrich (cuerpo, manga)
  garment/     ensamble de la prenda en piezas
  piece.py     modelo de pieza + entidades CAD neutras
  validation/  validaciones geométricas y de casado
  export/      exportadores DXF/SVG/PDF/JSON/CSV/SCR
  cli.py       línea de comandos
docs/          método, fórmulas y arquitectura
tests/         pytest (geometría, casado, exportación)
```

Ver `docs/arquitectura.md`, `docs/metodo_aldrich.md` y `docs/formulas.md`.

## Motor paramétrico

Ninguna coordenada es fija: cada punto se calcula desde parámetros (medidas +
holguras + constantes de método). Cambiar una medida regenera todo el patrón:

```python
from patronaje.garment.shirt import build_shirt
sh = build_shirt("M")          # otra talla, mismo motor
sh = build_shirt("S").layout() # posiciona las piezas
```

## Validaciones (previas a exportar)

Polígonos cerrados · sin autointersección · sin duplicados · **sisa = copa** ±
tolerancia · costados y hombros casan · cuello = escote · canesú = espalda ·
puño = boca de manga. El CLI imprime el reporte y **bloquea la exportación** si
hay errores (usar `--force` para omitir).

## Tests

```bash
python -m pytest -q
```
