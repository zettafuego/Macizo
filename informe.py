"""Arma el pedido al modelo y lee su respuesta.

El modelo redacta. No calcula. La ficha que entra aquí ya trae el RMR.
"""

from __future__ import annotations

import json
import re

SYSTEM = """Eres el redactor de Macizo, para un ingeniero de minas que ya mapeó el frente.
La ficha trae el RMR89 calculado. Ese número, la clase y los puntajes son la fuente.
No los recalcules ni los cambies. Si una pregunta pide otro número, di que la ficha manda.
No diseñes sostenimiento: no des longitud de perno, espaciamiento, espesor de shotcrete ni tipo de cuadro.
El tiempo de autosoporte es orientación empírica de Bieniawski 1989, no un permiso de excavación.
Escribe en español llano, como se habla en labor.
Responde solo un objeto JSON con estas claves:
- lectura: un párrafo de cuatro a seis oraciones sobre este frente.
- que_mirar: una lista de exactamente tres frases cortas, cosas que hay que volver a ver en el frente.
- limite: una oración que recuerde que esto no diseña el sostenimiento.
No uses markdown."""


def pedido(ficha: dict, pregunta: str = "", hilo: list | None = None) -> list:
    mensajes = [{"role": "system", "content": SYSTEM}]
    ficha_texto = json.dumps(ficha, ensure_ascii=False)
    mensajes.append({
        "role": "user",
        "content": "Redacta el informe de esta ficha. No cambies el RMR.\n" + ficha_texto,
    })
    for turno in (hilo or [])[-4:]:
        rol = turno.get("rol")
        texto = str(turno.get("texto") or "").strip()[:2000]
        if rol not in ("user", "assistant") or not texto:
            continue
        mensajes.append({"role": rol, "content": texto})
    pregunta = (pregunta or "").strip()[:600]
    if pregunta:
        mensajes.append({
            "role": "user",
            "content": "Responde esta pregunta sobre la misma ficha, sin cambiar el RMR:\n" + pregunta,
        })
    return mensajes


def texto_de_respuesta(payload: dict) -> str:
    directo = payload.get("output_text")
    if isinstance(directo, str) and directo.strip():
        return directo.strip()
    partes = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for bloque in item.get("content") or []:
            if not isinstance(bloque, dict):
                continue
            if bloque.get("type") in ("output_text", "text") and bloque.get("text"):
                partes.append(bloque["text"])
    return "\n".join(partes).strip()


def interpretar(texto: str) -> dict:
    limpio = (texto or "").strip()
    limpio = re.sub(r"^```(?:json)?\s*", "", limpio)
    limpio = re.sub(r"\s*```$", "", limpio)
    try:
        datos = json.loads(limpio)
    except json.JSONDecodeError:
        inicio = limpio.find("{")
        fin = limpio.rfind("}")
        datos = None
        if inicio >= 0 and fin > inicio:
            try:
                datos = json.loads(limpio[inicio:fin + 1])
            except json.JSONDecodeError:
                datos = None
        if not isinstance(datos, dict):
            return {
                "lectura": limpio or "El modelo no devolvió texto.",
                "que_mirar": [],
                "limite": "",
            }
    if not isinstance(datos, dict):
        raise ValueError("La respuesta no es un objeto.")
    mirar = datos.get("que_mirar") or []
    if not isinstance(mirar, list):
        mirar = [str(mirar)]
    return {
        "lectura": str(datos.get("lectura") or "").strip(),
        "que_mirar": [str(item).strip() for item in mirar if str(item).strip()][:3],
        "limite": str(datos.get("limite") or "").strip(),
    }
