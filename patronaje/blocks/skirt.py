"""Bloque de falda base (recta / lápiz) — construcción paramétrica.

Falda de dos paneles (delantero y trasero, ambos **al doblez** en CF/CB) con
**pinza de cintura** por panel y **curva de cadera**. La supresión cintura–cadera
de cada panel se reparte entre el **costado** y la **pinza** (el trasero toma más
que el delantero, como es habitual). Marco local: ``x`` hacia el costado (CF/CB en
``x = 0``), ``y`` hacia abajo (cintura ``y = 0`` → bajo).

Todos los contornos son la **línea de costura (net)**; el margen lo añade la pieza.
Reutiliza :func:`patronaje.blocks.fitted._insert_dart` para materializar la V de
la pinza en el borde de cintura.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..core.curves import smooth_curve
from ..parametric.parameters import Parameters
from .fitted import _insert_dart


@dataclass
class SkirtDraft:
    p: Parameters
    front: list = field(default_factory=list)
    back: list = field(default_factory=list)
    front_darts: list = field(default_factory=list)
    back_darts: list = field(default_factory=list)
    hip_y: float = 0.0
    hem_y: float = 0.0

    def _panel(self, dart_intake: float, dart_len: float, dart_frac: float):
        """Construye un panel (delantero o trasero) y su pinza."""
        p = self.p
        quarter_hip = p.cuarto_cadera
        quarter_waist = p.cuarto_cintura_falda
        supp = max(0.0, quarter_hip - quarter_waist)
        dart = min(dart_intake, supp)
        side_supp = supp - dart
        sw_x = quarter_hip - side_supp            # x de cintura en el costado
        hip_y, hem_y = self.hip_y, self.hem_y

        # borde de cintura (recto CF -> costado) con la pinza insertada
        waist = [(0.0, 0.0), (sw_x, 0.0)]
        center_x = sw_x * dart_frac
        apex = (center_x, dart_len)
        waist, dart_tuple = _insert_dart(waist, center_x / sw_x if sw_x else 0.0,
                                         dart, apex)

        # costado: curva de cintura a cadera, luego recto a bajo (lápiz)
        side = smooth_curve([(sw_x, 0.0), (quarter_hip - 0.3, hip_y * 0.55),
                             (quarter_hip, hip_y)], samples_per_span=8)

        contour = list(waist)                     # CF .. pinza .. costado
        contour += side[1:]                       # costado a cadera (curvo)
        contour += [(quarter_hip, hem_y)]         # cadera a bajo (recto)
        contour += [(0.0, hem_y)]                 # bajo a CF
        return contour, dart_tuple

    def build(self) -> "SkirtDraft":
        p = self.p
        self.hip_y = p.altura_cadera
        self.hem_y = p.largo_falda
        self.front, fd = self._panel(p.pinza_cint_del, p.largo_pinza_del, 0.45)
        self.back, bd = self._panel(p.pinza_cint_tra, p.largo_pinza_tra, 0.50)
        self.front_darts = [fd]
        self.back_darts = [bd]
        return self

    # ---- longitudes de casado ------------------------------------------
    def waist_length(self) -> float:
        """Largo total de cintura (ambos paneles, cuerpo entero) = cintura+holgura."""
        return 4.0 * self.p.cuarto_cintura_falda

    def hip_length(self) -> float:
        return 4.0 * self.p.cuarto_cadera


def build_skirt_block(p: Parameters) -> SkirtDraft:
    return SkirtDraft(p=p).build()
