import { CAPAS, CLASES_TESELA, ESTACIONES, FUENTES, FUENTES_MAPA, METRICAS } from "./datosModelo";
import { escapeHtml } from "./maps";
import { assetUrl } from "./paths";
import type { Nivel, Vista } from "./types";
import { ZONAS } from "./zonasModelo";

export function fmt(n: number | null | undefined, d = 3): string {
  if (n == null || Number.isNaN(n)) return "–";
  return n.toLocaleString("es-EC", { minimumFractionDigits: d, maximumFractionDigits: d });
}

function km2(n: number, d = 0): string {
  return n.toLocaleString("es-EC", { minimumFractionDigits: d, maximumFractionDigits: d });
}

function ent(n: number): string {
  return n.toLocaleString("es-EC");
}

export function fraseDelta(d: number | null | undefined): string {
  if (d == null || Number.isNaN(d)) return "sin dato";
  if (d >= 0.8) return "muy parecido, según el índice";
  if (d >= 0.5) return "parecido a medias, según el índice";
  if (d >= 0.2) return "poco parecido, según el índice";
  return "casi nada parecido, según el índice";
}

/** Bins aligned with fraseDelta: alto ≥ 0,8; medio ≥ 0,5; bajo ≥ 0,2; casi nulo. */
export function nivelDelta(d: number | null | undefined): string {
  if (d == null || Number.isNaN(d)) return "sin dato";
  if (d >= 0.8) return "alto";
  if (d >= 0.5) return "medio";
  if (d >= 0.2) return "bajo";
  return "casi nulo";
}

export function fraseParecido(cuerpo: "Marte" | "la Luna", d: number | null | undefined, conNumero = true): string {
  const n = nivelDelta(d);
  if (n === "sin dato") return `Parecido a ${cuerpo} según el índice: sin dato`;
  const num = conNumero && d != null ? ` (δ ${fmt(d, 2)})` : "";
  return `Parecido a ${cuerpo} según el índice: ${n}${num}`;
}

export function cajaExplica(titulo: string, cuerpo: string): string {
  return `<aside class="explica" data-testid="explica" aria-label="Qué significa esto">
    <p class="explica-t">${titulo}</p>
    <p>${cuerpo}</p>
  </aside>`;
}

type Banda = "marte" | "luna" | "conjunta";

export function bandaDeVista(vista: Vista): Banda {
  if (vista === "similitud-luna") return "luna";
  if (vista === "clases") return "conjunta";
  return "marte";
}

const PROV_ACENTO: Record<string, string> = { Manabi: "Manabí", "Los Rios": "Los Ríos", Sucumbios: "Sucumbíos" };
const PROV_REGION: Record<string, string> = {
  Guayas: "Costa",
  Manabi: "Costa",
  "El Oro": "Costa",
  "Los Rios": "Costa",
  Loja: "Sierra",
  Orellana: "Amazonía",
  Sucumbios: "Amazonía",
  "Galápagos": "Insular",
};

/* ---------------- Leyenda dentro del mapa ---------------- */

export function legendHTML(vista: Vista): string {
  const b = bandaDeVista(vista);
  const capa = CAPAS[b];
  const filas = CLASES_TESELA.map(
    (c) => `<li><span class="swatch" style="background:${c.rgb}"></span><span class="rng">${c.rango}</span><span>${c.nombre}</span></li>`,
  ).join("");
  return `<div class="title">${escapeHtml(capa.nombre)}</div>
    <p class="leg-line">${escapeHtml(capa.linea)}</p>
    <ul class="leg-clases" aria-label="Clases del índice">${filas}</ul>
    <ul class="leg-otros">
      <li><span class="swatch swatch-vacio"></span><span>${escapeHtml(CAPAS.mascara.nombre)}</span></li>
      <li><span class="swatch swatch-estacion"></span><span>${escapeHtml(CAPAS.estaciones.nombre)} (${ESTACIONES.length})</span></li>
    </ul>
    <details class="note"><summary>Cómo leer este mapa</summary><p>Al alejarte ves el mapa mundial en celdas de 0,05° (unos 5 km); al acercarte a Ecuador, celdas de 1 km. Umbral de alta similitud: índice ≥ 0,95. ${escapeHtml(CAPAS.mascara.linea)}</p></details>`;
}

/* ---------------- Panel de cada mapa ---------------- */

