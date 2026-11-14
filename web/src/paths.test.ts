import { describe, expect, it } from "vitest";
import { assetUrl } from "./paths";

describe("assetUrl", () => {
  it("keeps a leading-slash path under the Vite base", () => {
    const out = assetUrl("/productos/catalogo.json");
    expect(out.endsWith("productos/catalogo.json")).toBe(true);
    expect(out.startsWith("/")).toBe(true);
  });
});
