import maplibregl, { type Map as MapLibreMap, type Marker } from "maplibre-gl";
import type { Extension, Vista, ZonaPrioritaria } from "./types";

const ECUADOR_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    basemap: {
      type: "raster",
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      attribution: "© Esri, © OpenStreetMap contributors",
    },
  },
  layers: [
    { id: "fondo", type: "background", paint: { "background-color": "#0e1216" } },
    { id: "basemap", type: "raster", source: "basemap", paint: { "raster-opacity": 0.9 } },
  ],
};

const OVERLAY: Record<string, string> = {
  "similitud-marte": "/productos/delta_marte.png",
  "similitud-luna": "/productos/delta_luna.png",
  clases: "/productos/clases.png",
};

export function createEcuadorMap(container: HTMLElement, ext: Extension): MapLibreMap {
  const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const map = new maplibregl.Map({
    container,
    style: ECUADOR_STYLE,
    renderWorldCopies: false,
    attributionControl: { compact: true },
    bounds: [
      [ext.oeste, ext.sur],
      [ext.este, ext.norte],
    ],
    fitBoundsOptions: { padding: 24, duration: reduce ? 0 : 0 },
    pitchWithRotate: false,
    dragRotate: false,
  });
  map.touchZoomRotate.disableRotation();
  return map;
}

export function setOverlay(map: MapLibreMap, vista: Vista, ext: Extension, opacity = 0.82): void {
  const url = OVERLAY[vista];
  const coords: [[number, number], [number, number], [number, number], [number, number]] = [
    [ext.oeste, ext.norte],
    [ext.este, ext.norte],
    [ext.este, ext.sur],
    [ext.oeste, ext.sur],
  ];
  const apply = () => {
    if (map.getLayer("overlay")) map.removeLayer("overlay");
    if (map.getSource("overlay")) map.removeSource("overlay");
    if (!url) return;
    map.addSource("overlay", { type: "image", url, coordinates: coords });
    map.addLayer({
      id: "overlay",
      type: "raster",
      source: "overlay",
      paint: { "raster-opacity": opacity, "raster-fade-duration": 0 },
    });
  };
  if (map.loaded()) apply();
  else map.once("load", apply);
}

export function setOverlayOpacity(map: MapLibreMap, opacity: number): void {
  if (map.getLayer("overlay")) {
    map.setPaintProperty("overlay", "raster-opacity", opacity);
  }
}

const markers: Marker[] = [];

export function setMarkers(
  map: MapLibreMap,
  zonas: ZonaPrioritaria[],
  selectedId: string | null,
  onSelect: (id: string) => void,
): void {
  markers.splice(0).forEach((m) => m.remove());
  for (const z of zonas) {
    const el = document.createElement("button");
    el.type = "button";
    el.className = `map-pin map-pin-${z.clase}${z.id === selectedId ? " is-selected" : ""}`;
    el.dataset.zoneId = z.id;
    el.setAttribute("aria-label", `${z.nombre}, similitud a Marte ${z.delta_marte.toFixed(2)}, a la Luna ${z.delta_luna.toFixed(2)}`);
    el.innerHTML = `<span class="pin-dot" aria-hidden="true"></span><span class="pin-label">${escapeHtml(z.nombre)}</span>`;
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      onSelect(z.id);
    });
    markers.push(new maplibregl.Marker({ element: el, anchor: "bottom" }).setLngLat([z.lon, z.lat]).addTo(map));
  }
}

export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const toR = (d: number) => (d * Math.PI) / 180;
  const dLat = toR(lat2 - lat1);
  const dLon = toR(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toR(lat1)) * Math.cos(toR(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(a)));
}

export function nearestZone(
  lat: number,
  lon: number,
  zonas: ZonaPrioritaria[],
): { zona: ZonaPrioritaria; km: number } | null {
  let best: ZonaPrioritaria | null = null;
  let bestD = Infinity;
  for (const z of zonas) {
    const d = haversineKm(lat, lon, z.lat, z.lon);
    if (d < bestD) {
      bestD = d;
      best = z;
    }
  }
  return best ? { zona: best, km: bestD } : null;
}

export function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function destroyMap(map: MapLibreMap | null): void {
  markers.splice(0).forEach((m) => m.remove());
  map?.remove();
}
