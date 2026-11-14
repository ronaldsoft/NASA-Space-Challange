import maplibregl from "maplibre-gl";
import type { GeoJSONSource, ImageSource, Map as MapLibreMap, StyleSpecification } from "maplibre-gl";
import type { Extension, SitioValidacion, Vista, ZonaPrioritaria } from "./types";
import { assetUrl } from "./paths";

export type CuerpoGlobo = "tierra" | "luna" | "marte";
export type AreaTierra = "ecuador_continental" | "galapagos";

export const AREA_BOUNDS: Record<AreaTierra | "completo", Extension> = {
  completo: { oeste: -92.007, sur: -5.103, este: -74.997, norte: 1.701 },
  ecuador_continental: { oeste: -81.15, sur: -5.103, este: -74.997, norte: 1.55 },
  galapagos: { oeste: -92.05, sur: -1.55, este: -89.1, norte: 1.75 },
};

// Inset from exact poles/dateline: mercator y is Infinity at ±90 and MapLibre logs
// "x=0, y=Infinity, z=0 outside of bounds" if an image source uses those corners.
const WORLD: [[number, number], [number, number], [number, number], [number, number]] = [
  [-179.9, 85],
  [179.9, 85],
  [179.9, -85],
  [-179.9, -85],
];

function imageCoords(ext: Extension): [[number, number], [number, number], [number, number], [number, number]] {
  return [
    [ext.oeste, ext.norte],
    [ext.este, ext.norte],
    [ext.este, ext.sur],
    [ext.oeste, ext.sur],
  ];
}

function overlayUrl(vista: Vista): string {
  if (vista === "similitud-luna") return assetUrl("/productos/delta_luna.png");
  if (vista === "clases") return assetUrl("/productos/clases.png");
  return assetUrl("/productos/delta_marte.png");
}

function globeStyle(): StyleSpecification {
  return {
    version: 8,
    name: "analog-globo",
    sources: {
      land: {
        type: "geojson",
        data: assetUrl("/basemap/ne_110m_land.geojson"),
        attribution: "Natural Earth 110m land (dominio público)",
      },
      hs_tierra: {
        type: "image",
        url: assetUrl("/basemap/hillshade_tierra.png"),
        coordinates: WORLD,
      },
      hs_ecuador: {
        type: "image",
        url: assetUrl("/basemap/hillshade_ecuador.png"),
        coordinates: imageCoords(AREA_BOUNDS.completo),
      },
      hs_luna: {
        type: "image",
        url: assetUrl("/basemap/hillshade_luna.png"),
        coordinates: WORLD,
      },
      hs_marte: {
        type: "image",
        url: assetUrl("/basemap/hillshade_marte.png"),
        coordinates: WORLD,
      },
      overlay: {
        type: "image",
        url: assetUrl("/productos/delta_marte.png"),
        coordinates: imageCoords(AREA_BOUNDS.completo),
      },
      sitios: {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      },
    },
    layers: [
      { id: "fondo", type: "background", paint: { "background-color": "#02060c" } },
      {
        id: "hs-tierra",
        type: "raster",
        source: "hs_tierra",
        paint: { "raster-opacity": 0.9, "raster-fade-duration": 0 },
      },
      {
        id: "land-fill",
        type: "fill",
        source: "land",
        paint: { "fill-color": "#1a2430", "fill-opacity": 0.12 },
      },
      {
        id: "land-line",
        type: "line",
        source: "land",
        paint: { "line-color": "#8a9aac", "line-width": 0.45, "line-opacity": 0.65 },
      },
      {
        id: "hs-ecuador",
        type: "raster",
        source: "hs_ecuador",
        paint: { "raster-opacity": 0.8, "raster-fade-duration": 0 },
      },
      {
        id: "hs-luna",
        type: "raster",
        source: "hs_luna",
        paint: { "raster-opacity": 0.95, "raster-fade-duration": 0 },
        layout: { visibility: "none" },
      },
      {
        id: "hs-marte",
        type: "raster",
        source: "hs_marte",
        paint: { "raster-opacity": 0.95, "raster-fade-duration": 0 },
        layout: { visibility: "none" },
      },
      {
        id: "capa-delta",
        type: "raster",
        source: "overlay",
        paint: { "raster-opacity": 0.82, "raster-fade-duration": 0 },
      },
      {
        id: "sitios-halo",
        type: "circle",
        source: "sitios",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 0, 16, 2, 12, 5, 10],
          "circle-color": ["coalesce", ["get", "color"], "#e8a35c"],
          "circle-opacity": 0.32,
        },
      },
      {
        id: "sitios-punto",
        type: "circle",
        source: "sitios",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 0, 9, 2, 7, 5, 5.5],
          "circle-color": ["coalesce", ["get", "color"], "#e8a35c"],
          "circle-stroke-width": 1.4,
          "circle-stroke-color": "#0c1016",
          "circle-opacity": 0.95,
        },
      },
    ],
  };
}

