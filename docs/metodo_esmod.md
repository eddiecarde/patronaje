# Método ESMOD (francés)

A diferencia de los sistemas proporcionales, ESMOD (*méthode française*,
demi-mesure) parte de **medidas directas** del cuerpo: la **carrure** (ancho de
espalda) y la **encolure** (contorno de cuello) se usan tal cual, no como
proporción del busto. El bloque base lleva pinza de busto; para la **camisa
relajada** se omite. Implementado en `blocks/esmod_method.py` sobre el
constructor común `blocks/_bodice_common.py`.

## Fórmulas

| Concepto | Fórmula | Valor S |
|----------|---------|---------|
| Profundidad de sisa | `busto/10 + 12.5` | 21.3 |
| Ancho de espalda (carrure dos) | `ancho_espalda / 2` (directo) | 18.5 |
| Ancho de pecho (carrure devant) | `ancho_espalda/2 − 1.5` | 17.0 |
| Escote espalda ancho | `encolure/6 + 0.5` | 6.7 |
| Escote delantero ancho | `encolure/6 + 0.3` | 6.5 |
| Escote delantero profundidad | `encolure/6 + 2.2` | 8.4 |
| Subida escote espalda | `2.0` | 2.0 |
| Costado (1/4) | `(busto + holgura)/4` | 24.0 |
| Caída hombro (esp./del.) | `4.5 / 5.0` | 4.5 / 5.0 |

Manga: `cap_ratio 0.55`, bíceps resuelto para casar copa = sisa.

## Diferenciador
ESMOD es el único de los cuatro métodos que dimensiona espalda/pecho y escote a
partir de **medidas antropométricas directas** (`ancho_espalda`,
`contorno_cuello`) en vez de proporciones del busto — fiel a su filosofía de
patronaje a medida.
