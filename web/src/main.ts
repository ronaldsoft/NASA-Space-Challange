import "@fontsource/public-sans/400.css";
import "@fontsource/public-sans/500.css";
import "@fontsource/public-sans/600.css";
import "@fontsource/newsreader/400.css";
import "@fontsource/newsreader/500.css";
import "@fontsource/newsreader/600.css";
import "maplibre-gl/dist/maplibre-gl.css";
import "./style.css";

import type { Map as MapLibreMap } from "maplibre-gl";
import {
  explorarEcuadorHTML,
  futureWorkHTML,
  homeHTML,
  legendHTML,
  legendCuerpoHTML,
  legendStripHTML,
  mapPanelHTML,
  TOUR_PASOS,
  uncertaintyHTML,
  validationHTML,
} from "./content";
import { ESTACIONES_MAPA, MISIONES } from "./datosModelo";
import { createDataSource } from "./dataSource";
import { defTermino, GLOSARIO } from "./glossary";
import {
  applyGlobeState,
  clearMarkers,
  createGlobeMap,
  escapeHtml,
  setStationMarkers,
  setMissionMarkers,
  setOverlayOpacity,
  type AreaTierra,
  type CuerpoGlobo,
} from "./maps";
import { assetUrl } from "./paths";
import { isEn, LANG, LANGS, saveLang, tr, type Lang } from "./i18n";
import { NIVELES, type Catalogo, type Nivel, type Vista } from "./types";

const LS_NIVEL = "analog_nivel";
const LS_TOUR = "analog_tour_dismissed";
const LS_THEME = "analog_theme";

interface VistaItem {
  id: Vista;
  label: string;
  sub?: string;
}

const GRUPOS: { titulo: string; items: VistaItem[] }[] = [
  { titulo: tr("Resumen", "Overview"), items: [{ id: "inicio", label: tr("Inicio", "Home") }] },
  {
    titulo: tr("Mapas", "Maps"),
    items: [
      { id: "similitud-marte", label: tr("Similitud con Marte", "Similarity to Mars") },
      { id: "similitud-luna", label: tr("Similitud con la Luna", "Similarity to the Moon") },
      { id: "clases", label: tr("Marte y Luna a la vez", "Mars and Moon at once") },
    ],
  },
  {
    titulo: tr("Evidencia", "Evidence"),
    items: [
      { id: "validacion", label: tr("Validación", "Validation") },
      { id: "incertidumbre", label: tr("Límites", "Limits") },
    ],
  },
  { titulo: tr("Explorar", "Explore"), items: [{ id: "visualizador", label: tr("Explorar Ecuador", "Explore Ecuador") }] },
  { titulo: tr("Proyecto", "Project"), items: [{ id: "trabajo-futuro", label: tr("Trabajo futuro", "Future work") }] },
];

const HINT_VISTA: Record<string, string> = {
  inicio: tr("Qué medimos y con qué datos", "What we measure and with what data"),
  "similitud-marte": tr("Índice 0–100 frente a los sitios de aterrizaje en Marte", "0–100 index against the Mars landing sites"),
  "similitud-luna": tr("Índice 0–100 frente a los sitios de aterrizaje en la Luna", "0–100 index against the Moon landing sites"),
  clases: tr("El menor de los dos índices en cada celda", "The lower of the two indices in each cell"),
  validacion: tr("Evaluación por misión, autocorrelación y control de calidad", "Mission-level evaluation, autocorrelation and quality control"),
  incertidumbre: tr("Lo que el índice no mide", "What the index does not measure"),
  visualizador: tr("Relieve en 3D, leyenda y estadísticas de Ecuador", "3D relief, legend and statistics for Ecuador"),
  "trabajo-futuro": tr("Variables que se pueden añadir", "Variables that could be added"),
};

const TITULO_VISTA: Record<string, string> = {
  clases: tr("Marte y Luna a la vez", "Mars and Moon at once"),
};

