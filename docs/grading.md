# Grading (escalado) XS–XXL

## Principio: escalar por reglas paramétricas, no redibujar

El patrón es **paramétrico**: cada punto se calcula desde las medidas. Por eso
"gradar" es **regenerar** la prenda para cada talla con `build_shirt(size)` — no
se deforma ni se redibuja ninguna curva a mano. Esto cumple el requisito de
"escalar mediante reglas paramétricas".

Módulos: `grading/rules.py` (incrementos) y `grading/grader.py` (regeneración y
nido). La talla base de referencia es **S**.

## Regla de grading (incrementos entre tallas)

Saltos estándar de la industria, constantes en toda la escala:

| Medida | Incremento por talla |
|--------|----------------------|
| busto / cintura / cadera | 4.0 cm |
| largo_camisa | 2.0 cm |
| largo_manga | 1.5 cm |
| contorno_cuello | 1.0 cm |
| ancho_espalda | 1.5 cm |
| contorno_brazo | 1.5 cm |
| muñeca | 1.0 cm |
| hombro | 0.5 cm |

Los valores exactos por talla están en `SIZE_CHART`
(`patronaje/parametric/measurements.py`); `rules.increments()` los deriva y
`rules.delta_from_base(size)` da la diferencia acumulada respecto de S.

## Nido de grading

`grader.export_grade_nest(pieza, path)` superpone la línea de corte de una pieza
para todas las tallas, alineadas por un punto de referencia común, generando el
**nido** clásico (las curvas se abren proporcionalmente). Es la comprobación
visual de que el escalado es coherente. Se generan nidos de DELANTERO, ESPALDA y
MANGA.

## Uso

```bash
python -m patronaje.cli --all-sizes --output output
```

Genera `output/<talla>/` con los 9 formatos por talla y
`output/nido_grading_*.svg`. Una prueba (`tests/test_phase2.py`) verifica que el
área del delantero crece monótonamente XS→XXL.
