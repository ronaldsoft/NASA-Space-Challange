import { describe, expect, it } from "vitest";
import { fraseDelta, fraseParecido, nivelDelta } from "./content";

describe("fraseParecido", () => {
  it("describe δ 0,49 as bajo and includes the number", () => {
    expect(nivelDelta(0.49)).toBe("bajo");
    expect(fraseParecido("Marte", 0.49, true)).toBe(
      "Parecido a Marte según el índice: bajo (δ 0,49)",
    );
  });

  it("omits the number when asked", () => {
    expect(fraseParecido("la Luna", 0.82, false)).toBe(
      "Parecido a la Luna según el índice: alto",
    );
  });

  it("keeps the same bins as fraseDelta", () => {
    expect(fraseDelta(0.81)).toContain("muy parecido");
    expect(nivelDelta(0.81)).toBe("alto");
    expect(nivelDelta(0.5)).toBe("medio");
    expect(nivelDelta(0.2)).toBe("bajo");
    expect(nivelDelta(0.19)).toBe("casi nulo");
  });
});
