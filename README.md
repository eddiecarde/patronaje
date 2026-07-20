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

**Métodos de patronaje**: `aldrich` (por defecto), `mueller` (Müller & Sohn),
`bunka` (文化式) y `esmod`. El motor de geometría y todo lo demás se reutiliza
entre métodos — ver `docs/motor_metodos.md` y `docs/metodo_{aldrich,mueller,bunka,esmod}.md`.

**Estilos (manipulación de bloque)**: `--style flare` (túnica A-line) y `--style puff`
(manga abullonada) — del mismo bloque salen varias prendas. Ver `docs/manipulacion_bloque.md`.

**Bloque base entallado (pinzas + equilibrio)**: `--fit fitted` genera el sloper con
pinza de busto (trasladable con `--bust-dart shoulder|neck|armhole|french|waist`),
pinzas de cintura y de hombro, por cada método. Ver `docs/pinzas_equilibrio.md`.
Estilos **dart-aware** sobre el sloper: `princess`, `empire`, `peplum`.

**Modo a medida (made-to-measure)**: `--measurements cliente.json` traza el patrón
con las medidas de una persona (en lugar de una talla estándar). Las medidas se
**validan** (proporciones coherentes) antes de trazar. Ver `docs/a_medida.md`.

```bash
python -m patronaje.cli --measurements cliente.json --fit fitted --method mueller
```

**Otras prendas**: `--garment skirt` genera una **falda base recta (lápiz)** de dos
paneles con pinzas de cintura, curva de cadera y pretina (10 estilos: evasé,
acampanada, circular, tubo, mini, maxi, fruncida, tableada, yoke, godet).
`--garment trouser` genera un **pantalón base** de dos paneles con curva de tiro,
pinzas y pretina (9 estilos: recto, pitillo, wide, palazzo, campana, capri, short,
culotte, jogger). `--garment dress` genera un **vestido** = cuerpo entallado
(**por método**, con pinzas) + falda unidos en la costura de talle (7 estilos:
recto, evase, acampanada, sin_mangas, mini, maxi, godet). `--garment blazer`
genera una **chaqueta sastre** (**por método**) con **manga de dos piezas**
(mangón + soplillo con costuras que casan), **solapa** con pico, cuello sastre,
vista y **forro** (6 estilos: clasica, crop, longline, cruzada, un_boton,
sin_forro). Mismo motor, misma exportación. Ver `docs/falda.md`,
`docs/pantalon.md`, `docs/vestido.md` y `docs/blazer.md`.

```bash
python -m patronaje.cli --garment skirt   --style evase --size S
python -m patronaje.cli --garment trouser --size S --output output
```

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

> Los archivos de `output/` son **regenerables** por el CLI y están fuera del
> control de versiones (`.gitignore`); el repo solo conserva una **muestra
> talla S** + el visor como escaparate. Regenera todo con los comandos de arriba.

**Visor interactivo**: `python -m patronaje.viewer --output output` genera
`output/viewer.html` (elige método y estilo, con consumo y nº de piezas) y
`output/viewer_live.html`, un **visor en vivo** donde mueves las medidas y el
patrón se **recalcula al instante**: el núcleo (spline G2 + fórmulas Aldrich +
copa de manga por bisección) está **portado a JavaScript**, así que no necesita
servidor ni dependencias. La fidelidad del port se verifica contra el motor
Python (Δ < 0.0002 cm). Ver `docs/visor_vivo.md`.

**Maniquí 3D a medida (WebGL/PBR)**: `python -m patronaje.viewer3d` genera
`output/viewer_3d.html`, un maniquí de sastre (dress form) paramétrico construido
desde las medidas y renderizado con **WebGL**: **torso cerrado y suave**, materiales
**PBR** (lino/metal), **iluminación de estudio** y **sombras**, al estilo de una
horma profesional (Mujer / Hombre). La prenda se ve como **cáscara** con **mapa de
ajuste** (holgura por zona: cómodo/ajustado/tira/holgado) o **cae como tela** (solver
PBD). Se gira con el ratón (rueda para acercar). Es **autocontenido y sin red**: la
librería Three.js va **incrustada** en el HTML (no se descarga de ningún CDN); se
vendoriza en `patronaje/assets/three.min.js`. Ver `docs/visor_3d.md`.

Tallas disponibles: `XS S M L XL XXL` (medidas base en
`patronaje/parametric/measurements.py`). Grading: ver `docs/grading.md`;
formatos industriales: `docs/aama_astm.md`.

## Piezas generadas

Delantero · Espalda · Canesú · Manga · Puño · Tapeta · Cuello · Pie de cuello ·
Vista · Bolsillo (opcional).

Cada pieza incluye: línea de corte, línea de costura, línea de hilo, centro,
piquetes, perforaciones, puntos de control, nombre, número, talla, cantidad,
tipo de corte e indicación "AL DOBLEZ".

**Márgenes por borde:** el margen de costura no es uniforme — el **dobladillo**
lleva más margen (`margen_dobladillo`, 2.5 cm), las **costuras** el estándar
(`margen_costura`, 1.0 cm) y el **doblez** ninguno. Se añaden **piquetes de
dobladillo** automáticos en las esquinas del bajo para marcar la línea de doblez.

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

## Casado automático de piquetes

Las costuras que se cosen juntas reciben **piquetes coincidentes** colocados a la
misma fracción de longitud de arco (costado delantero↔trasero, hombro↔canesú,
costado de la falda). Así casan al coser sin fruncidos. Se validan por longitud
de tramo. Ver `docs/casado_piquetes.md`.

## Validaciones (previas a exportar)

Polígonos cerrados · sin autointersección · sin duplicados · **sisa = copa** ±
tolerancia · costados y hombros casan · cuello = escote · canesú = espalda ·
puño = boca de manga · **piquetes casados** (tramos de igual longitud). El CLI
imprime el reporte y **bloquea la exportación** si hay errores (usar `--force`).

## Tests

```bash
python -m pytest -q
```
