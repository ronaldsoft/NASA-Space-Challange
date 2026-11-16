import { beforeAll, describe, expect, it, vi } from "vitest";

/** El idioma se fija al importar el módulo: se simula la URL antes de cargarlo. */
async function load(lang: "es" | "en") {
  vi.resetModules();
  vi.stubGlobal("location", { search: `?lang=${lang}`, href: "http://localhost/", hash: "" });
  vi.stubGlobal("localStorage", { getItem: () => null, setItem: () => undefined });
  return import("./content");
}

describe("fraseParecido (español)", () => {
  let c: Awaited<ReturnType<typeof load>>;
  beforeAll(async () => {
    c = await load("es");
  });

  it("describe δ 0,49 as bajo and includes the number", () => {
    expect(c.nivelDelta(0.49)).toBe("bajo");
    expect(c.fraseParecido("Marte", 0.49, true)).toBe("Parecido a Marte según el índice: bajo (δ 0,49)");
  });

  it("omits the number when asked", () => {
    expect(c.fraseParecido("la Luna", 0.82, false)).toBe("Parecido a la Luna según el índice: alto");
  });

  it("keeps the same bins as fraseDelta", () => {
    expect(c.fraseDelta(0.81)).toContain("muy parecido");
    expect(c.nivelDelta(0.81)).toBe("alto");
    expect(c.nivelDelta(0.5)).toBe("medio");
    expect(c.nivelDelta(0.2)).toBe("bajo");
    expect(c.nivelDelta(0.19)).toBe("casi nulo");
  });
});

describe("fraseParecido (English)", () => {
  let c: Awaited<ReturnType<typeof load>>;
  beforeAll(async () => {
    c = await load("en");
  });

  it("uses English words and a decimal point", () => {
    expect(c.nivelDelta(0.49)).toBe("low");
    expect(c.fraseParecido("Marte", 0.49, true)).toBe("Similarity to Mars according to the index: low (δ 0.49)");
    expect(c.fraseParecido("la Luna", 0.82, false)).toBe("Similarity to the Moon according to the index: high");
  });

  it("keeps the same bins", () => {
    expect(c.nivelDelta(0.81)).toBe("high");
    expect(c.nivelDelta(0.5)).toBe("medium");
    expect(c.nivelDelta(0.19)).toBe("almost none");
  });
});
