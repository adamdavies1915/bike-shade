"""Optional integration test with a small synthetic classified raster."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
HAS_GIS=all(importlib.util.find_spec(x) for x in ('rasterio','shapely','pyproj'))

@unittest.skipUnless(HAS_GIS,'Install requirements.txt to run raster integration tests')
class RasterTests(unittest.TestCase):
    def test_pixel_classes_and_out_of_bounds(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        from shapely.geometry import box
        from analyze_canopy import measure
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.tif'
            values=np.full((10,10),2,dtype='uint8');values[:,:5]=11
            values[0,:5]=11;values[1,:5]=13;values[2,:5]=16
            with rasterio.open(path,'w',driver='GTiff',height=10,width=10,count=1,dtype='uint8',
                               crs='EPSG:26915',transform=from_origin(500000,3300010,1,1),nodata=0) as dst:
                dst.write(values,1)
            with rasterio.open(path) as src:
                self.assertEqual(measure(src,box(500000,3300000,500010,3300010))['canopy_pct'],50)
                self.assertIsNone(measure(src,box(499990,3300000,500010,3300010))['canopy_pct'])
                self.assertEqual(measure(src,box(500005,3300000,500010,3300010))['canopy_pct'],0)

if __name__=='__main__': unittest.main()
