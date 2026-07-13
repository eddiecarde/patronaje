# Método Müller & Sohn — construcción del bloque

Referencia: *M. Müller & Sohn, Schnittkonstruktion für Damen*. Sistema alemán
**proporcional**: el bloque se deriva del contorno de busto (B = *Brustumfang*)
repartiendo la mitad del busto en tres secciones y calculando escotes/hombros
por divisiones de B/20. Implementado en `blocks/mueller_bodice.py` y
`blocks/mueller_sleeve.py`; produce el mismo `BodiceDraft`/`SleeveDraft` que el
resto del motor, por lo que valida y exporta igual que Aldrich.

## Fórmulas (talla S, B = 88, holgura 8)

| Concepto | Fórmula | Valor S |
|----------|---------|---------|
| Profundidad de sisa (Armlochtiefe) | `B/10 + 12.0` | 20.8 |
| Costado / cuarto | `(B + holgura)/4` | 24.0 |
| Ancho de espalda (Rückenbreite) | `B/8 + 5.5` | 16.5 |
| Ancho de pecho (Brustbreite) | `B/8 + 6.5` | 17.5 |
| Escote espalda ancho | `B/20 + 2.5` | 6.9 |
| Escote delantero ancho | `B/20 + 2.0` | 6.4 |
| Escote delantero profundidad | `B/20 + 3.5` | 7.9 |
| Subida escote espalda | `2.0` | 2.0 |
| Caída de hombro (esp./del.) | `4.5 / 5.0` | 4.5 / 5.0 |

- **Líneas horizontales**: escote (y=0), pecho/sisa (`0.5–0.55 × prof_sisa`),
  axila (`prof_sisa`), dobladillo (`largo_camisa`). El talle de espalda
  (`talle_espalda`, Rückenlänge) sitúa la cintura de referencia.
- **Hombro**: largo = `hombro`; el punto de hombro se obtiene avanzando
  `√(hombro² − caída²)` desde el punto de cuello lateral.
- **Sisa**: spline G2 por hombro → Rückenbreite/Brustbreite → axila.
- **Manga** (`mueller_sleeve.py`): copa más alta que la camisa plana
  (`cap_ratio ≈ 0.58 × prof_sisa`), con el ancho de bíceps resuelto por
  bisección para casar `copa = sisa + holgura` (mismo criterio que el motor
  general). Si el bíceps no cubre el brazo, la altura de copa se reduce.

## Diferencias observadas frente a Aldrich (talla S)

| Magnitud | Aldrich | Müller |
|----------|---------|--------|
| Escote (½) | 19.3 cm | 17.6 cm |
| Sisa | 38.8 cm | 37.3 cm |
| Prof. de sisa | 22.0 cm | 20.8 cm |

Müller da un escote algo más alto/cerrado y una sisa más superficial y estrecha
(ancho de espalda/pecho proporcionales). Ambos bloques son válidos y casan
internamente (sisa=copa, cuello=escote, etc.).

## Medidas adicionales
Müller requiere `talle_espalda` (Rückenlänge) y `altura_cadera`, ya incluidas en
`SIZE_CHART` para todas las tallas.
