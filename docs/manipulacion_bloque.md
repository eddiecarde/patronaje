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
