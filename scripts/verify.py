"""Validate published data, and optionally require a completed canopy import."""
import json
import sys
from common import PUBLIC,BBOX,sha256

manifest=json.loads((PUBLIC/'manifest.json').read_text())
data=json.loads((PUBLIC/'routes.geojson').read_text())
assert data['type']=='FeatureCollection' and data['features']
assert manifest['segments']==len(data['features'])
scored=0
for feature in data['features']:
    p=feature['properties'];g=feature['geometry']
    assert g['type']=='LineString' and len(g['coordinates'])>=2
    assert p['source_layer'] in ('network','designated','construction')
    assert p['length_m']>=0
    for x,y in g['coordinates']:
        assert BBOX[0]-1e-6<=x<=BBOX[2]+1e-6 and BBOX[1]-1e-6<=y<=BBOX[3]+1e-6
    if p['canopy_pct'] is not None:
        scored+=1
        assert 0<=p['canopy_pct']<=100
        assert 90<=p['valid_coverage_pct']<=100
        assert p['length_m']<=100.01
if manifest['status']=='ready':
    assert manifest['canopy']['downloaded'] and scored>0
    assert manifest['measured_segments']==scored
    assert manifest['routes_sha256']==sha256(PUBLIC/'routes.geojson')
    assert (PUBLIC/'canopy.png').exists()
else:
    assert scored==0 and not manifest['canopy']['downloaded']
if '--require-canopy' in sys.argv:
    assert manifest['status']=='ready','Canopy import is still pending; do not describe this build as complete.'
print(f'Validated {len(data["features"])} route parts; {scored} canopy measurements; status={manifest["status"]}.')
