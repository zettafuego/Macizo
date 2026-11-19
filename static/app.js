const form = document.getElementById("ficha");
const estado = document.getElementById("estado");
const resultado = document.getElementById("resultado");
const informe = document.getElementById("informe");
const preguntaForm = document.getElementById("pregunta-form");
const redactarBtn = document.getElementById("redactar");

let ultimaFicha = null;
let hilo = [];

function datos() {
  const crudo = new FormData(form);
  return {
    frente: crudo.get("frente"),
    ucs_mpa: Number(crudo.get("ucs_mpa")),
    rqd: Number(crudo.get("rqd")),
    espaciado_m: Number(crudo.get("espaciado_m")),
    condicion: crudo.get("condicion"),
    agua: crudo.get("agua"),
    obra: crudo.get("obra"),
    orientacion: crudo.get("orientacion"),
  };
}

function escapar(texto) {
  return String(texto)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function pintarFicha(ficha) {
  ultimaFicha = ficha;
  resultado.hidden = false;
  document.getElementById("frente-nombre").textContent = ficha.frente || "Frente sin nombre";
  document.getElementById("rmr-numero").textContent = String(ficha.rmr);
  document.getElementById("clase-nombre").textContent = "Clase " + ficha.clase.id + " · " + ficha.clase.nombre;
  document.getElementById("parciales").innerHTML = ficha.parciales.map(function (p) {
    return "<li><span>" + escapar(p.clave) + " · " + escapar(p.detalle) + "</span><b>" + escapar(p.puntos) + "/" + escapar(p.max) + "</b></li>";
  }).join("");
  const signo = ficha.ajuste > 0 ? "+" : "";
  document.getElementById("ajuste").textContent =
    "Básico " + ficha.basico + "  ·  ajuste " + signo + ficha.ajuste + " (" + ficha.ajuste_detalle + ")";
  document.getElementById("autosoporte").textContent =
    "Autosoporte empírico: " + ficha.clase.autosoporte + ". Cohesión " + ficha.clase.cohesion + ", fricción " + ficha.clase.friccion + ".";
  document.getElementById("aviso").textContent = ficha.aviso;
}

function pintarInforme(texto) {
  informe.hidden = false;
  preguntaForm.hidden = false;
  document.getElementById("lectura").textContent = texto.lectura || "";
  document.getElementById("mirar").innerHTML = (texto.que_mirar || []).map(function (item) {
    return "<li>" + escapar(item) + "</li>";
  }).join("");
  document.getElementById("limite").textContent = texto.limite || "";
  if (texto.lectura) {
    hilo.push({ rol: "assistant", texto: texto.lectura });
    hilo = hilo.slice(-4);
  }
}

async function post(ruta, extra) {
  const cuerpo = Object.assign(datos(), extra || {});
  const resp = await fetch(ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  const json = await resp.json();
  if (!resp.ok) {
    if (json.ficha) pintarFicha(json.ficha);
    throw new Error(json.error || "No se pudo completar.");
  }
  return json;
}

form.addEventListener("submit", async function (evento) {
  evento.preventDefault();
  estado.textContent = "Calculando la ficha…";
  informe.hidden = true;
  preguntaForm.hidden = true;
  hilo = [];
  try {
    const json = await post("/api/calcular");
    pintarFicha(json.ficha);
    estado.textContent = "Ficha lista. El número ya no depende del modelo.";
  } catch (err) {
    estado.textContent = err.message;
  }
});

redactarBtn.addEventListener("click", async function () {
  estado.textContent = "Redactando sobre la ficha calculada…";
  redactarBtn.disabled = true;
  hilo = [];
  try {
    const json = await post("/api/informe");
    pintarFicha(json.ficha);
    pintarInforme(json.informe);
    estado.textContent = "Informe de " + json.modelo + ". El RMR sigue siendo el de la ficha.";
  } catch (err) {
    estado.textContent = err.message;
  } finally {
    redactarBtn.disabled = false;
  }
});

preguntaForm.addEventListener("submit", async function (evento) {
  evento.preventDefault();
  const pregunta = new FormData(preguntaForm).get("pregunta");
  if (!pregunta || !String(pregunta).trim()) return;
  estado.textContent = "Respondiendo con la misma ficha…";
  hilo.push({ rol: "user", texto: String(pregunta) });
  try {
    const json = await post("/api/informe", { pregunta: pregunta, hilo: hilo.slice(0, -1) });
    pintarFicha(json.ficha);
    pintarInforme(json.informe);
    estado.textContent = "Misma ficha, RMR " + json.ficha.rmr + ".";
    preguntaForm.reset();
  } catch (err) {
    hilo.pop();
    estado.textContent = err.message;
  }
});
