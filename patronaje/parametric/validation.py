"""Validación de medidas de entrada (antes de trazar el patrón).

Comprueba que un juego de medidas del cuerpo sea **completo, positivo y
proporcionalmente coherente** antes de construir los parámetros. Es la primera
línea de defensa del modo *a medida* (made-to-measure): evita trazar patrones
con medidas imposibles (cintura mayor que el busto, muñeca mayor que el brazo,
escote más ancho que la espalda…) que producirían geometría degenerada.

Cada problema se reporta como :class:`MeasurementIssue` con nivel ``error``
(bloquea el trazado salvo ``--force``) o ``warn`` (sólo avisa).
"""
from __future__ import annotations

from dataclasses import dataclass

# Medidas del cuerpo requeridas (las secundarias se estiman si faltan).
REQUIRED = [
    "busto", "cintura", "cadera", "largo_camisa", "largo_manga",
    "contorno_cuello", "ancho_espalda", "hombro", "contorno_brazo", "muneca",
]
# Medidas opcionales conocidas (no obligan, pero se validan si vienen).
OPTIONAL = ["talle_espalda", "altura_cadera"]

# Rangos humanos generosos (cm) para avisos de "fuera de rango".
_RANGES = {
    "busto": (60, 160), "cintura": (45, 150), "cadera": (60, 170),
    "largo_camisa": (40, 130), "largo_manga": (35, 80),
    "contorno_cuello": (28, 55), "ancho_espalda": (28, 55),
    "hombro": (8, 20), "contorno_brazo": (18, 55), "muneca": (12, 26),
    "talle_espalda": (32, 52), "altura_cadera": (14, 28),
}


@dataclass
class MeasurementIssue:
    level: str        # "error" | "warn"
    field: str
    message: str

    def __str__(self) -> str:
        mark = "XX" if self.level == "error" else "!!"
        return f"  [{mark}] {self.field}: {self.message}"


def validate_measurements(m: dict) -> list[MeasurementIssue]:
    """Devuelve la lista de problemas (vacía si todo es coherente)."""
    issues: list[MeasurementIssue] = []

    def err(field, msg):
        issues.append(MeasurementIssue("error", field, msg))

    def warn(field, msg):
        issues.append(MeasurementIssue("warn", field, msg))

    # 1) completitud y positividad
    for k in REQUIRED:
        if k not in m or m[k] is None:
            err(k, "medida requerida ausente")
        elif not isinstance(m[k], (int, float)):
            err(k, f"valor no numérico: {m[k]!r}")
        elif m[k] <= 0:
            err(k, f"debe ser positiva (={m[k]})")

    # claves desconocidas
    known = set(REQUIRED) | set(OPTIONAL)
    for k in m:
        if k not in known:
            warn(k, "medida desconocida (se ignora)")

    # si faltan medidas base, no se puede evaluar coherencia proporcional
    if any(i.level == "error" for i in issues):
        return issues

    # 2) rangos humanos (aviso)
    for k, (lo, hi) in _RANGES.items():
        if k in m and not (lo <= m[k] <= hi):
            warn(k, f"fuera de rango habitual [{lo}-{hi}]: {m[k]}")

    # 3) coherencia proporcional
    if m["muneca"] >= m["contorno_brazo"]:
        err("muneca", f"la muñeca ({m['muneca']}) no puede ser >= el brazo "
                      f"({m['contorno_brazo']})")
    if m["contorno_brazo"] >= m["busto"]:
        err("contorno_brazo", f"el brazo ({m['contorno_brazo']}) no puede ser "
                              f">= el busto ({m['busto']})")
    # escote no puede ser más ancho que media espalda (trazado degenerado)
    if m["contorno_cuello"] / 5.0 >= m["ancho_espalda"] / 2.0:
        err("contorno_cuello", "el escote resultante es más ancho que media "
                               "espalda; revise contorno_cuello/ancho_espalda")
    if m["ancho_espalda"] >= m["busto"] / 2.0:
        warn("ancho_espalda", f"el ancho de espalda ({m['ancho_espalda']}) es >= "
                              f"medio busto ({m['busto']/2:.1f}); inusual")
    if m["cintura"] > m["busto"]:
        warn("cintura", f"cintura ({m['cintura']}) mayor que busto ({m['busto']}); "
                        "cuerpo poco entallado")
    if m["cadera"] < m["cintura"]:
        warn("cadera", f"cadera ({m['cadera']}) menor que cintura ({m['cintura']}); "
                       "inusual")
    return issues


def has_errors(issues) -> bool:
    return any(i.level == "error" for i in issues)


def format_issues(issues) -> str:
    if not issues:
        return "=== MEDIDAS OK (sin observaciones) ==="
    n_err = sum(1 for i in issues if i.level == "error")
    n_warn = len(issues) - n_err
    lines = ["=== VALIDACIÓN DE MEDIDAS ==="]
    lines += [str(i) for i in issues]
    lines.append(f"--- {n_err} error(es), {n_warn} aviso(s) ---")
    return "\n".join(lines)
