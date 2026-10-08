"""Shared metadata and dependency-free measurement helpers."""
from pathlib import Path
import hashlib
import math
import json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
PUBLIC = ROOT / 'public' / 'data'
CANOPY_URL = ('https://chs.coast.noaa.gov/htdata/raster1/landcover/bulkdownload/'
              'hires/la/la_neworleans_2017_ccap_highres_landcover_20211213.tif')
CANOPY_METADATA = 'https://www.fisheries.noaa.gov/inport/item/65779'
BBOX = (-90.16, 29.875, -89.72, 30.18)
CANOPY_CLASSES = (11, 13, 16)
# C-CAP: 0 background, 1 unclassified. Treat both as unknown, never as zero canopy.
VALID_CLASSES = (2, 5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25)

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def canopy_stats(canopy_count, valid_count, total_count, minimum_valid=0.9):
    if not 0 <= canopy_count <= valid_count <= total_count:
        raise ValueError('Invalid raster counts')
    coverage = valid_count / total_count if total_count else 0
    return {
        'canopy_pct': round(100 * canopy_count / valid_count, 1)
            if valid_count and coverage >= minimum_valid else None,
        'valid_coverage_pct': round(100 * coverage, 1),
    }

def length_m(coords):
    total = 0
    for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
        lat1, lat2 = math.radians(y1), math.radians(y2)
        a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(math.radians(x2-x1)/2)**2
        total += 6371008.8 * 2 * math.asin(min(1, math.sqrt(a)))
    return total

def base_manifest(source):
    manifest = {
        'status': 'canopy_pending',
        'network': {'name': 'Bike Streets', 'url': 'https://bikestreets.com/la/new-orleans/',
                    'retrieved_utc': source['retrieved_utc'], 'bbox': source['bbox'],
                    'sha256': source['sha256']},
        'canopy': {'name': 'NOAA C-CAP New Orleans land cover', 'year': 2017,
                   'resolution_m': 1, 'url': CANOPY_URL, 'metadata_url': CANOPY_METADATA,
                   'downloaded': False, 'canopy_classes': CANOPY_CLASSES},
        'method': {'buffer_m': 10, 'maximum_segment_m': 100, 'minimum_valid_coverage_pct': 90,
                   'description': 'Percent of classified 1 m pixels within 10 m of each route segment that are tree canopy. This is nearby canopy, not time-of-day shade.'},
        'limitations': ['2017 imagery predates Hurricane Ida and subsequent tree loss and planting.',
                       'Routes are a dated snapshot; construction and riding conditions may have changed.',
                       'This recreation does not recover Laura Harris’s hand-selected connectors.'],
    }
    neighborhood_source = RAW / 'neighborhoods-source.json'
    if neighborhood_source.exists():
        manifest['neighborhoods'] = json.loads(neighborhood_source.read_text())
    return manifest
