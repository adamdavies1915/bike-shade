"""Fetch current OSM map API tiles for an existing review.geojson candidate set. Read-only; cached responses. Clear api-tiles to refresh."""
import json,math,pathlib,urllib.request,datetime
from shapely.geometry import shape,box
p=pathlib.Path(__file__).resolve().parents[1]/'docs/osm-audit';c=json.loads((p/'review.geojson').read_text())['features'];tiles=set()
for f in c:
 g=shape(f['geometry']).buffer(.0005);a,b,d,e=g.bounds
 for x in range(math.floor(a/.01),math.floor(d/.01)+1):
  for y in range(math.floor(b/.01),math.floor(e/.01)+1):
   if g.intersects(box(x*.01,y*.01,(x+1)*.01,(y+1)*.01)):tiles.add((x,y))
print('Tiles',len(tiles),flush=True)
(p/'api-tiles').mkdir(exist_ok=True)
for i,(x,y) in enumerate(sorted(tiles)):
 f=p/'api-tiles'/f'{x}_{y}.json'
 if not f.exists():
  bbox=[round(x*.01,4),round(y*.01,4),round((x+1)*.01,4),round((y+1)*.01,4)]
  u='https://api.openstreetmap.org/api/0.6/map.json?bbox='+','.join(map(str,bbox))
  d=json.load(urllib.request.urlopen(u,timeout=45));f.write_text(json.dumps(d))
 print(i+1,len(tiles),flush=True)
ways={};rels={};nodes={}
for f in (p/'api-tiles').glob('*.json'):
 for e in json.loads(f.read_text())['elements']:
  if e['type']=='node':nodes[e['id']]=e
  elif e['type']=='way':ways[e['id']]=e
  else:rels[e['id']]=e
out=[]
for e in ways.values():
 if 'highway' in e.get('tags',{}) and all(n in nodes for n in e['nodes']):e['geometry']=[{'lon':nodes[n]['lon'],'lat':nodes[n]['lat']} for n in e['nodes']];out.append(e)
d={'osm3s':{'timestamp_osm_base':None},'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'247 candidate city records plus 0.0005 degree padding; OSM primary map API','elements':out}
(p/'osm-current-candidates.json').write_text(json.dumps(d));(p/'osm-relations.json').write_text(json.dumps({'elements':list(rels.values())}));print('ways',len(out),'relations',len(rels),flush=True)
