import { assetUrl } from "./paths";
/**
 * Capa de datos. Por defecto: catálogo estático de la v1 congelada
 * (`/productos/catalogo.json`), apto para Vercel.
 * Si existen VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY (URL y clave
 * publicable; nunca una contraseña de base de datos), se consulta el
 * REST de Supabase: primero `analog_get_validation_table`, y si no existe
 * `get_validation_table`. El mapa sigue saliendo de los rásteres estáticos.
 * Si el RPC falla, se usa el catálogo estático.
 * Modelo v2: las métricas y la metadata de capas se leen de
 * `analog_v2_get_metrics` y `analog_v2_get_layers` (migración 013). Si fallan,
 * quedan las de `catalogo.json` (clave `modelo_v2`).
 */
import type { Catalogo, DataSource } from "./types";

export class MockDataSource implements DataSource {
  readonly kind = "mock" as const;
  private cache: Catalogo | null = null;

  async load(): Promise<Catalogo> {
    if (this.cache) return this.cache;
    const res = await fetch(assetUrl("/productos/catalogo.json"));
    if (!res.ok) throw new Error(`Catalog request failed (${res.status})`);
    this.cache = (await res.json()) as Catalogo;
    return this.cache;
  }
}

export class SupabaseDataSource implements DataSource {
  readonly kind = "supabase" as const;
  constructor(
    private readonly url: string,
    private readonly anonKey: string,
  ) {}

  private headers(): HeadersInit {
    return {
      apikey: this.anonKey,
      Authorization: `Bearer ${this.anonKey}`,
      "Content-Type": "application/json",
    };
  }

  /**
   * El mapa y las firmas siguen saliendo del catálogo estático (rásteres
   * precalculados). La tabla de validación y las fichas pueden venir del RPC.
   */
  private async rpc<T>(base: string, fn: string, body: unknown = {}): Promise<T | null> {
    try {
      const res = await fetch(`${base}/rest/v1/rpc/${fn}`, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify(body),
      });
      if (!res.ok) return null;
      return (await res.json()) as T;
    } catch {
      return null;
    }
  }

  /** Modelo v2 desde Supabase; si falla, se conserva el bloque de catalogo.json. */
  private async loadModeloV2(base: string, cat: Catalogo): Promise<void> {
    const [metricas, capas] = await Promise.all([
      this.rpc<Record<string, unknown>>(base, "analog_v2_get_metrics"),
      this.rpc<unknown[]>(base, "analog_v2_get_layers"),
    ]);
    if (metricas && Object.keys(metricas).length && capas?.length) {
      const { mascara_nasa_igbp, ...resto } = metricas as Record<string, unknown>;
      cat.modelo_v2 = {
        ...(cat.modelo_v2 ?? {}),
        metricas: resto,
        mascara: mascara_nasa_igbp ?? cat.modelo_v2?.mascara,
        capas,
        fuente_datos: "supabase",
      };
    } else if (cat.modelo_v2) {
      cat.modelo_v2.fuente_datos = "catalogo";
    }
  }

  async load(): Promise<Catalogo> {
    const mock = await new MockDataSource().load();
    const base = this.url.replace(/\/$/, "");
    await this.loadModeloV2(base, mock);
    if (mock.metricas_validacion.version === "modelo_v2") {
      // Modelo v2 principal: los percentiles de los sitios salen de analog_v2_get_stations; la tabla v1 no se usa.
      const est = await this.rpc<Array<{ kind: string; name: string; pct_marte_v2: number | null; pct_luna_v2: number | null }>>(
        base,
        "analog_v2_get_stations",
      );
      const porNombre = new Map((est ?? []).filter((e) => e.kind === "sitio_validacion").map((e) => [e.name, e]));
      if (porNombre.size) {
        mock.sitios_validacion = mock.sitios_validacion.map((s) => {
          const e = porNombre.get(s.nombre);
          if (!e) return s;
          return {
            ...s,
            delta_marte: e.pct_marte_v2 == null ? s.delta_marte : e.pct_marte_v2 / 100,
            delta_luna: e.pct_luna_v2 == null ? s.delta_luna : e.pct_luna_v2 / 100,
          };
        });
      }
      return mock;
    }
    try {
      let res = await fetch(`${base}/rest/v1/rpc/analog_get_validation_table`, {
        method: "POST",
        headers: this.headers(),
        body: "{}",
      });
      if (!res.ok) {
        res = await fetch(`${base}/rest/v1/rpc/get_validation_table`, {
          method: "POST",
          headers: this.headers(),
          body: "{}",
        });
      }
      if (!res.ok) return mock;
      const rows = (await res.json()) as Array<{
        sitio: string;
        latitud: number;
        longitud: number;
        buffer_km: number;
        etiqueta_conocida: string;
        clase_conocida: string;
        delta_marte: number;
        delta_luna: number;
        clase_predicha: string;
        acierto: boolean;
        fuente: string;
        es_provisional: boolean;
        es_mock: boolean;
      }>;
      if (!rows?.length) return mock;
      const byName = new Map(mock.sitios_validacion.map((s) => [s.nombre, s]));
      mock.sitios_validacion = rows.map((r) => {
        const prev = byName.get(r.sitio);
        return {
          nombre: r.sitio,
          lat: r.latitud,
          lon: r.longitud,
          buffer_km: r.buffer_km,
          etiqueta: r.etiqueta_conocida,
          fuente: r.fuente,
          elevacion_m: prev?.elevacion_m ?? 0,
          pendiente_deg: prev?.pendiente_deg ?? 0,
          rugosidad_tri: prev?.rugosidad_tri ?? 0,
          es_provisional: r.es_provisional,
          banda_latitud: prev?.banda_latitud ?? "",
          delta_marte: r.delta_marte,
          delta_luna: r.delta_luna,
          distancia_marte: prev?.distancia_marte ?? 0,
          distancia_luna: prev?.distancia_luna ?? 0,
          clase_predicha: r.clase_predicha,
          clase_conocida: r.clase_conocida,
          acierto: r.acierto,
        };
      });
      return mock;
    } catch {
      return mock;
    }
  }
}

export function createDataSource(): DataSource {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const key = import.meta.env.VITE_SUPABASE_ANON_KEY ?? import.meta.env.VITE_SUPABASE_KEY;
  if (url && key) return new SupabaseDataSource(url, key);
  return new MockDataSource();
}
