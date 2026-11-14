/**
 * Capturas 1920×1080 de la v1 congelada para el deck.
 * Uso: el preview de Vite debe estar en http://127.0.0.1:4173
 *   SHOT_DIR=/workspace/screenshots/final CHROME=/usr/bin/google-chrome npm run screenshot
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const OUT = process.env.SHOT_DIR || path.join(ROOT, "screenshots/final");
const URL = process.env.APP_URL || "http://127.0.0.1:4173/";
const CHROME =
  process.env.CHROME ||
  process.env.PUPPETEER_EXECUTABLE_PATH ||
  "/usr/bin/google-chrome";

const VISTAS = [
  { id: "similitud-marte", file: "01-similitud-marte.png" },
  { id: "similitud-luna", file: "02-similitud-luna.png" },
  { id: "validacion", file: "03-tabla-validacion.png" },
  { id: "diagnostico", file: "04-diagnostico.png" },
  { id: "incertidumbre", file: "05-nota-incertidumbre.png" },
  { id: "ficha", file: "06-ficha-zona.png" },
];

fs.mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: "shell",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
  defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 },
});

const page = await browser.newPage();
page.setDefaultTimeout(30000);
await page.goto(URL, { waitUntil: "networkidle0" });
await page.waitForSelector(".banner-real, .banner-mock");
await page.waitForFunction(() => {
  const canvas = document.querySelector("#map canvas");
  return canvas && canvas.width > 100;
});
await new Promise((r) => setTimeout(r, 1200));

for (const v of VISTAS) {
  await page.click(`button[data-vista="${v.id}"]`);
  if (v.id === "validacion") {
    await page.waitForSelector("table.validacion");
  }
  await new Promise((r) => setTimeout(r, 900));
  const dest = path.join(OUT, v.file);
  await page.screenshot({ path: dest, type: "png" });
  console.log("ok", dest);
}

await browser.close();
