# Macizo

Informe de un frente de roca. El RMR de Bieniawski 1989 lo calcula el código. Un modelo de lenguaje redacta esa ficha y contesta preguntas sobre ella, sin permiso para cambiar el número ni para diseñar el sostenimiento.

Lo armó Eduardo Yampier Sánchez Cotrina, ingeniero de minas. Es el proyecto de portafolio de un flujo LLM de punta a punta sobre un tema de labor: mapear, clasificar y dejar el párrafo por escrito.

## Qué hace una pasada

1. La persona anota resistencia, RQD, espaciado, condición de las discontinuidades, agua, obra y orientación.
2. `rmr.py` pone los puntajes publicados, suma el básico, aplica el ajuste y asigna la clase I a V.
3. Si pide el informe, `server.py` manda esa ficha ya calculada a la API de xAI (`grok-4.7`, Responses API, `store: false`).
4. El modelo devuelve un párrafo, tres cosas que volver a mirar en el frente y el límite del resultado.
5. Una pregunta posterior viaja con la misma ficha. El servidor vuelve a calcular antes de llamar al modelo.

La clave queda en el servidor. El navegador no la ve.

## Qué no hace

No usa la cartilla interna de ninguna unidad. No recomienda longitud de perno, espaciamiento, espesor de shotcrete ni cuadros. El tiempo de autosoporte que muestra la ficha es la orientación empírica de Bieniawski 1989, no un permiso de excavación.

GeoRMR sigue siendo la herramienta de faena. Macizo es la pieza pública del mismo oficio.

## Cómo correrlo

Hace falta Python 3.10 o mayor. No hay dependencias que instalar.

```bat
cd C:\Users\Eduardo\Macizo
copy .env.example .env
```

En `.env`, pega una clave de [console.x.ai](https://console.x.ai/team/default/api-keys):

```env
XAI_API_KEY=xai-...
```

Después:

```bat
python server.py
```

Abre http://127.0.0.1:8788

Sin clave, **Calcular** responde igual. **Redactar informe** explica que falta la clave y aun así devuelve la ficha.

Pruebas del cálculo y del formato de la respuesta, sin gastar la API:

```bat
python -m unittest test_rmr.py
```

## Piezas

| Archivo | Oficio |
| --- | --- |
| `rmr.py` | Puntajes, suma, clase y el rechazo de una ficha imposible |
| `informe.py` | El pedido al modelo y la lectura de su JSON |
| `server.py` | Estáticos, `POST /api/calcular`, `POST /api/informe`, `GET /api/health` |
| `static/` | La hoja de mapeo y el resultado |

Proveedor: xAI, compatible con la API de OpenAI. Base `https://api.x.ai/v1`. Modelo por defecto `grok-4.7`. Se cambia con `XAI_MODEL`.
