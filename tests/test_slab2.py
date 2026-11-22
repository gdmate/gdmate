"""Slab2 downloads use a local cache and publish only complete grid files."""
from io import BytesIO
from urllib.error import URLError

import pytest

from gdmate import slab2

GRID = b'CDF\x01' + bytes(64)
LISTING = b'''<a href="ker_slab2_dep_02.24.18.grd">depth</a>
<a href="ker_slab2_dip_02.24.18.grd">dip</a>'''


class Response(BytesIO):
    def __init__(self, data, length=None):
        super().__init__(data)
        self.headers = {'Content-Length': str(len(data) if length is None else length)}


def fake_server(monkeypatch, grid=GRID, length=None):
    calls = []

    def open_url(request, timeout):
        calls.append(request.full_url)
        if request.full_url.endswith('/'):
            return Response(LISTING)
        return Response(grid, length)

    monkeypatch.setattr(slab2, 'urlopen', open_url)
    return calls


def test_download_and_offline_cache(tmp_path, monkeypatch):
    calls = fake_server(monkeypatch)
    records = slab2.download_slab2('ker', tmp_path)
    assert len(calls) == 3
    assert [record['field'] for record in records] == ['depth', 'dip']
    for record in records:
        assert record['path'].read_bytes() == GRID
        assert record['size_bytes'] == len(GRID)
        assert not record['cached']
        assert record['url'].endswith(record['path'].name)

    def offline(*args, **kwargs):
        raise AssertionError('Cached files must work without network access')

    monkeypatch.setattr(slab2, 'urlopen', offline)
    assert all(record['cached'] for record in slab2.download_slab2('ker', tmp_path))


@pytest.mark.parametrize('grid,length', [(b'<html>error</html>', None), (GRID, 1000)])
def test_failed_download_leaves_no_partial_file(tmp_path, monkeypatch, grid, length):
    fake_server(monkeypatch, grid, length)
    with pytest.raises(RuntimeError, match='https://'):
        slab2.download_slab2('ker', tmp_path, fields=['depth'])
    assert list(tmp_path.iterdir()) == []


def test_failed_overwrite_preserves_existing_file(tmp_path, monkeypatch):
    fake_server(monkeypatch)
    record = slab2.download_slab2('ker', tmp_path, fields=['depth'])[0]
    fake_server(monkeypatch, b'error')
    with pytest.raises(RuntimeError):
        slab2.download_slab2('ker', tmp_path, fields=['depth'], overwrite=True)
    assert record['path'].read_bytes() == GRID
    assert len(list(tmp_path.iterdir())) == 1


def test_network_error_is_actionable(tmp_path, monkeypatch):
    def offline(*args, **kwargs):
        raise URLError('connection unavailable')

    monkeypatch.setattr(slab2, 'urlopen', offline)
    with pytest.raises(RuntimeError, match='USGS.*connection unavailable'):
        slab2.download_slab2('ker', tmp_path)


@pytest.mark.parametrize('kwargs', [dict(region='../ker'), dict(fields=['unknown']),
                                   dict(fields=[]), dict(timeout=0)])
def test_invalid_inputs(tmp_path, kwargs):
    options = dict(region='ker', data_dir=tmp_path)
    options.update(kwargs)
    with pytest.raises(ValueError):
        slab2.download_slab2(**options)


def test_region_missing_from_listing(tmp_path, monkeypatch):
    fake_server(monkeypatch)
    with pytest.raises(ValueError, match='No USGS'):
        slab2.download_slab2('abc', tmp_path)


def test_region_discovery_uses_only_matching_depth_grids(monkeypatch):
    listing = LISTING + b'''<a href="cas_slab2_dep_02.24.18.grd">Cascadia</a>
<a href="xxx_slab2_dip_02.24.18.grd">dip only</a>
<a href="../bad_slab2_dep_02.24.18.grd">not a file here</a>'''
    monkeypatch.setattr(slab2, 'urlopen', lambda *args, **kwargs: Response(listing))
    assert slab2.list_slab2_regions() == ['cas', 'ker']
