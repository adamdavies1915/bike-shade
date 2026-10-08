import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import PUBLIC,sha256

class PicksTests(unittest.TestCase):
    def test_traffic_picks_have_valid_source_scores_and_connected_geometry(self):
        from shapely.geometry import shape
        from shapely.ops import transform,unary_union
        from pyproj import Transformer
        metric=Transformer.from_crs(4326,26915,always_xy=True).transform
        source={f"osm:{f['properties']['id']}":f for f in json.loads((PUBLIC/'routes.geojson').read_text())['features'] if f['properties']['source_layer']=='designated'}
        source.update({f"city:{f['properties']['id']}":f for f in json.loads((PUBLIC/'city-bikeways.geojson').read_text())['features']})
        picks=json.loads((PUBLIC/'best-routes-traffic.geojson').read_text())
        self.assertEqual(picks['method']['network_sha256'],sha256(PUBLIC/'routes.geojson'))
        self.assertEqual(picks['method']['city_sha256'],sha256(PUBLIC/'city-bikeways.geojson'))
        self.assertEqual(len(picks['features']),10)
        for pick in picks['features']:
            p=pick['properties'];line=transform(metric,shape(pick['geometry']))
            self.assertEqual(p['network'],'traffic')
            self.assertAlmostEqual(line.length,1000,delta=.1)
            self.assertTrue(line.is_simple)
            parts=[source[i] for i in p['source_segment_ids']]
            valid=unary_union([transform(metric,shape(f['geometry'])) for f in parts]).buffer(.05)
            self.assertLess(line.difference(valid).length,.1)
            average=sum(source[i]['properties']['canopy_pct']*m for i,m in p['source_portions_m'])/sum(m for i,m in p['source_portions_m'])
            self.assertAlmostEqual(average,p['canopy_pct'],delta=.051)

    def test_picks_are_measured_connected_nonoverlapping_paths(self):
        from shapely.geometry import shape
        from shapely.ops import transform,unary_union
        from pyproj import Transformer
        metric=Transformer.from_crs(4326,26915,always_xy=True).transform
        source={f['properties']['id']:f for f in json.loads((PUBLIC/'routes.geojson').read_text())['features']}
        picks=json.loads((PUBLIC/'best-routes.geojson').read_text())
        self.assertEqual(picks['method']['network_sha256'],sha256(PUBLIC/'routes.geojson'))
        self.assertEqual(len(picks['features']),10)
        last=101;usages=[]
        for pick in picks['features']:
            p=pick['properties'];line=transform(metric,shape(pick['geometry']))
            self.assertAlmostEqual(line.length,1000,delta=.1)
            self.assertTrue(line.is_simple)
            self.assertLessEqual(p['canopy_pct'],last);last=p['canopy_pct']
            parts=[source[i] for i in p['source_segment_ids']]
            for f in parts:
                self.assertEqual(f['properties']['source_layer'],'network')
                self.assertFalse(f['properties'].get('is_under_construction'))
                self.assertIsNotNone(f['properties']['canopy_pct'])
            valid=unary_union([transform(metric,shape(f['geometry'])) for f in parts]).buffer(.05)
            self.assertLess(line.difference(valid).length,.1)
            usage=dict(p['source_portions_m'])
            average=sum(source[i]['properties']['canopy_pct']*m for i,m in usage.items())/sum(usage.values())
            self.assertAlmostEqual(average,p['canopy_pct'],delta=.051)
            for other in usages:self.assertLessEqual(sum(min(length,other.get(i,0)) for i,length in usage.items()),250.01)
            usages.append(usage)

    def test_city_layer_excludes_proposed_only_and_preserves_unknown(self):
        source=json.loads((PUBLIC/'city-bikeways-source.json').read_text())
        self.assertEqual(source['output_sha256'],sha256(PUBLIC/'city-bikeways.geojson'))
        features=json.loads((PUBLIC/'city-bikeways.geojson').read_text())['features']
        self.assertEqual(len(features),source['segments'])
        self.assertTrue(any(f['properties']['canopy_pct'] is not None for f in features))
        for f in features:
            p=f['properties']
            self.assertTrue(p['facility'].startswith('Existing '))
            if p['canopy_pct'] is not None:
                self.assertGreaterEqual(p['valid_coverage_pct'],90)
                self.assertTrue(0<=p['canopy_pct']<=100)
            else:self.assertLess(p['valid_coverage_pct'],90)

if __name__=='__main__':unittest.main()
