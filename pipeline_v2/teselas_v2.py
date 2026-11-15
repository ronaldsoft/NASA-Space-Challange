"""Teselas XYZ 256 px (EPSG:3857) del modelo v2, paleta de 5 clases y nodata transparente.
global/{marte,luna,conjunta}/z0-6 ; global_sin_ecuador/{banda}/6 (Ecuador recortado, Natural Earth 10m admin-0 ECU) ;
ecuador/{banda}/z5-9 (versión del artículo con máscara NASA IGBP).
Uso: python teselas_v2.py <dir_modelo_v2> <ne_10m_admin_0_countries.shp> <dir_salida_tiles>
"""
import math, os, sys, json
import numpy as np, rasterio, shapefile
from rasterio.features import rasterize
from rasterio.transform import from_origin
from PIL import Image

CLASES = [(0,49),(50,74),(75,89),(90,94),(95,100)]
RGBA = [(45,40,110,110),(118,42,160,165),(208,74,118,205),(248,150,64,235),(252,236,60,255)]
LUT = np.full(256, 5, np.uint8)
for i,(a,b) in enumerate(CLASES): LUT[a:b+1] = i
PAL = sum([list(c[:3]) for c in RGBA], []) + [0,0,0]
TRN = bytes([c[3] for c in RGBA] + [0])

def lonlat_px(z, x, y):
    n = 256*2**z
    px = x*256 + np.arange(256) + 0.5; py = y*256 + np.arange(256) + 0.5
    lon = px/n*360 - 180
    lat = np.degrees(np.arctan(np.sinh(math.pi*(1 - 2*py/n))))
    return lon, lat

def reducir(a, f):
    """Media de percentiles por bloques f×f ignorando nodata (>=1/4 válidos)."""
    if f == 1: return np.where(a == 255, np.nan, a).astype(np.float32)
    h, w = (a.shape[0]//f)*f, (a.shape[1]//f)*f
    b = a[:h,:w].reshape(h//f, f, w//f, f).astype(np.float32)
    v = b != 255
    s = np.where(v, b, 0).sum((1,3)); n = v.sum((1,3))
    return np.where(n >= max(1, f*f//4), s/np.maximum(n,1), np.nan).astype(np.float32)

def guardar(cl, path):
    """Escribe la tesela; si no tiene datos escribe una tesela transparente (vite preview
    devuelve index.html con 200 para archivos ausentes y MapLibre fallaría al decodificar)."""
    if (cl == 5).all():
        os.makedirs(os.path.dirname(path), exist_ok=True)

        im = Image.fromarray(np.full((256,256),5,np.uint8), "P"); im.putpalette(PAL); im.save(path, optimize=True, transparency=TRN)
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = Image.fromarray(cl, "P"); im.putpalette(PAL); im.save(path, optimize=True, transparency=TRN)
    return True

def teselas(arr, west, north, res, zooms, out, bbox, recorte=None):
    n_ok = 0
    for z in zooms:
        ppd_tile = 256*2**z/360; f = 1
        while f*2 <= (1/res)/ppd_tile: f *= 2
        a = reducir(arr, f); r = res*f
        n = 2**z
        x0 = int((bbox[0]+180)/360*n); x1 = int((bbox[2]+180)/360*n - 1e-9)
        def ty(lat): return int((1 - math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
        y0 = ty(min(bbox[3],85.05)); y1 = ty(max(bbox[1],-85.05))
        for x in range(x0, x1+1):
            for y in range(max(0,y0), min(n-1,y1)+1):
                lon, lat = lonlat_px(z, x, y)
                ci = np.floor((lon-west)/r).astype(int); ri = np.floor((north-lat)/r).astype(int)
                okc = (ci>=0)&(ci<a.shape[1]); okr = (ri>=0)&(ri<a.shape[0])
                if not okc.any() or not okr.any():
                    guardar(np.full((256,256),5,np.uint8), f"{out}/{z}/{x}/{y}.png"); continue
                v = np.full((256,256), np.nan, np.float32)
                v[np.ix_(okr,okc)] = a[np.ix_(ri[okr], ci[okc])]
                if recorte is not None: v[recorte(lon, lat)] = np.nan
                cl = np.where(np.isnan(v), 5, LUT[np.clip(np.round(np.nan_to_num(v)),0,100).astype(np.uint8)]).astype(np.uint8)
                n_ok += guardar(cl, f"{out}/{z}/{x}/{y}.png")
    return n_ok

def main(dmod, shp, out):
    sf = shapefile.Reader(shp); f_ = [i for i,r in enumerate(sf.records()) if r.as_dict().get("ADM0_A3") == "ECU"][0]
    geom = sf.shape(f_).__geo_interface__
    ew, en, er = -93.0, 3.0, 0.005
    ecu = rasterize([(geom,1)], out_shape=(int(10/er), int(20/er)), transform=from_origin(ew, en, er, er), all_touched=True, dtype="uint8").astype(bool)
    def recorte(lon, lat):
        ci = np.floor((lon-ew)/er).astype(int); ri = np.floor((en-lat)/er).astype(int)
        m = np.zeros((256,256), bool)
        okc = (ci>=0)&(ci<ecu.shape[1]); okr = (ri>=0)&(ri<ecu.shape[0])
        if okc.any() and okr.any(): m[np.ix_(okr,okc)] = ecu[np.ix_(ri[okr], ci[okc])]
        return m
    g = rasterio.open(f"{dmod}/mapa_analogia_tierra_5km_v2.tif"); gp = g.read()
    e = rasterio.open(f"{dmod}/similitud_ecuador_1km_v2.tif"); ep = e.read(); t = e.transform
    res = {}
    for i, b in enumerate(["marte","luna","conjunta"]):
        res[f"global/{b}"] = teselas(gp[i], -180, 90, 0.05, range(0,7), f"{out}/global/{b}", (-180,-85,180,85))
        res[f"global_sin_ecuador/{b}"] = teselas(gp[i], -180, 90, 0.05, [6], f"{out}/global_sin_ecuador/{b}", (-180,-85,180,85), recorte)
        res[f"ecuador/{b}"] = teselas(ep[i], t.c, t.f, t.a, range(5,10), f"{out}/ecuador/{b}", (t.c, t.f+t.e*e.height, t.c+t.a*e.width, t.f))
    meta = {"clases": [f"{a}–{b}" for a,b in CLASES], "rgba": RGBA, "teselas": res,
            "esquema": "XYZ, 256 px, EPSG:3857; píxel sin dato = transparente; z0–6 global, z6 sin Ecuador, z5–9 Ecuador"}
    json.dump(meta, open(f"{out}/teselas.json","w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:4])
