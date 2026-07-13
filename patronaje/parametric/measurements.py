"""Medidas base y construcción de :class:`Parameters` para la camisa.

Talla S internacional (medidas del enunciado) más las holguras y constantes de
método Aldrich. Aquí se definen tanto las medidas del cuerpo como los
*parámetros derivados* (profundidad de sisa, cuartos, anchos de escote, etc.),
cuya fórmula se documenta en ``docs/formulas.md``.

También se define la tabla de tallas base (para el grading de la Fase 2) con
sus incrementos, aunque en Fase 1 sólo se materializa la talla S.
"""
from __future__ import annotations

from .parameters import Parameters


# Medidas del cuerpo por talla (cm). Talla S = enunciado. El resto se completa
# con incrementos industriales estándar y se usa en el grading (Fase 2).
SIZE_CHART: dict[str, dict[str, float]] = {
    "XS": dict(busto=84, cintura=66, cadera=90, largo_camisa=66, largo_manga=58.5,
               contorno_cuello=36, ancho_espalda=35.5, hombro=12.0, contorno_brazo=28.5, muneca=17),
    "S":  dict(busto=88, cintura=70, cadera=94, largo_camisa=68, largo_manga=60,
               contorno_cuello=37, ancho_espalda=37, hombro=12.5, contorno_brazo=30, muneca=18),
    "M":  dict(busto=92, cintura=74, cadera=98, largo_camisa=70, largo_manga=61.5,
               contorno_cuello=38, ancho_espalda=38.5, hombro=13.0, contorno_brazo=31.5, muneca=19),
    "L":  dict(busto=96, cintura=78, cadera=102, largo_camisa=72, largo_manga=63,
               contorno_cuello=39, ancho_espalda=40, hombro=13.5, contorno_brazo=33, muneca=20),
    "XL": dict(busto=100, cintura=82, cadera=106, largo_camisa=74, largo_manga=64.5,
               contorno_cuello=40, ancho_espalda=41.5, hombro=14.0, contorno_brazo=34.5, muneca=21),
    "XXL": dict(busto=104, cintura=86, cadera=110, largo_camisa=76, largo_manga=66,
                contorno_cuello=41, ancho_espalda=43, hombro=14.5, contorno_brazo=36, muneca=22),
}

# Holguras de confección (ease) — camisa básica semi-entallada.
EASE = dict(
    holgura_busto=8.0,     # ease total al contorno de busto
    holgura_brazo=8.0,     # ease al contorno de brazo (para copa cómoda)
    holgura_muneca=6.0,    # ease en boca de manga (pliegues al puño)
    holgura_cuello=1.0,    # ease al contorno de cuello
)

# Constantes de método (Aldrich) y de confección.
METODO = dict(
    ease_sisa=0.5,           # holgura en profundidad de sisa (bloque cómodo)
    caida_hombro_esp=4.5,    # drop del hombro espalda
    caida_hombro_del=5.0,    # drop del hombro delantero
    subida_escote_esp=2.0,   # curva de escote espalda (rise en CB)
    linea_canesu=10.0,       # distancia desde SNP a la línea de canesú
    extension_boton=1.7,     # media tapeta / extensión de botonadura (a cada lado del CF)
    ancho_puno=6.0,          # alto del puño terminado
    prof_bolsillo=13.5,      # bolsillo de parche opcional
    ancho_bolsillo=12.0,
    margen_costura=1.0,      # margen de costura por defecto
    margen_dobladillo=2.5,   # dobladillo inferior
)


def build_parameters(size: str = "S") -> Parameters:
    """Construye el objeto :class:`Parameters` para una talla.

    Incluye medidas base, holguras, constantes de método y los parámetros
    *derivados* del trazo Aldrich (recalculados automáticamente).
    """
    if size not in SIZE_CHART:
        raise KeyError(f"Talla no disponible: {size}. Opciones: {list(SIZE_CHART)}")
    m = SIZE_CHART[size]

    p = Parameters()
    p.set("talla_nombre", 0, unidad="", descripcion=f"talla {size}")  # placeholder numérico
    # medidas del cuerpo
    p.set("busto", m["busto"], descripcion="contorno de busto")
    p.set("cintura", m["cintura"], descripcion="contorno de cintura")
    p.set("cadera", m["cadera"], descripcion="contorno de cadera")
    p.set("largo_camisa", m["largo_camisa"], descripcion="largo total desde nuca")
    p.set("largo_manga", m["largo_manga"], descripcion="largo de manga")
    p.set("contorno_cuello", m["contorno_cuello"], descripcion="contorno de cuello")
    p.set("ancho_espalda", m["ancho_espalda"], descripcion="ancho de espalda (across back)")
    p.set("hombro", m["hombro"], descripcion="largo de hombro")
    p.set("contorno_brazo", m["contorno_brazo"], descripcion="contorno de brazo")
    p.set("muneca", m["muneca"], descripcion="contorno de muñeca")

    # holguras
    for k, v in EASE.items():
        p.set(k, v, descripcion="holgura de confección")
    # constantes de método
    for k, v in METODO.items():
        p.set(k, v, unidad="cm", descripcion="constante de método Aldrich/confección")

    # -------- parámetros derivados (fórmulas Aldrich) --------------------
    p.derive("busto_patron", lambda q: q["busto"] + q["holgura_busto"],
             descripcion="busto con holgura", expr="busto + holgura_busto")
    p.derive("cuarto_busto", lambda q: (q["busto"] + q["holgura_busto"]) / 4.0,
             descripcion="cuarto de busto por panel", expr="(busto + holgura_busto)/4")
    p.derive("medio_busto", lambda q: (q["busto"] + q["holgura_busto"]) / 2.0,
             descripcion="medio contorno (mitad del cuerpo)", expr="(busto + holgura_busto)/2")
    p.derive("prof_sisa", lambda q: q["busto"] / 8.0 + 10.5 + q["ease_sisa"],
             descripcion="profundidad de sisa (scye depth)", expr="busto/8 + 10.5 + ease_sisa")
    p.derive("medio_espalda", lambda q: q["ancho_espalda"] / 2.0,
             descripcion="medio ancho de espalda", expr="ancho_espalda/2")
    p.derive("escote_esp_ancho", lambda q: q["contorno_cuello"] / 5.0 - 0.3,
             descripcion="ancho escote espalda", expr="contorno_cuello/5 - 0.3")
    p.derive("escote_del_ancho", lambda q: q["contorno_cuello"] / 5.0 - 0.5,
             descripcion="ancho escote delantero", expr="contorno_cuello/5 - 0.5")
    p.derive("escote_del_prof", lambda q: q["contorno_cuello"] / 5.0 + 2.0,
             descripcion="profundidad escote delantero", expr="contorno_cuello/5 + 2.0")
    p.derive("largo_manga_efec", lambda q: q["largo_manga"],
             descripcion="largo de manga hasta puño", expr="largo_manga")
    p.derive("boca_manga", lambda q: q["muneca"] + q["holgura_muneca"],
             descripcion="ancho boca de manga antes de pliegues", expr="muneca + holgura_muneca")
    p.derive("largo_puno", lambda q: q["muneca"] + 3.0,
             descripcion="largo del puño terminado (con holgura de cierre)", expr="muneca + 3.0")

    return p
