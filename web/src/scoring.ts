/**
 * Recálculo en el cliente del índice ANALOG/delta (mismo criterio que
 * pipeline/index.py) para la tabla de validación cuando se mueven los pesos.
 * Los rásteres precalculados siguen usando pesos iguales.
 */
import {
  INDEX_VARS,
  type Catalogo,
  type IndexVar,
  type SitioValidacion,
  type Weights,
} from "./types";

function assignBand(lat: number, bands: Catalogo["bandas_latitud"]): string {
  const a = Math.abs(lat);
  for (const b of bands) {
    if (a >= b.abs_lat_min && a < b.abs_lat_max) return b.nombre;
  }
  return "";
}

function classify(dm: number, dl: number, tM: number, tL: number): string {
  const m = dm >= tM;
  const l = dl >= tL;
  if (m && l) return "ambos";
  if (m) return "marte";
  if (l) return "luna";
  return "ninguno";
}

export function recomputeValidation(catalog: Catalogo, weights: Weights): SitioValidacion[] {
  const sum = INDEX_VARS.reduce((s, k) => s + Math.max(0, weights[k]), 0) || 1;
  const w = Object.fromEntries(INDEX_VARS.map((k) => [k, Math.max(0, weights[k]) / sum])) as Weights;

  const out = catalog.sitios_validacion.map((s) => {
    const band = s.banda_latitud || assignBand(s.lat, catalog.bandas_latitud);
    const raw: Record<IndexVar, number> = {
      latitude: Math.abs(s.lat),
      elevation: s.elevacion_m,
      slope: s.pendiente_deg,
      roughness: s.rugosidad_tri,
    };
    const dM = distanceTo(raw, band, "mars", catalog, w, catalog.modo_bandas);
    const dL = distanceTo(raw, band, "moon", catalog, w, catalog.modo_bandas);
    const dm = 1 - Math.min(dM / catalog.d_max.mars, 1);
    const dl = 1 - Math.min(dL / catalog.d_max.moon, 1);
    const pred = classify(dm, dl, catalog.umbrales.mars.threshold, catalog.umbrales.moon.threshold);
    return {
      ...s,
      delta_marte: dm,
      delta_luna: dl,
      distancia_marte: dM,
      distancia_luna: dL,
      clase_predicha: pred,
      acierto: pred === s.clase_conocida,
    };
  });
  return out;
}

function distanceTo(
  raw: Record<IndexVar, number>,
  band: string,
  body: "mars" | "moon",
  catalog: Catalogo,
  w: Weights,
  modo?: string,
): number {
  const params = Object.fromEntries(catalog.std_params[body].map((p) => [p.variable, p]));
  const bands = modo === "banda_propia"
    ? [band]
    : [...new Set(catalog.signatures[body].map((s) => s.lat_band))];
  let best = Infinity;
  for (const b of bands) {
    const sigs = catalog.signatures[body].filter((s) => s.lat_band === b);
    const sig = Object.fromEntries(sigs.map((s) => [s.variable, s]));
    let acc = 0;
    for (const v of INDEX_VARS) {
      const p = params[v];
      const s = sig[v];
      if (!p || !s || !Number.isFinite(s.median)) continue;
      const z = (raw[v] - p.center) / p.scale;
      const med = (s.median - p.center) / p.scale;
      const q1 = (s.q1 - p.center) / p.scale;
      const q3 = (s.q3 - p.center) / p.scale;
      let d = z - med;
      const iqr = q3 - q1;
      if (iqr > 1e-6) {
        let extra = 0;
        if (z < q1) extra = (q1 - z) / iqr;
        else if (z > q3) extra = (z - q3) / iqr;
        d = d + Math.sign(d || 1) * 0.5 * extra;
      }
      acc += w[v] * d * d;
    }
    best = Math.min(best, Math.sqrt(acc));
  }
  return best;
}
