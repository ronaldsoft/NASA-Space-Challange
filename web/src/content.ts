import { CAPAS, ESTACIONES, clasesTesela, FUENTES, FUENTES_MAPA, METRICAS, MISIONES, coordTexto, rangoTxt } from "./datosModelo";
import { CONTINENTES_EN, TIPOS_EN } from "./datosModelo.en";
import { isEn, LOCALE, tr } from "./i18n";
import { escapeHtml } from "./maps";
import { assetUrl } from "./paths";
import type { Nivel, Vista } from "./types";
import { ZONAS } from "./zonasModelo";

export function fmt(n: number | null | undefined, d = 3): string {
  if (n == null || Number.isNaN(n)) return "–";
  return n.toLocaleString(LOCALE, { minimumFractionDigits: d, maximumFractionDigits: d });
}

function km2(n: number, d = 0): string {
  return n.toLocaleString(LOCALE, { minimumFractionDigits: d, maximumFractionDigits: d });
}

function ent(n: number): string {
  return n.toLocaleString(LOCALE);
}

export function fraseDelta(d: number | null | undefined): string {
  if (d == null || Number.isNaN(d)) return tr("sin dato", "no data");
  if (d >= 0.8) return tr("muy parecido, según el índice", "very similar, according to the index");
  if (d >= 0.5) return tr("parecido a medias, según el índice", "somewhat similar, according to the index");
  if (d >= 0.2) return tr("poco parecido, según el índice", "slightly similar, according to the index");
  return tr("casi nada parecido, según el índice", "hardly similar at all, according to the index");
}

/** Bins aligned with fraseDelta: alto ≥ 0,8; medio ≥ 0,5; bajo ≥ 0,2; casi nulo. */
export function nivelDelta(d: number | null | undefined): string {
  if (d == null || Number.isNaN(d)) return tr("sin dato", "no data");
  if (d >= 0.8) return tr("alto", "high");
  if (d >= 0.5) return tr("medio", "medium");
  if (d >= 0.2) return tr("bajo", "low");
  return tr("casi nulo", "almost none");
}

export function fraseParecido(cuerpo: "Marte" | "la Luna", d: number | null | undefined, conNumero = true): string {
  const n = nivelDelta(d);
  const nombre = tr(cuerpo, cuerpo === "Marte" ? "Mars" : "the Moon");
  if (d == null || Number.isNaN(d)) return tr(`Parecido a ${nombre} según el índice: sin dato`, `Similarity to ${nombre} according to the index: no data`);
  const num = conNumero ? ` (δ ${fmt(d, 2)})` : "";
  return tr(`Parecido a ${nombre} según el índice: ${n}${num}`, `Similarity to ${nombre} according to the index: ${n}${num}`);
}

