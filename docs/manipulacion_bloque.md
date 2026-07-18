# Manipulación de bloque (estilos)

Además de trazar bloques con distintos **métodos**, el sistema genera **estilos**
a partir de un bloque base mediante las técnicas clásicas de manipulación de
patronaje, implementadas como operaciones geométricas en `patronaje/transform/`.

## Técnicas (operaciones)

`transform/operations.py`:

- **`pivot`** — traslado de pinza / apertura: rota una parte de la pieza
  alrededor de un punto (primitivo del *dart manipulation*).
- **`flare`** — vuelo A-line: separa la anchura crecientemente con la
  profundidad (límite continuo del *slash-and-spread*); el centro (doblez/CF)
  queda recto y sólo se abre el costado.
- **`widen`** — escala la anchura respecto de un eje (frunces/volumen).
- **`lift`** — levanta la copa de la manga (para cabeza abullonada).

## Estilos incluidos

`transform/styles.py` (aplicables con `apply_style(shirt, style)`):

| Estilo | Efecto | Operación |
|--------|--------|-----------|
| `flare` | Camisa acampanada / **túnica A-line** (vuelo en delantero y espalda) | `flare` |
| `puff` | **Manga abullonada** (volumen + copa levantada; cabeza fruncida) | `widen` + `lift` |
| `bell` | **Manga campana** (vuelo simétrico del codo a la boca de manga) | `flare_symmetric` |
| `mandarin` | **Cuello mao** (elimina la hoja; sólo banda más alta) | intercambio de pieza |
| `sleeveless` | **Sin mangas** (elimina manga/puño/tapeta; sisa con vista/bies) | eliminación de pieza |
| `crop` | **Crop** (recorta el largo de delantero/espalda/vista) | `clip_below` |
| `princess` | **Costura princesa** (parte el delantero en centro + costado) | `split_panel` |
| `short_sleeve` | **Manga corta** (recorta manga; sin puño/tapeta) | `clip_below` |
| `cap_sleeve` | **Manga cap** (muy corta sobre el hombro) | `clip_below` |
| `dress` | **Camisa-vestido** (alarga + vuelo) | `lengthen` + `flare` |
| `oversized` | **Corte holgado/oversize** (ensancha cuerpo y manga) | `widen` |
| `empire` | **Corte imperio** (talle + falda con vuelo) | `clip_below/above` + `flare` |
| `v_neck` | **Escote en V** (remodela escote; sin cuello) | remodelado de escote |
| `boat_neck` | **Escote barco** (ancho y poco profundo; sin cuello) | remodelado de escote |
| `hi_lo` | **Dobladillo asimétrico** (delantero corto, espalda largo) | `clip_below` |
| `cocoon` | **Dobladillo entallado** (estrecha la base) | `flare` (ratio negativo) |
| `peplum` | **Peplum** (talle + volante acampanado corto) | `clip` + `flare` |

**17 estilos** en total. `STYLES` en `styles.py` es el registro; añadir uno = una
función más. Primitivas: `pivot`, `flare`, `flare_symmetric`, `widen`, `lift`,
`lengthen`, `clip_below/clip_above`, `insert_on_contour`, `split_panel`, `dedup`.

## Uso

```bash
python -m patronaje.cli --size S --style flare --output output   # túnica A-line
python -m patronaje.cli --size S --style puff  --output output   # manga abullonada
```

Los archivos llevan sufijo de estilo (`camisa_S_flare.*`). Se puede combinar con
método: `--method mueller --style flare`.

## Validación
Los estilos que **fruncen** (p. ej. la manga abullonada) rompen a propósito el
casado `sisa = copa` (la cabeza se monta con frunce), por lo que en variantes de
estilo se validan sólo las comprobaciones **geométricas** (polígono cerrado,
simple, sin duplicados ni autointersección). El vuelo (`flare`) mantiene el
casado y pasa la validación completa.

## Extensión
Añadir un estilo = una función en `styles.py` que combine las operaciones y
reemplace los contornos de las piezas afectadas. Todo lo demás (exportadores,
tech pack, marker) se reutiliza. Próximos candidatos: costura princesa (traslado
de pinza a costura), manga campana, cuello mao, capucha.
