"""Refresh the public Bike Streets MVT snapshot, preserving all status layers."""
import concurrent.futures
import datetime as dt
import json
import math
import urllib.request
import numpy as np
import mapbox_vector_tile
from shapely.geometry import box,shape,mapping
from shapely.ops import transform,unary_union
from common import RAW,BBOX,sha256

Z=14
def tile(lon,lat):
    return int((lon+180)/360*2**Z),int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**Z)

def fetch(coords):
    x,y=coords
    url=f'https://bikestreets.com/api/v1/networkdeployment/tile/network/?z={Z}&x={x}&y={y}'
    request=urllib.request.Request(url,headers={'User-Agent':'BikeShade/0.1'})
    with urllib.request.urlopen(request,timeout=60) as response: data=response.read()
    path=RAW/'tiles'/f'{Z}_{x}_{y}.pbf';path.write_bytes(data)
    return x,y,data,{'url':url,'sha256':sha256(path)}

def main():
    (RAW/'tiles').mkdir(parents=True,exist_ok=True)
    x0,y0=tile(BBOX[0],BBOX[3]);x1,y1=tile(BBOX[2],BBOX[1])
    coords=[(x,y) for x in range(x0,x1+1) for y in range(y0,y1+1)]
    groups={};sources=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for x,y,data,source in pool.map(fetch,coords):
            sources.append(source)
            if not data: continue
            for name,layer in mapbox_vector_tile.decode(data,default_options={'y_coord_down':True}).items():
                if name not in ('network','designated','construction'): continue
                extent=layer['extent']
                def xy(px,py,z=None):
                    return ((x+np.asarray(px)/extent)/2**Z*360-180,
                            np.degrees(np.arctan(np.sinh(math.pi*(1-2*(y+np.asarray(py)/extent)/2**Z)))))
                for f in layer['features']:
                    g=transform(xy,shape(f['geometry'])).intersection(box(*BBOX))
                    if g.is_empty: continue
                    key=json.dumps({**f['properties'],'source_layer':name},sort_keys=True)
                    groups.setdefault(key,[]).append(g)
    if not groups: raise ValueError('No network data returned; existing snapshot retained')
    features=[{'type':'Feature','properties':json.loads(k),'geometry':mapping(unary_union(v))} for k,v in groups.items()]
    out=RAW/'bikestreets.geojson'
    temp=out.with_suffix('.tmp');temp.write_text(json.dumps({'type':'FeatureCollection','features':features}));temp.replace(out)
    manifest={'url':'https://bikestreets.com/la/new-orleans/','retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'bbox':BBOX,'sha256':sha256(out),'tiles':len(sources),'sources':sources,
              'license':'Bike Streets data retains its original rights; no open-data license verified.'}
    (RAW/'bikestreets-source.json').write_text(json.dumps(manifest,indent=2))
    print(f'Saved {len(sources)} tiles. Re-run analyze_canopy.py to regenerate the public map.')

if __name__=='__main__': main()
