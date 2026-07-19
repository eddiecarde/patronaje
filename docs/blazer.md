# Chaqueta / blazer (sastre)

El bloque más sofisticado del sistema. Reúne los elementos de sastrería que
faltaban, **por cada método** de patronaje (reutiliza el cuerpo entallado):

## Elementos sastre

- **Manga de dos piezas** (`blocks/blazer.TwoPieceSleeve`): mangón (superior,
  más ancho, copa alta) + soplillo (inferior, con scoop de axila). Las costuras
  delantera y trasera se construyen a la **misma longitud** (bombeo calculado con
  la sagita de una parábola), con **curvaturas opuestas** (mangón convexo,
  soplillo cóncavo), de modo que **casan** al coser y forman el codo.
- **Delantero con solapa** (notched lapel): línea de quiebre (roll line), solapa
  con pico y notch, extensión de botonadura. Las pinzas de busto y de cintura se
  modelan **interiores** (la de cintura como **ojo de pez**), sin cortar el bajo.
- **Cuello sastre**, **vista** (facing) que sigue la solapa, y **forro**
  (delantero = cuerpo menos la vista; espalda con **pliegue de holgura** en el CB).

## Uso

```bash
python -m patronaje.cli --garment blazer --size S
python -m patronaje.cli --garment blazer --method mueller --style cruzada
python -m patronaje.cli --garment blazer --style crop --all-sizes
```

Genera `blazer_<talla>[...]{dxf,svg,pdf,ai,json,csv,scr}` + marker. El tech pack
(específico de camisa) no se genera para el blazer.

## Piezas (8; 6 sin forro)

| Nº | Pieza              | Corte              |
|----|--------------------|--------------------|
| 1  | Chaqueta delantero | par: izq + der     |
| 2  | Chaqueta espalda   | al doblez (CB)     |
| 3  | Manga superior (mangón)  | par          |
| 4  | Manga inferior (soplillo)| par          |
| 5  | Cuello sastre      | par (+ entretela)  |
| 6  | Vista delantera    | par: izq + der     |
| 7  | Forro delantero    | par (forro)        |
| 8  | Forro espalda      | al doblez (forro)  |

## Casado

- **Costado** delantero↔espalda.
- **Costuras de la manga**: mangón↔soplillo, delantera y trasera (casan con
  Δ ≈ 0 por construcción de igual longitud).

## Métodos y estilos

Métodos (cuerpo por escuela): `aldrich`, `mueller`, `bunka`, `esmod`, `marti`,
`armstrong`.

| Estilo      | Efecto                                             |
|-------------|----------------------------------------------------|
| `clasica`   | una fila de botones, solapa con pico               |
| `crop`      | corto (recorta el cuerpo)                          |
| `longline`  | largo (alarga el cuerpo)                           |
| `cruzada`   | double-breasted: botonadura ancha + 2ª fila        |
| `un_boton`  | un solo botón (solapa larga)                       |
| `sin_forro` | desestructurado: elimina las piezas de forro       |
