"""Snapshot existing New Orleans city bikeways and measure nearby canopy locally."""
import collections
import datetime as dt
import json
import urllib.parse
import urllib.request
import rasterio
from pyproj import Transformer
from shapely.geometry import shape,mapping
from shapely.ops import transform,substring
from analyze_canopy import measure,line_parts,prepare_raster
from common import RAW,PUBLIC,sha256

SERVICE='https://services.arcgis.com/VhMjCzR3cIjEkh7L/ArcGIS/rest/services/Existing_and_Proposed_Bikeways_View_Layer/FeatureServer/0'
ITEM='https://www.arcgis.com/home/item.html?id=dbe68efb96304bd7b43c3424fceab175'
TYPES=('Existing Bike Lane','Existing Shared Lane','Existing Protected Bike Lane','Existing Bike Boulevard','Existing Bus/Bike Lane','Existing Shared Use Path')
WHERE='Existin_05 IN ('+','.join("'"+t+"'" for t in TYPES)+')'

def get(url,params):
    with urllib.request.urlopen(url+'?'+urllib.parse.urlencode(params),timeout=90) as response:d=json.load(response)
    if 'error' in d:raise RuntimeError(d['error'])
    return d

def main():
    metadata=get(SERVICE,{'f':'json'})
    expected=get(SERVICE+'/query',{'f':'json','where':WHERE,'returnCountOnly':'true'})['count']
    features=[]
    for offset in range(0,expected,1000):
        page=get(SERVICE+'/query',{'f':'geojson','where':WHERE,'outSR':4326,'returnGeometry':'true',
            'outFields':'FID,Centerl_02,Centerl_06,Centerl_07,Centerl_08,Existin_05,Existin_19,Existin_20,Existin_21,EditDate',
            'orderByFields':'FID','resultOffset':offset,'resultRecordCount':1000})
        features.extend(page['features'])
    assert len(features)==expected and len({f['properties']['FID'] for f in features})==expected
    raw=RAW/'city-bikeways.geojson';raw.write_text(json.dumps({'type':'FeatureCollection','features':features}))
    (RAW/'city-bikeways-metadata.json').write_text(json.dumps(metadata,indent=2))
    canopy=json.loads((RAW/'canopy-source.json').read_text())
    srcpath=prepare_raster(RAW/'noaa-new-orleans-2017.tif',canopy['sha256'])
    to_m=Transformer.from_crs(4326,26915,always_xy=True).transform
    to_ll=Transformer.from_crs(26915,4326,always_xy=True).transform
    output=[]
    with rasterio.open(srcpath) as src:
        to_src=Transformer.from_crs(26915,src.crs,always_xy=True).transform
        for f in features:
            p=f['properties']
            if not f['geometry']:continue
            for line in line_parts(transform(to_m,shape(f['geometry']))):
                offset=0.
                while offset<line.length-.01:
                    part=substring(line,offset,min(offset+100,line.length));offset+=100
                    stats=measure(src,transform(to_src,part.buffer(10,cap_style=2)))
                    props={'id':len(output),'city_id':p['FID'],'source_layer':'city',
                        'name':p['Centerl_06'] or p['Centerl_02'] or 'City bikeway',
                        'from':p['Centerl_07'],'to':p['Centerl_08'],'facility':p['Existin_05'],
                        'status':(p['Existin_19'] or '').strip(),'lts':p['Existin_20'],
                        'two_way':p['Existin_21'],'length_m':round(part.length,2),**stats}
                    output.append({'type':'Feature','properties':props,'geometry':mapping(transform(to_ll,part))})
    out=PUBLIC/'city-bikeways.geojson';out.write_text(json.dumps({'type':'FeatureCollection','features':output},separators=(',',':')))
    source={'name':'City of New Orleans existing bikeways','url':SERVICE,'item_url':ITEM,
        'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'service_data_last_edit_utc':dt.datetime.fromtimestamp(metadata['editingInfo']['dataLastEditDate']/1000,dt.timezone.utc).isoformat(),
        'filter':WHERE,'source_features':expected,'segments':len(output),'raw_sha256':sha256(raw),'output_sha256':sha256(out),
        'facility_counts':dict(collections.Counter(f['properties']['Existin_05'] for f in features)),
        'canopy_sha256':canopy['sha256'],'canopy_imagery_year':2017,
        'notes':'Existing facilities only; proposed-only facilities excluded. Snapshot is not a guarantee of present street conditions. Outside canopy subset remains unknown.'}
    (PUBLIC/'city-bikeways-source.json').write_text(json.dumps(source,indent=2))
    print(json.dumps(source,indent=2))

if __name__=='__main__':main()
