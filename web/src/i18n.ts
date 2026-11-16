/**
 * Idioma de la interfaz. Inglés primero; español como segunda opción.
 * El idioma se fija al cargar la página: cambiarlo guarda la preferencia y recarga.
 * Prioridad: ?lang=es|en en la URL, luego localStorage, luego inglés.
 */
export type Lang = "en" | "es";

export const LANGS: { id: Lang; label: string; name: string }[] = [
  { id: "en", label: "EN", name: "English" },
  { id: "es", label: "ES", name: "Español" },
];

const LS_LANG = "analog_lang";

function readLang(): Lang {
  try {
    const q = new URLSearchParams(location.search).get("lang");
    if (q === "en" || q === "es") {
      localStorage.setItem(LS_LANG, q);
      return q;
    }
  } catch {
    /* sin URL o sin almacenamiento */
  }
  try {
    const v = localStorage.getItem(LS_LANG);
    if (v === "en" || v === "es") return v;
  } catch {
    /* sin almacenamiento */
  }
  return "en";
}

export const LANG: Lang = readLang();
export const isEn = LANG === "en";
export const LOCALE = isEn ? "en-US" : "es-EC";

/** Elige el texto según el idioma: tr(español, inglés). */
export function tr<T>(es: T, en: T): T {
  return isEn ? en : es;
}

export function saveLang(l: Lang): void {
  try {
    localStorage.setItem(LS_LANG, l);
  } catch {
    /* la preferencia solo dura la sesión */
  }
}
