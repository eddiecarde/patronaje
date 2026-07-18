# Bloque base entallado: pinzas y equilibrio

Además del bloque de camisa (holgado, sin pinza), el sistema genera el **bloque
base entallado (sloper)**, que modela el cuerpo con **pinzas** y **equilibrio**,
por cada escuela/método. Implementado en `blocks/fitted.py` y ensamblado como
prenda en `garment/sloper.py`.

## Qué modela

- **Punto de busto (BP)**: referencia hacia donde apuntan las pinzas; su posición
  (semidistancia entre bustos) depende del método.
- **Pinza de busto**: da forma sobre el pecho. Se puede **trasladar** a distintas
  posiciones (traslado de pinza): `side`, `shoulder`, `neck`, `armhole`,
  `french`, `waist` — todas apuntan al BP y producen la misma prenda.
- **Pinzas de cintura** (delantera y trasera): suprimen la diferencia
  busto–cintura para entallar.
- **Pinza de hombro** (omóplato) en la espalda.
- **Costado entallado**: el costado entra en la cintura.
- **Equilibrio (balance)**: la pinza de busto añade largo al delantero de modo
  que, al cerrarla, el costado delantero casa con el trasero. El escote y la
  sisa provienen del método (cada escuela conserva su carácter).

Reparto de la supresión de cintura = `(busto+holgura)/4 − (cintura+ease)/4`,
distribuida entre el costado y las pinzas de cintura.

## Parámetros de pinza por método (`dart_spec`)

Cada método define su `DartSpec` (intake de pinza de busto, pinzas de cintura,
pinza de hombro, posición del BP, holgura de cintura). Ejemplos (talla S):

| Método | Pinza busto | BP (x) | Holgura cintura |
|--------|------------|--------|-----------------|
| Aldrich | 3.0 | busto/10+0.5 | 4.0 |
| Müller & Sohn | 3.5 | busto/10+1.0 | 3.0 |
| Bunka | 4.0 | busto/12+2.5 | 4.0 |
| ESMOD | 3.2 | busto/10 | 4.0 |
| Sistema Martí | 3.0 | busto/10+0.5 | 5.0 |
| Joseph-Armstrong | 2.5 | busto/10+0.5 | 4.0 |

## Uso

```bash
python -m patronaje.cli --size S --fit fitted --output output
python -m patronaje.cli --size S --fit fitted --bust-dart shoulder --method bunka --output output
```

Genera el sloper (delantero + espalda con pinzas + manga) con exportación CAD
completa; las pinzas se dibujan como patas (capa CONSTRUCCION) y vértice
(perforación en CENTROS). Combinable con los 6 métodos.

## Representación de la pinza
La pinza se materializa como una **muesca en V** en el contorno neto (patas +
vértice); al coser, la V se cierra y la tela se pliega. `Piece.darts` guarda
`(base1, apex, base2)` para dibujar las patas y la perforación del vértice.

## Validación
- Geometría: polígonos cerrados, simples, sin duplicados (todas las posiciones
  de pinza y las 6 tallas).
- Supresión de cintura = diferencia busto–cintura por panel (comprobado en tests).
- Equilibrio: el costado delantero (con la pinza de busto) casa con el trasero.

## Nota de alcance
El sloper es el **bloque base entallado** de cada escuela. Los 25 estilos de
manipulación de bloque operan hoy sobre el bloque de camisa; integrarlos sobre el
sloper con pinzas (p. ej. costura princesa que absorbe las pinzas de busto y
cintura) es la extensión natural a partir de esta base.
