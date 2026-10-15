"""Read-only spatial triage of city bikeways against saved current OSM ways.
Run: .venv/bin/python scripts/audit_osm.py
Inputs and outputs are local research artifacts; no OSM writes.
"""
import collections,csv,json
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import shape,LineString,box,mapping
from shapely.ops import transform,unary_union
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/osm-audit'
project=Transformer.from_crs(4326,26915,always_xy=True).transform
unproject=Transformer.from_crs(26915,4326,always_xy=True).transform
extent=transform(project,box(-90.16,29.875,-89.72,30.18))
def geom(f):return transform(project,shape(f['geometry'])).intersection(extent)
def signals(t):
    # Access permission alone is not a bike facility. Keep side-specific tags.
    allowed={'lane','track','opposite_lane','opposite_track','shared_lane','share_busway','opposite_share_busway','shared_busway','yes','designated','separate'}
    return t.get('highway')=='cycleway' or t.get('bicycle')=='designated' or t.get('cyclestreet')=='yes' or t.get('bicycle_road')=='yes' or any(k in {'cycleway','cycleway:left','cycleway:right','cycleway:both'} and v in allowed for k,v in t.items())
def main():
    raw=json.loads((OUT/'osm-current-candidates.json').read_text())
    assert not raw.get('remark'),raw.get('remark')
    ways=[w for w in raw['elements'] if w['type']=='way' and len(w.get('geometry',[]))>1]
    gs=[transform(project,LineString([(p['lon'],p['lat']) for p in w['geometry']])).intersection(extent) for w in ways]
    tree=STRtree(gs)
    rels=json.loads((OUT/'osm-relations.json').read_text())['elements']
    bike_members={m['ref'] for r in rels if r.get('tags',{}).get('route')=='bicycle' for m in r.get('members',[]) if m['type']=='way'}
    relationbuf=unary_union([g for w,g in zip(ways,gs) if w['id'] in bike_members]).buffer(20)
    accessbuf=unary_union([g for w,g in zip(ways,gs) if w.get('tags',{}).get('bicycle') in {'yes','permissive'}]).buffer(20)
    biked=unary_union([g for w,g in zip(ways,gs) if signals(w.get('tags',{}))]);buf=biked.buffer(20)
    old=json.loads((ROOT/'public/data/routes.geojson').read_text())['features']
    oldbuf=unary_union([geom(f) for f in old if f['properties']['source_layer']=='designated']).buffer(20)
    city=json.loads((ROOT/'public/data/city-bikeways.geojson').read_text())['features']
    groups=collections.defaultdict(list)
    for f in city:groups[f['properties']['city_id']].append(f)
    rows=[];features=[]
    for cid,fs in groups.items():
        g=unary_union([geom(f) for f in fs]);p=fs[0]['properties']
        if g.length<1:continue
        oldgap=g.difference(oldbuf).length;gap=g.difference(buf).length
        if oldgap<20:continue
        near=sorted([(g.intersection(gs[i].buffer(20)).length,int(i)) for i in tree.query(g.buffer(20))],reverse=True)
        nearby=[ways[i] for length,i in near if length>5][:8]
        coverage=100*(1-gap/g.length)
        category='already_has_bike_tags' if coverage>=90 else 'partial_bike_tags' if coverage>=10 else 'needs_survey'
        accesscoverage=100*g.intersection(accessbuf).length/g.length
        relationcoverage=100*g.intersection(relationbuf).length/g.length
        if category=='needs_survey' and accesscoverage>=90:category='bicycle_access_already_mapped'
        elif category=='needs_survey' and relationcoverage>=90:category='bicycle_route_relation_mapped'
        center=transform(unproject,g.centroid)
        row={'city_id':cid,'city_name':p['name'].strip() or '(unnamed)','from':p['from'],'to':p['to'],'city_facility':p['facility'],'length_m':round(g.length,1),'old_gap_m':round(oldgap,1),'current_gap_m':round(gap,1),'current_bike_tag_coverage_pct':round(coverage,1),'bicycle_access_coverage_pct':round(accesscoverage,1),'bicycle_relation_coverage_pct':round(relationcoverage,1),'triage':category,'lat':round(center.y,6),'lon':round(center.x,6),'osm_ways':' '.join(str(w['id']) for w in nearby),'osm_links':' '.join('https://www.openstreetmap.org/way/'+str(w['id']) for w in nearby),'osm_tags':json.dumps([{ 'id':w['id'],'timestamp':w.get('timestamp'),'tags':w.get('tags',{})} for w in nearby],separators=(',',':')),'survey_url':f'https://www.openstreetmap.org/#map=18/{center.y:.6f}/{center.x:.6f}'}
        rows.append(row);features.append({'type':'Feature','properties':row,'geometry':mapping(transform(unproject,g))})
    rows.sort(key=lambda r:r['current_gap_m'],reverse=True)
    with (OUT/'review.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    (OUT/'review.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}))
    cityg=unary_union([geom(f) for f in city]);oldgapg=cityg.difference(oldbuf)
    summary={'osm_retrieved_utc':raw['retrieved_utc'],'scope':raw['scope'],'ways':len(ways),'city_miles':cityg.length/1609.344,'old_gap_miles':oldgapg.length/1609.344,'candidate_city_records':len(rows),'triage_counts':dict(collections.Counter(r['triage'] for r in rows))}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
    for r in rows[:18]:print(r['city_id'],r['city_name'],r['city_facility'],r['current_gap_m'],r['current_bike_tag_coverage_pct'],r['osm_ways'])
if __name__=='__main__':main()
