# Visor en vivo (motor paramétrico en el navegador)

`output/viewer_live.html` es un visor donde se **elige la prenda, se mueven las
medidas con sliders y el patrón se recalcula al instante**, sin servidor ni
dependencias. Cubre **camisa, falda y pantalón**:

- **Camisa**: delantero, espalda, canesú y manga + casado escote/sisa/copa.
- **Falda**: delantera y trasera con pinzas + cintura/cadera/largo.
- **Pantalón**: delantero y trasero con curva de tiro y pinzas + entrepierna.

Todo en tiempo real.

```bash
python -m patronaje.viewer --output output   # genera viewer.html y viewer_live.html
```

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