function fuentesHTML(b: Banda): string {
  const items = FUENTES_MAPA[b]
    .map((id) => FUENTES[id])
    .map(
      (f) => `<li><strong>${escapeHtml(f.dato)}.</strong> ${escapeHtml(f.uso)}.<br><span class="cita">${escapeHtml(f.cita)}</span> <a href="${f.url}" target="_blank" rel="noopener noreferrer">Enlace</a></li>`,
    )
    .join("");
  return `<details class="fuentes" data-testid="fuentes-mapa"><summary>Fuentes de los datos de este mapa</summary><ol class="fuentes-lista">${items}</ol></details>`;
}

function tablaGlobal(b: "marte" | "luna"): string {
  const z = b === "marte" ? ZONAS.global_marte : ZONAS.global_luna;
  const filas = z.filas
    .map(
      (r) => `<tr><td>${escapeHtml(r.continente)} · ${escapeHtml(r.tipo === "Sin región fisiográfica cartografiada" ? "otras superficies" : r.tipo.toLowerCase())}</td><td class="num">${km2(r.area_km2)}</td><td class="num">${fmt(r.indice_medio, 2)}</td><td class="num">${fmt(r.indice_max, 2)}</td></tr>`,
    )
    .join("");
  return `<h3>Zonas más parecidas en el mundo</h3>
    <p>Celdas con índice ≥ 0,95: <strong>${km2(z.total_area_km2)} km²</strong> (${ent(z.total_celdas)} celdas de 0,05°). Agrupadas por continente y tipo de terreno; las 10 de mayor área. «Medio» y «Máx.»: índice medio y máximo de esas celdas.</p>
    <div class="tabla-wrap"><table class="validacion zonas" data-testid="zonas-global">
      <thead><tr><th>Continente · tipo de terreno</th><th>Área (km²)</th><th>Medio</th><th>Máx.</th></tr></thead>
      <tbody>${filas}</tbody></table></div>
    <p class="muted">«Otras superficies»: celdas fuera de los polígonos de regiones físicas de Natural Earth. Rusia al este de 60° E se cuenta en Asia. Área = número de celdas × área de la celda a su latitud.</p>`;
}

function tablaEcuador(b: Banda): string {
  const z = b === "marte" ? ZONAS.ecuador_marte : b === "luna" ? ZONAS.ecuador_luna : ZONAS.ecuador_conjunta;
  if (!z.filas.length) {
    return `<h3>Zonas más parecidas en Ecuador</h3>
      <p>Ninguna celda de Ecuador llega a 0,95 en el índice conjunto. El máximo es <strong>${fmt(z.max, 2)}</strong>; ${ent(z.clases[3].celdas)} celdas quedan entre 0,90 y 0,94 (${km2(z.clases[3].area_km2, 1)} km²).</p>`;
  }
  const filas = z.filas
    .map(
      (r) => `<tr><td>${escapeHtml(PROV_ACENTO[r.zona] ?? r.zona)} · ${escapeHtml(PROV_REGION[r.zona] ?? "–")}</td><td class="num">${km2(r.area_km2, 1)}</td><td class="num">${fmt(r.indice_medio, 2)}</td><td class="num">${fmt(r.indice_max, 2)}</td></tr>`,
    )
    .join("");
  return `<h3>Zonas más parecidas en Ecuador</h3>
    <p>Celdas de 1 km con índice ≥ 0,95: <strong>${km2(z.total_area_km2, 1)} km²</strong> (${ent(z.total_celdas)} de ${ent(z.evaluables)} celdas evaluadas). Agrupadas por provincia y región natural.</p>
    <div class="tabla-wrap"><table class="validacion zonas" data-testid="zonas-ecuador">
      <thead><tr><th>Provincia · región</th><th>Área (km²)</th><th>Medio</th><th>Máx.</th></tr></thead>
      <tbody>${filas}</tbody></table></div>
    <p class="muted">Área = número de celdas × área de la celda de 1/120° a su latitud. Celdas fuera de los polígonos de GADM (costa): ${ent(z.total_celdas - z.filas.reduce((s, r) => s + r.celdas, 0))}.</p>`;
}

