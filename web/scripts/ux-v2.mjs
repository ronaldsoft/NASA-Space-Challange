/**
 * Pruebas headless + capturas v2 (no toca screenshots/final).
 */
import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const OUT = process.env.SHOT_DIR || "/workspace/screenshots/v2";
const URL = process.env.APP_URL || "http://127.0.0.1:4173/";
const CHROME = process.env.CHROME || "/usr/bin/google-chrome";
fs.mkdirSync(OUT, { recursive: true });
const copyTo = process.env.SHOT_COPY || "/workspace/analogs/screenshots/v2";
fs.mkdirSync(copyTo, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: "shell",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
});

function attach(page, bag) {
  page.on("console", (msg) => {
    if (msg.type() === "error") bag.console.push(msg.text());
  });
  page.on("pageerror", (err) => bag.pageErrors.push(String(err)));
  page.on("response", (res) => {
    const u = res.url();
    if (res.status() >= 400 && !u.includes("favicon.ico")) {
      bag.failed.push(`${res.status()} ${u}`);
    }
  });
}

async function freshPage(viewport) {
  const page = await browser.newPage();
  const bag = { console: [], pageErrors: [], failed: [] };
  attach(page, bag);
  await page.setViewport({ ...viewport, deviceScaleFactor: 1 });
  page.setDefaultTimeout(30000);
  await page.goto(URL, { waitUntil: "networkidle0" });
  await page.evaluate(() => {
    localStorage.removeItem("analog_tour_dismissed");
    localStorage.setItem("analog_nivel", "explorador");
  });
  await page.reload({ waitUntil: "networkidle0" });
  await page.waitForSelector("[data-testid='home'], [data-testid='real-banner']");
  return { page, bag };
}

const report = { viewports: [], shots: [], keyboard: null };

