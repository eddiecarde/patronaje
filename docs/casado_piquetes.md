# Casado automático de piquetes

Dos bordes que se cosen juntos (costado delantero↔trasero, hombro↔canesú,
costado de la falda…) deben **casar en longitud**. Si se colocan piquetes a la
**misma fracción de longitud de arco** desde el extremo homólogo de cada borde,
ambos piquetes caen en puntos que se unen físicamente al coser: el operario
alinea los piquetes y la costura queda equilibrada, sin fruncidos ni desfases.

## Cómo funciona (`garment/notches.py`)

1. `seam_subpath(contorno, a, b)` extrae el sub-tramo del contorno de una pieza
   entre los vértices más cercanos a `a` y `b` (elige el camino corto por
   defecto; el polígono cerrado ofrece dos).
2. `match_seam(pieceA, a0,a1, pieceB, b0,b1, fractions=…)` extrae ambos tramos
   (con `a0` casando con `b0`), coloca un piquete a cada `fraction` de arco en
   **las dos piezas**, y devuelve las longitudes de tramo para verificar el
   casado.

Es **independiente de la prenda**: se le pasan las piezas y los extremos de la
costura. Cada prenda declara sus costuras principales:

- **Camisa** (`add_shirt_notches`): costado delantero↔espalda (2 piquetes),
  hombro delantero↔canesú (1 piquete). *En la camisa el hombro trasero va en el
  canesú/yoke, no en la espalda inferior.*
- **Falda** (`add_skirt_notches`): costado delantero↔trasero (1 piquete, de la
  cadera al bajo).

El resultado se guarda en `garment.seam_matching` como
`[(nombre, largo_A, largo_B), …]`.

## Validación

`validation.validators.validate_notch_matching(garment, report, tol=0.8)`
comprueba que cada costura casada tenga tramos de longitud igual (±tol). Como los
piquetes se colocan a la misma fracción de arco, tramos iguales ⇒ piquetes
coincidentes. Se incluye en `validate_all` (camisa) y en la validación de la
falda. Ejemplo de reporte:

```
[OK ] casado costado del/esp: tramos 46.0 vs 46.0 cm  [valor=0.000, tol=0.800]
[OK ] casado hombro del/canesú: tramos 12.5 vs 12.5 cm  [valor=0.000, tol=0.800]
```

## Extensión

Para casar una costura nueva basta con llamar a `match_seam` con los extremos
(en coordenadas del marco local de cada pieza) y añadir el resultado al reporte
de la prenda.