export function mapPanelHTML(vista: Vista, _nivel: Nivel): string {
  const b = bandaDeVista(vista);
  const capa = CAPAS[b];
  const glob =
    b === "conjunta"
      ? `<h3>Zonas más parecidas en el mundo</h3><p>En el mundo, ${ent(METRICAS.global.conjunta95)} celdas de 0,05° llegan a 0,95 en los dos cuerpos a la vez, de ${ent(METRICAS.global.celdas)} evaluadas.</p>`
      : tablaGlobal(b);
  return `<section class="prose" data-testid="panel-mapa">
    <h2>${escapeHtml(capa.nombre)}</h2>
    <p>${escapeHtml(capa.linea)} 1 es lo más parecido; 0,95 significa más parecido que el 95 % de la superficie terrestre evaluada.</p>
    <ul class="capas-lista">
      <li><strong>${escapeHtml(CAPAS.mascara.nombre)}.</strong> ${escapeHtml(CAPAS.mascara.linea)}</li>
      <li><strong>${escapeHtml(CAPAS.estaciones.nombre)}.</strong> ${escapeHtml(CAPAS.estaciones.linea)}</li>
    </ul>
    ${glob}
    ${tablaEcuador(b)}
    ${estacionesHTML()}
    ${fuentesHTML(b)}
  </section>`;
}

function estacionesHTML(): string {
  const li = ESTACIONES.map(
    (e) => `<li><strong>${escapeHtml(e.nombre)}</strong>, ${escapeHtml(e.lugar)}. ${escapeHtml(e.tipo)}. ${escapeHtml(e.estado)}. <a href="${e.fuente}" target="_blank" rel="noopener noreferrer">Fuente</a></li>`,
  ).join("");
  return `<details class="fuentes"><summary>${escapeHtml(CAPAS.estaciones.nombre)} (${ESTACIONES.length})</summary><ul class="fuentes-lista">${li}</ul></details>`;
}

/* ---------------- Inicio ---------------- */

export function homeHTML(_nivel: Nivel): string {
  const m = METRICAS;
  return `<section class="home" data-testid="home">
    <div class="home-hero">
      <div>
        <h2>¿Dónde en la Tierra se parece a la Luna y a Marte?</h2>
        <p class="lead">Comparamos cada celda de la superficie terrestre con los sitios donde aterrizaron 24 misiones en Marte y en la Luna, usando tres variables: elevación, pendiente y albedo. El resultado es un índice de 0 a 1 para todo el mundo (celdas de 5 km) y para Ecuador (celdas de 1 km).</p>
        <div class="home-actions">
          <button type="button" class="btn btn-primary" data-action="ir" data-ir="similitud-marte">Ver el mapa de Marte</button>
          <button type="button" class="btn btn-ghost" data-action="tour" data-testid="btn-tour">Guíame paso a paso</button>
          <button type="button" class="btn btn-ghost" data-action="ir" data-ir="visualizador">Explorar Ecuador</button>
        </div>
      </div>
      <div class="mapas-duo">
        <button type="button" class="mapa-thumb" data-action="ir" data-ir="similitud-marte">
          <span class="img"><img src="${assetUrl("/productos/indice_marte_mundo.png")}" alt="Índice de similitud con Marte en el mundo" width="1440" height="576" loading="lazy" /></span>
          <span class="cap"><strong>Marte</strong><span>Índice 0–1 en el mundo</span></span>
        </button>
        <button type="button" class="mapa-thumb" data-action="ir" data-ir="similitud-luna">
          <span class="img"><img src="${assetUrl("/productos/indice_luna_mundo.png")}" alt="Índice de similitud con la Luna en el mundo" width="1440" height="576" loading="lazy" /></span>
          <span class="cap"><strong>Luna</strong><span>Índice 0–1 en el mundo</span></span>
        </button>
      </div>
    </div>

    <div class="veredicto">
      <div>
        <h2>Cifras del modelo</h2>
        <p>Se evaluaron ${ent(m.global.celdas)} celdas de 0,05° en el mundo y ${ent(m.ecuador.celdas)} celdas de 1 km en Ecuador, después de quitar bosque, cultivos, humedales y zonas urbanas.</p>
      </div>
      <div>
        <div class="figuras">
          <div class="fig is-main"><span class="v">${km2(ZONAS.global_marte.total_area_km2)}<small> km²</small></span><span class="l">del mundo con índice de Marte ≥ 0,95</span></div>
          <div class="fig"><span class="v">${fmt(m.auc_marte.v, 2)}</span><span class="l">AUC Marte (IC 95 %: ${fmt(m.auc_marte.ic[0], 2)}–${fmt(m.auc_marte.ic[1], 2)})</span></div>
          <div class="fig"><span class="v">${fmt(m.auc_luna.v, 2)}</span><span class="l">AUC Luna (IC 95 %: ${fmt(m.auc_luna.ic[0], 2)}–${fmt(m.auc_luna.ic[1], 2)})</span></div>
        </div>
      </div>
    </div>

    <div class="como">
      <div>
        <h2>Cómo se calcula</h2>
        ${cajaExplica(
          "Lo que mide el índice",
          "Solo la superficie: elevación, pendiente y albedo. No mide clima, minerales ni historia geológica.",
        )}
      </div>
      <div><ol class="pasos-home">
        <li>Medimos elevación, pendiente y albedo en 100 000 puntos de la Tierra, de Marte y de la Luna, y pasamos cada variable a percentil dentro de su cuerpo.</li>
        <li>Tomamos la firma de los sitios de aterrizaje: 5 misiones en Marte y 14 en la Luna.</li>
        <li>Para cada celda terrestre calculamos la distancia a la firma más cercana y la convertimos en un índice de 0 a 1.</li>
        <li>Quitamos bosque, humedales, cultivos y zonas urbanas con la cobertura del suelo MODIS de la NASA.</li>
      </ol></div>
    </div>

    <div class="destinos">
      <h2>Sigue explorando</h2>
      <ul>
        <li><button type="button" class="home-card" data-action="ir" data-ir="similitud-luna"><strong>Mapa de la Luna</strong><span>El mismo índice frente a los sitios de aterrizaje lunares.</span></button></li>
        <li><button type="button" class="home-card" data-action="ir" data-ir="validacion"><strong>Validación</strong><span>Qué significa cada parámetro, su valor y los umbrales usados.</span></button></li>
        <li><button type="button" class="home-card" data-action="ir" data-ir="incertidumbre"><strong>Límites</strong><span>Lo que el índice no mide y de dónde salen los datos.</span></button></li>
        <li><button type="button" class="home-card" data-action="ir" data-ir="visualizador"><strong>Explorar Ecuador</strong><span>Relieve en 3D con la leyenda y las estadísticas del índice en Ecuador.</span></button></li>
      </ul>
    </div>
  </section>`;
}