// --- 1920 tests + screenshots ---
{
  const { page, bag } = await freshPage({ width: 1920, height: 1080 });
  await page.waitForSelector("[data-testid='home']");
  const homeText = await page.$eval("[data-testid='home']", (el) => el.innerText);
  if (!homeText.includes("¿Dónde en la Tierra")) throw new Error("home title missing");
  if (!homeText.includes("no pasó") && !homeText.toLowerCase().includes("no pasó")) {
    // honest banner is inside home
  }
  const honest = await page.$eval("[data-testid='aviso-honestidad']", (el) => el.innerText);
  if (!honest.includes("0,09") || !honest.includes("6 de 16")) throw new Error("honest results hidden on home");

  await page.screenshot({ path: path.join(OUT, "01-inicio.png"), type: "png" });

  await page.click("[data-testid='btn-tour']");
  await page.waitForSelector("[data-testid='tour-dialog']:not([hidden])");
  await new Promise((r) => setTimeout(r, 1400));
  await page.screenshot({ path: path.join(OUT, "02-recorrido.png"), type: "png" });
  await page.click("[data-tour='skip']");
  await page.waitForFunction(() => document.querySelector("[data-testid='tour-dialog']")?.hidden);

  // Mars explorador
  await page.click('button[data-vista="similitud-marte"]');
  await page.waitForFunction(() => document.getElementById("app")?.dataset.vista === "similitud-marte");
  await page.waitForFunction(() => {
    const c = document.querySelector("#map canvas");
    return c && c.width > 100;
  });
  await new Promise((r) => setTimeout(r, 1200));
  const leyenda = await page.$eval("[data-testid='leyenda']", (el) => el.innerText);
  if (!leyenda.includes("Más parecido") || !leyenda.includes("Menos parecido")) {
    throw new Error("legend words missing: " + leyenda);
  }
  await page.screenshot({ path: path.join(OUT, "03-marte-explorador.png"), type: "png" });

  // Científico on same map
  await page.click('button[data-nivel="cientifico"]');
  await page.waitForFunction(() => document.getElementById("app")?.dataset.nivel === "cientifico");
  await new Promise((r) => setTimeout(r, 400));
  const metrics = await page.$eval("#metrics-strip", (el) => el.innerText);
  if (!metrics.includes("IC 95")) throw new Error("científico metrics missing CI");
  await page.screenshot({ path: path.join(OUT, "04-marte-cientifico.png"), type: "png" });

  // Validation explorador
  await page.click('button[data-nivel="explorador"]');
  await page.waitForFunction(() => document.getElementById("app")?.dataset.nivel === "explorador");
  await page.click('button[data-vista="validacion"]');
  await page.waitForSelector("[data-testid='validacion-oficial']");
  const vExp = await page.$eval("[data-testid='validacion-oficial']", (el) => el.innerText);
  if (!vExp.includes("0,09") || !vExp.includes("6 de 16")) throw new Error("validation explorador hides results");
  if (!vExp.toLowerCase().includes("no")) throw new Error("validation should say it did not pass");
  await new Promise((r) => setTimeout(r, 300));
  await page.screenshot({ path: path.join(OUT, "05-validacion-explorador.png"), type: "png" });

  // Validation científico
  await page.click('button[data-nivel="cientifico"]');
  await page.waitForSelector("table.validacion");
  const vSci = await page.$eval("[data-testid='validacion-oficial']", (el) => el.innerText);
  if (!vSci.includes("modelo nulo") && !vSci.includes("Modelo nulo") && !vSci.includes("|lat|")) {
    throw new Error("científico validation missing null model: " + vSci.slice(0, 400));
  }
  if (!vSci.includes("0,09")) throw new Error("científico validation missing AUC");
  await new Promise((r) => setTimeout(r, 300));
  await page.screenshot({ path: path.join(OUT, "06-validacion-cientifico.png"), type: "png" });

  // Visualizer
  await page.click('button[data-vista="visualizador"]');
  await page.waitForSelector("#visualizador-wrap:not([hidden])");
  await page.waitForFunction(() => {
    const f = document.getElementById("visualizador-frame");
    return f && (f.getAttribute("src") || f.src || "").includes("/unity/visualizador/index.html");
  });
  await new Promise((r) => setTimeout(r, 4000));
  const iframeOk = await page.evaluate(() => {
    const f = document.getElementById("visualizador-frame");
    try {
      const doc = f.contentDocument;
      return { reachable: !!doc, hasCanvas: !!doc?.querySelector("canvas") };
    } catch (e) {
      return { reachable: false, error: String(e) };
    }
  });
  await page.screenshot({ path: path.join(OUT, "08-visualizador.png"), type: "png" });

  // Keyboard tab-through (new navigation on same page: go home first)
  await page.click('button[data-vista="inicio"]');
  await page.waitForSelector("[data-testid='home']");
  const focused = [];
  for (let i = 0; i < 20; i++) {
    await page.keyboard.press("Tab");
    const info = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      return {
        tag: el.tagName,
        id: el.id || "",
        text: (el.innerText || el.getAttribute("aria-label") || el.getAttribute("href") || "").slice(0, 60),
        testid: el.getAttribute("data-testid") || el.getAttribute("data-nivel") || el.getAttribute("data-vista") || "",
      };
    });
    if (info) focused.push(`${info.tag}#${info.id}[${info.testid}] ${info.text.replace(/\s+/g, " ")}`);
  }

  report.viewports.push({
    size: "1920x1080",
    console: bag.console,
    pageErrors: bag.pageErrors,
    failed: bag.failed,
    iframe: iframeOk,
    honestHome: honest,
    leyenda,
  });
  report.keyboard = focused;
  await page.close();
}

// 1366 and 390: smoke + no errors
for (const vp of [
  { width: 1366, height: 768, name: "1366x768" },
  { width: 390, height: 844, name: "390x844" },
]) {
  const { page, bag } = await freshPage(vp);
  await page.waitForSelector("[data-testid='home']");
  await page.click('button[data-vista="similitud-marte"]');
  await page.waitForFunction(() => document.getElementById("app")?.dataset.vista === "similitud-marte");
  await new Promise((r) => setTimeout(r, 1000));
  await page.click('button[data-vista="validacion"]');
  await page.waitForSelector("[data-testid='validacion-oficial']");
  if (vp.width === 390) {
    await page.click('button[data-vista="inicio"]');
    await page.waitForSelector("[data-testid='home']");
    await page.screenshot({ path: path.join(OUT, "07-movil.png"), type: "png" });
  }
  report.viewports.push({
    size: vp.name,
    console: bag.console,
    pageErrors: bag.pageErrors,
    failed: bag.failed,
  });
  await page.close();
}

await browser.close();

for (const f of fs.readdirSync(OUT)) {
  if (f.endsWith(".png")) fs.copyFileSync(path.join(OUT, f), path.join(copyTo, f));
}

console.log(JSON.stringify(report, null, 2));
const bad = report.viewports.some((v) => v.pageErrors.length || v.failed.length || v.console.length);
if (bad) {
  console.error("ISSUES_FOUND");
  process.exit(2);
}
console.log("ALL_CLEAN");
