# Falda base (recta / lápiz)

Primera prenda distinta de la camisa: demuestra que el motor paramétrico
generaliza a otros bloques reutilizando la misma infraestructura (piezas
neutras, validación, márgenes por borde, exportadores, marker).

## Uso

```bash
python -m patronaje.cli --garment skirt --size S --output output
python -m patronaje.cli --garment skirt --all-sizes                 # grada XS..XXL
python -m patronaje.cli --garment skirt --measurements cliente.json # a medida
```

Genera `falda_<talla>.{dxf,svg,pdf,ai,json,csv,scr}` + marker por ancho de tela.
El tech pack HTML es específico de la camisa y no se genera para la falda.

## Construcción (Aldrich, dos paneles)

Marco local: `x` hacia el costado (CF/CB en `x = 0`), `y` hacia abajo
(cintura `y = 0` → bajo).

- **Líneas base**: cintura (`y = 0`), cadera (`y = altura_cadera`), bajo
  (`y = largo_falda`).
- **Cuartos**: `cuarto_cadera = (cadera + holgura_cadera)/4`,
  `cuarto_cintura_falda = (cintura + holgura_cintura_falda)/4`.
- **Supresión** por panel = `cuarto_cadera − cuarto_cintura_falda`, repartida
  entre **costado** y **pinza de cintura**:
  `side_supp = supresión − pinza` (la pinza toma su intake nominal, el costado
  absorbe el resto). El delantero lleva menos intake y pinza más corta; el
  trasero, más intake y pinza más larga (apunta más abajo).
- **Costado**: curva suave de la cintura a la cadera (spline G2) y recto de la
  cadera al bajo (silueta lápiz).
- Ambos paneles van **al doblez** (CF/CB); el **bajo** lleva margen de
  dobladillo (`margen_dobladillo`) y el resto de bordes, margen de costura.

## Piezas

| Nº | Pieza            | Corte        | Notas                                  |
|----|------------------|--------------|----------------------------------------|
| 1  | Falda delantera  | al doblez    | 1 pinza de cintura, dobladillo          |
| 2  | Falda trasera    | al doblez    | 1 pinza (más larga), piquete de cadera  |
| 3  | Pretina          | 1 (+ entretela) | se dobla a la mitad, botón + ojal    |

## Parámetros nuevos

Medidas/constantes en `parametric/measurements.py`:
`holgura_cadera`, `holgura_cintura_falda`, `largo_falda`, `ancho_pretina`,
`pinza_cint_del`, `pinza_cint_tra`, `largo_pinza_del`, `largo_pinza_tra`, y los
derivados `cuarto_cadera`, `cuarto_cintura_falda`.

## Casado

- `waist_length()` = `cintura + holgura_cintura_falda` (largo de la pretina base).
- `hip_length()` = `cadera + holgura_cadera`.
- Piquete de cadera en el costado trasero para casar delantero↔trasero.