export const TOUR_PASOS: { vista: Vista; titulo: string; cuerpo: string }[] = [
  {
    vista: "similitud-marte",
    titulo: "Empecemos por Marte",
    cuerpo:
      "Cada color dice qué tan parecida es la celda a los sitios de aterrizaje en Marte, en un índice de 0 a 1. La leyenda está dentro del mapa. Aléjate para ver el mundo y acércate a Ecuador para ver celdas de 1 km.",
  },
  {
    vista: "similitud-luna",
    titulo: "Ahora, la Luna",
    cuerpo: "El mismo mapa comparado con los sitios de aterrizaje lunares. En el panel ves las zonas más parecidas por continente y por provincia.",
  },
  {
    vista: "validacion",
    titulo: "Validación",
    cuerpo: "Qué mide cada parámetro de validación, su valor con intervalo de confianza y los umbrales usados.",
  },
  {
    vista: "visualizador",
    titulo: "Explorar Ecuador",
    cuerpo: "El relieve de Ecuador en 3D, con la leyenda del índice y sus estadísticas: área por clase, distribución y máximos.",
  },
];

/* ---------------- Validación ---------------- */

export function validationHTML(_nivel: Nivel): string {
  const m = METRICAS;
  const r = m.recuperacion;
  return `<section class="prose" data-testid="validacion-oficial">
    <h2>Validación</h2>
    <p>Tres pruebas complementarias. Cada una responde a una pregunta distinta.</p>

    <h3>1. AUC: ¿el índice ordena bien?</h3>
    <p>El AUC (área bajo la curva ROC) es la probabilidad de que un lugar análogo reciba un índice más alto que uno no análogo. 0,5 equivale al azar y 1 a un orden perfecto. Entre corchetes, el intervalo de confianza del 95 % por remuestreo (bootstrap).</p>
    <div class="tabla-wrap"><table class="validacion">
      <thead><tr><th>Cuerpo</th><th>AUC</th><th>IC 95 %</th><th>Positivos / negativos</th></tr></thead>
      <tbody>
        <tr><td>Marte</td><td class="num">${fmt(m.auc_marte.v, 3)}</td><td class="num">[${fmt(m.auc_marte.ic[0], 2)}–${fmt(m.auc_marte.ic[1], 2)}]</td><td class="num">${m.auc_marte.pos} / ${m.auc_marte.neg}</td></tr>
        <tr><td>Luna</td><td class="num">${fmt(m.auc_luna.v, 3)}</td><td class="num">[${fmt(m.auc_luna.ic[0], 2)}–${fmt(m.auc_luna.ic[1], 2)}]</td><td class="num">${m.auc_luna.pos} / ${m.auc_luna.neg}</td></tr>
      </tbody></table></div>
    <p class="muted">La muestra es pequeña, por eso los intervalos son anchos. Los lugares no análogos son en su mayoría bosque y cultivo, que la máscara ya excluye, así que el AUC depende en parte de la máscara.</p>

    <h3>2. Recuperación frente a un modelo nulo: ¿supera al azar?</h3>
    <p>Cuenta cuántos lugares análogos de referencia caen en celdas con índice ≥ ${fmt(r.umbral, 2)} y lo compara con ${ent(r.permutaciones)} permutaciones al azar. En cada permutación, cada lugar se reubica en una celda elegible de un bloque de 10° × 10° de su misma franja de latitud.</p>
    <p>Resultado: <strong>${r.recuperados} de ${r.de}</strong>; el azar da en promedio ${fmt(r.nulo_media, 2)} (p = ${fmt(r.p, 2)}). Con p &gt; 0,05, la recuperación no se distingue del azar.</p>

    <h3>3. Estabilidad Jaccard: ¿cambia el resultado si quitamos algo?</h3>
    <p>El índice de Jaccard compara el conjunto de celdas ≥ 0,95 antes y después de un cambio: 1 es el mismo conjunto y 0 no comparten ninguna celda.</p>
    <ul>
      <li>Al quitar una variable (elevación, pendiente o albedo), en Ecuador: Marte ${fmt(m.jaccard_variable_ecuador.marte[0], 2)}–${fmt(m.jaccard_variable_ecuador.marte[1], 2)}; Luna ${fmt(m.jaccard_variable_ecuador.luna[0], 2)}–${fmt(m.jaccard_variable_ecuador.luna[1], 2)}. Rango conjunto: <strong>0,12–0,29</strong>. Las tres variables pesan: ninguna sobra.</li>
      <li>Al quitar una misión de referencia, en Ecuador: Marte ${fmt(m.jaccard_mision_ecuador.marte[0], 2)}–${fmt(m.jaccard_mision_ecuador.marte[1], 2)}; Luna ${fmt(m.jaccard_mision_ecuador.luna[0], 2)}–${fmt(m.jaccard_mision_ecuador.luna[1], 2)}.</li>
    </ul>

    <h3>Umbrales usados</h3>
    <ul>
      <li>Alta similitud: índice ≥ 0,95 (más parecido que el 95 % de la Tierra evaluada). Sensibilidad probada con 0,90 y 0,97.</li>
      <li>Bosque: se excluye la celda con más de 5 % de bosque IGBP (clases 1–5) o bosque mayoritario, y un borde de 3 × 3 celdas alrededor.</li>
      <li>Clases IGBP excluidas: 11 humedales permanentes, 12 cultivos, 13 zonas urbanas y 14 mosaico de cultivos y vegetación natural.</li>
      <li>Rejillas: mundo a 0,05° (unos 5 km) y Ecuador a 1/120° (unos 1 km).</li>
      <li>Referencia del percentil: 100 000 puntos por cuerpo.</li>
    </ul>
    <p class="muted">Celdas evaluadas: ${ent(m.global.celdas)} en el mundo y ${ent(m.ecuador.celdas)} en Ecuador. La máscara quitó ${ent(m.mascara.bosque)} celdas globales por bosque y ${ent(m.mascara.uso)} por otros usos.</p>

    <h3>Cómo mejorar la identificación</h3>
    <p>Se pueden añadir variables de hidromorfología para separar superficies que hoy se parecen solo por relieve y albedo: red de drenaje y su densidad, acumulación de flujo, humedad del suelo y formas de erosión (abanicos, cárcavas, cauces secos). Es trabajo futuro: no está calculado en esta entrega.</p>
  </section>`;
}

