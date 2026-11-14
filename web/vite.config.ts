import { defineConfig, type Connect } from "vite";

function unityMime(): {
  name: string;
  configureServer(server: { middlewares: Connect.Server }): void;
  configurePreviewServer(server: { middlewares: Connect.Server }): void;
} {
  const middleware: Connect.NextHandleFunction = (req, res, next) => {
    const url = req.url?.split("?")[0] ?? "";
    if (url.endsWith(".wasm")) res.setHeader("Content-Type", "application/wasm");
    else if (url.endsWith(".data") || url.endsWith(".bytes")) {
      res.setHeader("Content-Type", "application/octet-stream");
    }
    next();
  };
  return {
    name: "unity-webgl-mime",
    configureServer(server) {
      server.middlewares.use(middleware);
    },
    configurePreviewServer(server) {
      server.middlewares.use(middleware);
    },
  };
}

export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [unityMime()],
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
