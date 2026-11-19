"""Macizo: la ficha se calcula aquí y el párrafo sale de la API de xAI.

La clave no sale del servidor. Las respuestas no se guardan en la cuenta (store: false).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from informe import interpretar, pedido, texto_de_respuesta
from rmr import EntradaInvalida, evaluar

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
XAI_URL = "https://api.x.ai/v1/responses"
MODELO = "grok-4.7"


def cargar_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for linea in path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        if clave and clave not in os.environ:
            os.environ[clave] = valor


def clave_api() -> str:
    return (os.environ.get("XAI_API_KEY") or "").strip()


def modelo() -> str:
    return (os.environ.get("XAI_MODEL") or MODELO).strip() or MODELO


def redactar(ficha: dict, pregunta: str, hilo: list) -> dict:
    clave = clave_api()
    if not clave:
        raise RuntimeError("Falta XAI_API_KEY. El cálculo sí está. La redacción pide la clave en .env.")
    cuerpo = {
        "model": modelo(),
        "store": False,
        "input": pedido(ficha, pregunta, hilo),
    }
    req = urllib.request.Request(
        XAI_URL,
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + clave,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"La API respondió {exc.code}. {detalle}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No llegué a la API. {exc.reason}") from exc
    return interpretar(texto_de_respuesta(payload))


class MacizoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        ruta = self.path.split("?", 1)[0]
        if ruta == "/api/health":
            self._json(200, {"ok": True, "modelo": modelo(), "clave": bool(clave_api())})
            return
        if ruta == "/":
            ruta = "/index.html"
        self._estatico(ruta)

    def do_POST(self) -> None:
        ruta = self.path.split("?", 1)[0]
        if ruta not in ("/api/calcular", "/api/informe"):
            self._json(404, {"error": "No existe esa ruta."})
            return
        try:
            largo = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            largo = 0
        if largo > 20_000:
            self._json(413, {"error": "La ficha es demasiado larga."})
            return
        bruto = self.rfile.read(largo).decode("utf-8") if largo else ""
        try:
            datos = json.loads(bruto) if bruto else {}
        except json.JSONDecodeError:
            self._json(400, {"error": "El cuerpo no es JSON."})
            return
        if not isinstance(datos, dict):
            self._json(400, {"error": "El cuerpo tiene que ser un objeto."})
            return
        try:
            ficha = evaluar(datos)
        except EntradaInvalida as exc:
            self._json(400, {"error": str(exc)})
            return
        if ruta == "/api/calcular":
            self._json(200, {"ficha": ficha})
            return
        hilo = datos.get("hilo") if isinstance(datos.get("hilo"), list) else []
        try:
            texto = redactar(ficha, str(datos.get("pregunta") or ""), hilo)
        except RuntimeError as exc:
            self._json(503, {"error": str(exc), "ficha": ficha})
            return
        self._json(200, {"ficha": ficha, "informe": texto, "modelo": modelo()})

    def _estatico(self, ruta: str) -> None:
        relativo = ruta.lstrip("/")
        if not relativo or ".." in relativo.replace("\\", "/").split("/"):
            self.send_error(404)
            return
        archivo = (STATIC / relativo).resolve()
        if not str(archivo).startswith(str(STATIC.resolve())) or not archivo.is_file():
            self.send_error(404)
            return
        tipos = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}
        cuerpo = archivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipos.get(archivo.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, codigo: int, payload: dict) -> None:
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, fmt: str, *args) -> None:
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


def main() -> None:
    cargar_env()
    puerto = int(os.environ.get("PORT", "8788"))
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), MacizoHandler)
    print("Macizo en http://127.0.0.1:%s" % puerto)
    print("Modelo %s. Clave %s." % (modelo(), "lista" if clave_api() else "ausente"))
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrado.")


if __name__ == "__main__":
    main()
