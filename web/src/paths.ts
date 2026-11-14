/** Prefix a root-absolute asset path with Vite's base (needed on GitHub Pages). */
export function assetUrl(path: string): string {
  const base = import.meta.env.BASE_URL || "/";
  const p = path.startsWith("/") ? path.slice(1) : path;
  return `${base.endsWith("/") ? base : `${base}/`}${p}`;
}