/* ---------------- Límites ---------------- */

export function uncertaintyHTML(_nivel: Nivel): string {
  return `<section class="prose" data-testid="nota-incertidumbre">
    <h2>Límites del índice</h2>
    <h3>Qué mide y qué no</h3>
    <ul>
      <li>Mide elevación, pendiente y albedo. No mide clima, mineralogía, química del suelo ni historia geológica.</li>
      <li>Es relativo: 0,95 quiere decir más parecido que el 95 % de la Tierra evaluada, no «igual a Marte».</li>
    </ul>
    <h3>Datos</h3>
    <ul>
      <li>La elevación terrestre es GMTED2010 (USGS), no un producto NASA.</li>
      <li>La máscara usa MODIS MCD12Q1 v061 de 2022 leído de las teselas NASA GIBS; el producto MCD12C1 original pide inicio de sesión en Earthdata.</li>
      <li>Las celdas de 5 km y de 1 km suavizan el relieve local: un cráter o un cono pequeño cabe en una sola celda.</li>
      <li>Los datums verticales de Marte, la Luna y la Tierra no son equivalentes al metro; por eso cada variable se compara en percentiles dentro de su cuerpo.</li>
    </ul>
    <h3>Muestra de validación</h3>
    <p>La validación usa pocos lugares de referencia: los intervalos de confianza son anchos y la recuperación no supera al azar. Los detalles están en Validación.</p>
  </section>`;
}

