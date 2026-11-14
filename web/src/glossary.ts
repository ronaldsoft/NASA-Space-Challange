import { escapeHtml } from "./maps";
import type { Nivel } from "./types";

export interface Termino {
  id: string;
  etiqueta: string;
  corto: string;
  estudiante: string;
  cientifico: string;
}

export const GLOSARIO: Record<string, Termino> = {
  delta: {
    id: "delta",
    etiqueta: "δ",
    corto: "Un número de 0 a 1 que dice cuánto se parece un lugar de la Tierra a Marte o a la Luna, según el índice.",
    estudiante:
      "δ (delta) es el índice ANALOG: 1 es idéntico en las cuatro variables de superficie y 0 es lo más distinto. Se calcula a partir de una distancia (con una penalización por IQR) y se acota entre 0 y 1.",
    cientifico:
      "δ = 1 − min(d / d_max, 1), con d la distancia euclídea en el espacio estandarizado (latitud |lat|, elevación absoluta, pendiente Horn y TRI de Wilson), modo todas_min y penalización por IQR. d_max está congelado por cuerpo.",
  },
  auc: {
    id: "auc",
    etiqueta: "AUC",
    corto: "Una nota de 0 a 1 que dice si el índice distingue los lugares que sí son análogos de los que no. 0,5 es como lanzar una moneda; más bajo, peor que el azar.",
    estudiante:
      "El AUC (área bajo la curva ROC) es la probabilidad de que el índice asigne un δ más alto a un análogo etiquetado que a un no análogo. 0,5 es un clasificador aleatorio. Aquí, 0,09 (Marte) y 0,25 (Luna) indican que no discrimina bien.",
    cientifico:
      "AUC de la curva ROC del δ continuo frente a la etiqueta conocida, sobre 16 sitios (Río Tinto, Ries y Sudbury quedan fuera). Se reporta el intervalo de confianza bootstrap de 95 %. Un AUC < 0,5 es un índice invertido respecto a las etiquetas.",
  },
  youden: {
    id: "youden",
    etiqueta: "Youden",
    corto: "La regla con la que se eligió el corte entre «parece» y «no parece», antes de mirar Ecuador.",
    estudiante:
      "El criterio de Youden elige el umbral que maximiza sensibilidad + especificidad − 1. Ese corte se congeló sobre los 16 sitios del AUC, no sobre Ecuador.",
    cientifico:
      "Umbral de Youden (J = sensibilidad + especificidad − 1) fijado solo sobre los 16 sitios del AUC y congelado el 14 de noviembre de 2026 a las 13:40:40 (America/Guayaquil). Ecuador no intervino. En Marte el umbral quedó en 0,13 con especificidad 0.",
  },
  latitud: {
    id: "latitud",
    etiqueta: "latitud",
    corto: "Qué tan lejos está un lugar del ecuador. Cerca del ecuador es baja; cerca de los polos, alta.",
    estudiante:
      "El índice usa el valor absoluto de la latitud (|lat|): no distingue norte de sur. Sirve para comparar franjas equivalentes en los tres cuerpos.",
    cientifico:
      "La variable es |lat|, con peso 0,25. Las firmas se construyen por bandas A–G de |lat| (0–15, 15–30, 30–45, 45–60, 60–72, 72–80, 80–90). Ecuador cae en la banda A.",
  },
  elevacion: {
    id: "elevacion",
    etiqueta: "elevación",
    corto: "La altura del terreno, en metros, según el mapa de cada planeta o de la Tierra.",
    estudiante:
      "En la v1 se usa la elevación absoluta (altura sobre el datum de cada cuerpo), no el relieve relativo respecto a los alrededores.",
    cientifico:
      "Elevación absoluta, peso 0,25. Datums no homologables al metro: areoide MOLA (GMM3), esfera lunar de 1737,4 km y geoide EGM2008 (GLO-90; el 0 exacto es nodata).",
  },
  pendiente: {
    id: "pendiente",
    etiqueta: "pendiente",
    corto: "Qué tan inclinada está la superficie. Una llanura tiene pendiente baja; una ladera, alta.",
    estudiante:
      "Se calcula con el método de Horn en una ventana de 3×3 celdas, sobre el modelo de elevación ya remuestreado a ~1 km.",
    cientifico:
      "Pendiente de Horn 3×3, recalculada en la grilla geográfica de ~1 km (no se reutiliza un producto de pendiente de origen). Peso 0,25. Cerca de los polos, en proyección equirrectangular, es más incierta (banda G).",
  },
  rugosidad: {
    id: "rugosidad",
    etiqueta: "rugosidad",
    corto: "Qué tan irregular o «arrugado» es el terreno, aparte de la pendiente.",
    estudiante:
      "Se mide con el TRI (índice de rugosidad del terreno de Wilson) en 3×3 celdas: cuánto sube y baja el entorno inmediato, en metros.",
    cientifico:
      "TRI de Wilson 3×3 sobre el DEM remuestreado, en metros. Peso 0,25. A 1 km el TRI típico de Marte en la banda A es de unos 12 m; varios análogos de campo son más rugosos a esa escala.",
  },
  iqr: {
    id: "iqr",
    etiqueta: "IQR",
    corto: "Una forma de medir cuán «repartida» está una medida: si los valores típicos están muy juntos o muy sueltos.",
    estudiante:
      "El rango intercuartílico (IQR) es la distancia entre el percentil 25 y el 75. Si un lugar se sale de ese rango, el índice le aplica una penalización.",
    cientifico:
      "Penalización por IQR: si el valor estandarizado z queda fuera de [q1, q3], se suma 0,5 · |exceso| / IQR con el signo de (z − mediana) a la diferencia, antes de acumular d² ponderada.",
  },
  std: {
    id: "std",
    etiqueta: "std_params",
    corto: "Las reglas para poner cada medida en la misma escala antes de comparar.",
    estudiante:
      "Cada variable se centra y se escala con parámetros ajustados solo en Marte o solo en la Luna, y después se congelan. Así una pendiente y una latitud pueden compararse juntas.",
    cientifico:
      "std_params: center y scale por variable y cuerpo de referencia, ajustados solo sobre el cuerpo de referencia (Marte y Luna por separado), nunca con celdas terrestres, y congelados antes de Ecuador.",
  },
  bandas: {
    id: "bandas",
    etiqueta: "bandas de latitud",
    corto: "Franjas del planeta según la distancia al ecuador, para comparar lugares en la misma «franja».",
    estudiante:
      "Hay siete bandas (A a G). En cada una se guarda la mediana y el IQR de las variables en Marte y en la Luna. El modo todas_min toma la banda más cercana, aunque no sea la de la misma latitud.",
    cientifico:
      "Firmas por banda A–G (mediana e IQR, 56 000 muestras estratificadas por cuerpo). modo_bandas = todas_min: distancia mínima sobre todas las bandas; se guarda la banda ganadora. No se mezclan cuerpos.",
  },
  especificidad: {
    id: "especificidad",
    etiqueta: "especificidad",
    corto: "De los lugares que no deberían parecerse, ¿cuántos el índice deja correctamente fuera?",
    estudiante:
      "Especificidad es la proporción de no análogos que quedan por debajo del umbral. En Marte es 0: todos los no análogos también superan el corte.",
    cientifico:
      "Especificidad = VN / (VN + FP). Umbral de Youden de Marte: 0,13, sensibilidad 1,00, especificidad 0,00. Por eso el mapa de clases no es un inventario fiable y no se informan porcentajes de cobertura.",
  },
  nulo: {
    id: "nulo",
    etiqueta: "modelo nulo",
    corto: "Una comparación muy simple (solo la latitud) para ver si el índice completo aporta algo más.",
    estudiante:
      "El modelo nulo usa únicamente |lat|. En Marte su AUC es 0,58, mayor que el del índice completo (0,09): las cuatro variables juntas no mejoran a «solo la latitud» en este conjunto.",
    cientifico:
      "Modelo nulo de solo |lat|, con AUC e IC bootstrap 95 %. Marte 0,58 (supera al índice 0,09). Se reporta junto con el test de DeLong pareado (con |lat| frente a sin latitud).",
  },
  delong: {
    id: "delong",
    etiqueta: "DeLong",
    corto: "Una prueba estadística para comparar dos formas de medir y ver si de verdad son distintas.",
    estudiante:
      "El test de DeLong pareado compara el AUC de dos modelos sobre los mismos sitios (por ejemplo, con |lat| y sin |lat|).",
    cientifico:
      "Test de DeLong pareado sobre el mismo conjunto de sitios. Se informa ΔAUC y el p-valor para Marte y Luna, con |lat| frente a sin latitud, como información secundaria.",
  },
};

export function defTermino(id: string, nivel: Nivel): string {
  const t = GLOSARIO[id];
  if (!t) return "";
  if (nivel === "cientifico") return t.cientifico;
  if (nivel === "estudiante") return t.estudiante;
  return t.corto;
}

/** Marca un término con un control de glosario accesible (foco y clic). */
export function term(id: string, texto?: string): string {
  const t = GLOSARIO[id];
  const label = texto ?? t?.etiqueta ?? id;
  if (!t) return escapeHtml(label);
  return `<button type="button" class="term" data-term="${t.id}" aria-expanded="false" aria-controls="glosario-panel" title="${escapeHtml(t.corto)}">${escapeHtml(label)}</button>`;
}
