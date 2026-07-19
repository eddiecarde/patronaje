# Vestido base (con costura de talle)

El vestido **reutiliza dos bloques ya existentes** unidos en la línea de talle,
lo que le da **soporte multimétodo gratis**:

- **Cuerpo entallado** (`blocks/fitted`): pinza de busto (reubicable con
  `--bust-dart`), pinzas de cintura y de hombro, y **por cada método de
  patronaje** (Aldrich, Müller, Bunka, ESMOD, Martí, Armstrong).
- **Falda** (`blocks/skirt`): dos paneles con pinza y curva de cadera.

Ambas cinturas valen un cuarto de cintura, así que **casan en la costura de
talle** (la pequeña diferencia se reparte como holgura de montaje).

## Uso

```bash
python -m patronaje.cli --garment dress --size S
python -m patronaje.cli --garment dress --method mueller --bust-dart french
python -m patronaje.cli --garment dress --style evase --all-sizes
python -m patronaje.cli --garment dress --measurements cliente.json
```

Genera `vestido_<talla>[...]{dxf,svg,pdf,ai,json,csv,scr}` + marker. El tech pack
(específico de camisa) no se genera para el vestido.

## Piezas

| Nº | Pieza                      | Corte      | Notas                     |
|----|----------------------------|------------|---------------------------|
| 1  | Vestido delantero (talle)  | al doblez  | pinza de busto + cintura  |
| 2  | Vestido espalda (talle)    | al doblez  | pinza de hombro + cintura |
| 3  | Vestido falda delantera    | al doblez  | pinza, dobladillo         |
| 4  | Vestido falda trasera      | al doblez  | pinza, dobladillo         |
| 5  | Manga                      | par        | del método (opcional)     |

## Casado de talle

`add_dress_notches` compara el **ancho de cintura terminado** (con las pinzas
cerradas) del talle y de la falda, y coloca piquetes en las esquinas de talle
(CF/CB y costado). La costura casa dentro de una holgura de montaje (< 2 cm).

## Estilos (`transform/dress_styles.py`, `DRESS_STYLES`)

Actúan sobre la **falda** (vuelo desde la cadera, largo, godets) o la prenda (sin
mangas), **sin tocar la cintura**, de modo que la costura de talle sigue casando.

| Estilo        | Efecto                                          |
|---------------|-------------------------------------------------|
| `recto`       | falda tubo (silueta del bloque)                 |
| `evase`       | A-line (vuelo moderado)                          |
| `acampanada`  | falda amplia                                     |
| `sin_mangas`  | elimina la manga                                 |
| `mini`        | recorta la falda                                 |
| `maxi`        | alarga la falda con algo de vuelo                |
| `godet`       | godets triangulares en los costados             |
