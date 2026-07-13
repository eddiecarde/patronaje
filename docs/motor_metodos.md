# Motor multi-método: diseño de la capa de patronaje

## Idea central

El **motor de geometría** (`patronaje/core/`) y **todo lo que va después** —
modelo de pieza, validaciones, exportadores (DXF/SVG/PDF/AI/JSON/CSV/SCR),
grading, marker y tech pack— son **agnósticos del método de patronaje**. Son
matemática pura (CAGD) y lógica de producción reutilizable.

Lo único que cambia entre **Aldrich**, **Müller & Sohn**, **ESMOD** o **Bunka**
es la **capa de trazo del bloque**: las fórmulas y la secuencia de construcción
del cuerpo y de la manga. Por eso NO se reescribe el motor: se **abstrae la capa
de método**.

```
Parámetros ─▶ [DraftingMethod] ─▶ BodiceDraft / SleeveDraft ─▶ Piezas
                aldrich | mueller |                              │
                esmod   | bunka                                  ▼
                                     validación · export · grading · marker · tech pack
                                     (SE REUTILIZA SIN CAMBIOS)
```

## Interfaz `DraftingMethod` (`blocks/base.py`)

Contrato que cumple cada método:

| Miembro | Rol |
|---------|-----|
| `name`, `label`, `source`, `available` | identidad y estado del método |
| `required_measurements() -> set[str]` | qué medidas del cuerpo necesita |
| `build_bodice(p) -> BodiceDraft` | traza cuerpo (delantero + espalda) |
| `build_sleeve(p, sisa_len, ease) -> SleeveDraft` | traza manga casando copa = sisa |
| `check_measurements(p)` | valida que estén las medidas necesarias |

Los métodos devuelven los mismos `BodiceDraft`/`SleeveDraft` que el ensamble
(`garment/shirt.py`) ya sabe consumir: por eso las piezas resultantes son
intercambiables y **pasan las mismas validaciones de casado** (sisa=copa,
costados, hombros, cuello=escote, canesú=espalda, puño=boca).

## Registro y selección (`blocks/registry.py`)

```python
from patronaje.garment.shirt import build_shirt
sh = build_shirt("S", method="aldrich")   # método por defecto
build_shirt("S", method="mueller")         # -> NotImplementedError (planificado)
```

`list_methods()` enumera métodos y su estado (disponible / planificado) para
CLI/UX. Añadir un método = escribir su clase y registrarla; nada más cambia.

## Estado actual

| Método | Estado | Implementación |
|--------|--------|----------------|
| **Aldrich** | ✅ disponible | `blocks/aldrich_method.py` (referencia) |
| **Müller & Sohn** | 🟡 planificado | `blocks/mueller_method.py` (fórmulas documentadas) |
| **ESMOD** | ⬜ por diseñar | — |
| **Bunka** | ⬜ por diseñar | — |

## Diferencias de método a capturar (fidelidad, no cosmética)

| Método | Filosofía | Fórmulas núcleo (ejemplos) |
|--------|-----------|-----------------------------|
| **Aldrich** | Medidas + constantes de tabla | prof. sisa `= busto/8 + 10.5 + ease`; escote esp. `= cuello/5 − 0.3` |
| **Müller & Sohn** | Proporcional (Brustumfang + Rückenlänge), *Hilfslinien* | prof. sisa `= busto/10 + 10.5`; ancho espalda `= busto/8 + 5.5`; pinza de busto por dif. busto–cintura |
| **ESMOD** | Bloque con pinza de busto, balance por medidas directas | escote y pinzas por medidas reales; más medidas de entrada |
| **Bunka (文化式)** | 100 % proporcional desde el busto (B) | prof. sisa `= B/12 + 13.7`; escote del. `= B/24 + 3.4`; pinza busto `≈ (B/4 − 2.5)°` |

Los métodos proporcionales (Müller, Bunka) son los más directos de parametrizar;
ESMOD requiere medidas directas adicionales que se añadirían a `SIZE_CHART`.

## Toolkit compartido (ya disponible)

Todos los métodos se apoyan en el mismo instrumental de `core/`:

- **Escuadrado / líneas de construcción** y punto a distancia/ángulo
  (`geometry.point_at_distance`, `point_at_angle`, `line_intersection`).
- **Curvas G2** por spline natural (`curves.smooth_curve`) para escotes, sisas y
  copa; **Bézier** y **arcos tangentes** para uniones.
- **Offset** de costura y **validación topológica** (shapely) en la capa de pieza.
- **Casado copa = sisa** por bisección (patrón reutilizable en cualquier manga).

## Cómo añadir un método (receta)

1. Crear `blocks/<metodo>_method.py` con una clase `XxxMethod(DraftingMethod)`.
2. Implementar `required_measurements`, `build_bodice`, `build_sleeve` usando el
   toolkit de `core/` y, si hace falta, añadir medidas a `SIZE_CHART`.
3. Registrarla en `blocks/registry.py`.
4. Documentar fórmulas en `docs/` (como `metodo_aldrich.md`).
5. Las validaciones, exportadores, grading, marker y tech pack funcionan sin
   tocar nada.

## Próximo paso sugerido
Implementar **Müller & Sohn** siguiendo el plan de fórmulas de
`blocks/mueller_method.py` (añadir `talle_espalda` y `altura_cadera` a las
medidas), y comparar su bloque con el de Aldrich sobre las mismas medidas.
