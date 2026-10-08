"""Find high-canopy 1 km simple paths on the measured Bike Streets graph.

Bounded beam search, not an exhaustive routing optimizer. Degree-two chains are
contracted without losing per-segment coverage. No turns or gaps are invented.
"""
import collections
import datetime as dt
import json
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import shape, mapping, LineString
from shapely.ops import transform, substring, unary_union
from common import PUBLIC, sha256

TARGET=1000
BEAM=8
to_m=Transformer.from_crs(4326,26915,always_xy=True).transform
to_ll=Transformer.from_crs(26915,4326,always_xy=True).transform

def node(coordinate): return tuple(round(c,7) for c in coordinate)

def reverse(parts): return [(f,not direction) for f,direction in reversed(parts)]

def summarize(parts, limit=TARGET, geometry=False):
    length=covered=0.;coords=[];used=[]
    for f,direction in parts:
        line=f['_line']
        take=min(line.length,limit-length)
        if take<=0: break
        if geometry:
            if not direction: line=LineString(list(line.coords)[::-1])
            clipped=substring(line,0,take)
            points=list(clipped.coords)
            coords.extend(points if not coords else points[1:])
        length+=take;covered+=take*f['properties']['canopy_pct']/100
        used.append((f['properties']['id'],take))
    result={'length_m':length,'canopy_pct':100*covered/length if length else 0,'parts':used}
    if geometry: result['line']=LineString(coords)
    return result

