/**
 * Capturas del globo (banda_propia): 1920×1080 y 390×844, con el panel Unity
 * abierto en la misma página (sin otra pestaña).
 * Uso: preview en http://127.0.0.1:4173
 *   SHOT_DIR=/workspace/screenshots/globo CHROME=/usr/bin/google-chrome node scripts/screenshot-globo.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const OUT = process.env.SHOT_DIR || path.join(ROOT, "screenshots/globo");
const APP_URL = process.env.APP_URL || "http://127.0.0.1:4173/";
const CHROME =
  process.env.CHROME ||
  process.env.PUPPETEER_EXECUTABLE_PATH ||
  "/usr/bin/google-chrome";

fs.mkdirSync(OUT, { recursive: true });

const consoleErrors = [];
const httpErrors = [];
const ignorableConsole = (t) =>
  /Automatic fallback to software WebGL/i.test(t) || /favicon/i.test(t);

async function launch(viewport) {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "shell",
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--hide-scrollbars",
      "--enable-unsafe-swiftshader",
      "--use-gl=angle",
      "--use-angle=swiftshader",
    ],
    defaultViewport: { ...viewport, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(60000);
  page.on("pageerror", (e) => consoleErrors.push(`pageerror:${viewport.width}: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error") {
      const t = m.text();
      if (!ignorableConsole(t)) consoleErrors.push(`console:${viewport.width}: ${t}`);
    }
  });
  page.on("response", (res) => {
    const s = res.status();
    const u = res.url();
    if (s >= 400 && !u.includes("favicon")) httpErrors.push(`${s} ${u}`);
  });
  return { browser, page };
}

async function boot(page, hash = "similitud-marte") {
  await page.goto(APP_URL, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    localStorage.setItem("analog_nivel", "cientifico");
    localStorage.setItem("analog_tour_dismissed", "1");
  });
  const target = new URL("#" + hash, APP_URL).href;
  await page.goto(target, { waitUntil: "networkidle0" });
  const nivel = await page.evaluate(() => document.getElementById("app")?.dataset.nivel);
  if (nivel !== "cientifico") await page.reload({ waitUntil: "networkidle0" });
  await page.evaluate(() => {
    const skip = document.querySelector("[data-tour='skip']");
    if (skip instanceof HTMLElement && skip.offsetParent !== null) skip.click();
    const backdrop = document.getElementById("tour-backdrop");
    const dialog = document.getElementById("tour-dialog");
    if (backdrop) backdrop.hidden = true;
    if (dialog) dialog.hidden = true;
  });
  await page.evaluate((h) => {
    location.hash = h;
  }, hash);
  await page.waitForFunction((h) => location.hash.replace(/^#/, "") === h, {}, hash);
  await page.waitForSelector(".banner-real, .banner-mock");
  await page.waitForFunction(() => {
    const err = document.querySelector("#app > p");
    if (err && /Error al cargar/.test(err.textContent || "")) return "ERROR";
    const canvas = document.querySelector("#map canvas");
    return !!(canvas && canvas.width > 50);
  });
  await new Promise((r) => setTimeout(r, 2000));
}

async function shot(page, name) {
  const dest = path.join(OUT, name);
  await page.screenshot({ path: dest, type: "png" });
  console.log("ok", name, fs.statSync(dest).size);
}

async function clickPressed(page, selector, waitMs = 1800) {
  const el = await page.waitForSelector(selector, { visible: true, timeout: 10000 });
  await el.click();
  await new Promise((r) => setTimeout(r, waitMs));
}

{
  const { browser, page } = await launch({ width: 1920, height: 1080 });
  await boot(page);
  await shot(page, "01-globo-tierra-ecuador-delta-marte.png");
  await clickPressed(page, '[data-area="galapagos"]');
  await shot(page, "02-globo-tierra-galapagos.png");
  await clickPressed(page, '[data-area="ecuador_continental"]');
  await clickPressed(page, "#btn-sitios-validacion", 2200);
  await shot(page, "03-globo-tierra-sitios-relieve.png");
  await clickPressed(page, '[data-cuerpo-globo="luna"]');
  await shot(page, "04-globo-luna.png");
  await clickPressed(page, '[data-cuerpo-globo="marte"]');
  await shot(page, "05-globo-marte.png");
  await clickPressed(page, '[data-cuerpo-globo="tierra"]');
  await clickPressed(page, '[data-area="ecuador_continental"]');
  await (await page.waitForSelector("#btn-ver-unity", { visible: true })).click();
  await page.waitForSelector("#unity-panel.is-open");
  await page.waitForFunction(() => document.getElementById("unity-panel-frame")?.getAttribute("src"));
  await new Promise((r) => setTimeout(r, 8000));
  await shot(page, "06-globo-panel-unity.png");
  await browser.close();
}

{
  const { browser, page } = await launch({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await boot(page);
  await shot(page, "07-globo-movil-390x844.png");
  await (await page.waitForSelector("#btn-ver-unity", { visible: true })).click();
  await page.waitForSelector("#unity-panel.is-open");
  const ui = await page.evaluate(() => {
    const close = document.getElementById("btn-cerrar-unity");
    const r = document.getElementById("unity-panel")?.getBoundingClientRect();
    return {
      closeText: close?.textContent,
      closeVisible: !!(close && close.offsetParent !== null),
      w: r?.width,
      h: r?.height,
    };
  });
  console.log("mobile panel", ui);
  await new Promise((r) => setTimeout(r, 4000));
  await shot(page, "08-globo-movil-panel-unity.png");
  await browser.close();
  if (!ui.closeVisible || ui.closeText?.trim() !== "Cerrar") {
    console.error("Mobile Unity panel is missing a visible Cerrar button.");
    process.exitCode = 4;
  }
}

console.log("HTTP", httpErrors.length, httpErrors);
console.log("CONSOLE", consoleErrors.length);
for (const l of consoleErrors) console.log(" ", l);
if (httpErrors.length) process.exitCode = 2;
if (consoleErrors.length) process.exitCode = process.exitCode || 3;
process.exit(process.exitCode || 0);