export function futureWorkHTML(): string {
  return `<section class="prose" data-testid="trabajo-futuro">
    <h2>Trabajo futuro</h2>
    <ul>
      <li>Añadir variables de hidromorfología: red de drenaje, acumulación de flujo, humedad del suelo y formas de erosión.</li>
      <li>Reemplazar GMTED2010 por NASADEM (NASA) en la elevación terrestre.</li>
      <li>Probar escalas emparejadas entre cuerpos y relieve relativo en lugar de elevación absoluta.</li>
      <li>Ampliar la muestra de validación para estrechar los intervalos de confianza.</li>
    </ul>
    <p class="muted">Nada de esta lista está calculado en esta entrega.</p>
  </section>`;
}

/* ---------------- Explorar Ecuador ---------------- */

export function explorarEcuadorHTML(): string {
  const bloques = (["marte", "luna", "conjunta"] as const)
    .map((b) => {
      const z = b === "marte" ? ZONAS.ecuador_marte : b === "luna" ? ZONAS.ecuador_luna : ZONAS.ecuador_conjunta;
      const total = z.clases.reduce((s, c) => s + c.area_km2, 0);
      const barras = [...z.clases]
        .reverse()
        .map((c) => {
          const col = CLASES_TESELA.find((t) => t.rango === c.clase)?.rgb ?? "#888";
          const pct = (100 * c.area_km2) / total;
          return `<tr><td><span class="swatch" style="background:${col}"></span> ${c.clase}</td><td class="num">${km2(c.area_km2, 1)}</td><td class="num">${fmt(pct, 1)} %</td><td class="bar"><span style="width:${pct.toFixed(1)}%;background:${col}"></span></td></tr>`;
        })
        .join("");
      return `<h3>${escapeHtml(CAPAS[b].nombre)}</h3>
        <dl class="kv-mini">
          <div><dt>Índice máximo</dt><dd>${fmt(z.max, 2)}</dd></div>
          <div><dt>Mediana (cuartiles)</dt><dd>${fmt(z.mediana, 2)} (${fmt(z.p25, 2)}–${fmt(z.p75, 2)})</dd></div>
          <div><dt>Área ≥ 0,95</dt><dd>${km2(z.total_area_km2, 1)} km²</dd></div>
        </dl>
        <div class="tabla-wrap"><table class="validacion clases-area">
          <thead><tr><th>Clase</th><th>Área (km²)</th><th>%</th><th>Distribución</th></tr></thead>
          <tbody>${barras}</tbody></table></div>`;
    })
    .join("");
  return `<section class="prose explorar-ecuador" data-testid="explorar-ecuador">
    <h2>Explorar Ecuador</h2>
    <p>Estadísticas exploratorias del índice en ${ent(ZONAS.ecuador_marte.evaluables)} celdas de 1 km evaluadas (${km2(ZONAS.ecuador_marte.area_evaluable_km2)} km²), después de la máscara de vegetación y cultivos.</p>
    ${bloques}
    <p class="muted">Área = número de celdas × área de la celda de 1/120° a su latitud.</p>
  </section>`;
}
