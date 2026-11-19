import json
import unittest

from informe import interpretar, pedido, texto_de_respuesta
from rmr import EntradaInvalida, evaluar


FICHA_III = {
    "frente": "Nv 2450, crucero 3",
    "ucs_mpa": 70,
    "rqd": 60,
    "espaciado_m": 0.3,
    "condicion": "regular",
    "agua": "humeda",
    "obra": "tunel",
    "orientacion": "regular",
}


class RmrTest(unittest.TestCase):
    def test_frente_de_ejemplo_es_clase_iii(self):
        ficha = evaluar(FICHA_III)
        self.assertEqual([7, 13, 10, 20, 10], [p["puntos"] for p in ficha["parciales"]])
        self.assertEqual(60, ficha["basico"])
        self.assertEqual(-5, ficha["ajuste"])
        self.assertEqual(55, ficha["rmr"])
        self.assertEqual("III", ficha["clase"]["id"])
        self.assertEqual("Roca regular", ficha["clase"]["nombre"])

    def test_cortes_de_ucs_rqd_y_espaciado(self):
        self.assertEqual(15, evaluar(_con(ucs_mpa=251))["parciales"][0]["puntos"])
        self.assertEqual(12, evaluar(_con(ucs_mpa=250))["parciales"][0]["puntos"])
        self.assertEqual(12, evaluar(_con(ucs_mpa=100))["parciales"][0]["puntos"])
        self.assertEqual(7, evaluar(_con(ucs_mpa=99))["parciales"][0]["puntos"])
        self.assertEqual(1, evaluar(_con(ucs_mpa=1))["parciales"][0]["puntos"])
        self.assertEqual(0, evaluar(_con(ucs_mpa=0.5))["parciales"][0]["puntos"])

        self.assertEqual(20, evaluar(_con(rqd=90))["parciales"][1]["puntos"])
        self.assertEqual(17, evaluar(_con(rqd=89))["parciales"][1]["puntos"])
        self.assertEqual(17, evaluar(_con(rqd=75))["parciales"][1]["puntos"])
        self.assertEqual(13, evaluar(_con(rqd=74))["parciales"][1]["puntos"])
        self.assertEqual(8, evaluar(_con(rqd=25))["parciales"][1]["puntos"])
        self.assertEqual(3, evaluar(_con(rqd=0))["parciales"][1]["puntos"])

        self.assertEqual(20, evaluar(_con(espaciado_m=2.01))["parciales"][2]["puntos"])
        self.assertEqual(15, evaluar(_con(espaciado_m=2))["parciales"][2]["puntos"])
        self.assertEqual(10, evaluar(_con(espaciado_m=0.2))["parciales"][2]["puntos"])
        self.assertEqual(8, evaluar(_con(espaciado_m=0.06))["parciales"][2]["puntos"])
        self.assertEqual(5, evaluar(_con(espaciado_m=0.05))["parciales"][2]["puntos"])

    def test_clase_en_los_bordes(self):
        self.assertEqual("I", evaluar(_con(ucs_mpa=260, rqd=100, espaciado_m=3, condicion="muy_buena", agua="seca", orientacion="muy_favorable"))["clase"]["id"])
        self.assertEqual("II", evaluar(_con(ucs_mpa=70, rqd=80, espaciado_m=0.8, condicion="regular", agua="humeda", orientacion="favorable"))["clase"]["id"])
        self.assertEqual("V", evaluar(_con(ucs_mpa=2, rqd=10, espaciado_m=0.02, condicion="muy_pobre", agua="flujo", obra="talud", orientacion="muy_desfavorable"))["clase"]["id"])
        mala = evaluar(_con(ucs_mpa=2, rqd=10, espaciado_m=0.02, condicion="muy_pobre", agua="flujo", obra="talud", orientacion="muy_desfavorable"))
        self.assertEqual(0, mala["rmr"])

    def test_rechaza_rqd_imposible(self):
        with self.assertRaises(EntradaInvalida):
            evaluar(_con(rqd=120))

    def test_el_pedido_obliga_a_no_recalcular(self):
        ficha = evaluar(FICHA_III)
        mensajes = pedido(ficha, "¿Puedo abrir 8 m de luz?", [{"rol": "assistant", "texto": "Lectura previa."}])
        self.assertEqual("system", mensajes[0]["role"])
        self.assertIn("No los recalcules", mensajes[0]["content"])
        self.assertIn("55", mensajes[1]["content"])
        self.assertEqual("assistant", mensajes[2]["role"])
        self.assertIn("8 m", mensajes[3]["content"])

    def test_lee_json_con_cerco_y_texto_suelto(self):
        cercado = "```json\n" + json.dumps({
            "lectura": "Clase III.",
            "que_mirar": ["Agua", "Cuñas", "Relleno", "Sobra"],
            "limite": "No diseña.",
        }) + "\n```"
        dato = interpretar(cercado)
        self.assertEqual("Clase III.", dato["lectura"])
        self.assertEqual(["Agua", "Cuñas", "Relleno"], dato["que_mirar"])

        suelto = 'Nota previa {"lectura": "Va el párrafo.", "que_mirar": ["Uno"], "limite": "Tope."} gracias'
        dato = interpretar(suelto)
        self.assertEqual("Va el párrafo.", dato["lectura"])

    def test_saca_el_texto_del_sobre_de_la_api(self):
        payload = {
            "output": [
                {"type": "reasoning", "content": []},
                {"type": "message", "content": [{"type": "output_text", "text": "  listo  "}]},
            ]
        }
        self.assertEqual("listo", texto_de_respuesta(payload))
        self.assertEqual("directo", texto_de_respuesta({"output_text": "directo"}))


def _con(**cambios):
    base = dict(FICHA_III)
    base.update(cambios)
    return base


if __name__ == "__main__":
    unittest.main()
