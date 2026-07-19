# Visor 3D — maniquí a medida (Opción A)

`output/viewer_3d.html` muestra un **maniquí paramétrico** (dress form) construido
desde las medidas y la prenda como **cáscara** ajustada al cuerpo, coloreada por un
**mapa de ajuste** (holgura por zona). Se **gira con el ratón** y se recalcula al
mover las medidas — todo **autocontenido**, sin dependencias.

```bash
python -m patronaje.viewer3d --output output    # genera output/viewer_3d.html
# (también se genera al correr `python -m patronaje.viewer`)
```

## Dos modos

1. **Cáscara + mapa de ajuste** (por defecto): la prenda como superficie ajustada
   al cuerpo con su silueta y **holgura real**, para evaluar la **horma**. El mapa
   de ajuste colorea cada zona por la holgura: 🔴 tira (&lt;0), 🟠 ajustado (&lt;3 cm),
   🟢 cómodo, 🔵 holgado (&gt;11 cm).
2. **Caída (simulación)** — casilla *«Caída (sim)»*: la prenda pasa a ser una
   **malla de tela** que **cae por gravedad**, se sujeta por arriba (hombros o
   cintura) y **colisiona con el maniquí**, formando pliegues reales. Botón
   *«Re-drapear»* para volver a simular.

## Simulación de caída (Fase 2)

Un solver **PBD (Position-Based Dynamics)** en el navegador, sin dependencias:

- La prenda se malla como rejilla de partículas (anillos × segmentos).
- **Restricciones** de distancia: estructurales (anillo/columna), de **cizalla**
  (diagonales) y de **flexión** (salto de 2), que le dan comportamiento de tela.
- **Gravedad** + integración de Verlet + amortiguación; el anillo superior queda
  **fijo** (la prenda cuelga de ahí).
- **Colisión** con el maniquí: cada partícula se empuja fuera de la elipse del
  cuerpo a su altura (+ margen), así la tela se apoya y drapea sobre la figura.

Es una simulación de la prenda **ya montada** cayendo sobre el cuerpo; la Fase 3
sería coser las piezas planas por los **piquetes casados** antes de simular.

## Cómo funciona (sin dependencias)

- **Maniquí**: se construye por *loft* de **anillos elípticos** cuyo perímetro es la
  medida a cada nivel (cuello, busto, cintura, cadera) — con la relación
  ancho/fondo del cuerpo (Ramanujan para el perímetro de la elipse) — más cabeza,
  cuello y pedestal.
- **Prenda**: cáscara a *offset* del cuerpo por la holgura, con la silueta de cada
  tipo (torso + mangas para camisa/vestido/blazer; falda acampanada; dos piernas
  para el pantalón).
- **Render**: un pequeño **renderizador 3D por software** — proyección en
  perspectiva, sombreado *lambert* por cara y *painter's algorithm* (orden por
  profundidad) — dibuja sobre un `<canvas>`. La cámara **auto-encuadra** la figura.

## Medidas ajustables

Busto, holgura de busto, cintura, cadera, contorno de cuello, ancho de espalda,
altura de cadera, talle, estatura y largo de prenda. Cada cambio regenera el
maniquí y la prenda al instante, y actualiza el mapa de ajuste.
