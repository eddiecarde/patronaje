# Visor 3D — maniquí a medida (WebGL / PBR)

`output/viewer_3d.html` muestra un **maniquí de sastre (dress form) paramétrico
de cuerpo entero** renderizado con **WebGL** (Three.js), al estilo de una horma
profesional de atelier: **torso cerrado y suave** (cuello → hombros → busto →
cintura → cadera), **brazos** con mano redondeada que cuelgan a los costados,
**piernas** completas hasta el tobillo (sin pies) que emergen de la pelvis, y
**líneas de costura marcadas** (centro delantero/trasero, princesa, línea de
busto/pecho, cintura, hombro, costura de brazo y de pierna) dibujadas en
discontinuo sobre la lona. Remata con **pomo negro** sobre **poste** metálico y
**base rodante de 5 patas** negra. Hay maniquí de **Mujer** y de **Hombre**
(selector *«Cuerpo»*), con siluetas distintas (mujer en reloj de arena; hombre de
hombros anchos y torso recto) y **medidas por defecto** propias de cada uno.

A diferencia de la versión anterior (renderizador por software, aspecto
facetado), ahora se usan **materiales PBR** (lino/lona para el cuerpo, metal para
el poste, negro satinado para el pedestal), **iluminación de estudio** (luz clave
con sombra + relleno + contra) y **sombras suaves** proyectadas sobre el suelo,
con *tone mapping* ACES y salida sRGB. El resultado se acerca al aspecto de la
foto de referencia.

Todo es **autocontenido y sin red**: la librería Three.js va **incrustada** en el
propio HTML (no se descarga de ningún CDN), así que el visor funciona abriendo el
archivo, sin servidor ni conexión.

```bash
python -m patronaje.viewer3d --output output    # genera output/viewer_3d.html
# (también se genera al correr `python -m patronaje.viewer`)
```

## Dos modos

1. **Cáscara + mapa de ajuste** (por defecto): la prenda como superficie ajustada
   al cuerpo con su silueta y **holgura real**, para evaluar la **horma**. El mapa
   de ajuste colorea cada zona por la holgura: 🔴 tira (&lt;0), 🟠 ajustado (&lt;3 cm),
   🟢 cómodo, 🔵 holgado (&gt;11 cm). La casilla *«Ver prenda»* la muestra/oculta
   (para ver el maniquí desnudo).
2. **Caída (simulación)** — casilla *«Caída (sim)»*: la prenda pasa a ser una
   **malla de tela** que **cae por gravedad**, se sujeta por arriba (hombros o
   cintura) y **colisiona con el maniquí**, formando pliegues reales que se
   renderizan como tejido PBR. Botón *«Re-drapear»* para volver a simular.

## Cómo se construye

- **Figura**: se *loftea* una pila de **anillos elípticos** cuyo perímetro
  reproduce cada medida a su altura (cuello, busto, cintura, cadera) —con la
  relación ancho/fondo del cuerpo (Ramanujan para el perímetro de la elipse)— y
  se **cierra** por arriba (cúpula sobre el cuello) y por abajo (fondo
  redondeado). Los anillos se convierten en una **malla indexada** de Three.js con
  **normales promediadas** (`computeVertexNormals`), de ahí el aspecto suave. En
  el **hombro** se interpolan anillos intermedios con suavizado coseno (pendiente
  0 en los extremos) entre el trapecio del cuello, la línea de hombro y el pecho,
  de modo que la transición de anchura queda **redondeada** en vez de formar una
  arista/cresta marcada.
- **Brazos y piernas**: cápsulas cónicas (perímetro de brazo/muñeca y de cadera)
  cerradas en ambos extremos con un domo hacia el centroide del anillo (`capEnd`,
  válido para extremos fuera del eje) — mano y tobillo redondeados; el extremo
  superior queda hundido en el hombro/pelvis para que la unión no muestre bocas
  abiertas.
- **Costuras**: `LineSegments` con material discontinuo (`LineDashedMaterial`),
  siguiendo los anillos del cuerpo (verticales de centro/princesa/costado y
  horizontales de busto y cintura) y una costura por brazo y por pierna,
  desplazadas ligeramente hacia afuera para que se vean sobre la superficie.
- **Materiales (PBR)**: `MeshStandardMaterial` — cuerpo lino (rugosidad alta, sin
  metalicidad), poste metálico, pomo/pedestal negros. La prenda usa **colores por
  vértice** (el mapa de ajuste) sobre material semitransparente.
- **Luz y sombra**: hemisférica + 3 direccionales (clave/relleno/contra); la clave
  proyecta **sombra** (PCF suave) sobre un suelo de estudio. Cámara en órbita:
  arrastra para girar, rueda para acercar.
- **Prenda**: cáscara a *offset* del cuerpo por la holgura, siguiendo la silueta de
  cada tipo (torso para camisa/vestido/blazer; falda acampanada; dos perneras para
  el pantalón). Se muestra sin mangas sobre la horma, como en un atelier.

## Simulación de caída (PBD)

Un solver **PBD (Position-Based Dynamics)** en el navegador, sin dependencias:

- La prenda se malla como rejilla de partículas (anillos × segmentos).
- **Restricciones** de distancia: estructurales (anillo/columna), de **cizalla**
  (diagonales) y de **flexión** (salto de 2), que le dan comportamiento de tela.
- **Gravedad** + integración de Verlet + amortiguación; el anillo superior queda
  **fijo** (la prenda cuelga de ahí).
- **Colisión** con el maniquí: el **torso** empuja cada partícula fuera de su
  elipse a esa altura; las **piernas** (colisionadores cápsula, aunque no se
  dibujen en la horma) empujan al pantalón para que caiga como dos perneras.
- Cada paso reescribe las posiciones del `BufferGeometry` de la tela y recomputa
  normales, de modo que los pliegues se ven con sombreado PBR.

## Medidas ajustables

Busto, holgura de busto, cintura, cadera, contorno de cuello, ancho de espalda,
contorno de brazo, muñeca, altura de cadera, talle, estatura y largo de prenda.
Cada cambio regenera el maniquí y la prenda al instante, y actualiza el mapa de
ajuste.

## Por qué Three.js incrustado

Para alcanzar el aspecto fotográfico (PBR + sombras) hace falta un motor WebGL.
En lugar de cargarlo desde un CDN (lo que rompería el funcionamiento offline), la
librería se **vendoriza** en `patronaje/assets/three.min.js` y el generador la
**incrusta** en el HTML. Así el visor sigue siendo **un único archivo** que
funciona sin red — la restricción de "sin dependencias externas de red" se
mantiene, aunque el peso del archivo suba (~680 KB).
