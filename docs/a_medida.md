# Modo a medida (made-to-measure) y validación de medidas

Además de las tallas estándar (`XS…XXL`), el sistema puede trazar el patrón a
partir de un **juego de medidas personalizado** de una persona. El motor es el
mismo: sólo cambian los valores de entrada y todo el patrón se regenera.

## Uso

```bash
python -m patronaje.cli --measurements cliente.json --fit fitted --style empire
```

`--measurements` sustituye a `--size`. El nombre de talla (para rótulos y
archivos) sale del campo `nombre` del JSON o, si no existe, del nombre del
archivo.

## Formato del JSON

Admite dos formas equivalentes:

```json
{ "nombre": "ana",
  "medidas": {
    "busto": 90, "cintura": 68, "cadera": 96,
    "largo_camisa": 66, "largo_manga": 59,
    "contorno_cuello": 37, "ancho_espalda": 36.5,
    "hombro": 12.5, "contorno_brazo": 29, "muneca": 17 } }
```

o directamente el diccionario de medidas (`{ "busto": 90, ... }`), tomando el
nombre del archivo.

**Medidas requeridas:** `busto, cintura, cadera, largo_camisa, largo_manga,
contorno_cuello, ancho_espalda, hombro, contorno_brazo, muneca`.

**Secundarias (opcionales):** `talle_espalda` y `altura_cadera`; si faltan se
**estiman por proporción** respecto del busto (las usan los métodos
proporcionales como Müller).

## Validación de medidas

Antes de trazar, las medidas pasan por `parametric/validation.py`, que reporta:

- **Errores** (bloquean el trazado salvo `--force`):
  - medida requerida ausente, no numérica o no positiva,
  - muñeca ≥ contorno de brazo,
  - contorno de brazo ≥ busto,
  - escote resultante más ancho que media espalda (trazado degenerado).
- **Avisos** (sólo informan):
  - medida fuera del rango humano habitual,
  - clave desconocida (se ignora),
  - cintura mayor que el busto, cadera menor que la cintura, ancho de espalda
    ≥ medio busto.

Ejemplo de salida al abortar:

```
=== VALIDACIÓN DE MEDIDAS ===
  [!!] contorno_brazo: fuera de rango habitual [18-55]: 16
  [XX] muneca: la muñeca (18) no puede ser >= el brazo (16)
--- 1 error(es), 1 aviso(s) ---

[ABORTADO] Medidas incoherentes. Corrija el JSON o use --force.
```

## API

```python
from patronaje.parametric.validation import validate_measurements, has_errors
from patronaje.parametric.measurements import build_parameters_from_measurements
from patronaje.garment.sloper import build_sloper

medidas = {...}
issues = validate_measurements(medidas)
if not has_errors(issues):
    p = build_parameters_from_measurements(medidas, name="ana")
    sloper = build_sloper("ana", p=p).layout()   # cualquier método/estilo
```
