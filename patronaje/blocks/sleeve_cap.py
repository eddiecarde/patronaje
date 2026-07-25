"""Construcción de la **copa de manga por Bézier cúbica** (camisa de mujer).

Modelo didáctico y calibrable de la cabeza de manga: cada mitad de la copa se
traza como una **Bézier cúbica** entre el bíceps (base) y la cima (cabeza), con
dos puntos-guía proporcionales al ancho ``W`` y a la altura ``H`` de la copa.

Marco local de :func:`curva_copa_manga` (el del enunciado de patronaje):

    P0  = base, en (0, 0)
    2ª guía (cerca de la base) = (0.30·W, 0.30·H)
    1ª guía (cerca de la cima) = (0.65·W, 0.80·H)
    P3  = cima, en (W, H)                     ← compartida por ambas mitades

con ``W = ancho_manga / 2`` y ``H = altura_copa``. La curva es la Bézier
``P0 → 2ªguía → 1ªguía → P3``.

Diferenciación delantero/espalda: en el **delantero** se baja la 2ª guía
``DELANTERO_DIP`` cm en Y, lo que genera la ligera **concavidad** característica
cerca de la base (sirve para reconocer el delantero al coser y no confundirlo con
la espalda). La **espalda** usa los valores base.

Los coeficientes son **constantes ajustables** (calibrables contra el sistema de
patronaje de referencia). El resto de la app consume el resultado en su mismo
marco: la copa se entrega en el marco del bloque de manga (cima ``SH=(0,0)`` y
bíceps en ``(±W, H)`` con ``y`` hacia abajo), igual que las demás piezas.
"""
from __future__ import annotations

import math

from ..core.curves import CubicBezier

# --------------------------------------------------------------------------
# Coeficientes calibrables (fracciones de W y H, salvo DELANTERO_DIP en cm)
# --------------------------------------------------------------------------
GUIA2_FRAC_X = 0.30      # 2ª guía (cerca de la base): x = frac · W
GUIA2_FRAC_Y = 0.30      # 2ª guía: y = frac · H
GUIA1_FRAC_X = 0.65      # 1ª guía (cerca de la cima): x = frac · W
GUIA1_FRAC_Y = 0.80      # 1ª guía: y = frac · H
DELANTERO_DIP = 0.7      # cm que baja la 2ª guía del delantero (concavidad)

CAP_SAMPLES = 32         # muestras por media copa (densidad de la polilínea)


def curva_copa_manga(ancho_manga: float, altura_copa: float, lado: str,
                     samples: int = CAP_SAMPLES) -> dict:
    """Traza **media copa** de manga como Bézier cúbica (marco local del enunciado).

    Parámetros
    ----------
    ancho_manga : ancho total de la base de la manga (sisa + holgura). ``W`` es
        su mitad.
    altura_copa : altura de la cima de la copa sobre la línea base (``H``). Por
        defecto en la app ``contorno_sisa/3``, pero aquí se recibe ya resuelta.
    lado : ``"delantero"`` o ``"espalda"``. El delantero baja la 2ª guía
        ``DELANTERO_DIP`` cm (concavidad cerca de la base).

    Devuelve un dict con los puntos de control (``p0, guia2, guia1, p3``), la
    ``bezier`` y la polilínea ``curve`` muestreada, además de ``W`` y ``H``.
    """
    W = ancho_manga / 2.0
    H = altura_copa
    p0 = (0.0, 0.0)
    guia2 = (GUIA2_FRAC_X * W, GUIA2_FRAC_Y * H)     # cerca de la base
    guia1 = (GUIA1_FRAC_X * W, GUIA1_FRAC_Y * H)     # cerca de la cima
    p3 = (W, H)
    if lado == "delantero":
        guia2 = (guia2[0], guia2[1] - DELANTERO_DIP)  # concavidad del delantero
    bez = CubicBezier(p0, guia2, guia1, p3)           # P0 → 2ªguía → 1ªguía → P3
    return {
        "p0": p0, "guia2": guia2, "guia1": guia1, "p3": p3,
        "bezier": bez, "curve": bez.sample(samples), "W": W, "H": H, "lado": lado,
    }


# alias con la firma exacta pedida (camelCase)
curvaCopaManga = curva_copa_manga


# --------------------------------------------------------------------------
# Integración con el bloque de manga (marco cima=SH=(0,0), bíceps=(±bh, h))
# --------------------------------------------------------------------------
def _to_block(pt, bh: float, h: float, side: int) -> tuple[float, float]:
    """Marco local (base P0=(0,0), cima P3=(W,H)) → marco del bloque de manga.

    ``side = -1`` (espalda, lado izquierdo) o ``+1`` (delantero, lado derecho).
    La **cima** P3 cae en ``SH=(0,0)`` y la **base** P0 en el bíceps
    ``(side·bh, h)`` (con ``bh = W`` y ``y`` hacia abajo).
    """
    x, y = pt
    return (side * (bh - x), h - y)


def bezier_cap_curve(biceps_half: float, cap_height: float,
                     samples: int = CAP_SAMPLES) -> list[tuple[float, float]]:
    """Copa completa **BL → SH → BR** en el marco del bloque de manga.

    Une la media copa de **espalda** (izquierda) y la de **delantero** (derecha),
    compartiendo la cima ``SH=(0,0)``. ``ancho_manga = 2·biceps_half``.
    """
    ancho = 2.0 * biceps_half
    back = curva_copa_manga(ancho, cap_height, "espalda", samples)["curve"]
    front = curva_copa_manga(ancho, cap_height, "delantero", samples)["curve"]
    back_cb = [_to_block(pt, biceps_half, cap_height, -1) for pt in back]   # BL→SH
    front_cb = [_to_block(pt, biceps_half, cap_height, +1) for pt in front]  # BR→SH
    return back_cb + list(reversed(front_cb))[1:]                            # BL..SH..BR


def bezier_cap_guides(biceps_half: float, cap_height: float) -> list[list[tuple[float, float]]]:
    """Guías de construcción de la copa (**solo modo debug**, no van al PDF final).

    Devuelve polilíneas en el marco del bloque: para cada mitad, el **polígono de
    control** (P0–2ªguía–1ªguía–P3) y la **bisectriz** a 45° en el bíceps.
    """
    ancho = 2.0 * biceps_half
    guides: list[list[tuple[float, float]]] = []
    for lado, side in (("espalda", -1), ("delantero", +1)):
        r = curva_copa_manga(ancho, cap_height, lado)
        ctrl = [r["p0"], r["guia2"], r["guia1"], r["p3"]]
        guides.append([_to_block(pt, biceps_half, cap_height, side) for pt in ctrl])
        # bisectriz a 45° desde el bíceps (P0) hacia dentro de la copa
        blen = 0.22 * cap_height
        bis = [r["p0"], (r["p0"][0] + blen, r["p0"][1] + blen)]
        guides.append([_to_block(pt, biceps_half, cap_height, side) for pt in bis])
    return guides