/** Create the shared MapLibre 5 globe (Earth, Moon or Mars). No third-party tile keys. */
export function createGlobeMap(container: HTMLElement): MapLibreMap {
  const map = new maplibregl.Map({
    container,
    style: globeStyle(),
    center: [-79.6, -1.4],
    zoom: 5.15,
    minZoom: 0,
    maxZoom: 12,
    attributionControl: { compact: true },
    renderWorldCopies: false,
    pitch: 0,
    bearing: 0,
    fadeDuration: 0,
  });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true, showCompass: true }), "bottom-left");
  map.addControl(new maplibregl.GlobeControl(), "bottom-left");
  // MapOptions typings omit `projection`; set it every time the style is ready.
  // setProjection can reload the style, so a one-shot handler would miss the next load.
  const enableGlobe = () => {
    try {
      map.setProjection({ type: "globe" });
    } catch (err) {
      console.warn("No se pudo activar la proyección de globo:", err);
    }
  };
  map.on("style.load", enableGlobe);
  if (map.isStyleLoaded()) enableGlobe();
  return map;
}

/** @deprecated Use createGlobeMap. Kept so older calls still compile if any remain. */
export function createEcuadorMap(container: HTMLElement, _extents: Extension): MapLibreMap {
  void _extents;
  return createGlobeMap(container);
}

function visible(map: MapLibreMap, id: string, on: boolean): void {
  if (!map.getLayer(id)) return;
  map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
}

/** Color-blind-safe plasma ramp for δ (0–1). */
export function colorForDelta(d: number | null | undefined): string {
  if (d == null || Number.isNaN(d)) return "#9aa3b0";
  const t = Math.max(0, Math.min(1, d));
  const stops: [number, [number, number, number]][] = [
    [0, [13, 8, 135]],
    [0.25, [126, 3, 168]],
    [0.5, [204, 71, 120]],
    [0.75, [248, 148, 65]],
    [1, [240, 249, 33]],
  ];
  let i = 0;
  while (i < stops.length - 2 && t > stops[i + 1][0]) i += 1;
  const [t0, c0] = stops[i];
  const [t1, c1] = stops[i + 1];
  const u = (t - t0) / Math.max(t1 - t0, 1e-6);
  const r = Math.round(c0[0] + (c1[0] - c0[0]) * u);
  const g = Math.round(c0[1] + (c1[1] - c0[1]) * u);
  const b = Math.round(c0[2] + (c1[2] - c0[2]) * u);
  return `rgb(${r},${g},${b})`;
}

const siteMarkers: maplibregl.Marker[] = [];

function clearSiteMarkers(): void {
  siteMarkers.forEach((m) => m.remove());
  siteMarkers.length = 0;
}

export function setValidationSites(
  map: MapLibreMap,
  sitios: SitioValidacion[],
  vista: Vista,
  onClick?: (nombre: string) => void,
): void {
  // Do not wait for isStyleLoaded(): updating the overlay image can flip that
  // flag to false and would skip the 19 validation sites.
  if (!map.getSource("sitios")) return;
  const useLuna = vista === "similitud-luna";
  const features = sitios.map((s) => {
    const d = useLuna ? s.delta_luna : s.delta_marte;
    return {
      type: "Feature" as const,
      properties: {
        nombre: s.nombre,
        color: colorForDelta(d),
        delta: d ?? null,
      },
      geometry: { type: "Point" as const, coordinates: [s.lon, s.lat] },
    };
  });
  (map.getSource("sitios") as GeoJSONSource).setData({ type: "FeatureCollection", features });
  clearSiteMarkers();
  for (const s of sitios) {
    const d = useLuna ? s.delta_luna : s.delta_marte;
    const el = document.createElement("button");
    el.type = "button";
    el.className = "sitio-dot";
    el.style.background = colorForDelta(d);
    el.title = s.nombre;
    el.setAttribute("aria-label", s.nombre);
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      onClick?.(s.nombre);
    });
    siteMarkers.push(new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([s.lon, s.lat]).addTo(map));
  }
  if (onClick && !(map as MapLibreMap & { __sitiosBound?: boolean }).__sitiosBound) {
    (map as MapLibreMap & { __sitiosBound?: boolean }).__sitiosBound = true;
    map.on("click", "sitios-punto", (e) => {
      const nombre = e.features?.[0]?.properties?.nombre;
      if (typeof nombre === "string") {
        e.originalEvent?.stopPropagation();
        onClick(nombre);
      }
    });
    map.on("mouseenter", "sitios-punto", () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "sitios-punto", () => {
      map.getCanvas().style.cursor = "";
    });
  }
}

/** Hide Ecuador zone pins when the camera is zoomed out to the world. */
export function setZonePinsVisible(on: boolean): void {
  markers.forEach((m) => {
    m.getElement().style.display = on ? "" : "none";
  });
}

