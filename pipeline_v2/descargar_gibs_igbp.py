# Descarga teselas WMTS de NASA GIBS: MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual (MCD12Q1 v061, IGBP), año 2022.
import os, sys, concurrent.futures as cf, urllib.request, time
T="https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual/default/2022-01-01/500m/{z}/{r}/{c}.png"
def job(z,r,c):
    p=f"2022/{z}/{r}/{c}.png"
    if os.path.exists(p) and os.path.getsize(p)>0: return 0
    os.makedirs(os.path.dirname(p),exist_ok=True)
    for k in range(5):
        try:
            d=urllib.request.urlopen(T.format(z=z,r=r,c=c),timeout=60).read(); open(p,'wb').write(d); return 1
        except Exception as e:
            time.sleep(2+k*3)
    print("FALLO",p,file=sys.stderr); return -1
jobs=[]
z=int(sys.argv[1])
px=0.5625/2**z; tdeg=512*px
if z==6:
    for r in range(40):
        top=90-r*tdeg; bot=top-tdeg
        if bot>84 or top<-60: continue
        for c in range(80): jobs.append((z,r,c))
else:  # Ecuador bbox -92..-75, -5..2
    import math
    for r in range(int((90-2)/tdeg), int((90+5)/tdeg)+1):
        for c in range(int((180-92)/tdeg), int((180-75)/tdeg)+1): jobs.append((z,r,c))
print(len(jobs),"teselas")
with cf.ThreadPoolExecutor(24) as ex: res=list(ex.map(lambda a: job(*a), jobs))
print("ok",res.count(1),"existentes",res.count(0),"fallos",res.count(-1))
