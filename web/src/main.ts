import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "maplibre-gl/dist/maplibre-gl.css";
import "./style.css";

import type { Map as MapLibreMap, MapMouseEvent } from "maplibre-gl";
import {
  cardHTML,
  diagnosisHTML,
  fmt,
  fraseDelta,
  fraseParecido,
  futureWorkHTML,
  homeHTML,
  sitioCardHTML,
  TOUR_PASOS,
  uncertaintyHTML,
  validationHTML,
} from "./content";
import { createDataSource } from "./dataSource";
import { defTermino, GLOSARIO } from "./glossary";
import {
  applyGlobeState,
  AREA_BOUNDS,
  flyToSitios,
  clearMarkers,
  createGlobeMap,
  escapeHtml,
  nearestZone,
  setMarkers,
  setOverlayOpacity,
  type AreaTierra,
  type CuerpoGlobo,
} from "./maps";
import { assetUrl } from "./paths";
import { recomputeValidation } from "./scoring";
import {
  DEFAULT_WEIGHTS,
  NIVELES,
  VAR_LABELS,
  type Catalogo,
  type Nivel,
  type SitioValidacion,
  type Vista,
  type Weights,
} from "./types";

const LS_NIVEL = "analog_nivel";
const LS_TOUR = "analog_tour_dismissed";

const VISTAS_PRINCIPALES: { id: Vista; label: string }[] = [
  { id: "inicio", label: "Inicio" },
  { id: "similitud-marte", label: "Similitud a Marte" },
  { id: "similitud-luna", label: "Similitud a la Luna" },
  { id: "validacion", label: "Validación" },
  { id: "diagnostico", label: "Diagnóstico" },
  { id: "incertidumbre", label: "Incertidumbre" },
  { id: "visualizador", label: "Visualizador 3D" },
];

const VISTAS_MAS: { id: Vista; label: string }[] = [
  { id: "ficha", label: "Ficha de zona" },
  { id: "clases", label: "Clases (secundaria · especif. 0)" },
  { id: "clima", label: "Clima (no publicado)" },
  { id: "trabajo-futuro", label: "Trabajo futuro" },
];

const TODAS_VISTAS: Vista[] = [...VISTAS_PRINCIPALES, ...VISTAS_MAS].map((v) => v.id);
const TEXT_VISTAS: Vista[] = ["inicio", "validacion", "diagnostico", "incertidumbre", "trabajo-futuro"];
const MAP_VISTAS: Vista[] = ["similitud-marte", "similitud-luna", "clases", "ficha", "clima"];

function readNivel(): Nivel {
  const v = localStorage.getItem(LS_NIVEL);
  if (v === "explorador" || v === "estudiante" || v === "cientifico") return v;
  return "explorador";
}