export function applyGlobeState(
  map: MapLibreMap,
  opts: {
    cuerpo: CuerpoGlobo;
    area: AreaTierra;
    vista: Vista;
    opacity: number;
    sitios: SitioValidacion[];
    fly?: boolean;
  },
): void {
  if (!map.getLayer("fondo") && !map.isStyleLoaded()) return;
  const enTierra = opts.cuerpo === "tierra";
  visible(map, "hs-tierra", enTierra);
  visible(map, "land-fill", enTierra);
  visible(map, "land-line", enTierra);
  visible(map, "hs-ecuador", enTierra);
  visible(map, "hs-luna", opts.cuerpo === "luna");
  visible(map, "hs-marte", opts.cuerpo === "marte");
  visible(map, "capa-delta", enTierra);
  visible(map, "sitios-halo", enTierra);
  visible(map, "sitios-punto", enTierra);
  if (enTierra) {
    setValidationSites(map, opts.sitios, opts.vista === "clima" ? "similitud-marte" : opts.vista);
    const src = map.getSource("overlay") as ImageSource | undefined;
    const url = overlayUrl(opts.vista === "clima" ? "similitud-marte" : opts.vista);
    const coordinates = imageCoords(AREA_BOUNDS.completo);
    if (src && typeof src.updateImage === "function") {
      src.updateImage({ url, coordinates });
    }
    map.setPaintProperty("capa-delta", "raster-opacity", opts.opacity);
    if (opts.fly) flyToArea(map, AREA_BOUNDS[opts.area]);
  } else if (opts.fly) {
    map.easeTo({ center: [0, 0], zoom: 1.35, pitch: 0, bearing: 0, duration: 700 });
  }
}

export function setOverlay(map: MapLibreMap, vista: Vista, extents: Extension, opacity = 0.85): void {
  void extents;
  if (!map.isStyleLoaded() || !map.getSource("overlay")) return;
  const src = map.getSource("overlay") as ImageSource;
  if (typeof src.updateImage === "function") {
    src.updateImage({ url: overlayUrl(vista), coordinates: imageCoords(AREA_BOUNDS.completo) });
  }
  if (map.getLayer("capa-delta")) map.setPaintProperty("capa-delta", "raster-opacity", opacity);
}

export function setOverlayOpacity(map: MapLibreMap, opacity: number): void {
  if (map.getLayer("capa-delta")) map.setPaintProperty("capa-delta", "raster-opacity", opacity);
}

export function flyToArea(map: MapLibreMap, extents: Extension): void {
  setZonePinsVisible(true);
  map.fitBounds(
    [
      [extents.oeste, extents.sur],
      [extents.este, extents.norte],
    ],
    { padding: 48, duration: 800, essential: true },
  );
}

export function flyToSitios(map: MapLibreMap, sitios: { lon: number; lat: number }[]): void {
  void sitios;
  // Fixed Atlantic framing: Americas, Europe and Africa stay on the front of the
  // globe. Hawaii, Australia and the far polar sites are behind; the user can rotate.
  // fitBounds over all 19 sites would include Antarctica and Australia and face Africa.
  setZonePinsVisible(false);
  map.easeTo({ center: [-40, 22], zoom: 1.55, pitch: 0, bearing: 0, duration: 800, essential: true });
}

const markers: maplibregl.Marker[] = [];

export function setMarkers(
  map: MapLibreMap,
  zonas: ZonaPrioritaria[],
  selectedId: string | null,
  onSelect: (id: string) => void,
): void {
  markers.forEach((m) => m.remove());
  markers.length = 0;
  for (const z of zonas) {
    const el = document.createElement("button");
    el.type = "button";
    el.className = `map-pin${z.id === selectedId ? " is-selected" : ""}`;
    el.setAttribute("aria-label", z.nombre);
    el.innerHTML = `<span class="pin-dot"></span><span class="pin-label">${escapeHtml(z.nombre)}</span>`;
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      onSelect(z.id);
    });
    markers.push(new maplibregl.Marker({ element: el, anchor: "bottom" }).setLngLat([z.lon, z.lat]).addTo(map));
  }
}

export function clearMarkers(): void {
  markers.forEach((m) => m.remove());
  markers.length = 0;
}

export function nearestZone(
  lat: number,
  lon: number,
  zonas: ZonaPrioritaria[],
  maxKm = 80,
): { zona: ZonaPrioritaria; km: number } | null {
  let best: { zona: ZonaPrioritaria; km: number } | null = null;
  for (const z of zonas) {
    const km = haversineKm(lat, lon, z.lat, z.lon);
    if (km <= maxKm && (!best || km < best.km)) best = { zona: z, km };
  }
  return best;
}

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const p1 = (lat1 * Math.PI) / 180;
  const p2 = (lat2 * Math.PI) / 180;
  const dp = ((lat2 - lat1) * Math.PI) / 180;
  const dl = ((lon2 - lon1) * Math.PI) / 180;
  const a = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function escapeHtml(s: string): string {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
