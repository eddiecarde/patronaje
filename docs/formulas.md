# Fórmulas del motor paramétrico (talla S)

Todos los valores se derivan de las medidas del cuerpo, las holguras y las
constantes de método. Al cambiar cualquier medida, los derivados se recalculan y
el patrón se regenera. Fuente: `patronaje/parametric/measurements.py`.

## Medidas del cuerpo (talla S)

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| busto | 88.00 cm | contorno de busto |
| cintura | 70.00 cm | contorno de cintura |
| cadera | 94.00 cm | contorno de cadera |
| largo_camisa | 68.00 cm | largo total desde nuca |
| largo_manga | 60.00 cm | largo de manga |
| contorno_cuello | 37.00 cm | contorno de cuello |
| ancho_espalda | 37.00 cm | ancho de espalda (across back) |
| hombro | 12.50 cm | largo de hombro |
| contorno_brazo | 30.00 cm | contorno de brazo |
| muneca | 18.00 cm | contorno de muñeca |

## Holguras (ease)

| Parámetro | Valor |
|-----------|-------|
| holgura_busto | 8.00 cm |
| holgura_brazo | 8.00 cm |
| holgura_muneca | 6.00 cm |
| holgura_cuello | 1.00 cm |

## Constantes de método

`ease_sisa=0.5` · `caida_hombro_esp=4.5` · `caida_hombro_del=5.0` ·
`subida_escote_esp=2.0` · `linea_canesu=10.0` · `extension_boton=1.7` ·
`ancho_puno=6.0` · `margen_costura=1.0` · `margen_dobladillo=2.5`.

## Parámetros derivados (fórmulas)

| Parámetro | Fórmula | Valor S |
|-----------|---------|---------|
| busto_patron | `busto + holgura_busto` | 96.00 |
| cuarto_busto | `(busto + holgura_busto)/4` | 24.00 |
| medio_busto | `(busto + holgura_busto)/2` | 48.00 |
| prof_sisa (scye) | `busto/8 + 10.5 + ease_sisa` | 22.00 |
| medio_espalda | `ancho_espalda/2` | 18.50 |
| escote_esp_ancho | `contorno_cuello/5 − 0.3` | 7.10 |
| escote_del_ancho | `contorno_cuello/5 − 0.5` | 6.90 |
| escote_del_prof | `contorno_cuello/5 + 2.0` | 9.40 |
| boca_manga | `muneca + holgura_muneca` | 24.00 |
| largo_puno | `muneca + 3.0` | 21.00 |

## Longitudes resultantes (medidas sobre las curvas)

| Magnitud | Valor S | Uso |
|----------|---------|-----|
| escote (½, al doblez) | 19.26 cm | longitud base de cuello y pie de cuello |
| escote total (prenda) | ≈ 38.5 cm | contorno de cuello terminado |
| sisa (delantero+espalda) | 38.81 cm | objetivo de la copa de manga |
| copa de manga | 39.81 cm | `sisa + sleeve_ease(1.0)` |
| altura de copa | 9.90 cm | `prof_sisa × 0.45` (regla), ajustada |
| bíceps de manga | 32.98 cm | resuelto para casar copa=sisa (brazo+≈3) |

## Reglas de casado (validadas antes de exportar)

- `|copa − (sisa + sleeve_ease)| ≤ tol`
- costado delantero = costado espalda = `largo_camisa − prof_sisa`
- hombro delantero = hombro espalda = `hombro`
- pie de cuello = `escote(½) + extension_boton`
- pliegues de manga = `boca_manga − largo_puno` (1.5–6 cm)
- canesú (borde inferior) = espalda (borde superior) en la línea de canesú
