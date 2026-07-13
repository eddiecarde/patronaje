"""Datos de proceso: secuencia de confección, control de calidad y tolerancias.

Parametrizados donde aplica (medidas terminadas y tolerancias derivadas del
motor); el resto son estándares de confección de camisa.
"""
from __future__ import annotations


SEWING_SEQUENCE = [
    "Fusionar entretela a cuello, pie de cuello y puños.",
    "Confeccionar y fijar el bolsillo de parche al delantero (opcional).",
    "Preparar la tapeta/botonadura del delantero.",
    "Montar el canesú: unir a la espalda y encerrar los hombros del delantero.",
    "Armar cuello + pie de cuello y montarlo al escote casando el centro.",
    "Preparar aberturas de manga y montar las mangas a la sisa casando piquetes.",
    "Cerrar costados y bajo de manga en una sola costura continua.",
    "Confeccionar y montar los puños; formar los pliegues de la boca de manga.",
    "Hacer el dobladillo inferior.",
    "Realizar ojales y pegar botones (delantero, puños y pie de cuello).",
    "Acabados: recorte de hilos, planchado y control final de calidad.",
]

QC_CHECKLIST = [
    "Simetría izquierda/derecha (mangas, cuello, puños, largo de faldón).",
    "Puntas de cuello iguales y simétricas; pie de cuello parejo.",
    "Costuras 2.5–3 puntadas/cm, sin fruncidos ni saltos.",
    "Sisa y copa casan sin frunce excesivo; piquetes alineados.",
    "Botones firmes y ojales limpios, alineados con la botonadura.",
    "Puños simétricos; pliegues de manga uniformes.",
    "Medidas terminadas dentro de tolerancia (ver tabla).",
    "Sin manchas, hilos sueltos ni defectos de tela.",
    "Etiquetas de marca, talla y composición correctas y bien ubicadas.",
]


def finished_measurements(shirt) -> list[dict]:
    """Puntos de medida (POM) de la prenda terminada + tolerancia."""
    p = shirt.p
    b = shirt.bodice
    rows = [
        ("1/2 contorno de pecho", (p.busto + p.holgura_busto) / 2.0, 1.0),
        ("1/2 contorno de cadera", (p.cadera + 8) / 2.0, 1.0),
        ("Largo total (desde nuca)", p.largo_camisa, 1.0),
        ("Ancho de hombros", p.ancho_espalda + 2.0, 0.5),
        ("Largo de manga", p.largo_manga, 0.5),
        ("Contorno de sisa (1/2)", b.armhole_length(), 0.5),
        ("Contorno de puño", p.largo_puno, 0.3),
        ("Alto de puño", p.ancho_puno, 0.2),
        ("Contorno de cuello (terminado)", b.neckline_length() * 2.0, 0.5),
    ]
    return [{"pom": n, "valor_cm": round(v, 1), "tol_cm": t} for n, v, t in rows]


TOLERANCES = [
    ("Contornos (pecho, cadera)", "± 1.0 cm"),
    ("Largos (prenda, manga)", "± 1.0 / ± 0.5 cm"),
    ("Cuello terminado", "± 0.5 cm"),
    ("Puño (contorno / alto)", "± 0.3 / ± 0.2 cm"),
    ("Ancho de hombros", "± 0.5 cm"),
    ("Posición de bolsillo", "± 0.5 cm"),
    ("Casado de sisa/copa", "± 0.5 cm"),
    ("Simetría izq/der", "± 0.3 cm"),
]