const ICONOS: Record<string, string> = {
  inicio: '<path d="M9 3 16 15H2z"/>',
  "similitud-marte": '<circle cx="9" cy="9" r="6" fill="#e0643c" stroke="none"/>',
  "similitud-luna": '<circle cx="9" cy="9" r="5.2"/>',
  clases: '<rect x="3" y="3" width="5" height="5"/><rect x="10" y="3" width="5" height="5"/><rect x="3" y="10" width="5" height="5"/><rect x="10" y="10" width="5" height="5"/>',
  clima: '<circle cx="9" cy="9" r="5.5" stroke-dasharray="2.5 2.5"/>',
  validacion: '<path d="M3 9.5 7 13.5 15 4.5"/>',
  diagnostico: '<path d="M3 14V9M7 14V4M11 14V7M15 14V11"/>',
  incertidumbre: '<path d="M3 9h12M3 5.5v7M15 5.5v7"/>',
  ficha: '<path d="M9 16s5-4.6 5-8.2A5 5 0 0 0 4 7.8C4 11.4 9 16 9 16z"/><circle cx="9" cy="7.8" r="1.8"/>',
  visualizador: '<path d="M9 2 15 5.5v7L9 16 3 12.5v-7zM9 9v7M3 5.5 9 9l6-3.5"/>',
  "trabajo-futuro": '<path d="M3 9h11M10 5l4 4-4 4"/>',
};

function iconoVista(id: string): string {
  return `<svg viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${ICONOS[id] ?? ""}</svg>`;
}

const TODAS_VISTAS: Vista[] = GRUPOS.flatMap((g) => g.items.map((i) => i.id));
const ETIQUETA_VISTA: Record<string, string> = Object.fromEntries(
  GRUPOS.flatMap((g) => g.items.map((i) => [i.id, TITULO_VISTA[i.id] ?? i.label])),
);
const TEXT_VISTAS: Vista[] = ["inicio", "validacion", "incertidumbre", "trabajo-futuro"];
const MAP_VISTAS: Vista[] = ["similitud-marte", "similitud-luna", "clases"];

type Theme = "dark" | "light";

