# Visor en vivo (motor paramétrico en el navegador)

`output/viewer_live.html` es un visor donde se **elige la prenda, se mueven las
medidas con sliders y el patrón se recalcula al instante**, sin servidor ni
dependencias. Cubre las **cinco prendas**:

- **Camisa**: delantero, espalda, canesú y manga + casado escote/sisa/copa.
- **Falda**: delantera y trasera con pinzas + cintura/cadera/largo.
- **Pantalón**: delantero y trasero con curva de tiro y pinzas + entrepierna.
- **Vestido**: talle entallado (con pinzas) + falda + casado de talle.
- **Blazer**: delantero con solapa + espalda + **manga de dos piezas** (mangón +
  soplillo, cuyas costuras casan).

Todo en tiempo real.

```bash
python -m patronaje.viewer --output output   # genera viewer.html y viewer_live.html
```

## Edición directa sobre el lienzo (arrastrar puntos)

Además de los sliders, la casilla **«Editar (arrastrar puntos)»** muestra
**manijas** (los puntos ámbar) sobre puntos reales del trazo: escote, hombro,
busto/pecho, cintura, cadera, largo… Al **arrastrar** una manija la medida
correspondiente cambia y el patrón se **recalcula al instante**; el slider se
sincroniza solo. Cada manija se mueve por su **eje** (guía discontinua): las de
ancho en X, las de largo en Y.

Es **manipulación directa manteniendo el método**: la manija no mueve un vértice
suelto (eso rompería el bloque), sino que su posición se **invierte a la medida**
que la genera (p. ej. arrastrar el costado de la sisa reescribe el busto vía
`(busto+holgura)/4`), y el bloque se vuelve a trazar entero desde los parámetros.
Así se acerca la experiencia a la de un CAD de patronaje sin perder la coherencia
paramétrica. Cada prenda expone sus manijas (camisa 5 —escote, hombro, busto,
bajo y largo de manga—, falda y pantalón 4 —cintura, cadera, altura de cadera y
largo—, vestido 3, blazer 1).

Al arrastrar, la manija activa **muestra el valor en vivo** (p. ej. «Busto: 92»).
**Deshacer** con el botón o **Ctrl+Z** revierte la última edición (también las de
los sliders y el restablecer); la pila guarda las últimas 60 interacciones.

## Cómo funciona

El núcleo geométrico está **portado a JavaScript** dentro del propio HTML:

- **Spline cúbica natural** (C2 ⇒ G2) con parametrización chordal y solve
  tridiagonal (Thomas) — copia fiel de `core/curves.NaturalCubicSpline`.
- **Fórmulas del bloque Aldrich** (escotes, sisas, hombros, canesú) — copia de
  `blocks/aldrich_bodice`.
- **Copa de manga** resuelta por **bisección** para que copa = sisa + holgura —
  copia de `blocks/aldrich_sleeve`.
- **Pinza** (`insertDart`) — copia de `blocks/fitted._insert_dart`.
- **Bloques de falda y pantalón** — copia de `blocks/skirt` y `blocks/trouser`.
- **Cuerpo entallado** (`fittedBodice`) — copia de `blocks/fitted` (pinza de busto
  en el costado, pinzas de cintura y de hombro).
- **Manga de dos piezas** (`twoPieceSleeve`, con `bow`) — copia de `blocks/blazer`
  (costuras de igual longitud por sagita de parábola).

Al no depender de shapely/numpy, el visor es **autocontenido** (un solo archivo,
sin CDN ni red) y funciona offline o incrustado en cualquier página.

## Fidelidad

El port es una capa de **presentación**; la fuente de verdad sigue siendo el
motor Python. Un test comprueba que las longitudes calculadas en JS coinciden con
las del motor Python (`tests/test_viewer.py`):

```
JS  S : escote=19.2641 sisa=38.8082 copa=39.8082
PY  S : escote=19.2641 sisa=38.8082 copa=39.8082   (Δ < 0.0002 cm)
```

El test que usa navegador (Chromium headless vía Playwright) se **omite
automáticamente** si no hay navegador disponible (p. ej. en CI), pero la
comprobación de que el HTML es autocontenido corre siempre.

## Medidas ajustables

Busto, holgura de busto, contorno de cuello, ancho de espalda, hombro, contorno
de brazo, muñeca, largo de camisa y largo de manga. Cada cambio regenera las
cuatro piezas y actualiza el indicador de casado |sisa − copa| (verde si ≤ 1.5 cm).