function vistaFromHash(): Vista {
  const h = (location.hash || "").replace(/^#/, "");
  return (TODAS_VISTAS as string[]).includes(h) ? (h as Vista) : "inicio";
}

const state = {
  vista: "inicio" as Vista,
  nivel: readNivel() as Nivel,
  zonaId: null as string | null,
  sitioNombre: null as string | null,
  weights: { ...DEFAULT_WEIGHTS } as Weights,
  sitios: [] as SitioValidacion[],
  opacity: 0.82,
  tour: null as number | null,
  cuerpoGlobo: "tierra" as CuerpoGlobo,
  areaTierra: "ecuador_continental" as AreaTierra,
  unityAbierto: false,
};

function metricsStrip(cat: Catalogo, nivel: Nivel): string {
  const m = cat.metricas_validacion;
  const aciertos = m.aciertos_auc ?? m.aciertos ?? 6;
  const n = m.n_sitios_auc ?? 16;
  if (nivel === "explorador") {
    return `
      <div class="metric"><span class="k">${aciertos} de ${n}</span><span class="l">Aciertos en la prueba</span></div>
      <div class="metric"><span class="k">0,09</span><span class="l">Nota Marte (de 1)</span></div>
      <div class="metric"><span class="k">0,25</span><span class="l">Nota Luna (de 1)</span></div>`;
  }
  if (nivel === "estudiante") {
    return `
      <div class="metric"><span class="k">0,09</span><span class="l">AUC Marte</span></div>
      <div class="metric"><span class="k">0,25</span><span class="l">AUC Luna</span></div>
      <div class="metric"><span class="k">${aciertos}/${n}</span><span class="l">Aciertos (AUC)</span></div>`;
  }
  return `
    <div class="metric"><span class="k">0,09 [0,00–0,29]</span><span class="l">AUC Marte (IC 95 %)</span></div>
    <div class="metric"><span class="k">0,25 [0,00–0,69]</span><span class="l">AUC Luna (IC 95 %)</span></div>
    <div class="metric"><span class="k">0,13</span><span class="l">Umbral Marte</span></div>
    <div class="metric"><span class="k">0,79</span><span class="l">Umbral Luna</span></div>
    <div class="metric"><span class="k">${aciertos}/${n}</span><span class="l">Aciertos (AUC)</span></div>`;
}

function legendHTML(vista: Vista, nivel: Nivel): string {
  if (vista === "clases") {
    return `<div class="title">Vista secundaria del umbral congelado</div>
      <div class="warn-box">El umbral de Marte (0,13) tiene <strong>especificidad 0</strong>. Estos colores no son un inventario de análogos ni una clasificación. Prefiera los mapas continuos de δ.</div>
      <div><span class="swatch swatch-marte"></span>δ Marte ≥ 0,13 y δ Luna &lt; 0,79</div>
      <div><span class="swatch swatch-luna"></span>δ Luna ≥ 0,79 y δ Marte &lt; 0,13</div>
      <div><span class="swatch swatch-ambos"></span>supera ambos umbrales</div>
      <div><span class="swatch swatch-ninguno"></span>no supera ninguno</div>
      <p class="note">Los colores son los del ráster congelado v1; no se alteró el archivo. Es un recorte por umbral, no una etiqueta definitiva.</p>`;
  }
  if (vista === "clima") {
    return `<div class="title">Clima</div>
      <p class="note">No entra al índice y no se publica un ráster, para no confundirlo con un dato real.</p>`;
  }
  const cuerpo = vista === "similitud-luna" ? "la Luna" : "Marte";
  const ramp = vista === "similitud-luna" ? "ramp-luna" : "ramp-marte";
  const tech =
    nivel === "cientifico"
      ? `δ de 0 a 1 (0 = nada, 1 = idéntico en el espacio estandarizado). `
      : nivel === "estudiante"
        ? `δ va de 0 (nada parecido) a 1 (idéntico, según el índice). `
        : "";
  return `<div class="title">Parecido a ${cuerpo}</div>
    <div class="ramp ${ramp}" role="img" aria-label="De menos parecido a más parecido"></div>
    <div class="ramp-labels"><span>Menos parecido</span><span>Más parecido</span></div>
    <p class="note">${tech}La rampa de color es la del producto congelado v1 (no se modificó el archivo). Úsala junto con las palabras de la leyenda. El índice no pasó la validación: un color «más parecido» es una pista, no una certeza.</p>`;
}

function captionHTML(vista: Vista, cat: Catalogo, nivel: Nivel, cuerpo: CuerpoGlobo, area: AreaTierra): string {
  if (cuerpo === "luna") {
    return `<strong>Luna</strong> · relieve LOLA LDEM_64 (sombreado). El índice δ se calcula en la Tierra, no sobre este globo. El terreno 3D no está activo (pesa en móviles).`;
  }
  if (cuerpo === "marte") {
    return `<strong>Marte</strong> · relieve MOLA MEGDR 64 ppd (sombreado). El índice δ se calcula en la Tierra, no sobre este globo. El terreno 3D no está activo (pesa en móviles).`;
  }
  const ext = AREA_BOUNDS[area];
  const areaNom = area === "galapagos" ? "Galápagos" : "Ecuador continental";
  const isla =
    area === "galapagos"
      ? " · 6 606 celdas válidas de 1 km (Isabela 4 128; Darwin y Wolf: 0)"
      : " · 446 657 celdas válidas de 1 km";
  if (nivel === "explorador") {
    const dest = vista === "similitud-luna" ? "la Luna" : vista === "clases" ? "los umbrales congelados (vista secundaria)" : "Marte";
    return `<strong>${areaNom}</strong> · parecido a ${dest}, en cuadrados de unos 1 km${isla}. Relieve en sombreado.`;
  }
  const res = cat.grilla.resolucion_deg ?? cat.grilla.resolucion_objetivo_m;
  const base = `<strong>${areaNom}</strong> · lon ${ext.oeste.toFixed(2)}° a ${ext.este.toFixed(2)}° · lat ${ext.sur.toFixed(2)}° a ${ext.norte.toFixed(2)}° · ~1 km (${res}) · MOLA / LOLA / GLO-90 · v1 congelada · relieve en sombreado; el terreno 3D no está activo${isla}`;
  if (vista === "clima") return `${base} · capa no publicada, el clima no entra al índice`;
  if (vista === "clases") return `${base} · vista <strong>secundaria</strong> del umbral congelado: especificidad 0, sin porcentajes de cobertura`;
  return base;
}


function bannerAviso(cat: Catalogo, nivel: Nivel): string {
  if (cat.mock) return cat.aviso;
  if (nivel === "explorador") {
    return "Datos reales de superficie (MOLA, LOLA, GLO-90). El índice no pasó la validación: 6 de 16 aciertos.";
  }
  return cat.aviso;
}

async function main(): Promise<void> {
  const cat = await createDataSource().load();
  state.sitios = cat.sitios_validacion;
  state.zonaId = cat.zonas_prioritarias[0]?.id ?? null;
  state.vista = vistaFromHash();
  const app = document.getElementById("app")!;

  app.innerHTML = `
    <a class="skip-link" href="#contenido">Saltar al contenido</a>
    <div class="${cat.mock ? "banner-mock" : "banner-real"}" data-testid="${cat.mock ? "mock-banner" : "real-banner"}">
      <strong>${cat.mock ? "Datos MOCK" : "v1 congelada"}</strong>
      <span id="banner-aviso"></span>
    </div>
    <header class="header">
      <div class="brand">
        <h1>ANALOG / delta</h1>
        <p>¿Dónde en la Tierra se parece a la Luna y a Marte? · NASA Space Apps 2026 · Ecuador</p>
      </div>
      <div class="nivel-block">
        <span class="nivel-label" id="nivel-label">Nivel de detalle</span>
        <div class="nivel-sel" role="radiogroup" aria-labelledby="nivel-label" data-testid="nivel-selector">
          ${NIVELES.map(
            (n) =>
              `<button type="button" role="radio" data-nivel="${n.id}" aria-pressed="${n.id === state.nivel}" title="${escapeHtml(n.hint)}">${escapeHtml(n.label)}</button>`,
          ).join("")}
        </div>
      </div>
      <div class="metrics-strip" id="metrics-strip">${metricsStrip(cat, state.nivel)}</div>
    </header>
    <nav class="toolbar" aria-label="Secciones de la página">
      ${VISTAS_PRINCIPALES.map(
        (v) =>
          `<button type="button" data-vista="${v.id}" class="${v.id === state.vista ? "is-active" : ""}">${escapeHtml(v.label)}</button>`,
      ).join("")}
      <div class="more-wrap">
        <button type="button" id="btn-mas" aria-expanded="false" aria-controls="menu-mas">Más</button>
        <div class="more-menu" id="menu-mas" hidden role="menu">
          ${VISTAS_MAS.map(
            (v) => `<button type="button" role="menuitem" data-vista="${v.id}" >${escapeHtml(v.label)}</button>`,
          ).join("")}
          <button type="button" data-action="tour">Repetir el recorrido</button>
        </div>
      </div>
      <span class="hint" id="toolbar-hint"></span>
    </nav>
    <div id="visualizador-wrap" hidden>
      <iframe id="visualizador-frame" title="Visualizador 3D ANALOG v1" style="width:100%;height:calc(100vh - 64px);border:0" allow="fullscreen"></iframe>
    </div>
    <div class="main" id="contenido">
      <div class="map-col">
        <div class="map-caption" id="map-caption"></div>
        <div id="map" role="region" aria-label="Globo de Tierra, Luna o Marte"></div>
        <div class="map-controls">
          <div class="cuerpo-toggle" role="group" aria-label="Cuerpo del globo" data-testid="selector-cuerpo-globo">
            <button type="button" data-cuerpo-globo="tierra" aria-pressed="true">Tierra</button>
            <button type="button" data-cuerpo-globo="luna" aria-pressed="false">Luna</button>
            <button type="button" data-cuerpo-globo="marte" aria-pressed="false">Marte</button>
          </div>
          <div class="cuerpo-toggle solo-tierra" role="group" aria-label="Área en la Tierra" data-testid="selector-area">
            <button type="button" data-area="ecuador_continental" aria-pressed="true">Ecuador continental</button>
            <button type="button" data-area="galapagos" aria-pressed="false">Galápagos</button>
            <button type="button" id="btn-sitios-validacion" data-testid="btn-sitios-validacion" aria-pressed="false">Sitios de validación</button>
          </div>
          <div class="cuerpo-toggle solo-tierra" role="group" aria-label="Comparar con Marte o con la Luna" data-testid="toggle-cuerpo">
            <button type="button" data-cuerpo="marte" aria-pressed="true">Similitud a Marte</button>
            <button type="button" data-cuerpo="luna" aria-pressed="false">Similitud a la Luna</button>
          </div>
          <div class="opacidad-ctl solo-tierra" data-testid="control-opacidad">
            <label>Opacidad de la capa
              <input type="range" id="opacidad" min="20" max="100" step="1" value="${Math.round(state.opacity * 100)}" />
            </label>
          </div>
          <button type="button" class="btn btn-primary" id="btn-ver-unity" data-testid="btn-ver-unity" aria-expanded="false" aria-controls="unity-panel">Ver en 3D (Unity)</button>
        </div>
        <div class="map-legend" id="map-legend" data-testid="leyenda"></div>
        <div class="map-popup" id="map-popup" hidden role="dialog" aria-label="Ficha del punto"></div>
        <div id="unity-panel" class="unity-panel" hidden role="dialog" aria-modal="true" aria-labelledby="unity-panel-titulo">
          <div class="unity-panel-bar">
            <h2 id="unity-panel-titulo">Visualizador 3D</h2>
            <button type="button" class="btn" id="btn-cerrar-unity">Cerrar</button>
          </div>
          <iframe id="unity-panel-frame" title="Visualizador 3D ANALOG v1" allow="fullscreen"></iframe>
        </div>
      </div>
      <aside class="panel" aria-label="Explicación">
        <div class="panel-body" id="panel-body" tabindex="-1"></div>
        <div class="weights" id="weights-box">
          <div class="head">
            <span>Pesos del índice <small>(la v1 congelada usa 0,25 iguales; mover estos controles solo recalcula la tabla en pantalla, no altera umbrales, rásteres ni las métricas oficiales)</small></span>
            <button type="button" class="reset" id="reset-pesos">Restablecer</button>
          </div>
          <div class="weight-grid" id="weight-grid"></div>
        </div>
      </aside>
    </div>
    <div class="tour-backdrop" id="tour-backdrop" hidden></div>
    <div class="tour-dialog" id="tour-dialog" hidden role="dialog" aria-modal="true" aria-labelledby="tour-titulo" data-testid="tour-dialog">
      <p class="tour-progress" id="tour-progress"></p>
      <h2 id="tour-titulo"></h2>
      <p id="tour-cuerpo"></p>
      <div class="tour-actions">
        <button type="button" class="btn" data-tour="prev">Anterior</button>
        <button type="button" class="btn btn-primary" data-tour="next">Siguiente</button>
        <button type="button" class="btn btn-ghost" data-tour="skip">Saltar recorrido</button>
      </div>
    </div>
    <div id="glosario-panel" hidden role="tooltip"></div>
  `;

  const map: MapLibreMap = createGlobeMap(document.getElementById("map")!);

  const hintForNivel = () => {
    const el = document.getElementById("toolbar-hint")!;
    const n = NIVELES.find((x) => x.id === state.nivel);
    el.textContent = n ? n.hint : "";
  };

  const closeGlossary = () => {
    const panel = document.getElementById("glosario-panel")!;
    panel.hidden = true;
    app.querySelectorAll<HTMLButtonElement>(".term[aria-expanded='true']").forEach((b) => {
      b.setAttribute("aria-expanded", "false");
    });
  };

  const openGlossary = (btn: HTMLButtonElement) => {
    const id = btn.dataset.term ?? "";
    const t = GLOSARIO[id];
    const panel = document.getElementById("glosario-panel")!;
    if (!t) return;
    const open = btn.getAttribute("aria-expanded") === "true";
    closeGlossary();
    if (open) return;
    btn.setAttribute("aria-expanded", "true");
    panel.innerHTML = `<p class="g-k">${escapeHtml(t.etiqueta)}</p><p>${escapeHtml(defTermino(id, state.nivel))}</p>`;
    panel.hidden = false;
    const r = btn.getBoundingClientRect();
    const pw = Math.min(352, window.innerWidth - 16);
    let left = r.left;
    if (left + pw > window.innerWidth - 8) left = window.innerWidth - pw - 8;
    let top = r.bottom + 6;
    panel.style.position = "fixed";
    panel.style.width = `${pw}px`;
    panel.style.left = `${Math.max(8, left)}px`;
    panel.style.top = `${top}px`;
  };

  const bindGlossary = (root: ParentNode) => {
    root.querySelectorAll<HTMLButtonElement>("button.term").forEach((b) => {
      b.addEventListener("click", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        openGlossary(b);
      });
    });
  };

  const renderWeights = () => {
    const g = document.getElementById("weight-grid")!;
    g.innerHTML = (Object.keys(VAR_LABELS) as (keyof Weights)[])
      .map(
        (k) => `<label class="weight-row">${VAR_LABELS[k]}
        <input type="range" min="0" max="100" step="1" data-var="${k}" value="${Math.round(state.weights[k] * 100)}" />
        <span class="val">${state.weights[k].toFixed(2)}</span></label>`,
      )
      .join("");
    g.querySelectorAll<HTMLInputElement>("input[type=range]").forEach((inp) => {
      inp.addEventListener("input", () => {
        state.weights[inp.dataset.var as keyof Weights] = Number(inp.value) / 100;
        try {
          state.sitios = recomputeValidation(cat, state.weights);
        } catch {
          /* catálogo sin firmas completas */
        }
        renderWeights();
        renderPanel();
      });
    });
  };

  const hidePopup = () => {
    const pop = document.getElementById("map-popup");
    if (pop) pop.hidden = true;
  };

  const showZonePopup = (zonaId: string, at?: { x: number; y: number }) => {
    const z = cat.zonas_prioritarias.find((x) => x.id === zonaId);
    const pop = document.getElementById("map-popup")!;
    if (!z) {
      pop.hidden = true;
      return;
    }
    pop.innerHTML = `<button type="button" class="cerrar" aria-label="Cerrar ficha">×</button>
      <h3>${escapeHtml(z.nombre)}</h3>
      <p>${escapeHtml(fraseParecido("Marte", z.delta_marte, state.nivel !== "explorador"))}.</p>
      <p>${escapeHtml(fraseParecido("la Luna", z.delta_luna, state.nivel !== "explorador"))}.</p>
      <p class="muted">Es un índice, no una clasificación. Como la prueba general no se aprobó, esto es una pista, no una certeza.</p>
      <button type="button" class="btn" data-abrir-ficha="${z.id}">Ver ficha completa</button>`;
    pop.hidden = false;
    const col = document.querySelector(".map-col") as HTMLElement;
    const cr = col.getBoundingClientRect();
    const x = at?.x ?? cr.width * 0.5;
    const y = at?.y ?? cr.height * 0.4;
    pop.style.left = `${Math.min(Math.max(8, x - 40), cr.width - 280)}px`;
    pop.style.top = `${Math.min(Math.max(48, y - 10), cr.height - 200)}px`;
    pop.querySelector(".cerrar")?.addEventListener("click", hidePopup);
    pop.querySelector<HTMLButtonElement>("[data-abrir-ficha]")?.addEventListener("click", () => {
      state.zonaId = z.id;
      state.vista = "ficha";
      hidePopup();
      syncVista();
    });
  };

  const refreshMarkers = () => {
    setMarkers(map, cat.zonas_prioritarias, state.zonaId, (id) => {
      state.zonaId = id;
      showZonePopup(id);
      if (state.vista === "ficha") renderPanel();
    });
  };

  const overlayFor = (vista: Vista): Vista => {
    if (vista === "similitud-luna" || vista === "similitud-marte" || vista === "clases") return vista;
    return "similitud-marte";
  };

  const showMapLayer = (fly = false) => {
    const overlay = overlayFor(state.vista);
    applyGlobeState(map, {
      cuerpo: state.cuerpoGlobo,
      area: state.areaTierra,
      vista: state.vista === "clima" ? "similitud-marte" : overlay,
      opacity: state.opacity,
      sitios: state.sitios.length ? state.sitios : cat.sitios_validacion,
      fly,
    });
    document.getElementById("map-caption")!.innerHTML = captionHTML(state.vista, cat, state.nivel, state.cuerpoGlobo, state.areaTierra);
    document.getElementById("map-legend")!.innerHTML = legendHTML(overlay === "clases" || state.vista === "clima" ? state.vista : overlay, state.nivel);
    app.dataset.cuerpoGlobo = state.cuerpoGlobo;
    app.dataset.area = state.areaTierra;
    app.querySelectorAll<HTMLButtonElement>("[data-cuerpo-globo]").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.cuerpoGlobo === state.cuerpoGlobo));
    });
    app.querySelectorAll<HTMLButtonElement>("[data-area]").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.area === state.areaTierra));
    });
    app.querySelector<HTMLButtonElement>('[data-cuerpo="marte"]')?.setAttribute("aria-pressed", String(overlay !== "similitud-luna"));
    app.querySelector<HTMLButtonElement>('[data-cuerpo="luna"]')?.setAttribute("aria-pressed", String(overlay === "similitud-luna"));
    if (state.cuerpoGlobo === "tierra") refreshMarkers();
    else clearMarkers();
    requestAnimationFrame(() => map.resize());
  };

  let unityFocusPrev: HTMLElement | null = null;

  const hookUnityFrameEsc = () => {
    const frame = document.getElementById("unity-panel-frame") as HTMLIFrameElement | null;
    if (!frame) return;
    const listen = () => {
      try {
        const win = frame.contentWindow;
        const doc = frame.contentDocument;
        if (!win || !doc) return;
        const href = doc.location?.href ?? "";
        if (!href || href === "about:blank") return;
        const mark = frame as HTMLIFrameElement & { __escHookedDoc?: Document };
        if (mark.__escHookedDoc === doc) return;
        mark.__escHookedDoc = doc;
        const onEsc = (ev: KeyboardEvent) => {
          if (ev.key !== "Escape" || !state.unityAbierto) return;
          ev.preventDefault();
          ev.stopPropagation();
          closeUnityPanel();
        };
        win.addEventListener("keydown", onEsc, true);
        doc.addEventListener("keydown", onEsc, true);
      } catch {
        /* el iframe aún no está listo o no es mismo origen */
      }
    };
    const marked = frame as HTMLIFrameElement & { __escLoadBound?: boolean };
    if (!marked.__escLoadBound) {
      frame.addEventListener("load", listen);
      marked.__escLoadBound = true;
    }
    listen();
  };

  const openUnityPanel = () => {
    const panel = document.getElementById("unity-panel")!;
    const frame = document.getElementById("unity-panel-frame") as HTMLIFrameElement;
    unityFocusPrev = (document.activeElement instanceof HTMLElement ? document.activeElement : null);
    panel.hidden = false;
    panel.classList.add("is-open");
    state.unityAbierto = true;
    document.documentElement.classList.add("unity-abierto");
    document.getElementById("btn-ver-unity")?.setAttribute("aria-expanded", "true");
    if (!frame.getAttribute("src")) frame.src = assetUrl("/unity/visualizador/index.html");
    hookUnityFrameEsc();
    document.getElementById("btn-cerrar-unity")?.focus();
  };

  const closeUnityPanel = () => {
    const panel = document.getElementById("unity-panel");
    if (!panel) return;
    panel.hidden = true;
    panel.classList.remove("is-open");
    state.unityAbierto = false;
    document.documentElement.classList.remove("unity-abierto");
    document.getElementById("btn-ver-unity")?.setAttribute("aria-expanded", "false");
    const back = unityFocusPrev && document.contains(unityFocusPrev)
      ? unityFocusPrev
      : document.getElementById("btn-ver-unity");
    unityFocusPrev = null;
    back?.focus();
    requestAnimationFrame(() => {
      map.resize();
      requestAnimationFrame(() => map.resize());
    });
  };

  const renderPanel = () => {
    const body = document.getElementById("panel-body")!;
    const zona = cat.zonas_prioritarias.find((z) => z.id === state.zonaId) ?? cat.zonas_prioritarias[0];
    if (state.vista === "inicio") {
      body.innerHTML = homeHTML(state.nivel);
      bindGlossary(body);
      body.querySelectorAll<HTMLButtonElement>("[data-action]").forEach((b) => {
        b.addEventListener("click", () => {
          if (b.dataset.action === "tour") startTour();
          if (b.dataset.action === "ir" && b.dataset.ir) {
            state.vista = b.dataset.ir as Vista;
            syncVista();
          }
        });
      });
      return;
    }
    if (state.vista === "validacion") {
      const sitio = state.sitios.find((s) => s.nombre === state.sitioNombre);
      body.innerHTML = `${validationHTML(cat, state.sitios, state.nivel)}${sitio ? sitioCardHTML(sitio, state.nivel) : ""}`;
      bindGlossary(body);
      body.querySelectorAll<HTMLButtonElement>("[data-sitio-abrir]").forEach((b) => {
        b.addEventListener("click", () => {
          state.sitioNombre = b.dataset.sitioAbrir ?? null;
          renderPanel();
          document.querySelector("[data-testid='ficha-sitio']")?.scrollIntoView({ block: "nearest" });
        });
      });
      return;
    }
    if (state.vista === "diagnostico") {
      body.innerHTML = diagnosisHTML(state.nivel);
      bindGlossary(body);
      return;
    }
    if (state.vista === "incertidumbre") {
      body.innerHTML = uncertaintyHTML(cat, state.nivel);
      bindGlossary(body);
      return;
    }
    if (state.vista === "trabajo-futuro") {
      body.innerHTML = futureWorkHTML();
      return;
    }
    if (state.vista === "clases") {
      body.innerHTML = `<section class="prose">
        <div class="warn-box" data-testid="aviso-clases">El umbral de Youden de Marte tiene <strong>especificidad 0</strong>: todos los no análogos del conjunto también lo superan. Este mapa de clases es una vista secundaria y <strong>no es un inventario fiable</strong> de análogos. No se informan porcentajes de cobertura. Prefiera los mapas continuos de similitud a Marte y a la Luna.</div>
        ${zona ? cardHTML(zona, state.nivel) : ""}
      </section>`;
      bindGlossary(body);
      return;
    }
    if (state.vista === "ficha" && zona) {
      const list = cat.zonas_prioritarias
        .map(
          (z) =>
            `<li><button type="button" data-zona="${z.id}" class="${z.id === zona.id ? "is-selected" : ""}">${escapeHtml(z.nombre)}<span class="sc">${state.nivel === "explorador" ? escapeHtml(fraseParecido("Marte", z.delta_marte, false)) : `δM ${fmt(z.delta_marte, 2)} · δL ${fmt(z.delta_luna, 2)}`}</span></button></li>`,
        )
        .join("");
      body.innerHTML = `<h2>Zonas en Ecuador y Galápagos</h2><ul class="zona-list">${list}</ul>${cardHTML(zona, state.nivel)}`;
      bindGlossary(body);
      body.querySelectorAll<HTMLButtonElement>("[data-zona]").forEach((b) => {
        b.addEventListener("click", () => {
          state.zonaId = b.dataset.zona ?? null;
          renderPanel();
          refreshMarkers();
          if (state.zonaId) showZonePopup(state.zonaId);
        });
      });
      return;
    }
    const list = cat.zonas_prioritarias
      .map(
        (z) =>
          `<li><button type="button" data-zona="${z.id}" class="${z.id === zona?.id ? "is-selected" : ""}">${escapeHtml(z.nombre)}<span class="sc">${state.nivel === "explorador" ? fraseDelta(z.delta_marte) : `δM ${fmt(z.delta_marte, 2)} · δL ${fmt(z.delta_luna, 2)}`}</span></button></li>`,
      )
      .join("");
    body.innerHTML = `<h2>Zonas en Ecuador y Galápagos</h2>
      <p class="muted">Pulsa una zona o un punto del mapa. El índice no pasó la validación: estas cifras son pistas, no un inventario.</p>
      <ul class="zona-list">${list}</ul>${zona ? cardHTML(zona, state.nivel) : ""}`;
    bindGlossary(body);
    body.querySelectorAll<HTMLButtonElement>("[data-zona]").forEach((b) => {
      b.addEventListener("click", () => {
        state.zonaId = b.dataset.zona ?? null;
        showZonePopup(state.zonaId!);
        renderPanel();
        refreshMarkers();
      });
    });
  };

  const renderTour = () => {
    const box = document.getElementById("tour-dialog")!;
    const backdrop = document.getElementById("tour-backdrop")!;
    if (state.tour == null) {
      box.hidden = true;
      backdrop.hidden = true;
      return;
    }
    const paso = TOUR_PASOS[state.tour];
    document.getElementById("tour-progress")!.textContent = `Paso ${state.tour + 1} de ${TOUR_PASOS.length}`;
    document.getElementById("tour-titulo")!.textContent = paso.titulo;
    document.getElementById("tour-cuerpo")!.textContent = paso.cuerpo;
    const next = box.querySelector<HTMLButtonElement>("[data-tour='next']")!;
    next.textContent = state.tour === TOUR_PASOS.length - 1 ? "Terminar" : "Siguiente";
    box.querySelector<HTMLButtonElement>("[data-tour='prev']")!.disabled = state.tour === 0;
    box.hidden = false;
    backdrop.hidden = false;
    next.focus();
  };

  function startTour(): void {
    document.getElementById("menu-mas")?.setAttribute("hidden", "");
    document.getElementById("btn-mas")?.setAttribute("aria-expanded", "false");
    state.tour = 0;
    state.vista = TOUR_PASOS[0].vista;
    syncVista();
    renderTour();
  }

  function endTour(dismiss: boolean): void {
    if (dismiss) localStorage.setItem(LS_TOUR, "1");
    state.tour = null;
    renderTour();
  }

  const syncVista = () => {
    app.dataset.vista = state.vista;
    app.dataset.nivel = state.nivel;
    const allBtns = app.querySelectorAll<HTMLButtonElement>("button[data-vista]");
    allBtns.forEach((b) => {
      const on = b.dataset.vista === state.vista;
      b.classList.toggle("is-active", on);
      if (on) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
    const wrap = document.getElementById("visualizador-wrap");
    const frame = document.getElementById("visualizador-frame") as HTMLIFrameElement | null;
    const isViz = state.vista === "visualizador";
    if (wrap) wrap.hidden = !isViz;
    if (isViz) {
      closeUnityPanel();
      if (frame && !frame.getAttribute("src")) frame.src = assetUrl("/unity/visualizador/index.html");
    }
    const hash = `#${state.vista}`;
    if (location.hash !== hash) history.replaceState(null, "", hash);
    document.getElementById("metrics-strip")!.innerHTML = metricsStrip(cat, state.nivel);
    const aviso = document.getElementById("banner-aviso");
    if (aviso) aviso.textContent = bannerAviso(cat, state.nivel);
    hintForNivel();
    if (!isViz) {
      if (MAP_VISTAS.includes(state.vista)) showMapLayer();
      renderPanel();
    }
    const body = document.getElementById("panel-body");
    if (body && TEXT_VISTAS.includes(state.vista)) body.scrollTop = 0;
    requestAnimationFrame(() => map.resize());
  };

  // Events
  app.querySelectorAll<HTMLButtonElement>("[data-nivel]").forEach((b) => {
    b.addEventListener("click", () => {
      state.nivel = b.dataset.nivel as Nivel;
      localStorage.setItem(LS_NIVEL, state.nivel);
      app.querySelectorAll<HTMLButtonElement>("[data-nivel]").forEach((x) => {
        x.setAttribute("aria-pressed", String(x === b));
      });
      closeGlossary();
      syncVista();
    });
  });

  app.querySelectorAll<HTMLButtonElement>("button[data-vista]").forEach((b) => {
    b.addEventListener("click", () => {
      state.vista = b.dataset.vista as Vista;
      document.getElementById("menu-mas")?.setAttribute("hidden", "");
      document.getElementById("btn-mas")?.setAttribute("aria-expanded", "false");
      syncVista();
    });
  });

  document.getElementById("btn-mas")!.addEventListener("click", () => {
    const menu = document.getElementById("menu-mas")!;
    const open = menu.hasAttribute("hidden");
    if (open) menu.removeAttribute("hidden");
    else menu.setAttribute("hidden", "");
    document.getElementById("btn-mas")!.setAttribute("aria-expanded", String(open));
  });

  document.querySelector("[data-action='tour']")?.addEventListener("click", startTour);

  document.getElementById("reset-pesos")!.addEventListener("click", () => {
    state.weights = { ...DEFAULT_WEIGHTS };
    state.sitios = cat.sitios_validacion;
    renderWeights();
    renderPanel();
  });

  document.getElementById("opacidad")!.addEventListener("input", (ev) => {
    const v = Number((ev.target as HTMLInputElement).value) / 100;
    state.opacity = v;
    setOverlayOpacity(map, v);
  });

  app.querySelectorAll<HTMLButtonElement>("[data-cuerpo]").forEach((b) => {
    b.addEventListener("click", () => {
      state.cuerpoGlobo = "tierra";
      state.vista = b.dataset.cuerpo === "luna" ? "similitud-luna" : "similitud-marte";
      syncVista();
    });
  });

  app.querySelectorAll<HTMLButtonElement>("[data-cuerpo-globo]").forEach((b) => {
    b.addEventListener("click", () => {
      const next = b.dataset.cuerpoGlobo as CuerpoGlobo;
      const changed = next !== state.cuerpoGlobo;
      state.cuerpoGlobo = next;
      if (MAP_VISTAS.includes(state.vista) || state.vista === "inicio") showMapLayer(changed);
      else {
        app.dataset.cuerpoGlobo = state.cuerpoGlobo;
        app.querySelectorAll<HTMLButtonElement>("[data-cuerpo-globo]").forEach((x) => {
          x.setAttribute("aria-pressed", String(x.dataset.cuerpoGlobo === state.cuerpoGlobo));
        });
      }
    });
  });

  app.querySelectorAll<HTMLButtonElement>("[data-area]").forEach((b) => {
    b.addEventListener("click", () => {
      const next = b.dataset.area as AreaTierra;
      const changed = next !== state.areaTierra;
      state.areaTierra = next;
      state.cuerpoGlobo = "tierra";
      document.getElementById("btn-sitios-validacion")?.setAttribute("aria-pressed", "false");
      showMapLayer(changed);
    });
  });

  document.getElementById("btn-sitios-validacion")?.addEventListener("click", () => {
    state.cuerpoGlobo = "tierra";
    document.getElementById("btn-sitios-validacion")?.setAttribute("aria-pressed", "true");
    if (MAP_VISTAS.includes(state.vista) || state.vista === "inicio") showMapLayer(false);
    flyToSitios(map, state.sitios.length ? state.sitios : cat.sitios_validacion);
  });

  document.getElementById("btn-ver-unity")!.addEventListener("click", () => {
    if (state.unityAbierto) closeUnityPanel();
    else openUnityPanel();
  });
  document.getElementById("btn-cerrar-unity")!.addEventListener("click", closeUnityPanel);

  document.getElementById("tour-dialog")!.addEventListener("click", (ev) => {
    const t = (ev.target as HTMLElement).closest<HTMLButtonElement>("[data-tour]");
    if (!t || state.tour == null) return;
    if (t.dataset.tour === "skip") {
      endTour(true);
      return;
    }
    if (t.dataset.tour === "prev") state.tour = Math.max(0, state.tour - 1);
    if (t.dataset.tour === "next") {
      if (state.tour >= TOUR_PASOS.length - 1) {
        endTour(true);
        return;
      }
      state.tour += 1;
    }
    state.vista = TOUR_PASOS[state.tour].vista;
    syncVista();
    renderTour();
  });

  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Tab" && state.unityAbierto) {
      const closeBtn = document.getElementById("btn-cerrar-unity");
      const frame = document.getElementById("unity-panel-frame");
      const cycle = [closeBtn, frame].filter((el): el is HTMLElement => el instanceof HTMLElement);
      if (!cycle.length) return;
      const current = document.activeElement;
      ev.preventDefault();
      if (ev.shiftKey) {
        const i = cycle.indexOf(current as HTMLElement);
        const prev = i <= 0 ? cycle[cycle.length - 1] : cycle[i - 1];
        prev.focus();
      } else {
        const i = cycle.indexOf(current as HTMLElement);
        const next = i < 0 || i >= cycle.length - 1 ? cycle[0] : cycle[i + 1];
        next.focus();
      }
      return;
    }
    if (ev.key === "Escape") {
      if (state.tour != null) {
        ev.preventDefault();
        endTour(true);
        return;
      }
      if (state.unityAbierto) {
        ev.preventDefault();
        closeUnityPanel();
        return;
      }
      closeGlossary();
      hidePopup();
      document.getElementById("menu-mas")?.setAttribute("hidden", "");
    }
  });

  document.addEventListener("click", (ev) => {
    const t = ev.target as Node;
    const panel = document.getElementById("glosario-panel");
    if (panel && !panel.hidden && !panel.contains(t) && !(ev.target as HTMLElement).closest?.(".term")) {
      closeGlossary();
    }
  });

  window.addEventListener("hashchange", () => {
    const v = vistaFromHash();
    if (v !== state.vista) {
      state.vista = v;
      syncVista();
    }
  });

  map.on("style.load", () => {
    showMapLayer(false);
  });
  map.on("load", () => {
    showMapLayer(true);
    map.on("click", (e: MapMouseEvent) => {
      if (state.cuerpoGlobo !== "tierra") return;
      if (!MAP_VISTAS.includes(state.vista) && state.vista !== "inicio") return;
      if (TEXT_VISTAS.includes(state.vista)) return;
      const near = nearestZone(e.lngLat.lat, e.lngLat.lng, cat.zonas_prioritarias);
      if (!near) return;
      state.zonaId = near.zona.id;
      const col = document.querySelector(".map-col") as HTMLElement;
      const cr = col.getBoundingClientRect();
      showZonePopup(near.zona.id, { x: e.point.x, y: e.point.y + 48 });
      refreshMarkers();
      void cr;
    });
  });

  renderWeights();
  hintForNivel();
  app.dataset.nivel = state.nivel;
  syncVista();
}

main().catch((err) => {
  document.getElementById("app")!.innerHTML = `<p style="padding:2rem">Error al cargar el catálogo: ${escapeHtml(String(err))}</p>`;
});
