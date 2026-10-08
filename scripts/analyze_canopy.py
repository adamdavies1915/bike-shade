"""Measure actual classified NOAA raster pixels around metric route segments.

Run after fetch_canopy.py. Analysis uses native raster pixels, not the lower-resolution
PNG overview. No Esri software or services are used.
"""
import datetime as dt
import json
import math
import numpy as np
import rasterio
from rasterio.features import geometry_mask, geometry_window
from rasterio.windows import Window
from rasterio.warp import transform_bounds, reproject, Resampling
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform, substring, unary_union
from PIL import Image
from common import RAW, PUBLIC, BBOX, CANOPY_CLASSES, VALID_CLASSES, canopy_stats, base_manifest, sha256

def prepare_raster(original, source_hash):
    """Lossless spatial subset with tiles for efficient thousands-of-windows access."""
    target = RAW / 'canopy-analysis.tif'
    provenance = RAW / 'canopy-analysis-source.json'
    key = {'original_sha256': source_hash, 'bbox': list(BBOX), 'margin_m': 100}
    if target.exists() and provenance.exists() and json.loads(provenance.read_text()) == key:
        return target
    with rasterio.open(original) as src:
        west,south,east,north = transform_bounds('EPSG:4326',src.crs,*BBOX,densify_pts=21)
        from rasterio.windows import from_bounds
        win = from_bounds(west-100,south-100,east+100,north+100,src.transform)
        x,y = math.floor(win.col_off),math.floor(win.row_off)
        win = Window(x,y,math.ceil(win.col_off+win.width)-x,math.ceil(win.row_off+win.height)-y)
        profile = src.profile.copy()
        profile.update(width=int(win.width),height=int(win.height),transform=src.window_transform(win),
                       tiled=True,blockxsize=512,blockysize=512,compress='deflate',nodata=0)
        temp = target.with_suffix('.part')
        with rasterio.open(temp,'w',**profile) as dst:
            for y0 in range(0,int(win.height),512):
                rows=min(512,int(win.height)-y0)
                values=src.read(1,window=Window(win.col_off,win.row_off+y0,win.width,rows),boundless=True,fill_value=0)
                dst.write(values,1,window=Window(0,y0,win.width,rows))
        temp.replace(target)
    provenance.write_text(json.dumps(key))
    print('Prepared lossless tiled raster subset.',flush=True)
    return target

def measure(src, polygon):
    """Include pixels outside the raster in the missing-data denominator."""
    window = geometry_window(src, [mapping(polygon)], boundless=True)
    window = Window(int(window.col_off), int(window.row_off), int(window.width), int(window.height))
    pixels = src.read(1, window=window, boundless=True, masked=True)
    inside = geometry_mask([mapping(polygon)], out_shape=pixels.shape,
                           transform=src.window_transform(window), invert=True)
    valid = inside & ~np.ma.getmaskarray(pixels) & np.isin(pixels.data, VALID_CLASSES)
    canopy = valid & np.isin(pixels.data, CANOPY_CLASSES)
    return canopy_stats(int(canopy.sum()), int(valid.sum()), int(inside.sum()))

def make_overview(src):
    # Leaflet places image overlays in Web Mercator. Use that projection to avoid distortion.
    from rasterio.transform import from_bounds
    bounds = transform_bounds('EPSG:4326', 'EPSG:3857', *BBOX)
    width = 4096
    height = math.ceil(width * (bounds[3]-bounds[1])/(bounds[2]-bounds[0]))
    dst_transform = from_bounds(*bounds, width, height)
    values = np.zeros((height, width), dtype=np.uint8)
    reproject(source=rasterio.band(src,1), destination=values,
              src_transform=src.transform, src_crs=src.crs,
              dst_transform=dst_transform, dst_crs='EPSG:3857',
              resampling=Resampling.nearest, dst_nodata=0)
    rgba = np.zeros((height,width,4), dtype=np.uint8)
    rgba[np.isin(values,CANOPY_CLASSES)] = [65,120,65,200]
    Image.fromarray(rgba).save(PUBLIC / 'canopy.png', optimize=True)
    return {'url':'data/canopy.png', 'bounds':[[BBOX[1],BBOX[0]],[BBOX[3],BBOX[2]]],
            'display_only':True, 'resampling':'nearest', 'width':width, 'height':height}

def line_parts(g):
    if g.geom_type == 'LineString': yield g
    elif hasattr(g,'geoms'):
        for part in g.geoms: yield from line_parts(part)

def main():
    network_path = RAW / 'bikestreets.geojson'
    network_source = json.loads((RAW / 'bikestreets-source.json').read_text())
    canopy_source = json.loads((RAW / 'canopy-source.json').read_text())
    raster = RAW / 'noaa-new-orleans-2017.tif'
    if sha256(network_path) != network_source['sha256']: raise ValueError('Network checksum mismatch')
    if sha256(raster) != canopy_source['sha256']: raise ValueError('Canopy checksum mismatch')
    source = json.loads(network_path.read_text())
    to_metric = Transformer.from_crs(4326,26915,always_xy=True).transform
    from_metric = Transformer.from_crs(26915,4326,always_xy=True).transform
    features=[]
    PUBLIC.mkdir(parents=True,exist_ok=True)
    analysis_raster=prepare_raster(raster,canopy_source['sha256'])
    with rasterio.open(analysis_raster) as src:
        if not src.crs or src.count != 1: raise ValueError('Expected a single classified band with a CRS')
        to_raster = Transformer.from_crs(26915,src.crs,always_xy=True).transform
        for f in source['features']:
            # Dissolve duplicate tile overlaps within each status class before measuring.
            geom = transform(to_metric,unary_union(shape(f['geometry'])))
            for line in line_parts(geom):
                if line.length < .1: continue
                for offset in np.arange(0,line.length,100):
                    segment=substring(line,float(offset),min(float(offset)+100,line.length))
                    polygon=transform(to_raster,segment.buffer(10,cap_style=2))
                    stats=measure(src,polygon)
                    props={**f['properties'],'id':len(features),'length_m':round(segment.length,2),**stats}
                    features.append({'type':'Feature','properties':props,'geometry':mapping(transform(from_metric,segment))})
                    if len(features)%1000==0: print(f'Measured {len(features)} segments',flush=True)
        overview=make_overview(src)
    if not features or not any(f['properties']['canopy_pct'] is not None for f in features):
        raise ValueError('No measured segments; verify raster coverage and class values')
    out=PUBLIC/'routes.geojson'
    temp=out.with_suffix('.tmp')
    temp.write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':'),allow_nan=False))
    temp.replace(out)
    manifest=base_manifest(network_source)
    manifest.update(status='ready',segments=len(features),generated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    manifest['canopy'].update(downloaded=True,sha256=canopy_source['sha256'],
                              retrieved_utc=canopy_source['retrieved_utc'],overlay=overview)
    manifest['measured_segments']=sum(f['properties']['canopy_pct'] is not None for f in features)
    manifest['routes_sha256']=sha256(out)
    temp=PUBLIC/'manifest.tmp'
    temp.write_text(json.dumps(manifest,indent=2));temp.replace(PUBLIC/'manifest.json')
    print(f'Measured {manifest["measured_segments"]} of {len(features)} segments.')

if __name__=='__main__': main()
