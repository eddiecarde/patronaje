# Tech Pack y Plano de Corte (Fase 3)

## Tech Pack (`techpack/`)

Ficha técnica **autocontenida en HTML** (SVG inline, sin recursos externos),
lista para abrir en el navegador e imprimir a PDF A4. Se genera con
`techpack.export_techpack(shirt, path)` e incluye todas las secciones pedidas:

1. **Planos técnicos** delantero y trasero (fashion flats paramétricos,
   `flats.garment_flat_svg`).
2. **Detalles de pieza**: cuello, pie de cuello, manga, puño, bolsillo
   (`flats.piece_detail_svg`).
3. **Tabla de medidas** del cuerpo.
4. **Medidas terminadas + tolerancia** (POM, `sequence.finished_measurements`).
5. **Piezas del patrón** (cantidad, tipo de corte, al doblez).
6. **BOM** — lista de materiales (`bom.build_bom`): tela, entretela, botones,
   ojales, hilo, etiquetas.
7. **Consumo de tela y desperdicio** por ancho.
8. **Secuencia de confección** (`sequence.SEWING_SEQUENCE`).
9. **Control de calidad** (`sequence.QC_CHECKLIST`).
10. **Tolerancias** (`sequence.TOLERANCES`).

Todo es paramétrico: al cambiar la talla, medidas, BOM, consumo y planos se
regeneran.

## Plano de corte / marker (`marker/layout.py`)

Coloca todas las piezas de tela sobre un ancho dado y calcula **largo de tela** y
**desperdicio**. Características:

- Respeta la **línea de hilo**: no rota piezas 90°, sólo las coloca en su
  orientación de corte (como un marker real).
- Piezas **al doblez** se cortan completas (se reflejan en el doblez → ancho
  doble); piezas en **par** generan 2 instancias (2ª espejada).
- Dos algoritmos: `nest` (estantes por *bounding box*, conservador, sin
  solapamiento) y `nest_skyline` (**encaje del perfil real del contorno**: las
  piezas caen sobre la silueta y encajan en las concavidades; prueba varias
  ordenaciones y elige el menor largo). El marker y el reporte usan `nest_skyline`.
- **Bundle**: `nest_skyline(..., copies=N)` tiende **varias prendas** en el mismo
  trazo; `marker_report` prueba bundles y reporta la mejor eficiencia.
- Anchos soportados: **110 / 150 / 160 cm** (configurable).

### Métricas (por ancho)
- **largo** de tela (m) y **compra recomendada** (+7 % de mermas de tendido).
- **eficiencia** (1 prenda) y **eficiencia_bundle** (varias prendas) = área de
  piezas / (ancho × largo); **desperdicio** = 1 − eficiencia.

### Alcance / honestidad
La eficiencia de **una sola prenda** es baja por naturaleza: sus pocas piezas no
llenan el ancho de tela (p. ej. dos paneles de falda de ~50 cm en 150 cm). Por eso
se reporta también el **bundle** (varias prendas), que es como se tiende en una
sala de corte real y sube mucho la eficiencia. Un sistema CAM (AccuMark, Diamino,
Optitex) con *no-fit polygon* y mezcla de tallas la mejora aún más.

## Uso

```bash
python -m patronaje.cli --size S --output output    # incluye tech pack + markers
```

Genera `camisa_S_tech_pack.html` y `camisa_S_marker_{110,150,160}.svg`, además de
los formatos CAD de Fases 1–2.
