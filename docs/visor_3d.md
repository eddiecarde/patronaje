# Visor 3D — maniquí a medida (Opción A)

`output/viewer_3d.html` muestra un **maniquí paramétrico** (dress form) construido
desde las medidas y la prenda como **cáscara** ajustada al cuerpo, coloreada por un
**mapa de ajuste** (holgura por zona). Se **gira con el ratón** y se recalcula al
mover las medidas — todo **autocontenido**, sin dependencias.

```bash
python -m patronaje.viewer3d --output output    # genera output/viewer_3d.html
# (también se genera al correr `python -m patronaje.viewer`)
```

## Qué es (y qué no)

- **Es**: un maniquí a medida + la prenda "puesta" como superficie con su silueta y
  su **holgura real**, para evaluar la **horma** y las proporciones. El mapa de
  ajuste colorea cada zona por la holgura: 🔴 tira (&lt;0), 🟠 ajustado (&lt;3 cm),
  🟢 cómodo, 🔵 holgado (&gt;11 cm).
- **No es** (todavía): simulación de **caída** de la tela. Eso es la Fase 2 (mallar
  las piezas, coserlas por los piquetes casados y simular la caída con colisión).

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
