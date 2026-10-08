"""Download NOAA's original classified GeoTIFF atomically; no ArcGIS account/API."""
import datetime as dt
import json
import urllib.request
from common import RAW, CANOPY_URL, CANOPY_METADATA, sha256

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / 'noaa-new-orleans-2017.tif'
    if target.exists() and (RAW / 'canopy-source.json').exists():
        old = json.loads((RAW / 'canopy-source.json').read_text())
        if sha256(target) == old['sha256']:
            print('Verified cached canopy GeoTIFF.'); return
    tmp = target.with_suffix('.part')
    print('Downloading NOAA GeoTIFF (~957 MB).', flush=True)
    req = urllib.request.Request(CANOPY_URL, headers={'User-Agent': 'BikeShade/0.1 (public GIS download)'})
    try:
        with urllib.request.urlopen(req, timeout=120) as response, tmp.open('wb') as output:
            expected = int(response.headers.get('Content-Length', 0))
            total = 0
            while True:
                block = response.read(1024 * 1024)
                if not block: break
                output.write(block); total += len(block)
                if total % (50 * 1024 * 1024) == 0: print(f'{total // (1024*1024)} MB', flush=True)
            if expected and total != expected: raise ValueError('Incomplete download')
        with tmp.open('rb') as stream:
            if stream.read(4) not in (b'II*\x00', b'MM\x00*', b'II+\x00', b'MM\x00+'):
                raise ValueError('Download is not a TIFF')
        tmp.replace(target)
        meta = {'url': CANOPY_URL, 'metadata_url': CANOPY_METADATA,
                'retrieved_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                'imagery_year': 2017, 'bytes': total, 'sha256': sha256(target)}
        (RAW / 'canopy-source.json').write_text(json.dumps(meta, indent=2))
        print(f'Saved {target}')
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

if __name__ == '__main__': main()
