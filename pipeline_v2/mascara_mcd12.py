"""Máscara de cobertura NASA (IGBP de MODIS MCD12Q1 v061, año 2022) para el modelo v2.

Fuente usada: NASA GIBS, capa WMTS MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual
(IGBP de MCD12Q1 v061, Terra+Aqua), matriz 500m, paleta oficial
https://gibs.earthdata.nasa.gov/colormaps/v1.3/MODIS_IGBP_Land_Cover_Type.xml
Global: nivel 6 (0,5625/2^6 = 0,00879°, ~1 km) agregado a la grilla de 0,05° del modelo,
igual que MCD12C1 (fracción de cada clase IGBP por celda CMG de 0,05°).
Ecuador: nivel 7 (0,00439°, ~490 m) agregado a la grilla de 1/120° del artículo.

Reglas (decisión del 15-11-2026):
  bosque  = fracción IGBP 1–5 > 5 % o clase mayoritaria 1–5; se excluye con un borde 3×3.
  excluir además clase mayoritaria 11 (humedal), 12 (cultivo), 13 (urbano), 14 (mosaico cultivo).
Uso: python mascara_mcd12.py <dir_teselas_gibs> <dir_hackaton_outputs> <dir_salida>
"""
import glob, json, os, sys
import numpy as np
import rasterio
from PIL import Image
from scipy.ndimage import binary_dilation

PAL = {(33,138,33):1,(49,204,49):2,(152,204,49):3,(150,250,150):4,(141,186,141):5,(186,141,141):6,
       (245,222,179):7,(218,235,157):8,(255,213,0):9,(240,185,103):10,(71,131,181):11,(250,239,115):12,
       (255,0,0):13,(153,147,86):14,(255,255,255):15,(191,191,189):16,(134,202,227):17,(100,100,100):0}
LUT = np.zeros(256**3, np.uint8)
for (r,g,b),v in PAL.items(): LUT[(r<<16)|(g<<8)|b] = v
NC = 18
EXCL_USO = [11,12,13,14]

def tile_classes(path):
    a = np.asarray(Image.open(path).convert("RGBA"))
    k = (a[...,0].astype(np.uint32)<<16)|(a[...,1].astype(np.uint32)<<8)|a[...,2]
    c = LUT[k]; c[a[...,3]==0] = 0
    return c

def agregar(dir_t, z, res_cell, west, north, ncol, nrow):
    """Cuenta píxeles IGBP por celda de la grilla destino (centro del píxel)."""
    px = 0.5625/2**z; tdeg = 512*px
    cnt = np.zeros((nrow*ncol, NC), np.uint16)
    for f in glob.glob(f"{dir_t}/{z}/*/*.png"):
        r = int(f.split("/")[-2]); c = int(os.path.basename(f)[:-4])
        cl = tile_classes(f)
        lat = 90 - r*tdeg - (np.arange(512)+0.5)*px
        lon = -180 + c*tdeg + (np.arange(512)+0.5)*px
        ri = np.floor((north-lat)/res_cell).astype(int); ci = np.floor((lon-west)/res_cell).astype(int)
        okr = (ri>=0)&(ri<nrow); okc = (ci>=0)&(ci<ncol)
        if not okr.any() or not okc.any(): continue
        RI, CI = np.meshgrid(ri[okr], ci[okc], indexing="ij")
        sub = cl[np.ix_(okr, okc)]
        idx = (RI*ncol+CI).ravel()*NC + sub.ravel()
        u, n = np.unique(idx, return_counts=True)
        np.add.at(cnt.reshape(-1), u, n.astype(np.uint16))
    cnt = cnt.reshape(nrow, ncol, NC)
    tierra = cnt[...,1:17].sum(-1)
    frac_bosque = np.where(tierra>0, cnt[...,1:6].sum(-1)/np.maximum(tierra,1), 0.0)
    mayor = np.where(cnt.sum(-1)>0, cnt.argmax(-1), 255).astype(np.uint8)
    return cnt, frac_bosque, mayor

def mascaras(frac_bosque, mayor, borde=True):
    bosque = (frac_bosque > 0.05) | ((mayor>=1)&(mayor<=5))
    if borde: bosque = binary_dilation(bosque, np.ones((3,3),bool))
    uso = np.isin(mayor, EXCL_USO)
    return bosque, uso

