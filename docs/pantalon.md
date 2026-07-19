# Pantalón base (mujer)

Segunda prenda de cuerpo inferior y el bloque más complejo del sistema: dos
paneles (delantero y trasero) con **curva de tiro** (entrepierna), **pinza de
cintura**, curva de cadera y pierna que afina hacia la boca. Confirma que el
motor paramétrico soporta geometría con gancho (fork) y costuras internas.

## Uso

```bash
python -m patronaje.cli --garment trouser --size S --output output
python -m patronaje.cli --garment trouser --all-sizes
python -m patronaje.cli --garment trouser --measurements cliente.json
```

Genera `pantalon_<talla>.{dxf,svg,pdf,ai,json,csv,scr}` + marker. El tech pack
(específico de camisa) no se genera para el pantalón.

## Construcción (Aldrich, best-effort)

Marco local por panel: `x = 0` en la línea central (CF/CB), `x` hacia el costado,
`y` hacia abajo desde la cintura (`y = 0`).

- **Líneas base**: cintura (`0`), cadera (`altura_cadera`), tiro
  (`tiro = cadera/4 + 4`), rodilla (~47 % de tiro→bajo) y bajo (`largo_pantalon`).
- **Cuartos**: `cuarto_cadera_pant = (cadera + holgura_cadera_pant)/4`,
  `cuarto_cintura_pant = (cintura + holgura_cintura_pant)/4`.
- **Gancho (fork)**: extensión del tiro más allá de la línea central; el
  **trasero es más profundo** (`0.45·cuarto_cadera`) que el delantero
  (`0.20·cuarto_cadera`).
- **Supresión** cintura–cadera repartida entre costado y **pinza** (una por
  panel; trasera mayor y más larga). Costura central trasera **inclinada** 2 cm
  (equilibrio del asiento).
- **Curvas**: costura central + tiro, entrepierna y costado se trazan con splines
  G2; la pierna se centra en la **raya** (grainline) y afina a rodilla/bajo.
- **Márgenes**: dobladillo real en la boca; costura estándar en el resto.

> *Best-effort*: las constantes siguen las proporciones de Aldrich; conviene
> verificar la horma en una prueba real (igual que el resto de métodos).

## Piezas

| Nº | Pieza               | Corte           | Notas                        |
|----|---------------------|-----------------|------------------------------|
| 1  | Pantalón delantero  | par: izq + der  | pinza, raya, dobladillo      |
| 2  | Pantalón trasero    | par: izq + der  | gancho profundo, pinza, raya |
| 3  | Pretina             | 1 (+ entretela) | se dobla a la mitad          |

## Casado de piquetes

- **Entrepierna** delantero↔trasero (del gancho a la boca interior).
- **Costado** delantero↔trasero (de la cintura al bajo).

Ambos se colocan a la misma fracción de arco y se validan por longitud de tramo
(entrepierna del/tra casan con Δ < 0.6 cm; costado con Δ < 0.3 cm).
