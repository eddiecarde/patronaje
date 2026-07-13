# Formatos industriales: AAMA / ASTM D6673 y AI

## DXF AAMA / ASTM D6673 (`export/dxf_aama.py`)

**ASTM D6673** (evolución del *AAMA-DXF*) es el estándar de intercambio de
patrones entre sistemas CAD/CAM de sala de corte. Nuestra implementación:

- Escribe **DXF R2013** (`AC1027`), unidades en cm.
- Crea **un BLOQUE por pieza** (`P01_DELANTERO`, `P02_ESPALDA`, …) y lo inserta
  con **INSERT** en el modelspace, como espera el estándar.
- Reparte la geometría en **capas numeradas**:

  | Capa | Contenido                              |
  |------|----------------------------------------|
  | 1    | Contorno de corte (línea de la pieza)  |
  | 4    | Piquetes (notches)                     |
  | 6    | Perforaciones (drill holes)            |
  | 7    | Línea de hilo (grain reference)        |
  | 8    | Línea de costura interna / espejo      |
  | 11   | Líneas internas (dobleces/referencias) |
  | 13   | Anotación / nombre de pieza            |
  | 15   | Talla y cantidad                       |

Pasa la auditoría de `ezdxf` sin errores y abre en AutoCAD, DraftSight,
LibreCAD y BricsCAD.

### Alcance / honestidad (best-effort)
La geometría y la estructura de capas/bloques siguen la convención ASTM D6673,
pero **debe verificarse la importación en el software CAM destino** (Gerber
AccuMark, Lectra Modaris/Diamino, Optitex, CLO 3D, Browzwear). Algunos sistemas
esperan variantes específicas de *point codes* (turn point vs. curve point),
tablas de metadatos ASTM (nombre de estilo, categoría de pieza, cantidad como
atributos de bloque) o el archivo `.rul`/`.txt` de acompañamiento. Esas
extensiones se abordarán en una iteración dedicada con validación en el sistema
objetivo; **no se promete certificación de sala de corte sin esa verificación**.

## AI (`export/ai.py`)

El `.ai` moderno es un **PDF con estructura de Illustrator**. Generamos un PDF
vectorial a **escala real 1:1** en un único artboard con todas las piezas como
trazos reales, guardado con extensión `.ai`. Se abre en Illustrator, Inkscape y
Affinity como documento vectorial editable.

Para un AI **nativo** con capas de Illustrator idénticas a las lógicas del
patrón, conviene reimportar el **SVG** (que ya viene agrupado por capa) o el
**DXF**; el `.ai` generado prioriza compatibilidad y fidelidad geométrica.
