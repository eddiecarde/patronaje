"""Modelo de Pieza de patrón y entidades CAD asociadas.

Una :class:`Piece` reúne todo lo que el prompt exige por pieza:

    Curvas reales · líneas de construcción · líneas de costura · líneas de corte ·
    centro · línea de hilo · piquetes · perforaciones · puntos de control ·
    nombre · número · talla · cantidad a cortar · tipo de corte · "al doblez".

La geometría se guarda en el **marco local** de la pieza y se expone como una
lista de *entidades CAD neutras* (:class:`Entity`) etiquetadas por capa. Los
exportadores (DXF/SVG/PDF/JSON…) consumen esa lista, de modo que las piezas no
saben nada de formatos concretos.

Convención interna: ``y`` hacia abajo (marco de patronaje). El exportador decide
la orientación final (los DXF/SVG invierten Y para dejar la prenda "de pie").
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import Polygon
from shapely import set_precision

# --------------------------------------------------------------------------
# Capas (coinciden con las capas del DXF pedidas en el prompt)
# --------------------------------------------------------------------------
class Layer:
    CONSTRUCCION = "CONSTRUCCION"
    CORTE = "CORTE"
    COSTURA = "COSTURA"
    PIQUETES = "PIQUETES"
    TEXTOS = "TEXTOS"
    CENTROS = "CENTROS"
    HILO = "HILO"
    DOBLEZ = "DOBLEZ"
    BOTONES = "BOTONES"
    OJAL = "OJAL"
    REFERENCIAS = "REFERENCIAS"


ALL_LAYERS = [
    Layer.CONSTRUCCION, Layer.CORTE, Layer.COSTURA, Layer.PIQUETES, Layer.TEXTOS,
    Layer.CENTROS, Layer.HILO, Layer.DOBLEZ, Layer.BOTONES, Layer.OJAL, Layer.REFERENCIAS,
]

# color ACI por capa para el DXF (AutoCAD Color Index)
LAYER_COLORS = {
    Layer.CONSTRUCCION: 8,   # gris
    Layer.CORTE: 1,          # rojo
    Layer.COSTURA: 3,        # verde
    Layer.PIQUETES: 4,       # cyan
    Layer.TEXTOS: 7,         # blanco/negro
    Layer.CENTROS: 5,        # azul
    Layer.HILO: 2,           # amarillo
    Layer.DOBLEZ: 6,         # magenta
    Layer.BOTONES: 30,       # naranja
    Layer.OJAL: 200,         # rosa
    Layer.REFERENCIAS: 9,    # gris claro
}


# --------------------------------------------------------------------------
# Entidades CAD neutras
# --------------------------------------------------------------------------
@dataclass
class Entity:
    layer: str


@dataclass
class EPolyline(Entity):
    points: list[tuple[float, float]] = field(default_factory=list)
    closed: bool = False


@dataclass
class ELine(Entity):
    p1: tuple[float, float] = (0.0, 0.0)
    p2: tuple[float, float] = (0.0, 0.0)


@dataclass
class EText(Entity):
    pos: tuple[float, float] = (0.0, 0.0)
    text: str = ""
    height: float = 0.8
    rotation: float = 0.0
    align: str = "left"


@dataclass
class ECircle(Entity):
    center: tuple[float, float] = (0.0, 0.0)
    radius: float = 0.15


@dataclass
class ENotch(Entity):
    """Piquete: marca de casado sobre la línea de corte."""
    pos: tuple[float, float] = (0.0, 0.0)
    direction: tuple[float, float] = (0.0, 1.0)  # hacia el interior de la pieza
    depth: float = 0.6


# --------------------------------------------------------------------------
# Pieza
# --------------------------------------------------------------------------
@dataclass
class Piece:
    name: str
    number: int
    size: str
    quantity: int = 2
    cut_type: str = "par simétrico"       # tipo de corte
    on_fold: bool = False                  # "al doblez"
    fold_x: float | None = None            # x de la línea de doblez (si on_fold)

    net_contour: list[tuple[float, float]] = field(default_factory=list)  # línea de costura
    seam_allowance: float = 1.0            # margen de costura (cm)
    hem_allowance: float | None = None     # dobladillo (si aplica) en el borde inferior

    grain: tuple[tuple[float, float], tuple[float, float]] | None = None  # línea de hilo
    notches: list[tuple[float, float]] = field(default_factory=list)      # piquetes
    drills: list[tuple[float, float]] = field(default_factory=list)       # perforaciones
    control_points: list[tuple[float, float]] = field(default_factory=list)
    construction_lines: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)
    reference_texts: list[tuple[tuple[float, float], str]] = field(default_factory=list)
    buttons: list[tuple[float, float]] = field(default_factory=list)
    buttonholes: list[tuple[float, float, float, float]] = field(default_factory=list)  # x,y,ang,len

    offset: tuple[float, float] = (0.0, 0.0)  # posición al colocar en el plano/lienzo

    # ---- geometría derivada ---------------------------------------------
    def net_polygon(self) -> Polygon:
        poly = Polygon(self.net_contour)
        if not poly.is_valid:
            poly = poly.buffer(0)
        return poly

    def cut_contour(self) -> list[tuple[float, float]]:
        """Línea de corte = línea de costura + margen (respetando el doblez).

        Para piezas al doblez, el borde de doblez NO lleva margen: se refleja la
        pieza, se aplica el margen al contorno completo y se recorta a la mitad,
        dejando el doblez sobre su línea exacta.
        """
        sa = self.seam_allowance
        if sa <= 0:
            return list(self.net_contour)
        poly = self.net_polygon()
        grown = poly.buffer(sa, join_style="mitre", mitre_limit=2.5)
        if self.on_fold and self.fold_x is not None:
            fx = self.fold_x
            # recorta al semiplano de la pieza (lado con más área)
            from shapely.geometry import box
            minx, miny, maxx, maxy = grown.bounds
            pad = sa + 5.0
            # decide de qué lado del doblez está la pieza
            cx = poly.centroid.x
            if cx >= fx:
                clip = box(fx, miny - pad, maxx + pad, maxy + pad)
            else:
                clip = box(minx - pad, miny - pad, fx, maxy + pad)
            grown = grown.intersection(clip)
        grown = set_precision(grown, 1e-6)
        if grown.geom_type == "MultiPolygon":
            grown = max(grown.geoms, key=lambda g: g.area)
        return [(float(x), float(y)) for x, y in grown.exterior.coords]

    def centroid(self) -> tuple[float, float]:
        c = self.net_polygon().centroid
        return (c.x, c.y)

    def bbox(self) -> tuple[float, float, float, float]:
        return tuple(self.net_polygon().bounds)  # (minx,miny,maxx,maxy)

    def area(self) -> float:
        return self.net_polygon().area

    def perimeter(self) -> float:
        return self.net_polygon().length

    # ---- entidades para exportar ----------------------------------------
    def get_entities(self, *, include_seam: bool = True) -> list[Entity]:
        ents: list[Entity] = []
        # línea de corte (contorno principal)
        ents.append(EPolyline(Layer.CORTE, points=self.cut_contour(), closed=True))
        # línea de costura (net)
        if include_seam and self.seam_allowance > 0:
            ents.append(EPolyline(Layer.COSTURA, points=list(self.net_contour), closed=True))
        # línea de doblez
        if self.on_fold and self.fold_x is not None:
            minx, miny, maxx, maxy = self.bbox()
            ents.append(ELine(Layer.DOBLEZ, (self.fold_x, miny), (self.fold_x, maxy)))
        # línea de hilo (con puntas de flecha simples)
        if self.grain is not None:
            ents += self._grain_entities()
        # piquetes
        for n in self.notches:
            d = self._inward_dir(n)
            ents.append(ENotch(Layer.PIQUETES, pos=n, direction=d))
        # perforaciones
        for dpt in self.drills:
            ents.append(ECircle(Layer.CENTROS, center=dpt, radius=0.15))
        # puntos de control
        for cp in self.control_points:
            ents.append(ECircle(Layer.REFERENCIAS, center=cp, radius=0.1))
        # líneas de construcción
        for a, b in self.construction_lines:
            ents.append(ELine(Layer.CONSTRUCCION, a, b))
        # botones y ojales
        for bx, by in self.buttons:
            ents.append(ECircle(Layer.BOTONES, center=(bx, by), radius=0.55))
        for bx, by, ang, length in self.buttonholes:
            dx = math.cos(ang) * length / 2
            dy = math.sin(ang) * length / 2
            ents.append(ELine(Layer.OJAL, (bx - dx, by - dy), (bx + dx, by + dy)))
        # textos de referencia
        for pos, txt in self.reference_texts:
            ents.append(EText(Layer.REFERENCIAS, pos=pos, text=txt, height=0.5))
        # bloque de rótulo
        ents += self._label_entities()
        return [self._translated(e) for e in ents]

    # ---- helpers internos -----------------------------------------------
    def _grain_entities(self) -> list[Entity]:
        (x1, y1), (x2, y2) = self.grain
        ents: list[Entity] = [ELine(Layer.HILO, (x1, y1), (x2, y2))]
        # puntas de flecha
        ang = math.atan2(y2 - y1, x2 - x1)
        for (px, py), a in [((x2, y2), ang + math.pi), ((x1, y1), ang)]:
            for da in (0.4, -0.4):
                ents.append(ELine(Layer.HILO, (px, py),
                                  (px + math.cos(a + da) * 1.2, py + math.sin(a + da) * 1.2)))
        return ents

    def _inward_dir(self, pt: tuple[float, float]) -> tuple[float, float]:
        cx, cy = self.centroid()
        dx, dy = cx - pt[0], cy - pt[1]
        n = math.hypot(dx, dy) or 1.0
        return (dx / n, dy / n)

    def _label_entities(self) -> list[Entity]:
        cx, cy = self.centroid()
        lines = [
            f"{self.name}",
            f"Pieza N.{self.number:02d}",
            f"Talla: {self.size}",
            f"Cortar: {self.quantity}  ({self.cut_type})",
        ]
        if self.on_fold:
            lines.append("AL DOBLEZ")
        ents: list[Entity] = []
        y = cy - (len(lines) - 1) * 0.9
        for i, ln in enumerate(lines):
            h = 0.9 if i == 0 else 0.6
            ents.append(EText(Layer.TEXTOS, pos=(cx, y + i * 1.4), text=ln,
                              height=h, align="center"))
        return ents

    def _translated(self, e: Entity) -> Entity:
        ox, oy = self.offset
        if ox == 0 and oy == 0:
            return e
        if isinstance(e, EPolyline):
            return EPolyline(e.layer, [(x + ox, y + oy) for x, y in e.points], e.closed)
        if isinstance(e, ELine):
            return ELine(e.layer, (e.p1[0] + ox, e.p1[1] + oy), (e.p2[0] + ox, e.p2[1] + oy))
        if isinstance(e, EText):
            return EText(e.layer, (e.pos[0] + ox, e.pos[1] + oy), e.text, e.height, e.rotation, e.align)
        if isinstance(e, ECircle):
            return ECircle(e.layer, (e.center[0] + ox, e.center[1] + oy), e.radius)
        if isinstance(e, ENotch):
            return ENotch(e.layer, (e.pos[0] + ox, e.pos[1] + oy), e.direction, e.depth)
        return e
