import { defTermino, term } from "./glossary";
import { escapeHtml } from "./maps";
import type { Catalogo, Nivel, SitioValidacion, Vista, ZonaPrioritaria } from "./types";

export function fmt(n: number | null | undefined, d = 3): string {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toLocaleString("es-EC", { minimumFractionDigits: d, maximumFractionDigits: d });
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

export function fraseParecido(
  cuerpo: "Marte" | "la Luna",
  d: number | null | undefined,
  conNumero = true,
): string {
  const n = nivelDelta(d);
  if (n === "sin dato") return `Parecido a ${cuerpo} según el índice: sin dato`;
  const num = conNumero && d != null ? ` (δ ${fmt(d, 2)})` : "";
  return `Parecido a ${cuerpo} según el índice: ${n}${num}`;
}

export const NOTA_INDICE = "Es un índice, no una clasificación.";


const ISLAS_GALAPAGOS: { isla: string; n: number }[] = [
  { isla: "Isabela", n: 4128 },
  { isla: "Santa Cruz", n: 839 },
  { isla: "Fernandina", n: 527 },
  { isla: "Santiago", n: 451 },
  { isla: "San Cristóbal", n: 414 },
  { isla: "Floreana", n: 107 },
  { isla: "Marchena", n: 80 },
  { isla: "Española", n: 24 },
  { isla: "Pinta", n: 24 },
  { isla: "Santa Fe", n: 5 },
  { isla: "Baltra", n: 4 },
  { isla: "Pinzón", n: 2 },
  { isla: "Genovesa", n: 1 },
  { isla: "Rábida", n: 0 },
  { isla: "Seymour Norte", n: 0 },
  { isla: "Plaza Sur", n: 0 },
  { isla: "Wolf", n: 0 },
  { isla: "Darwin", n: 0 },
];

export function islasGalapagosHTML(nivel: Nivel): string {
  const filas = ISLAS_GALAPAGOS.map(
    (r) => `<tr><th scope="row">${escapeHtml(r.isla)}</th><td class="num">${r.n.toLocaleString("es-EC")}</td></tr>`,
  ).join("");
  const fuente =
    nivel === "explorador"
      ? "Cuenta: una celda de 1 km si su centro cae en la isla y tiene dato. Fuente del contorno: GADM 4.1. Darwin y Wolf no tienen celdas a esta escala."
      : "Se cuenta una celda de 1 km si su centro cae dentro del polígono (all_touched = False) y es válida en la máscara oficial de pendiente/TRI/δ (banda_propia). Fuente: GADM 4.1, provincia Galápagos (https://gadm.org/; 18 jul 2022). No se redistribuye el shapefile. Darwin y Wolf = 0. Galápagos no entra al AUC ni al umbral. Detalle: docs/galapagos_celdas_por_isla.md.";
  return `<h3>Celdas válidas por isla (Galápagos)</h3>
    <p>En total hay <strong>6 606</strong> celdas válidas de 1 km. Darwin y Wolf tienen <strong>0</strong>.</p>
    <table class="islas" data-testid="celdas-por-isla">
      <thead><tr><th>Isla</th><th>Celdas válidas</th></tr></thead>
      <tbody>${filas}</tbody>
    </table>
    <p class="muted">${fuente}</p>`;
}

export function cajaExplica(titulo: string, cuerpo: string): string {
  return `<aside class="explica" data-testid="explica">
    <p class="explica-k">¿Qué significa esto?</p>
    <p class="explica-t">${titulo}</p>
    <p>${cuerpo}</p>
  </aside>`;
}

export function avisoHonestidad(): string {
  return `<div class="honest-banner" role="status" data-testid="aviso-honestidad">
    <strong>Validación:</strong>
    el índice <em>no pasó</em>.
    AUC Marte <strong>0,09</strong>, AUC Luna <strong>0,25</strong>, aciertos <strong>6 de 16</strong>.
    Este resultado se muestra en los tres niveles.
  </div>`;
}

export function homeHTML(nivel: Nivel): string {
  const como =
    nivel === "explorador"
      ? `<ul class="pasos-home">
          <li><strong>1. Elegimos cuatro cosas que se pueden medir en la Tierra, en Marte y en la Luna:</strong> qué tan lejos está del ecuador, qué tan alto está, qué tan inclinado está y qué tan arrugado es el terreno.</li>
          <li><strong>2. Comparamos Ecuador, cuadrado a cuadrado de 1 km,</strong> con un «retrato típico» de la superficie de Marte y de la Luna.</li>
          <li><strong>3. Pusimos a prueba el índice</strong> en 16 lugares del mundo que ya se conocen como análogos o como no análogos.</li>
          <li><strong>4. El examen no se aprobó.</strong> Lo mostramos tal cual, y te explicamos por qué.</li>
        </ul>`
      : nivel === "estudiante"
        ? `<ul class="pasos-home">
          <li>El índice ${term("delta")} combina ${term("latitud")} (|lat|), ${term("elevacion")} absoluta, ${term("pendiente")} y ${term("rugosidad")} (TRI), con pesos iguales de 0,25.</li>
          <li>Las firmas se armaron por ${term("bandas")} en Marte (MOLA) y en la Luna (LOLA), y se aplicaron a una grilla de ~1 km sobre Ecuador y Galápagos (GLO-90).</li>
          <li>La validación usa 16 sitios etiquetados. El ${term("auc")} quedó en 0,09 (Marte) y 0,25 (Luna): el índice no discrimina bien.</li>
          <li>Por eso hay que leer los mapas <strong>continuos</strong> de δ, no un recuento de «cuánto de Ecuador es análogo».</li>
        </ul>`
        : `<ul class="pasos-home">
          <li>v1 congelada (14 de noviembre de 2026, America/Guayaquil): ${term("std")}, firmas por ${term("bandas")} A–G (mediana e IQR), distancia euclídea con penalización ${term("iqr")}, modo oficial <span class="mono">banda_propia</span> (la corrida se hizo después de ver el AUC de <span class="mono">todas_min</span>), umbrales de ${term("youden")} congelados antes de Ecuador y de Galápagos.</li>
          <li>Fuentes: MOLA MEGDR 64 ppd, LOLA LDEM_64 v3.1, Copernicus DEM GLO-90. Pendiente Horn y TRI Wilson recalculados en la grilla remuestreada.</li>
          <li>${term("auc")} Marte 0,09 (IC 95 % 0,00–0,29); Luna 0,25 (0,00–0,69). Aciertos 6/16. ${term("nulo")} de solo |lat|: AUC Marte 0,58. ${term("especificidad")} de Marte = 0.</li>
          <li>No se presentan porcentajes del mapa de clases. Una revisión v1.1 no fue aprobada y queda solo como trabajo futuro.</li>
        </ul>`;

  return `<section class="home" data-testid="home">
    <p class="eyebrow">NASA Space Apps 2026 · Sangolquí, Ecuador · v1 congelada</p>
    <h1>¿Dónde en la Tierra se parece a la Luna y a Marte?</h1>
    <p class="lead">Compara la <strong>superficie</strong> de Ecuador y Galápagos con la de Marte y la de la Luna. Elige el nivel de detalle arriba. La validación es la misma en los tres niveles.</p>
    ${avisoHonestidad()}
    <div class="home-actions">
      <button type="button" class="btn btn-primary" data-action="tour" data-testid="btn-tour">Empezar el recorrido</button>
      <button type="button" class="btn btn-ghost" data-action="ir" data-ir="similitud-marte">Ver el mapa de Marte</button>
      <button type="button" class="btn btn-ghost" data-action="ir" data-ir="visualizador">Abrir el visualizador 3D</button>
    </div>
    <h2>Cómo lo hicimos, en breve</h2>
    ${como}
    ${cajaExplica(
      "Qué mide el índice, y qué no",
      nivel === "cientifico"
        ? "La analogía es solo de superficie y con cuatro variables comparables. El clima, el albedo y la inercia térmica no entran. El mapa de clases de Ecuador no es un inventario fiable (especificidad 0 en Marte) y no se informan porcentajes de cobertura."
        : "El índice no afirma que un lugar de Ecuador «sea» Marte. Compara altura, inclinación, rugosidad y distancia al ecuador en celdas de 1 km. En 16 sitios conocidos no discriminó bien (AUC Marte 0,09; Luna 0,25).",
    )}
    <h2>Por dónde seguir</h2>
    <div class="home-cards">
      <button type="button" class="home-card" data-action="ir" data-ir="similitud-marte">
        <span class="k">Mapa</span><strong>Similitud a Marte</strong>
        <span>Colores sobre Ecuador: de menos parecido a más parecido, según el índice.</span>
      </button>
      <button type="button" class="home-card" data-action="ir" data-ir="similitud-luna">
        <span class="k">Mapa</span><strong>Similitud a la Luna</strong>
        <span>La misma idea, comparando con la superficie lunar.</span>
      </button>
      <button type="button" class="home-card" data-action="ir" data-ir="validacion">
        <span class="k">Prueba</span><strong>La validación</strong>
        <span>16 sitios conocidos. El índice acertó 6.</span>
      </button>
      <button type="button" class="home-card" data-action="ir" data-ir="diagnostico">
        <span class="k">Por qué</span><strong>El diagnóstico</strong>
        <span>Terreno planetario suave a 1 km, análogos más rugosos, y una muestra pequeña.</span>
      </button>
      <button type="button" class="home-card" data-action="ir" data-ir="incertidumbre">
        <span class="k">Límites</span><strong>Incertidumbre</strong>
        <span>Qué sí se puede afirmar, qué no, y de dónde salen los datos.</span>
      </button>
      <button type="button" class="home-card" data-action="ir" data-ir="visualizador">
        <span class="k">3D</span><strong>Visualizador 3D</strong>
        <span>Vista 3D del terreno con los productos congelados de la v1. Ecuador y Galápagos van en una sola grilla; no hay una vista aparte.</span>
      </button>
    </div>
  </section>`;
}

export const TOUR_PASOS: { vista: Vista; titulo: string; cuerpo: string }[] = [
  {
    vista: "similitud-marte",
    titulo: "El mapa de Marte",
    cuerpo:
      "Cada color sobre Ecuador dice cuánto se parece esa celda a la superficie típica de Marte, según el índice. La leyenda lo dice en palabras: de menos parecido a más parecido. Puedes tocar un punto o una zona para ver una ficha.",
  },
  {
    vista: "similitud-luna",
    titulo: "El mapa de la Luna",
    cuerpo:
      "Aquí la comparación es con la Luna, no con Marte. Usa el interruptor Marte/Luna cuando quieras alternar sin salir del mapa. El dato no cambia: solo cambia el cuerpo de referencia.",
  },
  {
    vista: "validacion",
    titulo: "La prueba con lugares conocidos",
    cuerpo:
      "Antes de hablar de Ecuador, el índice se puso a prueba en 16 sitios del mundo. Acertó 6. El AUC fue 0,09 en Marte y 0,25 en la Luna: no distinguió bien los análogos de los que no lo son. Este resultado se muestra en todos los niveles.",
  },
  {
    vista: "diagnostico",
    titulo: "Por qué falló",
    cuerpo:
      "A 1 km, Marte se ve bastante plano. Algunos análogos famosos son más rugosos, y varias llanuras terrestres quedan «más cerca» de Marte que ellos. Un cráter pequeño casi desaparece en un cuadrado de 1 km. Y solo se probaron 16 sitios.",
  },
  {
    vista: "incertidumbre",
    titulo: "Lo que sí, y lo que no",
    cuerpo:
      "El método es reproducible y las fuentes están documentadas. No se puede presentar un mapa de clases de Ecuador como un inventario de análogos, ni hablar de clima: el clima no entra al índice y no se publica.",
  },
  {
    vista: "visualizador",
    titulo: "Visualizador 3D",
    cuerpo:
      "Este visualizador 3D usa los mismos productos congelados de la v1, en una sola grilla de Ecuador y Galápagos (12 zonas). No hay una vista aparte de Galápagos. No consulta bases de datos en vivo. Puedes verlo a pantalla completa.",
  },
];

export function validationHTML(cat: Catalogo, sitios: SitioValidacion[], nivel: Nivel): string {
  const aciertos = cat.metricas_validacion.aciertos_auc ?? cat.metricas_validacion.aciertos ?? 6;
  const n = cat.metricas_validacion.n_sitios_auc ?? 16;
  if (nivel === "explorador") {
    const cards = sitios
      .filter((s) => !s.excluido_auc)
      .map((s) => {
        const ok = s.acierto;
        const dm = fraseDelta(s.delta_marte);
        const dl = fraseDelta(s.delta_luna);
        return `<article class="sitio-card ${ok ? "is-ok" : "is-fail"}" data-sitio="${escapeHtml(s.nombre)}">
          <button type="button" class="sitio-card-btn" data-sitio-abrir="${escapeHtml(s.nombre)}">
            <h3>${escapeHtml(nombreCorto(s.nombre))}</h3>
            <p class="sitio-tag">${ok ? "El índice acertó" : "El índice no acertó"} · conocido como ${etiquetaAmiga(s.clase_conocida)}</p>
            <p>Marte: ${dm}. Luna: ${dl}.</p>
          </button>
        </article>`;
      })
      .join("");
    return `<section class="prose" data-testid="validacion-oficial">
      <h2>¿El índice acertó? No del todo</h2>
      ${avisoHonestidad()}
      <p>La prueba usó <strong>${n} sitios</strong> ya clasificados por especialistas (análogos de Marte o de la Luna, o no análogos). El índice acertó <strong>${aciertos} de ${n}</strong>.</p>
      <p>El ${term("auc", "AUC")} va de 0 a 1. Un valor de <strong>0,50</strong> equivale a elegir al azar. Aquí fue <strong>0,09</strong> para Marte y <strong>0,25</strong> para la Luna: en Marte, peor que el azar.</p>
      ${cajaExplica(
        "¿Por qué se veían tan altos algunos no análogos?",
        "A la escala de 1 km, una llanura o un bosque puede parecerse a un Marte «suave». Eso no convierte a esos lugares en análogos de misión. El diagnóstico lo cuenta con más calma.",
      )}
      <h3>Los 16 sitios del examen</h3>
      <div class="sitio-grid" data-testid="sitios-explorador">${cards}</div>
      <p class="muted">Tres sitios más (Río Tinto, Ries y Sudbury) se listan en el proyecto pero no entraron al examen. En el nivel Científico está la tabla completa, con intervalos de confianza y el modelo que usa solo la latitud.</p>
    </section>`;
  }

  if (nivel === "estudiante") {
    return `<section class="prose" data-testid="validacion-oficial">
      <h2>Validación de la v1</h2>
      ${avisoHonestidad()}
      <p>El ${term("auc")} mide si el ${term("delta")} tiende a ser más alto en análogos etiquetados que en no análogos. Un valor de 0,5 es un clasificador aleatorio. Los umbrales se eligieron con el criterio de ${term("youden")} sobre estos 16 sitios y se <strong>congelaron antes de Ecuador</strong>.</p>
      <ul class="auc-lead">
        <li><strong>AUC Marte: 0,09</strong> (IC 95 % 0,00–0,29). Umbral 0,13; sensibilidad 1,00; precisión 0,50; ${term("especificidad")} 0,00.</li>
        <li><strong>AUC Luna: 0,25</strong> (IC 95 % 0,00–0,69). Umbral 0,79; sensibilidad 0,20; precisión 1,00; especificidad 1,00.</li>
        <li>Aciertos de clase: <strong>${aciertos} de ${n}</strong>.</li>
      </ul>
      ${cajaExplica(
        "Un AUC menor que 0,5 no se «voltea»",
        "Significa que, en este conjunto, varios no análogos quedan más cerca de la firma típica que los análogos. El equipo acordó no invertir el índice ni retocar los pesos después de ver el número.",
      )}
      <h3>Por qué el AUC de banda_propia coincide con el de todas_min</h3>
      <p>Las dos corridas dan el mismo AUC (Marte 0,09, Luna 0,25). En la Luna, la banda propia ya era la ganadora en los 16 sitios, así que δ no cambia. En Marte δ sí se mueve en 5 de 16 sitios (el d_max pasa de 5,784 a 7,105), pero el orden entre análogos y no análogos no cambia: el U de Mann–Whitney sigue siendo 6 de 64 pares. Por eso el AUC no se mueve aunque el mapa de Marte sí.</p>
      <h3>Tabla de sitios</h3>
      ${tableHTML(sitios, "estudiante")}
    </section>`;
  }

  // científico
  return `<section class="prose" data-testid="validacion-oficial">
    <h2>Validación oficial de la v1 congelada</h2>
    ${avisoHonestidad()}
    <p>Configuración oficial: firmas por ${term("bandas")}, modo <span class="mono">banda_propia</span>, vector con |lat|, elevación absoluta, pesos iguales y umbrales de ${term("youden")} congelados antes de Ecuador y de Galápagos. ${term("std")} ajustados solo en el cuerpo de referencia. <strong>La corrida con <span class="mono">banda_propia</span> se hizo después de ver el AUC de <span class="mono">todas_min</span>.</strong> Galápagos no entra al AUC ni al umbral.</p>
    <ul class="auc-lead">
      <li><strong>AUC Marte: 0,09</strong> (IC bootstrap 95 %: 0,00–0,29). Umbral 0,13; sensibilidad 1,00; precisión 0,50; especificidad 0,00.</li>
      <li><strong>AUC Luna: 0,25</strong> (IC bootstrap 95 %: 0,00–0,69). Umbral 0,79; sensibilidad 0,20; precisión 1,00; especificidad 1,00.</li>
      <li>Aciertos en los sitios del AUC: <strong>${aciertos} de ${n}</strong>.</li>
    </ul>
    <p>El índice no discrimina bien (ambos AUC &lt; 0,5). No se presentan porcentajes del mapa de clases de Ecuador.</p>
    <h3>Por qué el AUC coincide con el de <span class="mono">todas_min</span></h3>
    <p>El AUC es el mismo (Marte 0,09375, Luna 0,2545). No son cifras copiadas. En la Luna, la banda ganadora de <span class="mono">todas_min</span> ya era la propia en 16 de 16 sitios; δ Luna es idéntica (SHA-256 de <span class="mono">delta_luna.png</span>: <span class="mono">5eb786ef…</span>). En Marte la banda ganadora cambia en 5 de 16 y δ se mueve (<span class="mono">d_max</span> de 5,784 a 7,105); el mapa cambia (oficial <span class="mono">47839ad2…</span>, corrida previa <span class="mono">0152dfb6…</span>). El orden entre análogos y no análogos no cambia: U de Mann–Whitney = 6 de 64 pares, así que AUC = 6/64 = 0,09375.</p>
    <h3>Tabla de sitios</h3>
    ${tableHTML(sitios, "cientifico")}
    ${variantMetricsHTML(cat)}
  </section>`;
}

function nombreCorto(n: string): string {
  return n.split(",")[0].split(" (")[0];
}

function etiquetaAmiga(cls: string): string {
  if (cls === "marte") return "análogo de Marte";
  if (cls === "luna") return "análogo de la Luna";
  if (cls === "ambos") return "análogo de ambos";
  if (cls === "ninguno") return "no análogo";
  return cls;
}

function segunIndiceCelda(s: SitioValidacion, nivel: Nivel): string {
  if (s.clase_predicha == null || s.clase_predicha === "" || s.excluido_auc) {
    return "<span class='muted'>excluido del AUC</span>";
  }
  const con = nivel !== "explorador";
  return `${escapeHtml(fraseParecido("Marte", s.delta_marte, con))}<br>${escapeHtml(fraseParecido("la Luna", s.delta_luna, con))}`;
}

function tableHTML(sitios: SitioValidacion[], nivel: Nivel): string {
  const compact = nivel !== "cientifico";
  const rows = sitios
    .map((s) => {
      const fail = s.entra_al_auc !== false && !s.excluido_auc && !s.acierto;
      return `<tr class="${fail ? "is-fail" : ""}">
        <td><button type="button" class="linkish" data-sitio-abrir="${escapeHtml(s.nombre)}" title="${escapeHtml(s.nombre)}">${escapeHtml(nombreCorto(s.nombre))}</button></td>
        ${compact ? "" : `<td class="mono">${s.lat.toFixed(3)}, ${s.lon.toFixed(3)}</td><td>${s.buffer_km}</td>
        <td>${escapeHtml(s.banda_latitud ?? "")} → M ${escapeHtml(s.banda_ganadora_marte ?? "—")} / L ${escapeHtml(s.banda_ganadora_luna ?? "—")}</td>`}
        <td>${escapeHtml(etiquetaAmiga(s.clase_conocida))}</td>
        <td>${segunIndiceCelda(s, nivel)}</td>
        <td class="mono">${fmt(s.delta_marte, 2)}</td>
        <td class="mono">${fmt(s.delta_luna, 2)}</td>
        <td class="${s.excluido_auc ? "" : s.acierto ? "ok" : "fail"}">${s.excluido_auc ? "fuera del AUC" : s.acierto ? "sí" : "no"}</td>
        ${compact ? "" : `<td title="${escapeHtml(s.cita ?? s.fuente ?? "")}">${escapeHtml((s.cita ?? s.fuente ?? "").slice(0, 80))}${(s.cita ?? "").length > 80 ? "…" : ""}</td>
        <td>${s.excluido_auc ? "no" : "sí"}${s.coordenada_no_verificada ? " · coord. no verif." : ""}</td>`}
      </tr>`;
    })
    .join("");
  const head = compact
    ? `<th>Sitio</th><th>Etiqueta conocida</th><th>Según el índice</th><th>δ Marte</th><th>δ Luna</th><th>Acierto</th>`
    : `<th>Sitio</th><th>Lat, lon</th><th>Buf. km</th><th>Banda propia → ganadora</th>
      <th>Etiqueta conocida</th><th>Según el índice</th><th>δ Marte</th><th>δ Luna</th>
      <th>Acierto</th><th>Cita</th><th>AUC</th>`;
  return `<div class="tabla-wrap"><table class="validacion" data-testid="tabla-validacion">
    <thead><tr>${head}</tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

function variantMetricsHTML(cat: Catalogo): string {
  type VariantMetrics = {
    etiqueta: string;
    marte: { auc: number; ic95_inferior?: number; ic95_superior?: number; sensitivity: number; precision: number };
    luna: { auc: number; ic95_inferior?: number; ic95_superior?: number; sensitivity: number; precision: number };
  };
  const variants = (cat as unknown as { metricas_por_variante?: Record<string, VariantMetrics> }).metricas_por_variante;
  const delong = (
    cat as unknown as {
      delong_pareado?: Record<string, { diferencia: number; p_valor: number }>;
    }
  ).delong_pareado;
  const nulo = (
    cat as unknown as {
      modelo_nulo_solo_abs_lat?: {
        marte: { auc: number; ic95_inferior: number; ic95_superior: number };
        luna: { auc: number; ic95_inferior: number; ic95_superior: number };
        nota: string;
      };
    }
  ).modelo_nulo_solo_abs_lat;
  let html = `<details class="secondary-metrics" open><summary>Variantes, ${escapeHtml("DeLong")} y modelo nulo</summary>`;
  if (variants) {
    html += `<div class="tabla-wrap"><table class="validacion"><thead><tr>
      <th>Variante</th><th>AUC Marte (IC 95 %)</th><th>Sens.</th><th>Prec.</th>
      <th>AUC Luna (IC 95 %)</th><th>Sens.</th><th>Prec.</th></tr></thead><tbody>`;
    for (const v of Object.values(variants)) {
      html += `<tr>
        <td>${escapeHtml(v.etiqueta)}</td>
        <td class="mono">${fmt(v.marte.auc, 2)} [${fmt(v.marte.ic95_inferior, 2)}–${fmt(v.marte.ic95_superior, 2)}]</td>
        <td class="mono">${fmt(v.marte.sensitivity, 2)}</td>
        <td class="mono">${fmt(v.marte.precision, 2)}</td>
        <td class="mono">${fmt(v.luna.auc, 2)} [${fmt(v.luna.ic95_inferior, 2)}–${fmt(v.luna.ic95_superior, 2)}]</td>
        <td class="mono">${fmt(v.luna.sensitivity, 2)}</td>
        <td class="mono">${fmt(v.luna.precision, 2)}</td>
      </tr>`;
    }
    html += `</tbody></table></div>`;
  }
  if (delong) {
    const m = delong.marte_con_vs_sin_latitud;
    const l = delong.luna_con_vs_sin_latitud;
    html += `<p>Test de ${term("delong")} pareado (con |lat| frente a sin latitud): Marte ΔAUC=${fmt(m?.diferencia, 3)}, p=${fmt(m?.p_valor, 3)}; Luna ΔAUC=${fmt(l?.diferencia, 3)}, p=${fmt(l?.p_valor, 3)}.</p>`;
  }
  if (nulo) {
    html += `<p><strong>${term("nulo", "Modelo nulo (solo |lat|)")}</strong>: AUC Marte ${fmt(nulo.marte.auc, 2)} [${fmt(nulo.marte.ic95_inferior, 2)}–${fmt(nulo.marte.ic95_superior, 2)}]; AUC Luna ${fmt(nulo.luna.auc, 2)} [${fmt(nulo.luna.ic95_inferior, 2)}–${fmt(nulo.luna.ic95_superior, 2)}]. ${escapeHtml(nulo.nota ?? "")}</p>`;
  }
  html += `</details>`;
  return html;
}

export function diagnosisHTML(nivel: Nivel): string {
  if (nivel === "explorador") {
    return `<section class="prose" data-testid="diagnostico">
      <h2>¿Por qué no funcionó bien?</h2>
      ${avisoHonestidad()}
      <p>A una resolución de <strong>1 km</strong>, el terreno típico de Marte se ve bastante <strong>plano</strong>.</p>
      <h3>Lo plano se parece a lo plano</h3>
      <p>Algunas llanuras o bosques de la Tierra también se ven planos a esa escala. El índice, que solo mira la forma del terreno, los acerca mucho a Marte. En cambio, varios lugares que sí se usan como análogos (volcanes, valles fríos, campos de lava) se ven más <strong>arrugados</strong> y quedan más lejos de esa foto típica.</p>
      <h3>Un cráter pequeño casi se esconde</h3>
      <p>Un cráter de poco más de un kilómetro, como Meteor Crater, cabe casi en un solo cuadrado: a esta escala se ve casi plano. Eso no quiere decir que deje de ser un análogo interesante a otra escala; quiere decir que <strong>esta regla, a 1 km, no lo ve</strong>.</p>
      <h3>Pocos lugares en la prueba</h3>
      <p>Solo se examinaron 16 sitios. Con tan pocos ejemplos es fácil equivocarse, y por eso no se retocó el índice después de ver la nota, ni se «volvió al revés» para que la cifra se viera mejor.</p>
      ${cajaExplica(
        "Entonces, ¿para qué sirve el mapa?",
        "Sirve para ver un retrato honesto de la superficie a 1 km, no para declarar que un porcentaje de Ecuador «es Marte». El mapa de clases no se usa como inventario, porque el corte de Marte dejó entrar a todos los no análogos.",
      )}
      <h3>Yasuní, un control en selva plana</h3>
      <p>En el Parque Nacional Yasuní, selva casi plana (pendiente mediana 0,3°), la similitud a Marte sale en 0,96. Un valor alto, aquí, indica sobre todo terreno llano a 1 km.</p>
      ${islasGalapagosHTML("explorador")}
    </section>`;
  }
  if (nivel === "estudiante") {
    return `<section class="prose" data-testid="diagnostico">
      <h2>Diagnóstico: por qué falló la v1</h2>
      ${avisoHonestidad()}
      <p>Con la configuración congelada, el ${term("auc")} de Marte es <strong>0,09</strong> (IC 95 % 0,00–0,29) y el de la Luna, <strong>0,25</strong> (0,00–0,69). El ${term("nulo")} que usa solo ${term("latitud")} obtiene un AUC de Marte de <strong>0,58</strong>, mayor que el del índice completo.</p>
      <h3>A 1 km el terreno planetario típico es suave</h3>
      <p>En el MEGDR, la mediana de ${term("pendiente")} de la banda A es ≈ 0,79° y la de ${term("rugosidad")} (TRI), unos 12 m. No análogos como Bondville o Tapajós también son casi planos a esta escala; Tapajós llega a δ Marte = 0,98, por encima de Yungay, Askja o Haughton.</p>
      <h3>Los análogos de campo suelen ser más rugosos, y se aceptan por geología</h3>
      <p>University Valley, Mauna Kea o Sverrefjell conservan más relieve a 1 km y se alejan de la firma típica. El índice no mira mineralogía ni historia geológica.</p>
      <h3>Fallos de escala</h3>
      <p>Meteor Crater (~1,2 km) e Inferno Chasm quedan casi planos en la grilla. Eso es un límite de resolución, no una sentencia sobre el sitio a otra escala.</p>
      <h3>Muestra pequeña y decisión de no retocar</h3>
      <p>n = 16, intervalos anchos. No se invirtió el índice ni se retocaron pesos o umbrales después del AUC, ni con Ecuador. El umbral de Marte (0,13) tiene ${term("especificidad")} 0: el mapa de clases no es un inventario y no se dan porcentajes de cobertura.</p>
      <h3>Control en Yasuní</h3>
      <p>En el polígono oficial del Parque Nacional Yasuní (n = 10 272 celdas; pendiente 0,30°) la mediana de δ Marte es 0,963 con <span class="mono">banda_propia</span> (0,954 en la corrida previa). Un δ alto indica sobre todo terreno llano a 1 km.</p>
      ${islasGalapagosHTML("estudiante")}
    </section>`;
  }
  return `<section class="prose" data-testid="diagnostico">
    <h2>Diagnóstico: por qué falló la v1</h2>
    ${avisoHonestidad()}
    <p>El índice v1, en datos reales y con la configuración congelada (<span class="mono">banda_propia</span>, vector con |lat|, elevación absoluta, pesos iguales), <strong>no discrimina</strong> los análogos etiquetados de los no análogos. El AUC de Marte es <strong>0,09</strong> (IC 95 % 0,00–0,29) y el de la Luna, <strong>0,25</strong> (IC 95 % 0,00–0,69), ambos por debajo de 0,5. El modelo nulo que usa solo |lat| obtiene un AUC de Marte de <strong>0,58</strong>, mayor que el del índice completo.</p>
    <h3>El terreno planetario típico a 1 km es suave</h3>
    <p>A ~1 km, Marte en el MEGDR es muy suave: la mediana de pendiente de la banda A es 0,79° (IQR 0,34–1,90°) y la de TRI, 12 m. Los no análogos terrestres del conjunto (llanura agrícola de Bondville, bosque de Tapajós, Hyytiälä, etc.) también son casi planos a esta escala (pendientes 0,1–0,7°, TRI de unos pocos metros). En ese espacio, Tapajós llega a δ Marte = 0,98, más alto que Yungay, Askja o Haughton.</p>
    <h3>Los análogos aceptados son sobre todo geológicos y mineralógicos, y más rugosos</h3>
    <p>Varios análogos de campo se aceptan por su geología o mineralogía, no porque su pendiente y su TRI a 1 km imiten la mediana planetaria. Los que conservan más relieve a esta escala (University Valley, Mauna Kea, Sverrefjell) se alejan de la firma típica de Marte. Al comparar solo una superficie suave a 1 km, el índice acerca más a las llanuras que a esos análogos.</p>
    <h3>Fallos de escala, no necesariamente de analogía</h3>
    <p>Meteor Crater (~1,2 km de diámetro) e Inferno Chasm quedan casi planos en la grilla de 1 km (pendiente mediana del buffer ≈ 0,5°). El índice los acerca a Marte, no a la Luna. Eso es un límite de resolución, no una sentencia sobre el valor del sitio como análogo a otra escala.</p>
    <h3>Muestra pequeña</h3>
    <p>El umbral y el AUC se fijaron solo sobre 16 sitios. Los intervalos de confianza son anchos. No se invirtió el índice, no se retocaron los pesos y no se reajustó el umbral después de ver el AUC ni con Ecuador.</p>
    <h3>Cómo hay que leer el resultado</h3>
    <p>El umbral de Youden de Marte queda en 0,13, con sensibilidad 1,0 y <strong>especificidad 0,0</strong>: todos los no análogos también lo superan. Por eso el mapa de clases no es un inventario fiable y no se presentan porcentajes de Ecuador como «análogo de Marte». Los mapas que hay que leer son los continuos de δ Marte y δ Luna, junto con esta validación y la nota de incertidumbre.</p>
    <h3>Control en Yasuní</h3>
    <p>En el polígono oficial del Parque Nacional Yasuní (WDPA/WDPCA site_id 186; n = 10 272; pendiente mediana 0,30°, TRI 5,38 m) la mediana de δ Marte es 0,9628 con <span class="mono">banda_propia</span> y 0,9543 en la corrida previa <span class="mono">todas_min</span>. Un δ alto indica sobre todo terreno llano a 1 km. Detalle: <span class="mono">docs/control_yasuni.md</span>.</p>
    ${islasGalapagosHTML("cientifico")}
  </section>`;
}

export function uncertaintyHTML(cat: Catalogo, nivel: Nivel): string {
  if (nivel === "explorador") {
    return `<section class="prose" data-testid="nota-incertidumbre">
      <h2>Qué se puede decir, y qué no</h2>
      ${avisoHonestidad()}
      <p>Comparamos solo la <strong>forma de la superficie</strong>: altura, inclinación, rugosidad y distancia al ecuador. No entran el clima, el color del suelo ni el calor que retiene el terreno. Por eso esta página no habla de «clima análogo».</p>
      <h3>Sí podemos decir</h3>
      <ul>
        <li>El método está documentado y no se cambió después de ver los resultados en Ecuador.</li>
        <li>Los mapas salen de datos públicos de Marte, de la Luna y de la Tierra.</li>
        <li>A 1 km, el retrato típico de Marte (y, un poco menos, el de la Luna) se parece más a llanuras suaves que a varios análogos clásicos de campo.</li>
      </ul>
      <h3>No podemos decir</h3>
      <ul>
        <li>No podemos señalar un porcentaje de Ecuador como «análogo de Marte» o «de la Luna». El corte usado para pintar clases dejó pasar a todos los no análogos de la prueba.</li>
        <li>No publicamos un mapa de clima, para no confundirlo con un dato real de este trabajo.</li>
      </ul>
      <h3>Cómo se compara cada lugar</h3>
      <p>La corrida oficial usa la franja de latitud de cada lugar (<span class="mono">banda_propia</span>), como pide el §5 del método. Antes se corrió otra regla (<span class="mono">todas_min</span>: la franja más cercana de las siete). Esa corrida oficial se hizo después de ver el resultado de la primera. Las dos dan la misma nota.</p>
      ${cajaExplica(
        "Los datos no son perfectos",
        "Un kilómetro es un cuadrito grande: se pierde el detalle de un cráter pequeño o de una ladera andina. Las «alturas» de cada cuerpo no están en la misma referencia al metro. Y solo se probaron 16 lugares.",
      )}
      <p class="muted">${escapeHtml(cat.nota_de_incertidumbre ?? "")}</p>
    </section>`;
  }
  if (nivel === "estudiante") {
    return `<section class="prose" data-testid="nota-incertidumbre">
      <h2>Nota de incertidumbre — v1 congelada</h2>
      ${avisoHonestidad()}
      <p>Fecha de congelación: 14 de noviembre de 2026 (America/Guayaquil). Variables: ${term("latitud")}, ${term("elevacion")}, ${term("pendiente")} y ${term("rugosidad")}, pesos iguales. No entran albedo, inercia térmica ni meteorología.</p>
      <h3>Qué quedó congelado</h3>
      <ol>
        <li>${term("std")} y firmas por ${term("bandas")} (mediana e ${term("iqr")}), solo sobre Marte (MOLA MEGDR 64 ppd) y la Luna (LOLA LDEM_64).</li>
        <li>En cada sitio, la mediana de las celdas válidas del buffer (haversina), no la «mejor» celda. Río Tinto, Ries y Sudbury se listan pero no entran al AUC.</li>
        <li>Umbral de ${term("youden")} y modo oficial <span class="mono">banda_propia</span>, congelados antes de Ecuador y de Galápagos. Galápagos no entra al AUC ni al umbral.</li>
      </ol>
      <h3>Límites</h3>
      <ul>
        <li>Resolución única de ~1 km: suaviza relieve local (Andes, cráteres, conos).</li>
        <li>Datums verticales no homologables al metro (areoide MOLA, esfera 1737,4 km, EGM2008).</li>
        <li>Muestra del AUC n = 16; banda A sin positivos terrestres (Ecuador se evalúa ahí, no se calibra).</li>
      </ul>
      <p>No se presentan porcentajes de cobertura por clase. No se publica capa climática.</p>
      <h3>Modo oficial <span class="mono">banda_propia</span> y el §5</h3>
      <p>La corrida oficial usa <span class="mono">banda_propia</span>: cada celda se compara solo con la firma de su propia banda de |lat|, como pide el §5 del método. Antes se corrió <span class="mono">todas_min</span> (la menor distancia a las siete bandas). <strong>La corrida con <span class="mono">banda_propia</span> se hizo después de ver el AUC de <span class="mono">todas_min</span>.</strong> El AUC no cambió (Marte 0,09; Luna 0,25; 6 de 16). <span class="mono">todas_min</span> queda como corrida previa, no se borra. Detalle en <span class="mono">docs/nota_incertidumbre.md</span>.</p>
      <p class="muted">${escapeHtml(cat.nota_de_incertidumbre ?? "")}</p>
    </section>`;
  }
  return `<section class="prose" data-testid="nota-incertidumbre">
    <h2>Nota de incertidumbre — v1 congelada</h2>
    ${avisoHonestidad()}
    <p>Fecha de congelación de parámetros, firmas y umbrales: 14 de noviembre de 2026 (America/Guayaquil, UTC-5). El índice v1 usa solo <strong>latitud (|lat|), elevación, pendiente y rugosidad (TRI 3×3)</strong>, con pesos iguales. <strong>No incluye albedo, inercia térmica ni ninguna variable meteorológica</strong> (veredicto de Expertos). Por eso no puede llamarse «clima análogo» ni «análogo ambiental completo».</p>
    <h3>Qué quedó congelado</h3>
    <ol>
      <li>Los parámetros de estandarización y las firmas por banda A–G (mediana e IQR) se ajustaron solo sobre muestras estratificadas de Marte (MOLA MEGDR 64 ppd) y de la Luna (LOLA LDEM_64), sin mezclar los dos cuerpos ni usar celdas terrestres.</li>
      <li>En cada sitio de validación se tomó la mediana de las celdas válidas dentro del buffer oficial (distancia haversina). No se eligió la «mejor» celda, para no inflar el AUC. Río Tinto, Ries y Sudbury se listan pero no entran al AUC.</li>
      <li>El umbral se volvió a fijar con el criterio de Youden, en modo <span class="mono">banda_propia</span>, solo sobre los mismos 16 sitios del AUC, y se congeló. Ecuador y Galápagos no intervinieron en esa decisión. Galápagos es solo área de evaluación.</li>
    </ol>
    <p>Askja permanece en el AUC con la coordenada confirmada 65,060, −16,640 y buffer de 6 km (Blasizzo et al., 2022).</p>
    <h3>Resultado de la validación</h3>
    <p>En datos reales el índice no discrimina bien. AUC Marte <strong>0,09</strong> (IC 95 % 0,00–0,29); AUC Luna <strong>0,25</strong> (IC 95 % 0,00–0,69). Aciertos de clase: 6 de 16. El modelo nulo de solo |lat| obtiene un AUC de Marte de 0,58, mayor que el del índice completo. El índice invertido (AUC &lt; 0,5) indica que varios no análogos quedan más cerca de la firma típica de Marte que los análogos etiquetados.</p>
    <h3>Limitaciones de los datos</h3>
    <ul>
      <li>La analogía es solo de superficie y únicamente con las variables comparables. El clima no entra al índice y no se publica un ráster climático.</li>
      <li>La resolución única de ~1 km suaviza el relieve local, sobre todo en los Andes y en cráteres o conos de unos pocos kilómetros.</li>
      <li>Los datums verticales no son homologables al metro (areoide MOLA, esfera lunar de 1737,4 km, geoide EGM2008).</li>
      <li>Albedo e inercia térmica no entran al índice v1 y no se descargaron.</li>
      <li>Pendiente y TRI en proyección equirrectangular cerca de los polos son más inciertos (banda G).</li>
      <li>La banda A no tiene positivos terrestres (Ecuador se evalúa ahí, no se calibra). La muestra del AUC es pequeña (16 sitios).</li>
    </ul>
    <h3>Qué sí se puede afirmar, y qué no</h3>
    <ul>
      <li><strong>Sí:</strong> el flujo es reproducible, los parámetros están congelados, las fuentes (MOLA, LOLA, GLO-90) están documentadas y la validación usa la lista verificada de Expertos.</li>
      <li><strong>Sí:</strong> a 1 km, la firma típica de Marte (y, en menor grado, de la Luna) en pendiente y TRI se parece más a llanuras terrestres suaves que a varios análogos clásicos de campo, cuyo relieve distintivo no sobrevive a esa escala.</li>
      <li><strong>No:</strong> no se puede presentar el mapa de clases de Ecuador como un inventario fiable de análogos. El umbral de Marte no tiene poder de discriminación en este conjunto (especificidad 0). No se informan porcentajes de cobertura por clase.</li>
      <li><strong>No:</strong> no se publica una capa climática ni se presenta un ejemplo sintético como si fuera un dato real.</li>
    </ul>
    <h3>Conjuntos de datos (citas)</h3>
    <ul>
      <li>MOLA MEGDR 64 ppd — <a href="https://pds-geosciences.wustl.edu/missions/mgs/megdr.html" rel="noopener noreferrer">PDS Geosciences</a></li>
      <li>LOLA LDEM_64 v3.1 — <a href="https://pds-geosciences.wustl.edu/missions/lro/lola.htm" rel="noopener noreferrer">PDS Geosciences</a></li>
      <li>Copernicus DEM GLO-90 — DOI <a href="https://doi.org/10.5270/ESA-c5d3d65" rel="noopener noreferrer">10.5270/ESA-c5d3d65</a></li>
    </ul>
    <h3>Modo oficial <span class="mono">banda_propia</span> y el §5 del método</h3>
    <p>La corrida oficial de la v1 usa <span class="mono">banda_propia</span>: δ se calcula solo con la firma de la banda de |lat| de la celda, como pide el §5 de <span class="mono">proyecto_ronald.txt</span> («En Marte y en la Luna se extraen celdas dentro de esas mismas bandas de latitud»). Antes se corrió <span class="mono">todas_min</span> (menor distancia a las firmas de las bandas A–G), congelada a las 13:40:40. <strong>La corrida con <span class="mono">banda_propia</span> se hizo después de ver el AUC de <span class="mono">todas_min</span></strong> (15:31:26). El AUC no cambió (Marte 0,09, IC 0,00–0,29; Luna 0,25, IC 0,00–0,69; 6 de 16). <span class="mono">todas_min</span> queda como corrida previa, no se borra. Actas: <span class="mono">docs/version_congelada_v1_banda_propia.md</span> (oficial) y <span class="mono">docs/version_congelada_v1.md</span> (corrida previa). Detalle en <span class="mono">docs/nota_incertidumbre.md</span>.</p>
    <p class="muted">${escapeHtml(cat.nota_de_incertidumbre ?? "")}</p>
  </section>`;
}

export function futureWorkHTML(): string {
  return `<section class="prose" data-testid="trabajo-futuro">
    <h2>Trabajo futuro (no forma parte del resultado congelado)</h2>
    <p class="warn-box"><strong>NO aprobado.</strong> El 14 de noviembre de 2026 (America/Guayaquil) no se aprobó una revisión v1.1. Lo que sigue es solo texto de trabajo futuro: no es un producto corrido, no sustituye a la v1 y no aparece como capa ni como selector de firmas en este tablero.</p>
    <p>Una línea posible sería construir firmas sobre <strong>sitios objetivo definidos a priori</strong> por criterios de misión, no sobre las medianas de bandas de latitud: Jezero, Gale, la zona de exploración Erebus Montes en Arcadia, la EZ DBDM en Deuteronilus, y las nueve <strong>regiones candidatas para el primer alunizaje de Artemis</strong>.</p>
    <p>En esa línea, el vector podría usar <strong>relieve relativo</strong> (no elevación absoluta), pendiente y TRI a <strong>escala emparejada</strong> entre cuerpos, y dejar fuera la latitud. Esa revisión no se implementa ni se puntúa aquí.</p>
  </section>`;
}

export function cardHTML(z: ZonaPrioritaria, nivel: Nivel): string {
  const c = z.clima;
  const conNum = nivel !== "explorador";
  const umbral =
    nivel === "cientifico"
      ? `<p class="muted">Umbral congelado (número, no una etiqueta de clase): Marte 0,13; Luna 0,79.</p>`
      : "";
  const humana = `<p class="lectura-delta">${escapeHtml(fraseParecido("Marte", z.delta_marte, conNum))}. ${escapeHtml(fraseParecido("la Luna", z.delta_luna, conNum))}.</p>
    <p class="muted">${NOTA_INDICE} Como la validación general no se aprobó, tómalo como una pista del mapa, no como una certeza.</p>${umbral}`;
  if (nivel === "explorador") {
    return `<article class="ficha" data-testid="ficha-zona">
      <h3>${escapeHtml(z.nombre)}</h3>
      <div class="meta">${escapeHtml(z.lat.toFixed(3))}°, ${escapeHtml(z.lon.toFixed(3))}°</div>
      ${humana}
    </article>`;
  }
  const vars =
    nivel === "estudiante"
      ? `<div class="kv">
      <div class="item"><span class="l">${term("latitud")}</span><span class="v">${z.firma_superficie.latitud.toFixed(2)}°</span></div>
      <div class="item"><span class="l">${term("elevacion")}</span><span class="v">${Math.round(z.elevacion_m)} m</span></div>
      <div class="item"><span class="l">${term("pendiente")}</span><span class="v">${fmt(z.pendiente_deg, 1)}°</span></div>
      <div class="item"><span class="l">${term("rugosidad")} (TRI)</span><span class="v">${fmt(z.rugosidad_tri, 0)} m</span></div>
      <div class="item"><span class="l">${term("delta")} Marte</span><span class="v">${fmt(z.delta_marte, 2)}</span></div>
      <div class="item"><span class="l">${term("delta")} Luna</span><span class="v">${fmt(z.delta_luna, 2)}</span></div>
    </div>`
      : `<div class="kv">
      <div class="item"><span class="l">Latitud</span><span class="v">${z.firma_superficie.latitud.toFixed(2)}°</span></div>
      <div class="item"><span class="l">Elevación</span><span class="v">${Math.round(z.elevacion_m)} m</span></div>
      <div class="item"><span class="l">Pendiente</span><span class="v">${fmt(z.pendiente_deg, 1)}°</span></div>
      <div class="item"><span class="l">Rugosidad (TRI)</span><span class="v">${fmt(z.rugosidad_tri, 0)} m</span></div>
      <div class="item"><span class="l">δ Marte</span><span class="v">${fmt(z.delta_marte, 2)}</span></div>
      <div class="item"><span class="l">δ Luna</span><span class="v">${fmt(z.delta_luna, 2)}</span></div>
      <div class="item"><span class="l">Banda propia</span><span class="v">${escapeHtml(z.banda_latitud)}</span></div>
      <div class="item"><span class="l">Banda ganadora</span><span class="v">M ${escapeHtml(z.banda_ganadora_marte ?? "—")} / L ${escapeHtml(z.banda_ganadora_luna ?? "—")}</span></div>
    </div>`;
  return `<article class="ficha" data-testid="ficha-zona">
    <h3>${escapeHtml(z.nombre)}</h3>
    <div class="meta">${z.lat.toFixed(3)}°, ${z.lon.toFixed(3)}°</div>
    ${humana}
    <h2>Firma de superficie (entra al índice)</h2>
    ${vars}
    <div class="clima-box">
      <div class="tag">${escapeHtml(c.advertencia ?? "El clima no entra al índice.")}</div>
      <p>${escapeHtml(c.disponible === false ? (c.nota ?? "No se publica un ráster ni cifras climáticas en esta entrega, para no presentar un ejemplo sintético como si fuera un dato real.") : (c.nota ?? ""))}</p>
    </div>
  </article>`;
}

export function sitioCardHTML(s: SitioValidacion, nivel: Nivel): string {
  const conNum = nivel !== "explorador";
  return `<article class="ficha" data-testid="ficha-sitio">
    <h3>${escapeHtml(s.nombre)}</h3>
    <div class="meta">${s.lat.toFixed(3)}°, ${s.lon.toFixed(3)}°${s.excluido_auc ? " · fuera del AUC" : s.acierto ? " · acierto" : " · no acierto"}</div>
    <p>Etiqueta conocida (la del examen de validación, no una clase del mapa de Ecuador): <strong>${escapeHtml(etiquetaAmiga(s.clase_conocida))}</strong>. ${s.excluido_auc ? "No entra al cálculo del AUC." : `${NOTA_INDICE}`}</p>
    <p>${escapeHtml(fraseParecido("Marte", s.delta_marte, conNum))}. ${escapeHtml(fraseParecido("la Luna", s.delta_luna, conNum))}.</p>
    ${nivel === "cientifico" ? `<p class="muted">Buffer ${s.buffer_km} km · banda ${escapeHtml(s.banda_latitud ?? "—")} · ${escapeHtml(s.cita ?? s.fuente ?? "")}</p>` : ""}
  </article>`;
}

export function defAbreviada(id: string, nivel: Nivel): string {
  return defTermino(id, nivel);
}