export function cajaExplica(titulo: string, cuerpo: string): string {
  return `<aside class="explica" data-testid="explica" aria-label="${tr("Qué significa esto", "What this means")}">
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
  Guayas: tr("Costa", "Coast"),
  Manabi: tr("Costa", "Coast"),
  "El Oro": tr("Costa", "Coast"),
  "Los Rios": tr("Costa", "Coast"),
  Loja: tr("Sierra", "Highlands"),
  Orellana: tr("Amazonía", "Amazon"),
  Sucumbios: tr("Amazonía", "Amazon"),
  "Galápagos": tr("Insular", "Island"),
};

/* ---------------- Leyenda dentro del mapa ---------------- */

const HOW_TO_READ = tr("Cómo leer este mapa", "How to read this map");

/** Leyenda del globo de Marte o de la Luna: sitios de aterrizaje de las firmas. */
export function legendCuerpoHTML(cuerpo: "marte" | "luna"): string {
  const usadas = MISIONES.filter((m) => m.cuerpo === cuerpo && m.usada).length;
  const fuera = MISIONES.filter((m) => m.cuerpo === cuerpo && !m.usada).length;
  const nombre = cuerpo === "marte" ? tr("Marte", "Mars") : tr("Luna", "Moon");
  const relieve = cuerpo === "marte" ? "MOLA MEGDR 64 ppd (NASA)" : "LOLA LDEM_64 (NASA)";
  return `<div class="title">${nombre} · ${tr("relieve sombreado", "shaded relief")}</div>
    <p class="leg-line">${escapeHtml(CAPAS.misiones.linea)}</p>
    <ul class="leg-otros leg-misiones">
      <li><span class="swatch swatch-mision swatch-mision-${cuerpo}"></span><span>${escapeHtml(CAPAS.misiones.nombre)} (${usadas})</span></li>
      ${fuera ? `<li><span class="swatch swatch-mision swatch-mision-${cuerpo} is-fuera"></span><span>${escapeHtml(CAPAS.misiones_fuera.nombre)} (${fuera})</span></li>` : ""}
    </ul>
    <details class="note"><summary>${HOW_TO_READ}</summary><p>${tr(
      `Pasa el cursor o toca un sitio para ver sus coordenadas. Relieve: ${escapeHtml(relieve)}. El índice se calcula sobre la Tierra; aquí solo se ven los puntos de referencia.`,
      `Hover over or tap a site to see its coordinates. Relief: ${escapeHtml(relieve)}. The index is computed on Earth; here you only see the reference points.`,
    )} ${fuera ? escapeHtml(CAPAS.misiones_fuera.linea) : ""}</p></details>`;
}

/** Tira compacta de las 5 clases (leyenda plegada en móvil). */
export function legendStripHTML(vista: Vista): string {
  return [...clasesTesela(bandaDeVista(vista))]
    .reverse()
    .map((c) => `<span class="swatch" style="background:${c.rgb}" title="${rangoTxt(c.rango)} ${c.nombre}"></span>`)
    .join("");
}

export function legendHTML(vista: Vista): string {
  const b = bandaDeVista(vista);
  const capa = CAPAS[b];
  const filas = clasesTesela(b).map(
    (c) => `<li><span class="swatch" style="background:${c.rgb}"></span><span class="rng">${rangoTxt(c.rango)}</span><span>${c.nombre}</span></li>`,
  ).join("");
  return `<div class="title">${escapeHtml(capa.nombre)}</div>
    <p class="leg-line">${escapeHtml(capa.linea)}</p>
    <ul class="leg-clases" aria-label="${tr("Clases del índice", "Index classes")}">${filas}</ul>
    <ul class="leg-otros">
      <li><span class="swatch swatch-vacio"></span><span>${escapeHtml(CAPAS.mascara.nombre)}</span></li>
      <li><span class="swatch swatch-estacion"></span><span>${escapeHtml(CAPAS.estaciones.nombre)} (${ESTACIONES.length})</span></li>
      <li class="leg-pista"><span class="swatch swatch-mision swatch-mision-marte"></span><span>${escapeHtml(CAPAS.misiones.nombre)}: ${tr("cambia el globo a Marte o Luna", "switch the globe to Mars or Moon")}</span></li>
    </ul>
    <details class="note"><summary>${HOW_TO_READ}</summary><p>${tr(
      "Al alejarte ves el modelo global en celdas de 0,05° (unos 5,56 km); al acercarte a Ecuador, el modelo de Ecuador en celdas de 30″ (cerca de 1 km). Son dos modelos con soporte y máscara distintos: el de Ecuador no es una ampliación del global. Índice de 0 a 100; alta similitud: ≥ 95. Puntajes anteriores al filtro de calidad MODIS (QA).",
      "Zoomed out you see the global model in 0.05° cells (about 5.56 km); zoomed in on Ecuador, the Ecuador model in 30″ cells (about 1 km). They are two models with different support and masks: the Ecuador one is not a zoom of the global one. Index from 0 to 100; high similarity: ≥ 95. Scores before the MODIS quality (QA) filter.",
    )} ${escapeHtml(CAPAS.mascara.linea)}</p></details>`;
}

/* ---------------- Panel de cada mapa ---------------- */

function fuentesHTML(b: Banda): string {
  const items = FUENTES_MAPA[b]
    .map((id) => FUENTES[id])
    .map(
      (f) => `<li><strong>${escapeHtml(f.dato)}.</strong> ${escapeHtml(f.uso)}.<br><span class="cita">${escapeHtml(f.cita)}</span> <a href="${f.url}" target="_blank" rel="noopener noreferrer">${tr("Enlace", "Link")}</a></li>`,
    )
    .join("");
  return `<details class="fuentes" data-testid="fuentes-mapa"><summary>${tr("Fuentes de los datos de este mapa", "Data sources for this map")}</summary><ol class="fuentes-lista">${items}</ol></details>`;
}

function continente(c: string): string {
  return isEn ? (CONTINENTES_EN[c] ?? c) : c;
}

function tipoTerreno(t: string): string {
  if (isEn) return TIPOS_EN[t] ?? t.toLowerCase();
  return t === "Sin región fisiográfica cartografiada" ? "otras superficies" : t.toLowerCase();
}

function tablaGlobal(b: "marte" | "luna"): string {
  const z = b === "marte" ? ZONAS.global_marte : ZONAS.global_luna;
  const filas = z.filas
    .map(
      (r) => `<tr><td>${escapeHtml(continente(r.continente))} · ${escapeHtml(tipoTerreno(r.tipo))}</td><td class="num">${km2(r.area_km2)}</td><td class="num">${fmt(r.indice_medio, 1)}</td><td class="num">${fmt(r.indice_max, 0)}</td></tr>`,
    )
    .join("");
  const q = METRICAS.global.qa1;
  const qaCeldas = b === "marte" ? q.marte95 : q.luna95;
  const qaKm2 = b === "marte" ? q.marte95_km2 : q.luna95_km2;
  return `<h3>${tr("Zonas más parecidas en el mundo", "Most similar zones in the world")}</h3>
    <p>${tr(
      `Celdas con índice ≥ 95, antes del filtro QA: <strong>${ent(z.total_celdas)} celdas de 0,05°</strong> (${km2(z.total_area_km2)} km²) de ${ent(METRICAS.global.celdas)} elegibles. Con QA≤1 quedan ${ent(qaCeldas)} (${km2(qaKm2)} km²), sin recalibrar los puntajes. Agrupadas por continente y tipo de terreno; las 10 de mayor área. «Medio» y «Máx.»: índice medio y máximo de esas celdas.`,
      `Cells with an index ≥ 95, before the QA filter: <strong>${ent(z.total_celdas)} cells of 0.05°</strong> (${km2(z.total_area_km2)} km²) out of ${ent(METRICAS.global.celdas)} eligible. With QA≤1, ${ent(qaCeldas)} remain (${km2(qaKm2)} km²), without recalibrating the scores. Grouped by continent and terrain type; the 10 largest by area. “Mean” and “Max.”: mean and maximum index of those cells.`,
    )}</p>
    <div class="tabla-wrap"><table class="validacion zonas" data-testid="zonas-global">
      <thead><tr><th>${tr("Continente · tipo de terreno", "Continent · terrain type")}</th><th>${tr("Área (km²)", "Area (km²)")}</th><th>${tr("Medio", "Mean")}</th><th>${tr("Máx.", "Max.")}</th></tr></thead>
      <tbody>${filas}</tbody></table></div>
    <p class="muted">${tr(
      "«Otras superficies»: celdas fuera de los polígonos de regiones físicas de Natural Earth. Rusia al este de 60° E se cuenta en Asia. Área = número de celdas × área de la celda a su latitud.",
      "“Other surfaces”: cells outside the Natural Earth physical-region polygons. Russia east of 60° E is counted in Asia. Area = number of cells × cell area at its latitude.",
    )}</p>`;
}

function avisoQaEcuador(b: Banda): string {
  const e = METRICAS.ecuador;
  const conj = b === "conjunta"
    ? tr(
        ` Los dos píxeles conjuntos iniciales tienen QA ${e.qa_conjuntas[0]} y ${e.qa_conjuntas[1]} y se retiran como candidatos.`,
        ` The two initial joint pixels have QA ${e.qa_conjuntas[0]} and ${e.qa_conjuntas[1]} and are withdrawn as candidates.`,
      )
    : "";
  return `<div class="aviso-qa" data-testid="aviso-qa"><p>${tr(
    `<strong>Control de calidad MODIS:</strong> solo ${ent(e.qa1.celdas)} de ${ent(e.celdas)} celdas (${fmt(e.qa1.pct, 2)} %) cumplen QA≤1 y ninguna con índice ≥ 95 lo cumple; con el filtro permisivo QA≤2 (${ent(e.qa2.celdas)} celdas) tampoco queda ninguna.${conj} No hay sitios recomendados: el resultado muestra que la observación radiométrica no basta para priorizar lugares, no que falten análogos en Ecuador.`,
    `<strong>MODIS quality control:</strong> only ${ent(e.qa1.celdas)} of ${ent(e.celdas)} cells (${fmt(e.qa1.pct, 2)}%) meet QA≤1 and none with an index ≥ 95 does; with the permissive QA≤2 filter (${ent(e.qa2.celdas)} cells) none remains either.${conj} No site is recommended: the result shows the radiometric observation is not enough to prioritize places, not that Ecuador lacks analogs.`,
  )}</p></div>`;
}

function tablaEcuador(b: Banda): string {
  const z = b === "marte" ? ZONAS.ecuador_marte : b === "luna" ? ZONAS.ecuador_luna : ZONAS.ecuador_conjunta;
  const titulo = tr("Zonas con índice alto en Ecuador, antes del filtro QA", "High-index zones in Ecuador, before the QA filter");
  const filas = z.filas
    .map(
      (r) => `<tr><td>${escapeHtml(PROV_ACENTO[r.zona] ?? r.zona)} · ${escapeHtml(PROV_REGION[r.zona] ?? "–")}</td><td class="num">${km2(r.area_km2, 1)}</td><td class="num">${fmt(r.indice_medio, 1)}</td><td class="num">${fmt(r.indice_max, 0)}</td></tr>`,
    )
    .join("");
  return `<h3>${titulo}</h3>
    <p>${tr(
      `Celdas de 30″ (cerca de 1 km) con índice ≥ 95 en el modelo inicial: <strong>${ent(z.total_celdas)} de ${ent(z.evaluables)}</strong> celdas evaluadas (${km2(z.total_area_km2, 1)} km²). Agrupadas por provincia y región natural.`,
      `30″ cells (about 1 km) with an index ≥ 95 in the initial model: <strong>${ent(z.total_celdas)} of ${ent(z.evaluables)}</strong> evaluated cells (${km2(z.total_area_km2, 1)} km²). Grouped by province and natural region.`,
    )}</p>
    ${avisoQaEcuador(b)}
    <div class="tabla-wrap"><table class="validacion zonas" data-testid="zonas-ecuador">
      <thead><tr><th>${tr("Provincia · región", "Province · region")}</th><th>${tr("Área (km²)", "Area (km²)")}</th><th>${tr("Medio", "Mean")}</th><th>${tr("Máx.", "Max.")}</th></tr></thead>
      <tbody>${filas}</tbody></table></div>
    <p class="muted">${tr(
      `Área = número de celdas × área de la celda de 1/120° a su latitud. Celdas fuera de los polígonos de GADM (costa): ${ent(z.total_celdas - z.filas.reduce((s, r) => s + r.celdas, 0))}.`,
      `Area = number of cells × area of the 1/120° cell at its latitude. Cells outside the GADM polygons (coast): ${ent(z.total_celdas - z.filas.reduce((s, r) => s + r.celdas, 0))}.`,
    )}</p>`;
}

export function mapPanelHTML(vista: Vista, _nivel: Nivel): string {
  const b = bandaDeVista(vista);
  const capa = CAPAS[b];
  const glob =
    b === "conjunta"
      ? `<h3>${tr("Zonas más parecidas en el mundo", "Most similar zones in the world")}</h3><p>${tr(
          `En el mundo, ${ent(METRICAS.global.conjunta95)} celdas de 0,05° (${km2(METRICAS.global.conjunta95_km2)} km²) llegan a 95 en los dos índices redondeados a la vez, de ${ent(METRICAS.global.celdas)} elegibles. La banda binaria histórica, que aplica ≥ 95 antes del redondeo, da ${ent(METRICAS.global.conjunta95_historica)} celdas (${km2(METRICAS.global.conjunta95_historica_km2)} km²). Con QA≤1 quedan ${ent(METRICAS.global.qa1.conjunta95)} (${km2(METRICAS.global.qa1.conjunta95_km2)} km²).`,
          `Worldwide, ${ent(METRICAS.global.conjunta95)} cells of 0.05° (${km2(METRICAS.global.conjunta95_km2)} km²) reach 95 in both rounded indices at once, out of ${ent(METRICAS.global.celdas)} eligible. The historical binary band, which applies ≥ 95 before rounding, gives ${ent(METRICAS.global.conjunta95_historica)} cells (${km2(METRICAS.global.conjunta95_historica_km2)} km²). With QA≤1, ${ent(METRICAS.global.qa1.conjunta95)} remain (${km2(METRICAS.global.qa1.conjunta95_km2)} km²).`,
        )}</p>`
      : tablaGlobal(b);
  return `<section class="prose" data-testid="panel-mapa">
    <h2>${escapeHtml(capa.nombre)}</h2>
    <p>${escapeHtml(capa.linea)} ${tr(
      "El índice va de 0 a 100: es la proporción del fondo terrestre con una distancia a la firma mayor o igual a la de la celda. 95 significa que el 95 % del fondo queda más lejos de la firma.",
      "The index goes from 0 to 100: it is the share of the land background whose distance to the signature is greater than or equal to the cell’s. 95 means 95% of the background lies farther from the signature.",
    )}</p>
    <ul class="capas-lista">
      <li><strong>${escapeHtml(CAPAS.mascara.nombre)}.</strong> ${escapeHtml(CAPAS.mascara.linea)}</li>
      <li><strong>${escapeHtml(CAPAS.estaciones.nombre)}.</strong> ${escapeHtml(CAPAS.estaciones.linea)}</li>
      <li><strong>${escapeHtml(CAPAS.misiones.nombre)}.</strong> ${escapeHtml(CAPAS.misiones.linea)} ${tr("Se ven en los globos de Marte y la Luna.", "You can see them on the Mars and Moon globes.")}</li>
    </ul>
    ${glob}
    ${tablaEcuador(b)}
    ${estacionesHTML()}
    ${misionesHTML(b)}
    ${fuentesHTML(b)}
  </section>`;
}

function misionesHTML(b: Banda): string {
  const cuerpos: ("marte" | "luna")[] = b === "conjunta" ? ["marte", "luna"] : [b];
  const bloques = cuerpos
    .map((c) => {
      const li = MISIONES.filter((m) => m.cuerpo === c)
        .map(
          (m) =>
            `<li><strong>${escapeHtml(m.mision)}</strong> (${m.anio}), ${escapeHtml(m.terreno)}. ${escapeHtml(coordTexto(m.lat, m.lon))}.${m.usada ? "" : tr(" Fuera de la firma.", " Outside the signature.")} <a href="${m.fuente}" target="_blank" rel="noopener noreferrer">${tr("Fuente", "Source")}</a></li>`,
        )
        .join("");
      const usadas = MISIONES.filter((m) => m.cuerpo === c && m.usada).length;
      const total = MISIONES.filter((m) => m.cuerpo === c).length;
      return `<p class="muted">${c === "marte" ? tr("Marte", "Mars") : tr("Luna", "Moon")}: ${tr(`${usadas} usadas de ${total}.`, `${usadas} used out of ${total}.`)}</p><ul class="fuentes-lista">${li}</ul>`;
    })
    .join("");
  const total = MISIONES.filter((m) => cuerpos.includes(m.cuerpo) && m.usada).length;
  return `<details class="fuentes" data-testid="misiones-firma"><summary>${escapeHtml(CAPAS.misiones.nombre)} (${total})</summary>${bloques}<p class="muted">${escapeHtml(FUENTES.misiones.cita)}</p></details>`;
}

function estacionesHTML(): string {
  const li = ESTACIONES.map(
    (e) => `<li><strong>${escapeHtml(e.nombre)}</strong>, ${escapeHtml(e.lugar)}. ${escapeHtml(e.tipo)}. ${escapeHtml(e.estado)}. <a href="${e.fuente}" target="_blank" rel="noopener noreferrer">${tr("Fuente", "Source")}</a></li>`,
  ).join("");
  return `<details class="fuentes"><summary>${escapeHtml(CAPAS.estaciones.nombre)} (${ESTACIONES.length})</summary><ul class="fuentes-lista">${li}</ul></details>`;
}

/* ---------------- Inicio ---------------- */

export function homeHTML(_nivel: Nivel): string {
  const m = METRICAS;
  return `<section class="home" data-testid="home">
    <div class="home-hero">
      <div>
        <h2>${tr("¿Dónde en la Tierra se parece a la Luna y a Marte?", "Where on Earth looks like the Moon and Mars?")}</h2>
        <p class="lead">${tr(
          "Un modelo exploratorio compara cada celda terrestre con los sitios de aterrizaje en Marte y en la Luna (19 firmas de referencia de 24 misiones), usando tres variables: elevación, pendiente y señal radiométrica. El resultado es un índice de 0 a 100 para todo el mundo (celdas de 0,05°) y, en un modelo aparte, para Ecuador (celdas de 30″). No recomienda sitios.",
          "An exploratory model compares every land cell with the landing sites on Mars and the Moon (19 reference signatures from 24 missions), using three variables: elevation, slope and radiometric signal. The result is a 0 to 100 index for the whole world (0.05° cells) and, in a separate model, for Ecuador (30″ cells). It does not recommend sites.",
        )}</p>
        <div class="home-actions">
          <button type="button" class="btn btn-primary" data-action="ir" data-ir="similitud-marte">${tr("Ver el mapa de Marte", "See the Mars map")}</button>
          <button type="button" class="btn btn-ghost" data-action="tour" data-testid="btn-tour">${tr("Guíame paso a paso", "Guide me step by step")}</button>
          <button type="button" class="btn btn-ghost" data-action="ir" data-ir="visualizador">${tr("Explorar Ecuador", "Explore Ecuador")}</button>
        </div>
      </div>
      <div class="mapas-duo">
        <button type="button" class="mapa-thumb" data-action="ir" data-ir="similitud-marte">
          <span class="img"><img src="${assetUrl("/productos/indice_marte_mundo.png")}" alt="${tr("Índice de similitud con Marte en el mundo", "Similarity index to Mars across the world")}" width="1440" height="576" loading="lazy" /></span>
          <span class="cap"><strong>${tr("Marte", "Mars")}</strong><span>${tr("Índice 0–100 en el mundo", "0–100 index across the world")}</span></span>
        </button>
        <button type="button" class="mapa-thumb" data-action="ir" data-ir="similitud-luna">
          <span class="img"><img src="${assetUrl("/productos/indice_luna_mundo.png")}" alt="${tr("Índice de similitud con la Luna en el mundo", "Similarity index to the Moon across the world")}" width="1440" height="576" loading="lazy" /></span>
          <span class="cap"><strong>${tr("Luna", "Moon")}</strong><span>${tr("Índice 0–100 en el mundo", "0–100 index across the world")}</span></span>
        </button>
      </div>
    </div>

    <div class="veredicto">
      <div>
        <h2>${tr("Cifras del modelo", "Model figures")}</h2>
        <p>${tr(
          `Se evaluaron ${ent(m.global.celdas)} celdas de 0,05° en el mundo y ${ent(m.ecuador.celdas)} celdas de 30″ en Ecuador, tras la máscara ESA CCI 2022. La evaluación por misión no respalda discriminación y, tras el control de calidad MODIS, ningún candidato ≥ 95 persiste en Ecuador: el índice es exploratorio y no se recomiendan sitios.`,
          `We evaluated ${ent(m.global.celdas)} cells of 0.05° worldwide and ${ent(m.ecuador.celdas)} cells of 30″ in Ecuador, after the ESA CCI 2022 mask. The mission-level evaluation does not support discrimination and, after the MODIS quality control, no candidate ≥ 95 remains in Ecuador: the index is exploratory and no site is recommended.`,
        )}</p>
      </div>
      <div>
        <div class="figuras">
          <div class="fig is-main"><span class="v">${ent(m.global.marte95)}</span><span class="l">${tr("celdas del mundo con índice de Marte ≥ 95, antes de QA", "world cells with a Mars index ≥ 95, before QA")} (${tr("QA≤1", "QA≤1")}: ${ent(m.global.qa1.marte95)})</span></div>
          <div class="fig"><span class="v">${fmt(m.evaluacion_mision.global.auc, 2)}</span><span class="l">${tr("AUC por exclusión de misión", "Leave-one-mission-out AUC")} (${tr("p exacta", "exact p")} ${fmt(m.evaluacion_mision.global.p, 3)})</span></div>
          <div class="fig"><span class="v">0</span><span class="l">${tr(`candidatos ≥ 95 en Ecuador con QA≤1 (${ent(m.ecuador.qa1.celdas)} de ${ent(m.ecuador.celdas)} celdas pasan QA≤1)`, `candidates ≥ 95 in Ecuador with QA≤1 (${ent(m.ecuador.qa1.celdas)} of ${ent(m.ecuador.celdas)} cells pass QA≤1)`)}</span></div>
        </div>
      </div>
    </div>

    <div class="como">
      <div>
        <h2>${tr("Cómo se calcula", "How it is calculated")}</h2>
        ${cajaExplica(
          tr("Lo que mide el índice", "What the index measures"),
          tr(
            "Solo la superficie: elevación, pendiente y señal radiométrica. No incorpora variables climáticas ni mide mineralogía, granulometría o historia del agua.",
            "Surface only: elevation, slope and radiometric signal. It includes no climate variables and does not measure mineralogy, grain size or water history.",
          ),
        )}
      </div>
      <div><ol class="pasos-home">
        <li>${tr(
          "Medimos elevación, pendiente y señal radiométrica en 100 000 puntos por cuerpo (Tierra, Marte y Luna) y pasamos cada variable al percentil de su distribución empírica dentro de su cuerpo.",
          "We measured elevation, slope and radiometric signal at 100,000 points per body (Earth, Mars and the Moon) and turned each variable into the percentile of its empirical distribution within its own body.",
        )}</li>
        <li>${tr(
          "La firma de cada sitio de aterrizaje es la mediana de 81 muestras en una cuadrícula de 9 × 9 (radio máximo de 5,66 km). Referencias: 5 misiones en Marte y 14 en la Luna.",
          "Each landing site’s signature is the median of 81 samples on a 9 × 9 grid (maximum radius 5.66 km). References: 5 missions on Mars and 14 on the Moon.",
        )}</li>
        <li>${tr(
          "Para cada celda terrestre calculamos la distancia euclidiana, con pesos iguales, a la firma más próxima. El índice de 0 a 100 es la proporción del fondo terrestre con una distancia mayor o igual.",
          "For each land cell we computed the equally weighted Euclidean distance to the nearest signature. The 0 to 100 index is the share of the land background with a greater or equal distance.",
        )}</li>
        <li>${tr(
          "Excluimos celdas con la cobertura ESA CCI 2022 y erosión de un píxel, y después revisamos la calidad del albedo MODIS (QA).",
          "We excluded cells with the ESA CCI 2022 land cover and one-pixel erosion, and then checked the MODIS albedo quality (QA).",
        )}</li>
      </ol></div>
    </div>

    <div class="destinos">
      <h2>${tr("Sigue explorando", "Keep exploring")}</h2>
      <ul>
        <li><button type="button" class="home-card" data-action="ir" data-ir="similitud-luna"><strong>${tr("Mapa de la Luna", "Moon map")}</strong><span>${tr("El mismo índice frente a los sitios de aterrizaje lunares.", "The same index against the lunar landing sites.")}</span></button></li>
        <li><button type="button" class="home-card" data-action="ir" data-ir="validacion"><strong>${tr("Validación", "Validation")}</strong><span>${tr("Evaluación por misión, autocorrelación, control de calidad y umbrales.", "Mission-level evaluation, autocorrelation, quality control and thresholds.")}</span></button></li>
        <li><button type="button" class="home-card" data-action="ir" data-ir="incertidumbre"><strong>${tr("Límites", "Limits")}</strong><span>${tr("Lo que el índice no mide y de dónde salen los datos.", "What the index does not measure and where the data comes from.")}</span></button></li>
        <li><button type="button" class="home-card" data-action="ir" data-ir="visualizador"><strong>${tr("Explorar Ecuador", "Explore Ecuador")}</strong><span>${tr("Relieve en 3D con la leyenda y las estadísticas del índice en Ecuador.", "3D relief with the legend and the index statistics for Ecuador.")}</span></button></li>
      </ul>
    </div>
  </section>`;
}

export const TOUR_PASOS: { vista: Vista; titulo: string; cuerpo: string }[] = [
  {
    vista: "similitud-marte",
    titulo: tr("Empecemos por Marte", "Let’s start with Mars"),
    cuerpo: tr(
      "Cada color dice qué tan parecida es la celda a los sitios de aterrizaje en Marte, en un índice de 0 a 100. La leyenda está dentro del mapa. Aléjate para ver el modelo global y acércate a Ecuador para ver su modelo de celdas de 30″.",
      "Each color tells you how similar a cell is to the Mars landing sites, on a 0 to 100 index. The legend is inside the map. Zoom out to see the global model and zoom in on Ecuador to see its 30″ cell model.",
    ),
  },
  {
    vista: "similitud-luna",
    titulo: tr("Ahora, la Luna", "Now, the Moon"),
    cuerpo: tr(
      "El mismo mapa comparado con los sitios de aterrizaje lunares. En el panel ves las zonas más parecidas por continente y por provincia.",
      "The same map compared with the lunar landing sites. In the panel you see the most similar zones by continent and by province.",
    ),
  },
  {
    vista: "validacion",
    titulo: tr("Validación", "Validation"),
    cuerpo: tr(
      "La evaluación por exclusión de misión, la autocorrelación espacial y el control de calidad MODIS, con los umbrales usados.",
      "The leave-one-mission-out evaluation, spatial autocorrelation and MODIS quality control, with the thresholds used.",
    ),
  },
  {
    vista: "visualizador",
    titulo: tr("Explorar Ecuador", "Explore Ecuador"),
    cuerpo: tr(
      "El relieve de Ecuador en 3D, con la leyenda del índice y sus estadísticas antes del filtro QA: área por clase, distribución y máximos.",
      "Ecuador’s relief in 3D, with the index legend and its statistics before the QA filter: area by class, distribution and maximums.",
    ),
  },
];

/* ---------------- Validación ---------------- */

export function validationHTML(_nivel: Nivel): string {
  const m = METRICAS;
  const ev = m.evaluacion_mision;
  const e = m.ecuador;
  const g = m.global;
  const moran = m.moran.filas.map((f) => `<tr><td>${escapeHtml(f.variable)}</td><td class="num">${fmt(f.i, 3)}</td><td class="num">${fmt(m.moran.p, 3)}</td></tr>`).join("");
  const filaQa = (l: string, c: number, a: number, b: number, j: number) =>
    `<tr><td>${l}</td><td class="num">${ent(c)}</td><td class="num">${ent(a)}</td><td class="num">${ent(b)}</td><td class="num">${ent(j)}</td></tr>`;
  return `<section class="prose" data-testid="validacion-oficial">
    <h2>${tr("Validación", "Validation")}</h2>
    <p>${tr(
      "Cuatro análisis del artículo final. Ninguno convierte el índice en una probabilidad de éxito: el uso que sostienen es exploratorio.",
      "Four analyses from the final article. None turns the index into a probability of success: they support an exploratory use.",
    )}</p>

    <h3>${tr("1. Evaluación por exclusión de misión", "1. Leave-one-mission-out evaluation")}</h3>
    <p>${tr(
      `Usa ${ev.misiones} misiones marcianas: ${ev.altas} con evidencia hidrogeomorfológica alta frente a ${ev.medias} medias o medio-altas (InSight queda fuera). Se deja fuera cada misión, se igualan a cuatro las referencias altas y se enumeran las ${ev.global.asignaciones} asignaciones posibles de las etiquetas para una prueba exacta de cola superior.`,
      `It uses ${ev.misiones} Mars missions: ${ev.altas} with high hydrogeomorphological evidence against ${ev.medias} medium or medium-high (InSight is left out). Each mission is left out, the high references are matched at four, and all ${ev.global.asignaciones} possible label assignments are enumerated for an exact upper-tail test.`,
    )}</p>
    <div class="tabla-wrap"><table class="validacion">
      <thead><tr><th>${tr("Escala", "Scale")}</th><th>AUC</th><th>${tr("p exacta de cola superior", "Exact upper-tail p")}</th><th>${tr("Asignaciones", "Assignments")}</th></tr></thead>
      <tbody>
        <tr><td>${tr("Global, soporte cercano a 5 km", "Global, support of about 5 km")}</td><td class="num">${fmt(ev.global.auc, 2)}</td><td class="num">${fmt(ev.global.p, 3)}</td><td class="num">${ev.global.asignaciones}</td></tr>
        <tr><td>${tr("Ecuador, soporte cercano a 1 km", "Ecuador, support of about 1 km")}</td><td class="num">${fmt(ev.ecuador.auc, 2)}</td><td class="num">${fmt(ev.ecuador.p, 3)}</td><td class="num">${ev.ecuador.asignaciones}</td></tr>
      </tbody></table></div>
    <p><strong>${tr(
      "La evaluación no respalda discriminación útil de las etiquetas altas frente a medias o medio-altas.",
      "The evaluation does not support useful discrimination of high labels against medium or medium-high ones.",
    )}</strong> ${tr(
      `El procedimiento original, con cuatro referencias para los sitios altos y cinco para los demás, daba ${fmt(ev.auc_procedimiento_original, 2)}; la comparación igualada evita esa asimetría. El diagnóstico tiene nueve misiones, no miles de píxeles, y la prueba es condicional a la intercambiabilidad de etiquetas: no elimina el sesgo de selección de las misiones.`,
      `The original procedure, with four references for high sites and five for the rest, gave ${fmt(ev.auc_procedimiento_original, 2)}; the matched comparison avoids that asymmetry. The diagnostic has nine missions, not thousands of pixels, and the test is conditional on label exchangeability: it does not remove the selection bias of the missions.`,
    )}</p>

    <h3>${tr("2. Sensibilidad", "2. Sensitivity")}</h3>
    <p>${tr(
      `Se retiraron prototipos, se cambiaron pesos, se omitieron variables y se variaron umbrales. Jaccard por área compara intersección y unión de las selecciones. Retirar Phoenix reduce el Jaccard por área de la selección ≥ 95 a <strong>${fmt(m.jaccard_retiro.phoenix, 3)}</strong>; retirar Opportunity produce <strong>${fmt(m.jaccard_retiro.opportunity, 3)}</strong>. Retirar un precedente marciano altera las selecciones de cola aunque la correlación global de rangos siga alta.`,
      `Prototypes were removed, weights changed, variables omitted and thresholds varied. Area-based Jaccard compares the intersection and union of the selections. Removing Phoenix lowers the area-based Jaccard of the ≥ 95 selection to <strong>${fmt(m.jaccard_retiro.phoenix, 3)}</strong>; removing Opportunity gives <strong>${fmt(m.jaccard_retiro.opportunity, 3)}</strong>. Removing a Mars precedent changes the tail selections even though the global rank correlation stays high.`,
    )}</p>

    <h3>${tr("3. Autocorrelación espacial en Ecuador", "3. Spatial autocorrelation in Ecuador")}</h3>
    <p>${tr(
      `I de Moran en ${ent(m.moran.celdas)} celdas, con ${m.moran.vecinos} vecinos y ${m.moran.permutaciones} permutaciones. Describe dependencia, no exactitud predictiva (Moran, 1950).`,
      `Moran’s I on ${ent(m.moran.celdas)} cells, with ${m.moran.vecinos} neighbors and ${m.moran.permutaciones} permutations. It describes dependence, not predictive accuracy (Moran, 1950).`,
    )}</p>
    <div class="tabla-wrap"><table class="validacion">
      <thead><tr><th>${tr("Variable", "Variable")}</th><th>${tr("I de Moran", "Moran’s I")}</th><th>${tr("p de permutación", "Permutation p")}</th></tr></thead>
      <tbody>${moran}</tbody></table></div>
    <p class="muted">${tr(
      `La p de ${fmt(m.moran.p, 3)} es el mínimo resoluble con ${m.moran.permutaciones} permutaciones. La dependencia positiva y las huellas radiométricas compartidas impiden tratar las ${ent(e.celdas)} celdas como observaciones independientes.`,
      `The p of ${fmt(m.moran.p, 3)} is the minimum that ${m.moran.permutaciones} permutations can resolve. Positive dependence and shared radiometric footprints mean the ${ent(e.celdas)} cells cannot be treated as independent observations.`,
    )}</p>

    <h3>${tr("4. Control de calidad MODIS y retiro de candidatos", "4. MODIS quality control and withdrawal of candidates")}</h3>
    <p>${tr(
      "Se extrajeron Albedo_Quality, Percent_Inputs y Percent_Snow. QA 0 es inversión completa en todos los insumos; QA 1 exige al menos 90 % de inversiones completas y 75 % de las mejores. QA≤1 es el filtro estricto y QA≤2 el permisivo. Los filtros conservan los puntajes históricos y no recalibran el fondo.",
      "Albedo_Quality, Percent_Inputs and Percent_Snow were extracted. QA 0 is a full inversion in all inputs; QA 1 requires at least 90% full inversions and 75% of the best ones. QA≤1 is the strict filter and QA≤2 the permissive one. The filters keep the historical scores and do not recalibrate the background.",
    )}</p>
    <div class="tabla-wrap"><table class="validacion">
      <thead><tr><th>${tr("Filtro en Ecuador", "Filter in Ecuador")}</th><th>${tr("Celdas", "Cells")}</th><th>${tr("Marte ≥ 95", "Mars ≥ 95")}</th><th>${tr("Luna ≥ 95", "Moon ≥ 95")}</th><th>${tr("Conjunta ≥ 95", "Joint ≥ 95")}</th></tr></thead>
      <tbody>
        ${filaQa(tr("Máscara inicial", "Initial mask"), e.celdas, e.marte95, e.luna95, e.conjunta95)}
        ${filaQa("QA≤2", e.qa2.celdas, e.qa2.marte95, e.qa2.luna95, e.qa2.conjunta95)}
        ${filaQa("QA≤1", e.qa1.celdas, e.qa1.marte95, e.qa1.luna95, e.qa1.conjunta95)}
        ${filaQa(tr("QA≤1, terreno y nuevo borde", "QA≤1, terrain and new edge"), e.qa1_terreno.celdas, 0, 0, 0)}
      </tbody></table></div>
    <p>${tr(
      `Solo el ${fmt(e.qa1.pct, 2)} % de las celdas iniciales cumple QA≤1; ${ent(e.qa255)} tienen QA 255 pese a contar con albedo numérico. Los dos píxeles conjuntos originales tienen QA ${e.qa_conjuntas[0]} y ${e.qa_conjuntas[1]} y se retiran. El cribado de calidad, terreno y bordes conserva ${ent(e.qa1_terreno.celdas)} celdas (${fmt(e.qa1_terreno.km2, 2)} km²), con máximos de ${e.qa1_terreno.max_marte} para Marte, ${e.qa1_terreno.max_luna} para la Luna y ${e.qa1_terreno.max_conjunta} conjunto. <strong>Se retiran las recomendaciones de sitio:</strong> esto muestra que la observación radiométrica no basta para priorizar lugares, no que falten análogos en Ecuador.`,
      `Only ${fmt(e.qa1.pct, 2)}% of the initial cells meet QA≤1; ${ent(e.qa255)} have QA 255 despite having a numeric albedo. The two original joint pixels have QA ${e.qa_conjuntas[0]} and ${e.qa_conjuntas[1]} and are withdrawn. The quality, terrain and edge screening keeps ${ent(e.qa1_terreno.celdas)} cells (${fmt(e.qa1_terreno.km2, 2)} km²), with maximums of ${e.qa1_terreno.max_marte} for Mars, ${e.qa1_terreno.max_luna} for the Moon and ${e.qa1_terreno.max_conjunta} joint. <strong>Site recommendations are withdrawn:</strong> this shows the radiometric observation is not enough to prioritize places, not that Ecuador lacks analogs.`,
    )}</p>
    <div class="tabla-wrap"><table class="validacion">
      <thead><tr><th>${tr("Indicador global", "Global indicator")}</th><th>${tr("Celdas iniciales", "Initial cells")}</th><th>${tr("Celdas QA≤1", "QA≤1 cells")}</th><th>${tr("Área QA≤1 (km²)", "QA≤1 area (km²)")}</th></tr></thead>
      <tbody>
        <tr><td>${tr("Dominio elegible", "Eligible domain")}</td><td class="num">${ent(g.celdas)}</td><td class="num">${ent(g.qa1.celdas)}</td><td class="num">${ent(g.qa1.area_km2)}</td></tr>
        <tr><td>${tr("Marte ≥ 95", "Mars ≥ 95")}</td><td class="num">${ent(g.marte95)}</td><td class="num">${ent(g.qa1.marte95)}</td><td class="num">${ent(g.qa1.marte95_km2)}</td></tr>
        <tr><td>${tr("Luna ≥ 95", "Moon ≥ 95")}</td><td class="num">${ent(g.luna95)}</td><td class="num">${ent(g.qa1.luna95)}</td><td class="num">${ent(g.qa1.luna95_km2)}</td></tr>
        <tr><td>${tr("Conjunta ≥ 95", "Joint ≥ 95")}</td><td class="num">${ent(g.conjunta95)}</td><td class="num">${ent(g.qa1.conjunta95)}</td><td class="num">${ent(g.qa1.conjunta95_km2)}</td></tr>
      </tbody></table></div>
    <p class="muted">${tr(
      `QA≤1 conserva el ${fmt(g.qa1.pct_area, 2)} % del área global de la máscara inicial y el ${fmt(g.qa1.pct_area_conjunta, 2)} % del área de la selección conjunta. Permanecer tras QA no demuestra analogía material ni idoneidad de una estación.`,
      `QA≤1 keeps ${fmt(g.qa1.pct_area, 2)}% of the global area of the initial mask and ${fmt(g.qa1.pct_area_conjunta, 2)}% of the joint selection’s area. Remaining after QA does not demonstrate material analogy or suitability for a station.`,
    )}</p>

    <h3>${tr("Sin validación externa terrestre", "No external terrestrial validation")}</h3>
    <p>${tr(
      "Las estaciones existentes no aportan respuestas comparables para calibrar el mapa. Cuando existan esos datos harán falta técnicas de separación espacial (Roberts et al., 2017; Valavi et al., 2019).",
      "Existing stations do not provide comparable responses to calibrate the map. When such data exist, spatial separation techniques will be needed (Roberts et al., 2017; Valavi et al., 2019).",
    )}</p>

    <h3>${tr("Umbrales y rejillas", "Thresholds and grids")}</h3>
    <ul>
      <li>${tr("Clases del índice 0–100: 0–49 muy baja, 50–74 baja, 75–89 moderada, 90–94 alta y 95–100 muy alta.", "0–100 index classes: 0–49 very low, 50–74 low, 75–89 moderate, 90–94 high and 95–100 very high.")}</li>
      <li>${tr("El corte entero ≥ 95 puede incluir percentiles continuos desde 94,5 por redondeo. El índice conjunto es el mínimo de los índices de Marte y de la Luna redondeados.", "The integer cut ≥ 95 can include continuous percentiles from 94.5 because of rounding. The joint index is the minimum of the rounded Mars and Moon indices.")}</li>
      <li>${tr(`Mundo a 0,05° (unos 5,56 km en el ecuador): ${ent(g.celdas)} celdas y ${fmt(g.area_mkm2, 2)} millones de km² tras la máscara. Máscara: clase ESA CCI 2022 más próxima al centro de la celda y erosión de un píxel.`, `World at 0.05° (about 5.56 km at the equator): ${ent(g.celdas)} cells and ${fmt(g.area_mkm2, 2)} million km² after the mask. Mask: the ESA CCI 2022 class nearest to the cell center and one-pixel erosion.`)}</li>
      <li>${tr(`Ecuador a 30″ (cerca de 1 km): ${ent(e.celdas)} celdas sustentadas por ${ent(e.huellas_modis)} huellas MODIS distintas. Máscara: fracción de clases forestales y agua agregada desde 300 m y erosión de un píxel. Es un modelo aparte, no una ampliación del global.`, `Ecuador at 30″ (about 1 km): ${ent(e.celdas)} cells supported by ${ent(e.huellas_modis)} distinct MODIS footprints. Mask: fraction of forest and water classes aggregated from 300 m and one-pixel erosion. It is a separate model, not a zoom of the global one.`)}</li>
      <li>${tr("Referencia del percentil: la distribución empírica de 100 000 puntos por cuerpo.", "Percentile reference: the empirical distribution of 100,000 points per body.")}</li>
    </ul>

    <h3>${tr("Propuesta: variables de hidromorfología", "Proposal: hydromorphology variables")}</h3>
    <p>${tr(
      "Propuesta del equipo, no calculada: añadir red de drenaje y su densidad, acumulación de flujo, humedad del suelo y formas de erosión (abanicos, cárcavas, cauces secos) para separar superficies que hoy se parecen solo por relieve y señal radiométrica.",
      "Team proposal, not computed: add drainage network and its density, flow accumulation, soil moisture and erosion landforms (fans, gullies, dry channels) to separate surfaces that today look alike only by relief and radiometric signal.",
    )}</p>

    <details class="fuentes"><summary>${tr("Referencias del método", "Method references")}</summary><ol class="fuentes-lista">
      <li>Moran, P. A. P. (1950). Notes on continuous stochastic phenomena. Biometrika, 37(1–2), 17–23. <a href="https://doi.org/10.1093/biomet/37.1-2.17" target="_blank" rel="noopener noreferrer">doi:10.1093/biomet/37.1-2.17</a></li>
      <li>Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 40(8), 913–929. <a href="https://doi.org/10.1111/ecog.02881" target="_blank" rel="noopener noreferrer">doi:10.1111/ecog.02881</a></li>
      <li>Valavi, R., Elith, J., Lahoz-Monfort, J. J., &amp; Guillera-Arroita, G. (2019). blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. Methods in Ecology and Evolution, 10(2), 225–232. <a href="https://doi.org/10.1111/2041-210X.13107" target="_blank" rel="noopener noreferrer">doi:10.1111/2041-210X.13107</a></li>
      <li>European Space Agency Climate Change Initiative (2022). Land cover map of 2022. <a href="https://climate.esa.int/en/projects/land-cover/" target="_blank" rel="noopener noreferrer">climate.esa.int</a></li>
      <li>NASA LAADS DAAC. MCD43C3 collection 6.1 file specification. <a href="https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/61/MCD43C3" target="_blank" rel="noopener noreferrer">ladsweb.modaps.eosdis.nasa.gov</a></li>
    </ol></details>
  </section>`;
}

/* ---------------- Límites ---------------- */

export function uncertaintyHTML(_nivel: Nivel): string {
  const lm = METRICAS.luna_muestra;
  return `<section class="prose" data-testid="nota-incertidumbre">
    <h2>${tr("Límites del índice", "Limits of the index")}</h2>
    <h3>${tr("Qué mide y qué no", "What it measures and what it does not")}</h3>
    <ul>
      <li>${tr("Mide la similitud ordinal de elevación, pendiente y señal radiométrica. No incorpora variables climáticas. Una semejanza topográfica no reproduce gravedad, atmósfera, mineralogía, granulometría ni historia del agua.", "It measures the ordinal similarity of elevation, slope and radiometric signal. It includes no climate variables. A topographic resemblance does not reproduce gravity, atmosphere, mineralogy, grain size or water history.")}</li>
      <li>${tr("Es relativo: 95 quiere decir que el 95 % del fondo terrestre queda más lejos de la firma, no «igual a Marte».", "It is relative: 95 means 95% of the land background lies farther from the signature, not “equal to Mars”.")}</li>
      <li>${tr("No es una probabilidad de éxito: los aterrizajes se eligieron a propósito y no hay una muestra de fracasos comparables. No demuestra aptitud para una estación permanente ni se recomiendan sitios.", "It is not a probability of success: landings were chosen deliberately and there is no sample of comparable failures. It does not demonstrate suitability for a permanent station, and no site is recommended.")}</li>
    </ul>
    <h3>${tr("Datos", "Data")}</h3>
    <ul>
      <li>${tr("La Tierra usa albedo de cielo blanco MODIS MCD43C3, Marte albedo bolométrico TES y la Luna reflectancia WAC. Estas magnitudes no son físicamente intercambiables: los percentiles comparan posición relativa dentro de cada cuerpo, sin demostrar equivalencia espectral.", "Earth uses MODIS MCD43C3 white-sky albedo, Mars TES bolometric albedo and the Moon WAC reflectance. These quantities are not physically interchangeable: percentiles compare relative position within each body, without demonstrating spectral equivalence.")}</li>
      <li>${tr("MCD43C3 (fecha nominal 13 de septiembre de 2026) combina una ventana de 16 días y conserva una huella de unos 5,6 km aunque se remuestree a 1 km.", "MCD43C3 (nominal date 13 September 2026) combines a 16-day window and keeps a footprint of about 5.6 km even when resampled to 1 km.")}</li>
      <li>${tr(`La Luna combina reflectancia WAC EMP a 643 nm entre ±60° y un mosaico WAC morfológico en las regiones polares: ${ent(lm.emp)} registros EMP y ${ent(lm.polar)} del mosaico polar, con medianas cercanas a ${fmt(lm.mediana_emp, 3)} y ${fmt(lm.mediana_polar, 3)}. La diferencia está confundida con terreno, latitud, iluminación y normalización.`, `The Moon combines WAC EMP reflectance at 643 nm within ±60° and a morphologic WAC mosaic in the polar regions: ${ent(lm.emp)} EMP records and ${ent(lm.polar)} from the polar mosaic, with medians of about ${fmt(lm.mediana_emp, 3)} and ${fmt(lm.mediana_polar, 3)}. The difference is confounded with terrain, latitude, illumination and normalization.`)}</li>
      <li>${tr("La revisión de código detectó interpolación periódica dentro de teselas planetarias parciales y un tratamiento tardío de valores especiales WAC. El posible error cerca de las uniones no se cuantificó: la extracción debe regenerarse con mosaicos y halos correctos antes de inferencias de precisión.", "The code review found periodic interpolation inside partial planetary tiles and late handling of special WAC values. The possible error near seams was not quantified: the extraction must be regenerated with correct mosaics and halos before precision inferences.")}</li>
      <li>${tr("La máscara global usa la clase ESA CCI más próxima al centro de la celda y no estima cobertura forestal subpíxel. La muestra terrestre representa la cobertura disponible, no toda la superficie del planeta.", "The global mask uses the ESA CCI class nearest to the cell center and does not estimate sub-pixel forest cover. The land sample represents the available coverage, not the whole surface of the planet.")}</li>
      <li>${tr("La elevación terrestre es GMTED2010 (USGS), no un producto NASA. Las 81 muestras de cada firma no son independientes.", "Land elevation is GMTED2010 (USGS), not a NASA product. The 81 samples of each signature are not independent.")}</li>
    </ul>
    <h3>${tr("Evaluación", "Evaluation")}</h3>
    <p>${tr("La evaluación por misión no respalda discriminación, no hay validación externa terrestre y el control de calidad deja a Ecuador sin candidatos ≥ 95. Los detalles están en Validación.", "The mission-level evaluation does not support discrimination, there is no external terrestrial validation, and the quality control leaves Ecuador with no candidates ≥ 95. Details are in Validation.")}</p>
  </section>`;
}

export function futureWorkHTML(): string {
  return `<section class="prose" data-testid="trabajo-futuro">
    <h2>${tr("Trabajo futuro", "Future work")}</h2>
    <ul>
      <li>${tr("Regenerar la extracción planetaria con mosaicos y halos correctos antes de cualquier inferencia de precisión.", "Regenerate the planetary extraction with correct mosaics and halos before any precision inference.")}</li>
      <li>${tr("Aplicar técnicas de separación espacial cuando existan datos terrestres comparables para una validación externa.", "Apply spatial separation techniques once comparable terrestrial data exist for an external validation.")}</li>
      <li>${tr("Propuesta: añadir variables de hidromorfología (red de drenaje, acumulación de flujo, humedad del suelo y formas de erosión).", "Proposal: add hydromorphology variables (drainage network, flow accumulation, soil moisture and erosion landforms).")}</li>
    </ul>
    <p class="muted">${tr("Nada de esta lista está calculado en esta entrega.", "None of this list is computed in this release.")}</p>
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
          const col = clasesTesela(b).find((t) => t.rango === c.clase)?.rgb ?? "#888";
          const pct = (100 * c.area_km2) / total;
          return `<tr><td><span class="swatch" style="background:${col}"></span> ${rangoTxt(c.clase)}</td><td class="num">${km2(c.area_km2, 1)}</td><td class="num">${fmt(pct, 1)} %</td><td class="bar"><span style="width:${pct.toFixed(1)}%;background:${col}"></span></td></tr>`;
        })
        .join("");
      return `<h3>${escapeHtml(CAPAS[b].nombre)}</h3>
        <dl class="kv-mini">
          <div><dt>${tr("Índice máximo", "Maximum index")}</dt><dd>${fmt(z.max, 0)}</dd></div>
          <div><dt>${tr("Mediana (cuartiles)", "Median (quartiles)")}</dt><dd>${fmt(z.mediana, 0)} (${fmt(z.p25, 0)}–${fmt(z.p75, 0)})</dd></div>
          <div><dt>${tr("Celdas ≥ 95, antes de QA", "Cells ≥ 95, before QA")}</dt><dd>${ent(z.total_celdas)} (${km2(z.total_area_km2, 1)} km²)</dd></div>
        </dl>
        <div class="tabla-wrap"><table class="validacion clases-area">
          <thead><tr><th>${tr("Clase", "Class")}</th><th>${tr("Área (km²)", "Area (km²)")}</th><th>%</th><th>${tr("Distribución", "Distribution")}</th></tr></thead>
          <tbody>${barras}</tbody></table></div>`;
    })
    .join("");
  return `<section class="prose explorar-ecuador" data-testid="explorar-ecuador">
    <h2>${tr("Explorar Ecuador", "Explore Ecuador")}</h2>
    <p>${tr(
      `Estadísticas exploratorias del índice (0–100) en ${ent(ZONAS.ecuador_marte.evaluables)} celdas de 30″ evaluadas (${km2(ZONAS.ecuador_marte.area_evaluable_km2)} km²), tras la máscara ESA CCI 2022 y antes del filtro de calidad MODIS.`,
      `Exploratory statistics of the index (0–100) over ${ent(ZONAS.ecuador_marte.evaluables)} evaluated 30″ cells (${km2(ZONAS.ecuador_marte.area_evaluable_km2)} km²), after the ESA CCI 2022 mask and before the MODIS quality filter.`,
    )}</p>
    ${avisoQaEcuador("conjunta")}
    ${bloques}
    <p class="muted">${tr("Área = número de celdas × área de la celda de 1/120° a su latitud.", "Area = number of cells × area of the 1/120° cell at its latitude.")}</p>
  </section>`;
}
