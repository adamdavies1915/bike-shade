"""Prepare the cached public network without claiming canopy measurements exist."""
import json
from common import RAW, PUBLIC, base_manifest, length_m, sha256

def main():
    source = json.loads((RAW / 'bikestreets-source.json').read_text())
    if sha256(RAW / 'bikestreets.geojson') != source['sha256']:
        raise ValueError('Network checksum differs from provenance')
    network = json.loads((RAW / 'bikestreets.geojson').read_text())
    features = []
    for f in network['features']:
        g = f['geometry']
        lines = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for line in lines:
            if len(line) < 2: continue
            features.append({'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': line},
                'properties': {**f['properties'], 'id': len(features), 'length_m': round(length_m(line), 1),
                               'canopy_pct': None, 'valid_coverage_pct': None}})
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / 'routes.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': features}, separators=(',', ':')))
    manifest = base_manifest(source)
    manifest['segments'] = len(features)
    (PUBLIC / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(f'Prepared {len(features)} real network parts; canopy remains explicitly unknown.')

if __name__ == '__main__': main()