function readTheme(): Theme {
  try {
    const v = localStorage.getItem(LS_THEME);
    if (v === "dark" || v === "light") return v;
  } catch {
    /* almacenamiento no disponible */
  }
  return window.matchMedia?.("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function lsSet(k: string, v: string): void {
  try {
    localStorage.setItem(k, v);
  } catch {
    /* almacenamiento no disponible: la preferencia solo dura la sesión */
  }
}

function readNivel(): Nivel {
  try {
    const v = localStorage.getItem(LS_NIVEL);
    if (v === "explorador" || v === "estudiante" || v === "cientifico") return v;
  } catch {
    /* sin almacenamiento */
  }
  return "explorador";
}

function vistaFromHash(): Vista {
  const h = (location.hash || "").replace(/^#/, "");
  return (TODAS_VISTAS as string[]).includes(h) ? (h as Vista) : "inicio";
}

const state = {
  vista: "inicio" as Vista,
  nivel: readNivel() as Nivel,
  opacity: 0.82,
  tour: null as number | null,
  cuerpoGlobo: "tierra" as CuerpoGlobo,
  areaTierra: "ecuador_continental" as AreaTierra,
  unityAbierto: false,
};

function metricsStrip(_cat: Catalogo, nivel: Nivel): string {
  const fila = (l: string, v: string) => `<div><dt>${l}</dt><dd>${v}</dd></div>`;
  const d = (x: string) => (isEn ? x.replace(/,/g, ".") : x);
  const umbral = tr("índice ≥ 95 (escala 0–100)", "index ≥ 95 (0–100 scale)");
  const auc = fila(tr("AUC por exclusión de misión", "Leave-one-mission-out AUC"), d("0,40") + tr(" (p 0,683 mundo · 0,714 Ecuador)", " (p 0.683 world · 0.714 Ecuador)"));
  const qa = fila(tr("Ecuador con QA≤1", "Ecuador with QA≤1"), tr("0 candidatos ≥ 95", "0 candidates ≥ 95"));
  if (nivel === "explorador") {
    return auc + fila(tr("Umbral", "Threshold"), umbral) + qa;
  }
  return (
    auc +
    fila(tr("Umbral", "Threshold"), umbral) +
    qa +
    fila(tr("Rejillas", "Grids"), tr("0,05° mundo · 30″ Ecuador", "0.05° world · 30″ Ecuador"))
  );
}

function captionHTML(vista: Vista, _cat: Catalogo, _nivel: Nivel, cuerpo: CuerpoGlobo, area: AreaTierra): string {
  if (cuerpo === "luna") {
    return tr(
      `<strong>Luna</strong> · relieve LOLA LDEM_64 (NASA), sombreado, con los sitios de aterrizaje de las firmas. El índice se calcula sobre la Tierra.`,
      `<strong>Moon</strong> · LOLA LDEM_64 relief (NASA), shaded, with the landing sites of the signatures. The index is computed on Earth.`,
    );
  }
  if (cuerpo === "marte") {
    return tr(
      `<strong>Marte</strong> · relieve MOLA MEGDR 64 ppd (NASA), sombreado, con los sitios de aterrizaje de las firmas. El índice se calcula sobre la Tierra.`,
      `<strong>Mars</strong> · MOLA MEGDR 64 ppd relief (NASA), shaded, with the landing sites of the signatures. The index is computed on Earth.`,
    );
  }
  const dest = vista === "similitud-luna" ? tr("la Luna", "the Moon") : vista === "clases" ? tr("Marte y la Luna a la vez", "Mars and the Moon at once") : tr("Marte", "Mars");
  const areaNom = area === "galapagos" ? "Galápagos" : tr("Ecuador continental", "mainland Ecuador");
  return tr(
    `<strong>Similitud con ${dest}</strong> · mundo a 0,05°, ${areaNom} a 30″ al acercarte · MOLA, LOLA, MODIS (NASA), ESA CCI y GMTED2010 (USGS)`,
    `<strong>Similarity to ${dest}</strong> · world at 0.05°, ${areaNom} at 30″ when you zoom in · MOLA, LOLA, MODIS (NASA), ESA CCI and GMTED2010 (USGS)`,
  );
}

function bannerAviso(cat: Catalogo, _nivel: Nivel): string {
  if (cat.mock) return cat.aviso;
  return tr("Datos: MOLA, TES, LOLA, LROC WAC y MODIS MCD43C3 (NASA); cobertura ESA CCI 2022; elevación terrestre GMTED2010 (USGS).", "Data: MOLA, TES, LOLA, LROC WAC and MODIS MCD43C3 (NASA); ESA CCI 2022 land cover; land elevation GMTED2010 (USGS).");
}

async function main(): Promise<void> {
  const cat = await createDataSource().load();
  state.vista = vistaFromHash();
  const app = document.getElementById("app")!;

  const theme0 = readTheme();
  document.documentElement.dataset.theme = theme0;
  app.classList.toggle("has-mock-banner", cat.mock);

  const railNav = GRUPOS.map(
    (g) => `<div class="rail-group">
      <h2 id="g-${g.titulo.toLowerCase()}">${escapeHtml(g.titulo)}</h2>
      <ul aria-labelledby="g-${g.titulo.toLowerCase()}">${g.items
        .map(
          (v) =>
            `<li><button type="button" class="rail-link${v.id === state.vista ? " is-active" : ""}" data-vista="${v.id}">${iconoVista(v.id)}<span>${escapeHtml(v.label)}</span>${v.sub ? `<span class="sub">${escapeHtml(v.sub)}</span>` : ""}</button></li>`,
        )
        .join("")}</ul>
    </div>`,
  ).join("");

  app.innerHTML = `
    <a class="skip-link" href="#contenido">${tr("Saltar al contenido", "Skip to content")}</a>
    ${
      cat.mock
        ? `<div class="banner-mock" data-testid="mock-banner"><strong>${tr("Datos MOCK", "MOCK data")}</strong><span id="banner-aviso"></span></div>`
        : `<div hidden></div>`
    }
    <div class="rail-scrim" id="rail-scrim" hidden></div>
    <aside class="rail" id="rail" aria-label="${tr("Navegación principal", "Main navigation")}">
      <div class="brand">
        <svg class="brand-mark" viewBox="0 0 44 44" fill="none" aria-hidden="true" focusable="false">
          <path class="orb-line" d="M22 9 36.5 34H7.5z" stroke-width="1.6" stroke-linejoin="round"/>
          <g class="orb-dots">
            <circle class="dot dot-tierra" cx="22" cy="9" r="6"/>
            <circle class="dot dot-luna" cx="7.5" cy="34" r="5"/>
            <circle class="dot dot-marte" cx="36.5" cy="34" r="5.5"/>
          </g>
        </svg>
        <div>
          <p class="brand-name">ANALOG<span>/</span>delta</p>
          <p class="brand-sub">${tr("La Tierra frente a Marte<br />y la Luna", "Earth against Mars<br />and the Moon")}</p>
        </div>
      </div>
      <nav class="rail-nav" aria-label="${tr("Vistas", "Views")}">${railNav}</nav>
      <div class="status" data-testid="${cat.mock ? "mock-status" : "real-banner"}">
        <div class="status-head"><strong>${cat.mock ? tr("Datos MOCK", "MOCK data") : tr("Validación", "Validation")}</strong></div>
        <dl id="metrics-strip">${metricsStrip(cat, state.nivel)}</dl>
        ${cat.mock ? "" : `<details><summary>${tr("Fuente de los datos", "Data source")}</summary><p id="banner-aviso"></p></details>`}
      </div>
    </aside>
    <div class="stage">
      <header class="topbar">
        <button type="button" class="icon-btn" id="btn-menu" aria-label="${tr("Abrir el menú", "Open the menu")}" aria-expanded="false" aria-controls="rail">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3 5.5h14M3 10h14M3 14.5h14"/></svg>
        </button>
        <div class="topbar-title">
          <h1 class="crumb" id="crumb">${tr("Inicio", "Home")}</h1>
          <p class="crumb-hint" id="toolbar-hint"></p>
        </div>
        <div class="topbar-tools">
          <button type="button" class="btn btn-ghost btn-small" data-action="tour">${tr("Guíame", "Guide me")}</button>
          <div class="seg lang-seg" role="group" aria-label="${tr("Idioma", "Language")}" data-testid="selector-idioma">
            ${LANGS.map((l) => `<button type="button" data-lang="${l.id}" lang="${l.id}" aria-pressed="${l.id === LANG}" title="${l.name}">${l.label}</button>`).join("")}
          </div>
          <button type="button" class="icon-btn" id="btn-theme" aria-label="${tr("Cambiar al tema claro", "Switch to the light theme")}" title="${tr("Cambiar tema", "Change theme")}">
            <svg class="theme-icon-dark" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16.5 11.6A7 7 0 0 1 8.4 3.5a7 7 0 1 0 8.1 8.1z"/></svg>
            <svg class="theme-icon-light" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><circle cx="10" cy="10" r="3.6"/><path d="M10 2.5v2M10 15.5v2M2.5 10h2M15.5 10h2M4.7 4.7l1.4 1.4M13.9 13.9l1.4 1.4M4.7 15.3l1.4-1.4M13.9 6.1l1.4-1.4"/></svg>
          </button>
        </div>
        <div class="nivel-block">
          <span class="seg-label" id="nivel-label">${tr("Nivel de detalle", "Level of detail")}</span>
          <div class="seg" role="radiogroup" aria-labelledby="nivel-label" data-testid="nivel-selector">
            ${NIVELES.map(
              (n) =>
                `<button type="button" role="radio" data-nivel="${n.id}" aria-checked="${n.id === state.nivel}" title="${escapeHtml(n.hint)}">${escapeHtml(n.label)}</button>`,
            ).join("")}
          </div>
        </div>
      </header>
      <div id="visualizador-wrap" hidden>
        <iframe id="visualizador-frame" title="${tr("Explorar Ecuador en 3D", "Explore Ecuador in 3D")}" allow="fullscreen"></iframe>
        <aside class="explorar-panel" id="explorar-panel" aria-label="${tr("Leyenda y estadísticas de Ecuador", "Legend and statistics for Ecuador")}"></aside>
      </div>
      <div class="main" id="contenido" tabindex="-1">
        <div class="map-col">
          <div id="map" role="region" aria-label="${tr("Globo de Tierra, Luna o Marte", "Globe of Earth, the Moon or Mars")}"></div>
          <div class="map-bar">
            <div class="seg cuerpo-toggle" role="group" aria-label="${tr("Cuerpo del globo", "Globe body")}" data-testid="selector-cuerpo-globo">
              <button type="button" data-cuerpo-globo="tierra" aria-pressed="true">${tr("Tierra", "Earth")}</button>
              <button type="button" data-cuerpo-globo="luna" aria-pressed="false">${tr("Luna", "Moon")}</button>
              <button type="button" data-cuerpo-globo="marte" aria-pressed="false">${tr("Marte", "Mars")}</button>
            </div>
            <div class="seg cuerpo-toggle solo-tierra" role="group" aria-label="${tr("Área en la Tierra", "Area on Earth")}" data-testid="selector-area">
              <button type="button" data-area="ecuador_continental" aria-pressed="true">${tr("Ecuador continental", "Mainland Ecuador")}</button>
              <button type="button" data-area="galapagos" aria-pressed="false">Galápagos</button>
            </div>
            <div class="seg cuerpo-toggle solo-tierra" role="group" aria-label="${tr("Comparar con Marte o con la Luna", "Compare with Mars or the Moon")}" data-testid="toggle-cuerpo">
              <button type="button" data-cuerpo="marte" aria-pressed="true">${tr("Similitud con Marte", "Similarity to Mars")}</button>
              <button type="button" data-cuerpo="luna" aria-pressed="false">${tr("Similitud con la Luna", "Similarity to the Moon")}</button>
            </div>
            <div class="opacidad-ctl solo-tierra" data-testid="control-opacidad">
              <label>${tr("Opacidad de la capa", "Layer opacity")}
                <input type="range" id="opacidad" min="20" max="100" step="1" value="${Math.round(state.opacity * 100)}" />
              </label>
            </div>
            <button type="button" class="btn btn-primary btn-small" id="btn-ver-unity" data-testid="btn-ver-unity" aria-expanded="false" aria-controls="unity-panel">${tr("Explorar Ecuador en 3D", "Explore Ecuador in 3D")}</button>
          </div>
          <div class="map-legend" id="map-legend" data-testid="leyenda" role="region" aria-label="${tr("Leyenda del mapa", "Map legend")}"></div>
          <div class="map-caption" id="map-caption"></div>
          <div class="map-popup" id="map-popup" hidden role="dialog" aria-label="${tr("Ficha del punto", "Point details")}"></div>
          <div id="unity-panel" class="unity-panel" hidden role="dialog" aria-modal="true" aria-labelledby="unity-panel-titulo">
            <div class="unity-panel-bar">
              <h2 id="unity-panel-titulo">${tr("Explorar Ecuador", "Explore Ecuador")}</h2>
              <button type="button" class="btn btn-small" id="btn-cerrar-unity">${tr("Cerrar", "Close")}</button>
            </div>
            <iframe id="unity-panel-frame" title="${tr("Explorar Ecuador en 3D", "Explore Ecuador in 3D")}" allow="fullscreen"></iframe>
          </div>
        </div>
        <aside class="panel" aria-label="${tr("Explicación", "Explanation")}">
          <div class="panel-body" id="panel-body" tabindex="-1"></div>
        </aside>
      </div>
    </div>
    <div class="tour-backdrop" id="tour-backdrop" hidden></div>
    <div class="tour-dialog" id="tour-dialog" hidden role="dialog" aria-modal="true" aria-labelledby="tour-titulo" data-testid="tour-dialog">
      <p class="tour-progress" id="tour-progress"></p>
      <h2 id="tour-titulo"></h2>
      <p id="tour-cuerpo"></p>
      <div class="tour-actions">
        <button type="button" class="btn btn-ghost" data-tour="prev">${tr("Anterior", "Back")}</button>
        <button type="button" class="btn btn-primary" data-tour="next">${tr("Siguiente", "Next")}</button>
        <button type="button" class="btn btn-ghost" data-tour="skip">${tr("Saltar recorrido", "Skip the tour")}</button>
      </div>
    </div>
    <div id="glosario-panel" hidden role="tooltip"></div>
  `;

  const map: MapLibreMap = createGlobeMap(document.getElementById("map")!);

  const hintForNivel = () => {
    document.getElementById("toolbar-hint")!.textContent = HINT_VISTA[state.vista] ?? "";
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

  const hidePopup = () => {
    const pop = document.getElementById("map-popup");
    if (pop) pop.hidden = true;
  };

  const refreshMarkers = () => {
    setStationMarkers(map, ESTACIONES_MAPA());
  };

  const overlayFor = (vista: Vista): Vista => {
    if (vista === "similitud-luna" || vista === "similitud-marte" || vista === "clases") return vista;
    return "similitud-marte";
  };

  /** Leyenda dentro del mapa. En móvil queda plegada: botón «Leyenda» con la tira de colores; se abre al tocarlo. */
  const setLegend = (html: string, strip: string) => {
    const el = document.getElementById("map-legend")!;
    const abierta = el.dataset.abierta === "1";
    el.innerHTML = `<button type="button" class="leg-toggle" aria-expanded="${abierta}" aria-controls="map-legend-body"><span class="leg-toggle-txt">${abierta ? tr("Ocultar leyenda", "Hide legend") : tr("Leyenda", "Legend")}</span><span class="leg-strip" aria-hidden="true">${strip}</span></button><div class="leg-body" id="map-legend-body">${html}</div>`;
    el.querySelector<HTMLButtonElement>(".leg-toggle")!.addEventListener("click", () => {
      const abrir = el.dataset.abierta !== "1";
      el.dataset.abierta = abrir ? "1" : "0";
      const b = el.querySelector<HTMLButtonElement>(".leg-toggle")!;
      b.setAttribute("aria-expanded", String(abrir));
      b.querySelector(".leg-toggle-txt")!.textContent = abrir ? tr("Ocultar leyenda", "Hide legend") : tr("Leyenda", "Legend");
    });
  };

  const showMapLayer = (fly = false) => {
    const overlay = overlayFor(state.vista);
    setMissionMarkers(map, MISIONES);
    applyGlobeState(map, {
      cuerpo: state.cuerpoGlobo,
      area: state.areaTierra,
      vista: overlay,
      opacity: state.opacity,
      fly,
    });
    document.getElementById("map-caption")!.innerHTML = captionHTML(state.vista, cat, state.nivel, state.cuerpoGlobo, state.areaTierra);
    setLegend(
      state.cuerpoGlobo === "tierra" ? legendHTML(overlay) : legendCuerpoHTML(state.cuerpoGlobo),
      state.cuerpoGlobo === "tierra" ? legendStripHTML(overlay) : `<span class="swatch swatch-mision swatch-mision-${state.cuerpoGlobo}"></span>`,
    );
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
    if (!frame.getAttribute("src")) frame.src = assetUrl(`/unity/visualizador/index.html?lang=${LANG}`);
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

  const buildToc = (body: HTMLElement) => {
    body.querySelector(".toc")?.remove();
    if (state.vista === "inicio") return;
    const heads = Array.from(body.querySelectorAll<HTMLElement>(".prose > h3"));
    if (heads.length < 2) return;
    const nav = document.createElement("nav");
    nav.className = "toc";
    nav.setAttribute("aria-label", tr("En esta página", "On this page"));
    nav.innerHTML = `<p class="toc-t">${tr("En esta página", "On this page")}</p><ul>${heads
      .map((h, i) => {
        h.id = `sec-${i}`;
        h.tabIndex = -1;
        return `<li><button type="button" data-toc="sec-${i}">${escapeHtml(h.textContent ?? "")}</button></li>`;
      })
      .join("")}</ul>`;
    nav.addEventListener("click", (ev) => {
      const b = (ev.target as HTMLElement).closest<HTMLButtonElement>("[data-toc]");
      if (!b) return;
      const el = document.getElementById(b.dataset.toc!);
      el?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      el?.focus({ preventScroll: true });
    });
    body.appendChild(nav);
  };

  const renderPanelInner = () => {
    const body = document.getElementById("panel-body")!;
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
      body.innerHTML = validationHTML(state.nivel);
      return;
    }
    if (state.vista === "incertidumbre") {
      body.innerHTML = uncertaintyHTML(state.nivel);
      return;
    }
    if (state.vista === "trabajo-futuro") {
      body.innerHTML = futureWorkHTML();
      return;
    }
    body.innerHTML = mapPanelHTML(state.vista, state.nivel);
  };

  const renderPanel = () => {
    renderPanelInner();
    const body = document.getElementById("panel-body");
    if (body && TEXT_VISTAS.includes(state.vista)) buildToc(body);
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
    document.getElementById("tour-progress")!.textContent = tr(`Paso ${state.tour + 1} de ${TOUR_PASOS.length}`, `Step ${state.tour + 1} of ${TOUR_PASOS.length}`);
    document.getElementById("tour-titulo")!.textContent = paso.titulo;
    document.getElementById("tour-cuerpo")!.textContent = paso.cuerpo;
    const next = box.querySelector<HTMLButtonElement>("[data-tour='next']")!;
    next.textContent = state.tour === TOUR_PASOS.length - 1 ? tr("Terminar", "Finish") : tr("Siguiente", "Next");
    box.querySelector<HTMLButtonElement>("[data-tour='prev']")!.disabled = state.tour === 0;
    box.hidden = false;
    backdrop.hidden = false;
    next.focus();
  };

  function startTour(): void {
    setRail(false);
    state.tour = 0;
    state.vista = TOUR_PASOS[0].vista;
    syncVista();
    renderTour();
  }

  function endTour(dismiss: boolean): void {
    if (dismiss) lsSet(LS_TOUR, "1");
    state.tour = null;
    renderTour();
  }

  function setRail(open: boolean): void {
    app.classList.toggle("rail-open", open);
    const scrim = document.getElementById("rail-scrim");
    if (scrim) scrim.hidden = !open;
    document.getElementById("btn-menu")?.setAttribute("aria-expanded", String(open));
    document.getElementById("btn-menu")?.setAttribute("aria-label", open ? tr("Cerrar el menú", "Close the menu") : tr("Abrir el menú", "Open the menu"));
    if (open) app.querySelector<HTMLButtonElement>(".rail-link.is-active, .rail-link")?.focus();
  }

  function applyTheme(t: Theme): void {
    document.documentElement.dataset.theme = t;
    const btn = document.getElementById("btn-theme");
    btn?.setAttribute("aria-label", t === "dark" ? tr("Cambiar al tema claro", "Switch to the light theme") : tr("Cambiar al tema oscuro", "Switch to the dark theme"));
  }

  let lastAnimVista: Vista | null = null;

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
      if (frame && !frame.getAttribute("src")) frame.src = assetUrl(`/unity/visualizador/index.html?lang=${LANG}`);
      const ep = document.getElementById("explorar-panel");
      if (ep && !ep.innerHTML) ep.innerHTML = `<div class="map-legend explorar-legend">${legendHTML("clases")}</div>${explorarEcuadorHTML()}`;
    }
    const crumb = document.getElementById("crumb");
    if (crumb) crumb.textContent = ETIQUETA_VISTA[state.vista] ?? tr("Inicio", "Home");
    document.title = `${ETIQUETA_VISTA[state.vista] ?? tr("Inicio", "Home")} · ANALOG/delta`;
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
    if (body && state.vista !== lastAnimVista) {
      lastAnimVista = state.vista;
      body.classList.remove("anim");
      void body.offsetWidth;
      body.classList.add("anim");
      window.setTimeout(() => body.classList.remove("anim"), 1600);
    }
    requestAnimationFrame(() => map.resize());
  };

  // Events
  app.querySelectorAll<HTMLButtonElement>("[data-nivel]").forEach((b) => {
    b.addEventListener("click", () => {
      state.nivel = b.dataset.nivel as Nivel;
      lsSet(LS_NIVEL, state.nivel);
      app.querySelectorAll<HTMLButtonElement>("[data-nivel]").forEach((x) => {
        x.setAttribute("aria-checked", String(x === b));
      });
      closeGlossary();
      syncVista();
    });
  });

  app.querySelectorAll<HTMLButtonElement>("button[data-vista]").forEach((b) => {
    b.addEventListener("click", () => {
      state.vista = b.dataset.vista as Vista;
      setRail(false);
      syncVista();
      (document.getElementById("contenido") as HTMLElement | null)?.scrollTo?.({ top: 0 });
      window.scrollTo({ top: 0 });
    });
  });

  document.getElementById("btn-menu")!.addEventListener("click", () => setRail(!app.classList.contains("rail-open")));
  document.getElementById("rail-scrim")!.addEventListener("click", () => setRail(false));

  document.getElementById("btn-theme")!.addEventListener("click", () => {
    const next: Theme = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    applyTheme(next);
    lsSet(LS_THEME, next);
  });

  document.querySelector(".topbar [data-action='tour']")?.addEventListener("click", startTour);

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
      showMapLayer(changed);
    });
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
      const i = cycle.indexOf(document.activeElement as HTMLElement);
      ev.preventDefault();
      if (ev.shiftKey) cycle[i <= 0 ? cycle.length - 1 : i - 1].focus();
      else cycle[i < 0 || i >= cycle.length - 1 ? 0 : i + 1].focus();
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
      if (app.classList.contains("rail-open")) {
        setRail(false);
        document.getElementById("btn-menu")?.focus();
        return;
      }
      closeGlossary();
      hidePopup();
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
  });

  document.documentElement.lang = LANG;
  app.querySelectorAll<HTMLButtonElement>("[data-lang]").forEach((b) => {
    b.addEventListener("click", () => {
      const l = b.dataset.lang as Lang;
      if (l === LANG) return;
      saveLang(l);
      // quitar ?lang= para que no pise la elección, y recargar de verdad (asignar la misma URL no recarga)
      const url = new URL(location.href);
      url.searchParams.delete("lang");
      history.replaceState(null, "", url.toString());
      location.reload();
    });
  });
  applyTheme(theme0);
  hintForNivel();
  app.dataset.nivel = state.nivel;
  syncVista();
}

main().catch((err) => {
  document.getElementById("app")!.innerHTML = `<p style="padding:2rem">${tr("Error al cargar el catálogo", "Could not load the catalog")}: ${escapeHtml(String(err))}</p>`;
});
