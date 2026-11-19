"""RMR de Bieniawski 1989, calculado en código.

Los cortes son los de la clasificación publicada. No son la cartilla
interna de ninguna unidad minera.
"""

from __future__ import annotations


class EntradaInvalida(ValueError):
    pass


CONDICION = {
    "muy_buena": (30, "Muy buena", "Rugosas, no continuas, sin separación, paredes sanas."),
    "buena": (25, "Buena", "Ligeramente rugosas, separación menor de 1 mm, paredes poco alteradas."),
    "regular": (20, "Regular", "Ligeramente rugosas, separación menor de 1 mm, paredes muy alteradas."),
    "pobre": (10, "Pobre", "Estriadas o con relleno duro menor de 5 mm, o separación de 1 a 5 mm."),
    "muy_pobre": (0, "Muy pobre", "Relleno blando mayor de 5 mm o separación mayor de 5 mm."),
}

AGUA = {
    "seca": (15, "Completamente seca"),
    "humeda": (10, "Húmeda"),
    "mojada": (7, "Mojada"),
    "goteo": (4, "Goteo"),
    "flujo": (0, "Flujo"),
}

OBRA = {
    "tunel": "Túnel",
    "cimentacion": "Cimentación",
    "talud": "Talud",
}

# Ajuste por orientación de las discontinuidades. Bieniawski 1989.
ORIENTACION = {
    "muy_favorable": {"tunel": 0, "cimentacion": 0, "talud": 0, "etiqueta": "Muy favorable"},
    "favorable": {"tunel": -2, "cimentacion": -2, "talud": -5, "etiqueta": "Favorable"},
    "regular": {"tunel": -5, "cimentacion": -7, "talud": -25, "etiqueta": "Regular"},
    "desfavorable": {"tunel": -10, "cimentacion": -15, "talud": -50, "etiqueta": "Desfavorable"},
    "muy_desfavorable": {"tunel": -12, "cimentacion": -25, "talud": -60, "etiqueta": "Muy desfavorable"},
}

CLASES = (
    {"id": "I", "min": 81, "nombre": "Roca muy buena", "cohesion": "> 400 kPa", "friccion": "> 45°", "autosoporte": "20 años para 15 m de luz"},
    {"id": "II", "min": 61, "nombre": "Roca buena", "cohesion": "300 – 400 kPa", "friccion": "35 – 45°", "autosoporte": "1 año para 10 m de luz"},
    {"id": "III", "min": 41, "nombre": "Roca regular", "cohesion": "200 – 300 kPa", "friccion": "25 – 35°", "autosoporte": "1 semana para 5 m de luz"},
    {"id": "IV", "min": 21, "nombre": "Roca mala", "cohesion": "100 – 200 kPa", "friccion": "15 – 25°", "autosoporte": "10 horas para 2,5 m de luz"},
    {"id": "V", "min": 0, "nombre": "Roca muy mala", "cohesion": "< 100 kPa", "friccion": "< 15°", "autosoporte": "30 min para 1 m de luz"},
)

AVISO = (
    "El RMR y el tiempo de autosoporte son orientación empírica de Bieniawski 1989. "
    "No diseñan el sostenimiento ni reemplazan al geomecánico de la unidad."
)


def puntaje_ucs(mpa: float) -> int:
    if mpa > 250:
        return 15
    if mpa >= 100:
        return 12
    if mpa >= 50:
        return 7
    if mpa >= 25:
        return 4
    if mpa >= 5:
        return 2
    if mpa >= 1:
        return 1
    return 0


def puntaje_rqd(pct: float) -> int:
    if pct >= 90:
        return 20
    if pct >= 75:
        return 17
    if pct >= 50:
        return 13
    if pct >= 25:
        return 8
    return 3


def puntaje_espaciado(metros: float) -> int:
    if metros > 2:
        return 20
    if metros >= 0.6:
        return 15
    if metros >= 0.2:
        return 10
    if metros >= 0.06:
        return 8
    return 5


def clase_de(rmr: int) -> dict:
    for fila in CLASES:
        if rmr >= fila["min"]:
            return dict(fila)
    return dict(CLASES[-1])


def _numero(datos: dict, clave: str, etiqueta: str) -> float:
    if clave not in datos:
        raise EntradaInvalida(f"Falta {etiqueta}.")
    try:
        return float(datos[clave])
    except (TypeError, ValueError):
        raise EntradaInvalida(f"{etiqueta} tiene que ser un número.") from None


def _opcion(datos: dict, clave: str, tabla: dict, etiqueta: str) -> str:
    valor = str(datos.get(clave, "")).strip()
    if valor not in tabla:
        raise EntradaInvalida(f"{etiqueta} no está en la tabla.")
    return valor


def evaluar(datos: dict) -> dict:
    if not isinstance(datos, dict):
        raise EntradaInvalida("La ficha tiene que ser un objeto.")

    ucs = _numero(datos, "ucs_mpa", "la resistencia UCS")
    rqd = _numero(datos, "rqd", "el RQD")
    espaciado = _numero(datos, "espaciado_m", "el espaciado")
    if ucs < 0 or ucs > 400:
        raise EntradaInvalida("La UCS queda fuera de 0 a 400 MPa.")
    if rqd < 0 or rqd > 100:
        raise EntradaInvalida("El RQD queda fuera de 0 a 100.")
    if espaciado < 0 or espaciado > 20:
        raise EntradaInvalida("El espaciado queda fuera de 0 a 20 m.")

    condicion_id = _opcion(datos, "condicion", CONDICION, "La condición de las discontinuidades")
    agua_id = _opcion(datos, "agua", AGUA, "El agua")
    obra_id = _opcion(datos, "obra", OBRA, "La obra")
    orientacion_id = _opcion(datos, "orientacion", ORIENTACION, "La orientación")

    p_ucs = puntaje_ucs(ucs)
    p_rqd = puntaje_rqd(rqd)
    p_esp = puntaje_espaciado(espaciado)
    p_cond, cond_nombre, cond_detalle = CONDICION[condicion_id]
    p_agua, agua_nombre = AGUA[agua_id]
    ajuste = ORIENTACION[orientacion_id][obra_id]
    basico = p_ucs + p_rqd + p_esp + p_cond + p_agua
    rmr = max(0, min(100, basico + ajuste))
    clase = clase_de(rmr)
    frente = str(datos.get("frente") or "").strip()[:120]

    return {
        "frente": frente,
        "parciales": [
            {"clave": "Resistencia", "detalle": f"UCS {ucs:g} MPa", "puntos": p_ucs, "max": 15},
            {"clave": "RQD", "detalle": f"{rqd:g} %", "puntos": p_rqd, "max": 20},
            {"clave": "Espaciado", "detalle": f"{espaciado:g} m", "puntos": p_esp, "max": 20},
            {"clave": "Discontinuidades", "detalle": f"{cond_nombre}. {cond_detalle}", "puntos": p_cond, "max": 30},
            {"clave": "Agua", "detalle": agua_nombre, "puntos": p_agua, "max": 15},
        ],
        "basico": basico,
        "ajuste": ajuste,
        "ajuste_detalle": f"{ORIENTACION[orientacion_id]['etiqueta']} en {OBRA[obra_id].lower()}",
        "rmr": rmr,
        "clase": clase,
        "fuente": "Bieniawski, Z. T. (1989). Engineering Rock Mass Classifications.",
        "aviso": AVISO,
    }
