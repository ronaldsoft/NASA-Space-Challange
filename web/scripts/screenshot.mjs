/**
 * Capturas 1920×1080 de la v1 oficial (banda_propia) para el deck.
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
  { id: "similitud-marte", file: "01-similitud-marte.png", wait: "#map canvas" },
  { id: "similitud-luna", file: "02-similitud-luna.png", wait: "#map canvas" },
  { id: "validacion", file: "03-tabla-validacion.png", wait: "table.validacion" },
  { id: "diagnostico", file: "04-diagnostico.png", wait: "[data-testid='diagnostico']" },
  { id: "incertidumbre", file: "05-nota-incertidumbre.png", wait: "[data-testid='nota-incertidumbre']" },
  { id: "ficha", file: "06-ficha-zona.png", wait: ".ficha, #panel-body" },
];

fs.mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: "shell",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars", "--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader"],
  defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 },
});

const page = await browser.newPage();
page.setDefaultTimeout(45000);
await page.goto(URL, { waitUntil: "domcontentloaded" });
await page.evaluate(() => {
  localStorage.setItem("analog_nivel", "cientifico");
  localStorage.setItem("analog_tour_dismissed", "1");
});
await page.goto(URL, { waitUntil: "networkidle0" });
await page.waitForSelector(".banner-real, .banner-mock");
await page.evaluate(() => {
  const skip = document.querySelector("[data-tour='skip']");
  if (skip instanceof HTMLElement && skip.offsetParent !== null) skip.click();
  const backdrop = document.getElementById("tour-backdrop");
  const dialog = document.getElementById("tour-dialog");
  if (backdrop) backdrop.hidden = true;
  if (dialog) dialog.hidden = true;
});

for (const v of VISTAS) {
  await page.evaluate((id) => {
    location.hash = id;
  }, v.id);
  await page.waitForFunction((id) => location.hash.replace(/^#/, "") === id, {}, v.id);
  if (v.wait) {
    await page.waitForSelector(v.wait, { timeout: 20000 });
  }
  if (v.id === "similitud-marte" || v.id === "similitud-luna" || v.id === "ficha") {
    await page.waitForFunction(() => {
      const canvas = document.querySelector("#map canvas");
      return canvas && canvas.width > 100;
    });
    await new Promise((r) => setTimeout(r, 1500));
  } else {
    await new Promise((r) => setTimeout(r, 700));
  }
  const dest = path.join(OUT, v.file);
  await page.screenshot({ path: dest, type: "png" });
  console.log("ok", dest);
}

await browser.close();
