# Arquitectura del sistema

El sistema es **modular** y separa con claridad el motor de cálculo de los
formatos de salida, de modo que el mismo núcleo sirve para cualquier prenda.

```
Parámetros ──▶ Bloques Aldrich ──▶ Piezas ──▶ Validación ──▶ Exportadores
 (medidas)      (geometría)        (metadata)   (casado)      (DXF/SVG/PDF/…)
```

## Capas del código

### `core/` — motor geométrico y matemático
- **`point.py`** — `Point` con ID, descripción, coordenadas, relaciones y
  restricciones (trazabilidad de cada punto). `polyline_length` para medir
  costuras.
- **`geometry.py`** — álgebra vectorial, intersección de rectas, punto a
  distancia/ángulo, *offset* de polilíneas (líneas de costura), **arcos
  tangentes** (fillets G1), área y bounding box.
- **`curves.py`** — `CubicBezier`, `NaturalCubicSpline` (interpolante, C2 ⇒
  **G2**), `smooth_curve` (escotes/sisas/copa), verificación de continuidad
  `continuity_between` (G0/G1/G2) y `chord_error` (aptitud CNC).

### `parametric/` — motor paramétrico
- **`parameters.py`** — `Parameters`: registro con parámetros base y
  **derivados** (funciones que se recalculan solas). Acceso por atributo o clave.
- **`measurements.py`** — tabla de tallas XS–XXL, holguras, constantes de
  método y todas las fórmulas Aldrich derivadas.

### `blocks/` — trazos base (método Aldrich)
- **`aldrich_bodice.py`** — bloque de cuerpo (delantero + espalda) con escotes y
  sisas G2; separa canesú y espalda; mide escote y sisa.
- **`aldrich_sleeve.py`** — manga con **altura de copa por regla** y **bíceps
  resuelto por bisección** para casar `copa = sisa + holgura`.

### `garment/` — ensamble de la prenda
- **`shirt.py`** — construye las 10 piezas con toda su metadata y hace el layout.
- **`pieces/simple_shapes.py`** — rectángulos redondeados y bandas curvas
  (puño, tapeta, cuello, pie de cuello, bolsillo).

### `piece.py` — modelo de pieza + entidades CAD neutras
`Piece` guarda contorno net (costura), margen, línea de hilo, piquetes,
perforaciones, botones/ojales, textos y metadata. Expone `get_entities()` como
lista de entidades neutras (`EPolyline`, `ELine`, `EText`, `ECircle`, `ENotch`)
etiquetadas por capa. La línea de corte se calcula por *offset* (shapely),
respetando el borde de doblez.

### `validation/` — comprobaciones previas a exportar
Geometría (cerrado, simple, sin duplicados) y casado (sisa=copa, costados,
hombros, cuello=escote, canesú=espalda, puño=boca).

### `export/` — exportadores
Cada exportador consume las entidades neutras. `_common.py` centraliza el
aplanado y la reorientación de ejes. Formatos: DXF R2013, SVG, PDF 1:1 y A4,
JSON, CSV, SCR.

## Convención de coordenadas
- **Marco interno (patronaje):** `x` hacia el costado, `y` hacia abajo (largo de
  prenda). Es el natural del patronaje.
- **Marco CAD (DXF/PDF):** `y` hacia arriba. Los exportadores invierten Y.
- **SVG:** `y` hacia abajo (igual que el interno), no se invierte.

## Extensión a otras prendas
El patrón de diseño es: definir un *bloque* (en `blocks/`) y un *ensamble* (en
`garment/`) que produzca objetos `Piece`. Todo lo demás — validación,
exportación, layout — se reutiliza sin cambios.
