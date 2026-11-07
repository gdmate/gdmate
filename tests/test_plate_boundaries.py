"""Cached PB2002 data and geographic line parsing without GIS dependencies."""
import json
from io import BytesIO

import numpy as np
import pytest

from gdmate import plate_boundaries as pb


@pytest.fixture
def collection():
    return dict(type='FeatureCollection', features=[
        dict(type='Feature', geometry=dict(type='LineString',
             coordinates=[[179, 10], [-179, 11]]), properties={}),
        dict(type='Feature', geometry=dict(type='MultiLineString',
             coordinates=[[[0, 0], [1, 1]], [[2, 2], [3, 3]]]), properties={}),
    ])


def test_boundary_download_is_opt_in(tmp_path):
    with pytest.raises(FileNotFoundError, match='download=True'):
        pb.load_plate_boundaries(tmp_path)


def test_download_and_offline_cache(tmp_path, monkeypatch, collection):
    payload = json.dumps(collection).encode()
    monkeypatch.setattr(pb, 'urlopen', lambda *a, **kw: BytesIO(payload))
    downloaded = pb.load_plate_boundaries(tmp_path, download=True)
    assert len(pb.plate_boundary_segments(downloaded)) == 3
    assert downloaded['gdmate_provenance']['source_url'] == pb.PB2002_URL
    assert len(downloaded['gdmate_provenance']['source_sha256']) == 64

    def offline(*args, **kwargs):
        raise AssertionError('Cache must not require network')

    monkeypatch.setattr(pb, 'urlopen', offline)
    assert pb.load_plate_boundaries(tmp_path) == downloaded


def test_dateline_crossing_and_multiline_parts(collection):
    segments = pb.plate_boundary_segments(collection)
    assert len(segments) == 3
    np.testing.assert_allclose(segments[0], [[179, 10], [181, 11]])
    np.testing.assert_allclose(segments[1], [[0, 0], [1, 1]])


@pytest.mark.parametrize('payload', [b'<html>error</html>',
                                   b'{"type":"FeatureCollection","features":[]}'])
def test_bad_response_is_not_cached(tmp_path, monkeypatch, payload):
    monkeypatch.setattr(pb, 'urlopen', lambda *a, **kw: BytesIO(payload))
    with pytest.raises(RuntimeError, match='PB2002'):
        pb.load_plate_boundaries(tmp_path, download=True)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('coordinates', [[[0, 91], [1, 2]],
                                        [[float('nan'), 0], [1, 2]], [[0, 0]]])
def test_invalid_coordinates_rejected(collection, coordinates):
    collection['features'][0]['geometry']['coordinates'] = coordinates
    with pytest.raises(ValueError):
        pb.plate_boundary_segments(collection)