def resumen(p, ok):
    m, l = p[0], p[1]
    v = ok & (m!=255)
    return {"celdas": int(v.sum()), "marte_ge95": int((v&(m>=95)).sum()), "luna_ge95": int((v&(l>=95)).sum()),
            "conjunta_ge95_min": int((v&(np.minimum(m,l)>=95)).sum())}

def main(dir_t, dir_h, out):
    os.makedirs(out, exist_ok=True)
    stats = {}
    # ---------- Global 0,05° ----------
    src = rasterio.open(f"{dir_h}/mapa_analogia_tierra_5km.tif"); p = src.read(); prof = src.profile
    cnt, fb, may = agregar(dir_t, 6, 0.05, -180.0, 90.0, 7200, 3600)
    bosque, uso = mascaras(fb, may)
    with rasterio.open(f"{out}/igbp_cmg_2022_005.tif","w",**{**prof,"count":2,"dtype":"uint8","nodata":255}) as d:
        d.write(np.clip(np.round(fb*100),0,100).astype(np.uint8),1); d.write(may,2)
        d.set_band_description(1,"Fraccion bosque IGBP 1-5 (%)"); d.set_band_description(2,"Clase IGBP mayoritaria")
    base = p[0]!=255
    stats["global"] = {
        "v1_sin_mascara_nasa": resumen(p, base),
        "variante_solo_bosque": resumen(p, base & ~bosque),
        "principal_bosque_y_uso": resumen(p, base & ~bosque & ~uso),
        "excluidas_por_bosque": int((base & bosque).sum()),
        "excluidas_por_uso_sin_bosque": int((base & uso & ~bosque).sum()),
        "celdas_sin_dato_igbp": int((base & (may==255)).sum()),
    }
    ok = base & ~bosque & ~uso
    q = p.copy(); q[:, ~ok] = 255
    q[2] = np.where(ok, np.minimum(p[0],p[1]), 255)
    with rasterio.open(f"{out}/mapa_analogia_tierra_5km_v2.tif","w",**prof) as d:
        d.write(q)
        for i,n in enumerate(["P_analogia_Marte_percentil","P_analogia_Luna_percentil","P_conjunto_minimo"],1): d.set_band_description(i,n)
    # ---------- Ecuador 1/120° (artículo) ----------
    e = rasterio.open(f"{dir_h}/articulo/recursos/geodatos/similitud_ecuador_1km.tif"); pe = e.read(); profe = e.profile
    t = e.transform
    cnte, fbe, maye = agregar(dir_t, 7, t.a, t.c, t.f, e.width, e.height)
    bos_e = (maye>=1)&(maye<=5); uso_e = np.isin(maye, EXCL_USO)
    base_e = pe[0]!=255
    def res_e(ok):
        return {"celdas": int(ok.sum()), "marte_ge95": int((ok&(pe[0]>=95)).sum()), "luna_ge95": int((ok&(pe[1]>=95)).sum()),
                "conjunta_ge95": int((ok&(pe[2]>=95)).sum()), "conjunta_max": int(pe[2][ok].max()) if ok.any() else None}
    oke = base_e & ~bos_e & ~uso_e
    stats["ecuador"] = {"articulo_sin_mascara_nasa": res_e(base_e), "principal_bosque_y_uso": res_e(oke),
        "excluidas_por_uso": int((base_e & uso_e).sum()), "excluidas_por_bosque_igbp": int((base_e & bos_e).sum()),
        "excluidas_cultivo_12_14": int((base_e & np.isin(maye,[12,14])).sum())}
    qe = pe.copy(); qe[:, ~oke] = 255
    with rasterio.open(f"{out}/similitud_ecuador_1km_v2.tif","w",**profe) as d:
        d.write(qe)
        for i,n in enumerate(["Percentil Marte alto","Percentil Luna explorada","Percentil conjunto minimo"],1): d.set_band_description(i,n)
    with rasterio.open(f"{out}/igbp_ecuador_2022_1km.tif","w",**{**profe,"count":1}) as d: d.write(maye,1)
    json.dump(stats, open(f"{out}/mascara_mcd12_resumen.json","w"), indent=1, ensure_ascii=False)
    print(json.dumps(stats, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main(*sys.argv[1:4])