def main(network='network'):
    fs=json.loads((PUBLIC/'routes.geojson').read_text())['features']
    closed=[transform(to_m,shape(f['geometry'])) for f in fs if f['properties']['source_layer']=='construction' or f['properties'].get('is_under_construction')]
    closed=unary_union(closed).buffer(2) if closed else None
    if network=='traffic':
        fs=[f for f in fs if f['properties']['source_layer']=='designated']
        for f in fs:f['properties']['id']=f"osm:{f['properties']['id']}"
        city=json.loads((PUBLIC/'city-bikeways.geojson').read_text())['features']
        for f in city:f['properties']['id']=f"city:{f['properties']['id']}"
        fs+=city
    edges={};adj=collections.defaultdict(list)
    for f in fs:
        p=f['properties']
        if p['source_layer'] not in (('network',) if network=='network' else ('designated','city')) or p.get('is_under_construction') or p['canopy_pct'] is None: continue
        line=transform(to_m,shape(f['geometry']))
        if line.length<.1: continue
        if closed is not None and line.intersection(closed).length>min(10,line.length*.2): continue
        f['_line']=line
        a,b=map(node,(f['geometry']['coordinates'][0],f['geometry']['coordinates'][-1]))
        if a==b: continue
        i=p['id'];edges[i]=(a,b,f);adj[a].append(i);adj[b].append(i)
    # Contract chains. Iterate non-degree-two vertices first, then closed cycles.
    visited=set();graph=collections.defaultdict(list);chains=[]
    vertices=sorted(adj,key=lambda n:len(adj[n])==2)
    for start in vertices:
        for first in adj[start]:
            if first in visited: continue
            parts=[];current=start;e=first
            while True:
                visited.add(e);a,b,f=edges[e];direction=current==a
                parts.append((f,direction));current=b if direction else a
                available=[x for x in adj[current] if x not in visited]
                if len(adj[current])!=2 or not available: break
                e=available[0]
            ci=len(chains);chains.append(parts)
            graph[start].append((current,ci,True));graph[current].append((start,ci,False))
    candidates=[]
    for index,start in enumerate(graph):
        # State: current node, ordered parts, visited vertices, traveled distance.
        frontier=[(start,[],frozenset([start]),0.)]
        for _ in range(60):
            next_states=[]
            for current,path,seen,distance in frontier:
                for end,ci,direction in graph[current]:
                    if end in seen: continue
                    more=chains[ci] if direction else reverse(chains[ci])
                    new=path+more
                    metrics=summarize(new)
                    if metrics['length_m']>=TARGET-.01:
                        candidates.append((metrics['canopy_pct'],new));continue
                    next_states.append((end,new,seen|{end},metrics['length_m']))
            if not next_states: break
            next_states.sort(key=lambda x:summarize(x[1])['canopy_pct'],reverse=True)
            frontier=next_states[:BEAM]
        if index and index%1000==0: print(f'Searched {index} junctions',flush=True)
    # Long chains can contain the best stretch away from their endpoints.
    for chain in chains:
        if sum(f['_line'].length for f,d in chain)>TARGET:
            for oriented in (chain,reverse(chain)):
                for offset in range(len(oriented)):
                    metrics=summarize(oriented[offset:])
                    if metrics['length_m']>=TARGET-.01:candidates.append((metrics['canopy_pct'],oriented[offset:]))
    neighborhoods=[(f['properties']['name'],transform(to_m,shape(f['geometry']))) for f in json.loads((PUBLIC/'neighborhoods.geojson').read_text())['features']]
    picks=[];selected_parts=[];selected_lines=[]
    for score,parts in sorted(candidates,key=lambda x:x[0],reverse=True):
        if len(picks)>=10: break
        metrics=summarize(parts,geometry=True)
        usage=dict(metrics['parts'])
        if any(sum(min(length,other.get(i,0)) for i,length in usage.items())>TARGET*.25 for other in selected_parts): continue
        line=metrics.pop('line')
        # Prevent disjoint chains from becoming an apparent continuous route.
        if abs(line.length-TARGET)>1: raise ValueError('Unexpected discontinuity in candidate')
        if not line.is_simple: continue
        # Different source geometries can represent the same street. Avoid duplicate picks.
        if network=='traffic' and any(line.intersection(other.buffer(5)).length>TARGET*.25 for other in selected_lines):continue
        name=max(neighborhoods,key=lambda n:line.intersection(n[1]).length)
        label=name[0] if line.intersection(name[1]).length>0 else 'Greater New Orleans'
        rank=len(picks)+1
        props={'rank':rank,'name':f'{label} · route {rank}','neighborhood':label,
               'network':network,
               'sources':sorted({f['properties']['source_layer'] for f,direction in parts[:len(metrics['parts'])]}),
               'length_m':round(metrics['length_m'],1),'canopy_pct':round(score,1),
               'source_segment_ids':[i for i,length in metrics['parts']],
               'source_portions_m':[[i,round(length,3)] for i,length in metrics['parts']]}
        picks.append({'type':'Feature','properties':props,'geometry':mapping(transform(to_ll,line))})
        selected_parts.append(usage)
        selected_lines.append(line)
    if not picks:raise ValueError('No connected routes found')
    output={'type':'FeatureCollection','features':picks,
            'method':{'target_length_m':TARGET,'algorithm':'Degree-two contraction and bounded beam search; not an exhaustive optimum.',
                      'beam_width':BEAM,'overlap_limit_pct':25,'ranking':'Length-weighted mean of nearby canopy percentages.',
                      'construction':'Exclude flagged segments and substantial overlaps with construction linework.',
                      'network_sha256':sha256(PUBLIC/'routes.geojson'),
                      'network':network,'city_sha256':sha256(PUBLIC/'city-bikeways.geojson') if network=='traffic' else None,
                      'spatial_overlap_tolerance_m':5 if network=='traffic' else None,
                      'limitations':'Exploratory connected corridors, not turn-by-turn routing. One-way rules and crossing safety are not supplied by the source tiles.',
                      'imagery_year':2017,'generated_utc':dt.datetime.now(dt.timezone.utc).isoformat()}}
    (PUBLIC/('best-routes-traffic.geojson' if network=='traffic' else 'best-routes.geojson')).write_text(json.dumps(output,separators=(',',':')))
    print(json.dumps([f['properties']|{'source_segment_ids':len(f['properties']['source_segment_ids']),'source_portions_m':'omitted'} for f in picks],indent=2))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--network',choices=['network','traffic','all'],default='all')
    args=parser.parse_args()
    for network in (['network','traffic'] if args.network=='all' else [args.network]):main(network)
