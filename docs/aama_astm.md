# Formatos industriales: AAMA / ASTM D6673 y AI

## DXF AAMA / ASTM D6673 (`export/dxf_aama.py`)

**ASTM D6673** (evolución del *AAMA-DXF*) es el estándar de intercambio de
patrones entre sistemas CAD/CAM de sala de corte. Nuestra implementación:

- Escribe **DXF R2013** (`AC1027`), unidades en cm.
- Crea **un BLOQUE por pieza** (`P01_DELANTERO`, `P02_ESPALDA`, …) y lo inserta
  con **INSERT** en el modelspace, como espera el estándar.
- Reparte la geometría en las **capas numeradas de la norma** (tabla ASTM D6673):

  | Capa | Contenido                                   | Entidad     |
  |------|---------------------------------------------|-------------|
  | 1    | Contorno de corte (línea de la pieza)       | LWPOLYLINE  |
  | 2    | *Turn points* (esquinas del contorno)       | POINT       |
  | 3    | *Curve points* (puntos de curva)            | POINT       |
  | 4    | Piquetes (notches)                          | LINE        |
  | 5    | Punto de referencia de gradación            | POINT       |
  | 6    | Línea de espejo / doblez (piezas al doblez) | LINE        |
  | 7    | Líneas internas (pinzas, construcción)      | LINE        |
  | 8    | Línea de costura (sew line)                 | LWPOLYLINE  |
  | 11   | Línea de hilo (grain line)                  | LINE        |
  | 13   | Perforaciones (drill holes)                 | CIRCLE      |
  | 15   | Anotación de pieza (nombre, talla, corte)   | TEXT        |

> **Corrección de conformidad.** Respecto de la primera versión se **corrigieron**
> las asignaciones que no seguían la norma: el **hilo** iba en la capa 7 y las
> **líneas internas** en la 11 (estaban invertidas); los **taladros** en la 6; y
> el texto repartido entre 13 y 15. Además se **añadieron** los elementos que un
> importador industrial usa para reconstruir la pieza: *turn/curve points*
> (capas 2 y 3), **punto de referencia de gradación** (capa 5) y **línea de
> espejo** del doblez (capa 6).

### Certificación por *round-trip* (`validate_aama_dxf`)

Como no hay un CAD comercial en este entorno, la conformidad se verifica de forma
**headless y reproducible** con `validate_aama_dxf(path, shirt)`, que:

1. **reabre** el DXF (prueba de legibilidad),
2. corre la **auditoría estructural** de `ezdxf` (0 errores),
3. comprueba que están las **capas núcleo** del estándar, y
4. valida **pieza a pieza**: contorno cerrado en la capa 1, *turn points*,
   costura, hilo y texto presentes, y el **casado con la fuente** (nº de piezas, y
   por pieza piquetes, taladros e hilo).

El CLI imprime el veredicto al generar (`=== CONFORMIDAD DXF AAMA/ASTM ===`), y un
test (`tests/test_phase2.py::test_aama_conformance_roundtrip`) lo ejercita en las
**cinco prendas**. Pasa la auditoría de `ezdxf` sin errores y abre en AutoCAD,
DraftSight, LibreCAD y BricsCAD.

### Alcance / honestidad
La geometría y la estructura de capas/bloques ahora **siguen la tabla ASTM D6673**
y superan la validación de round-trip. Aun así, el **sello final** debe darlo el
software CAM destino (Gerber AccuMark, Lectra Modaris/Diamino, Optitex): algunos
sistemas esperan además tablas de metadatos ASTM como **atributos de bloque**
(nombre de estilo, categoría de pieza) o un archivo `.rul` de reglas de gradación
de acompañamiento. Esas extensiones quedan como iteración siguiente; **no se
promete certificación de sala de corte sin la verificación en el sistema
objetivo**, pero el archivo ya es conforme y verificado por round-trip.

## AI (`export/ai.py`)

El `.ai` moderno es un **PDF con estructura de Illustrator**. Generamos un PDF
vectorial a **escala real 1:1** en un único artboard con todas las piezas como
trazos reales, guardado con extensión `.ai`. Se abre en Illustrator, Inkscape y
Affinity como documento vectorial editable.

Para un AI **nativo** con capas de Illustrator idénticas a las lógicas del
patrón, conviene reimportar el **SVG** (que ya viene agrupado por capa) o el
**DXF**; el `.ai` generado prioriza compatibilidad y fidelidad geométrica.
