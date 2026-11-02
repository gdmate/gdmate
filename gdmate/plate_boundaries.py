"""PB2002 plate boundaries from Bird (2003), converted by fraxen/tectonicplates.

Data conversion credits: Hugo Ahlenius/Nordpil and GeoJSON contributor csterling.
Dataset license: https://opendatacommons.org/licenses/by/1.0/.
"""

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

import numpy as np

PB2002_URL = (
    'https://raw.githubusercontent.com/fraxen/tectonicplates/master/'
    'GeoJSON/PB2002_boundaries.json'
)


def plate_boundary_segments(collection):
    """Validate a GeoJSON FeatureCollection and return separate lon/lat arrays.

    Supports LineString and MultiLineString. Longitudes are unwrapped within
    each line to avoid jumps across +/-180 degrees. Separate features and
    multiline parts remain separate; GMT handles projection and seam clipping.
    Other geometry types, invalid coordinates and empty collections raise
    ValueError instead of silently omitting boundaries.
    """
    if (not isinstance(collection, dict)
            or collection.get('type') != 'FeatureCollection'):
        raise ValueError('Expected a GeoJSON FeatureCollection')
    features = collection.get('features')
    if not isinstance(features, list) or not features:
        raise ValueError('No plate boundary features found')
    segments = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get('type') != 'Feature':
            raise ValueError('Invalid GeoJSON feature')
        geometry = feature.get('geometry')
        if not isinstance(geometry, dict):
            raise ValueError('Invalid GeoJSON line geometry')
        kind = geometry.get('type')
        if kind not in ('LineString', 'MultiLineString'):
            raise ValueError(f'Unsupported plate boundary geometry: {kind}')
        coordinates = geometry.get('coordinates', [])
        parts = [coordinates] if kind == 'LineString' else coordinates
        for part in parts:
            line = np.asarray(part, dtype=float)
            if (line.ndim != 2 or line.shape[0] < 2 or line.shape[1] < 2
                    or not np.isfinite(line[:, :2]).all()
                    or (np.abs(line[:, 1]) > 90).any()):
                raise ValueError(
                    'Boundary lines require at least two finite lon/lat nodes'
                )
            line = line[:, :2].copy()
            line[:, 0] = np.degrees(np.unwrap(np.radians(line[:, 0])))
            segments.append(line)
    if not segments:
        raise ValueError('No plate boundary lines found')
    return segments


def load_plate_boundaries(data_dir, *, download=False, timeout=30):
    """Load a cached PB2002 GeoJSON collection; opt in to a missing download.

    Set ``download=True`` to fetch from PB2002_URL when the snapshot is absent.
    Existing snapshots are validated and reused offline. The saved GeoJSON has
    a foreign member, ``gdmate_provenance``, recording source URL, source SHA256,
    retrieval time, citation, conversion credits and license. No GIS package is
    required. Failed downloads do not leave partial cached files.
    """
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    path = Path(data_dir).expanduser().resolve() / 'PB2002_boundaries.json'
    if path.is_file():
        collection = json.loads(path.read_text(encoding='utf-8'))
        plate_boundary_segments(collection)
        return collection
    if not download:
        raise FileNotFoundError(f'{path}: set download=True to fetch PB2002')
    temporary = None
    try:
        request = Request(PB2002_URL, headers={'User-Agent': 'gdmate/0.1'})
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
        collection = json.loads(payload)
        plate_boundary_segments(collection)
        collection['gdmate_provenance'] = dict(
            source_url=PB2002_URL, source_sha256=hashlib.sha256(payload).hexdigest(),
            downloaded_utc=datetime.now(timezone.utc).isoformat(),
            citation='Bird (2003), https://doi.org/10.1029/2001GC000252',
            credits='Hugo Ahlenius, Nordpil; GeoJSON conversion: csterling',
            license='https://opendatacommons.org/licenses/by/1.0/',
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                suffix='.json', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(collection, stream)
            stream.write('\n')
        os.replace(temporary, path)
        return collection
    except (OSError, ValueError, HTTPException) as error:
        raise RuntimeError(
            f'Could not download PB2002 from {PB2002_URL}: {error}'
        ) from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
