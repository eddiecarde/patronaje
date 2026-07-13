# Método Aldrich — construcción del bloque de camisa

Referencia: Winifred Aldrich, *Metric Pattern Cutting for Women's Wear*. Se
adapta el bloque de cuerpo y de manga a una **camisa básica semi-entallada** con
holgura de busto de 8 cm. Todo se construye por coordenadas `(x, y)` en el marco
de patronaje (`x` al costado, `y` hacia abajo). Cada punto tiene ID (ver
`aldrich_bodice.py`).

## 1. Bloque de cuerpo

### Rectángulo base
- **Profundidad de sisa** (línea de pecho): `prof_sisa = busto/8 + 10.5 + ease_sisa`.
  Determina la altura de la axila.
- **Cuarto de busto** por panel: `cuarto_busto = (busto + holgura)/4`. Fija el
  costado (delantero y espalda comparten la misma `x` de costado ⇒ los costados
  casan en longitud y el contorno cierra a `busto + holgura`).

### Espalda (al doblez en el centro de espalda, `x = 0`)
- **Escote:** ancho `escote_esp_ancho = cuello/5 − 0.3`; el centro de espalda
  (nuca) baja `subida_escote_esp = 2.0` respecto del punto de cuello lateral
  (SNP). La curva sube suavemente de CB a SNP (spline G2).
- **Hombro:** desde SNP se baja `caida_hombro_esp = 4.5` y se avanza
  `√(hombro² − caída²)` en horizontal → punto de hombro (SP). Así el **largo de
  hombro = `hombro`** exacto.
- **Ancho de espalda:** punto a `medio_espalda = ancho_espalda/2` sobre la línea
  de espalda (`0.55 × prof_sisa`). La **sisa** es una spline G2 que pasa por
  SP → ancho de espalda → axila (curvatura continua, apta CNC).
- **Línea de canesú:** horizontal a `linea_canesu = 10` desde la línea superior;
  separa el canesú (arriba) de la espalda (abajo).

### Delantero (centro delantero en `x = 0`; la botonadura se añade como extensión)
- **Escote más profundo:** ancho `escote_del_ancho = cuello/5 − 0.5`, profundidad
  `escote_del_prof = cuello/5 + 2.0`. Scoop delantero por spline G2.
- **Hombro:** `caida_hombro_del = 5.0`, largo de hombro = `hombro` (casa con la
  espalda).
- **Ancho de pecho:** `medio_espalda − 1.5` (pecho algo más estrecho que espalda)
  sobre `0.60 × prof_sisa`. **Sisa** delantera por spline G2 SP → pecho → axila.
- **Extensión de botonadura:** banda de `extension_boton = 1.7` a cada lado del CF;
  el CF (`x = 0`) queda como línea de referencia con botones y ojales.

## 2. Bloque de manga (una pieza)

La manga es simétrica respecto de su línea central (línea de hilo). El principio
industrial es **longitud de copa = longitud de sisa ± tolerancia**.

- **Altura de copa** por regla proporcional: `cap_height ≈ 0.45 × prof_sisa`
  (copa relativamente plana, propia de camisa). Se reduce si hiciera falta.
- **Ancho de bíceps** resuelto por **bisección** hasta que la longitud de la
  curva de copa iguale `sisa + sleeve_ease`. Resulta `biceps ≈ contorno_brazo +
  3 cm` de holgura, garantizando ajuste del brazo **y** casado con la sisa.
- **Copa:** dos ramas spline (delantera más plana, trasera más llena) con el
  "scoop" de axila; muestreadas para CNC.
- **Boca de manga:** `boca_manga = muneca + holgura_muneca`; se reduce a
  `largo_puno` mediante pliegues (`boca_manga − largo_puno`).

## 3. Piezas derivadas
- **Canesú y espalda** salen del bloque de cuerpo separados por la línea de
  canesú; sus bordes casan en anchura.
- **Cuello y pie de cuello** se dimensionan a la **longitud de escote** medida
  (curva), de modo que casan con el escote.
- **Puño** de largo `largo_puno`; **tapeta** de manga; **vista** delantera
  siguiendo escote y borde de botonadura; **bolsillo** de parche opcional.

## 4. Por qué casa todo
Las longitudes críticas (sisa, escote, boca de manga) se **miden sobre las
curvas reales** y se usan para dimensionar las piezas que se cosen a ellas. Por
eso la manga, el cuello y el puño se regeneran para seguir casando ante
cualquier cambio de medida. Las comprobaciones están en
`patronaje/validation/validators.py`.
