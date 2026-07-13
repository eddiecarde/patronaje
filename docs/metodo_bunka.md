# Método Bunka (文化式)

Sistema japonés (Bunka Fashion College) **proporcional al contorno de busto (B)**.
El sloper clásico (原型) incluye pinza de busto y pinzas de cintura; para la
**camisa relajada** se omiten las pinzas (bloque sin pinza, costado recto),
conservando las proporciones Bunka. Implementado en `blocks/bunka_method.py`
sobre el constructor común `blocks/_bodice_common.py`.

## Fórmulas (B = busto)

| Concepto | Fórmula | Valor S (B=88) |
|----------|---------|----------------|
| Profundidad de sisa (袖ぐり深) | `B/12 + 13.7` | 21.0 |
| Ancho de espalda (背幅) | `B/8 + 7.4` | 18.4 |
| Ancho de pecho (胸幅) | `B/8 + 6.2` | 17.2 |
| Escote delantero ancho (前ネック幅) | `B/24 + 3.4` | 7.1 |
| Escote delantero profundidad | `fnw + 0.5` | 7.6 |
| Escote espalda ancho | `fnw + 0.2` | 7.3 |
| Subida escote espalda | `bnw / 3` | 2.4 |
| Costado (1/4) | `(B + holgura)/4` | 24.0 |
| Caída hombro (esp./del.) | `4.0 / 5.5` | 4.0 / 5.5 |

Manga: copa alta (`cap_ratio 0.60`) con bíceps resuelto por bisección para
casar copa = sisa.

## Nota de adaptación
Bunka es un sistema para sloper ajustado con pinzas; esta implementación produce
un **bloque de camisa Bunka-based** (sin pinza, para prenda holgada), usando la
red proporcional Bunka para escote, sisa y anchos. Requiere `talle_espalda`.
