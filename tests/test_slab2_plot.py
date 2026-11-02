"""Scientific grid conversion and an optional real PyGMT render."""

import numpy as np
import pytest

from gdmate import slab2


def test_missing_plot_grid(tmp_path):
    with pytest.raises(FileNotFoundError):
        slab2.plot_slab2_depth(tmp_path / 'missing.grd')


@pytest.mark.parametrize('values', [np.full((3, 3), np.nan), np.full((3, 3), np.inf)])
def test_invalid_depth_values(tmp_path, values):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    grid = xr.DataArray(values, coords={'lat': [-32, -31, -30],
                                      'lon': [180, 181, 182]}, dims=('lat', 'lon'))
    path = tmp_path / 'depth.grd'
    grid.to_netcdf(path, engine='h5netcdf')
    with pytest.raises(ValueError):
        slab2.load_slab2_depth(path)


def test_depth_sign_coordinates_and_missing_values(tmp_path):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    values = np.array([[-10., -100., -200.], [-20., np.nan, -250.],
                       [-30., -150., -300.]])
    grid = xr.DataArray(values, coords={'lat': [-32, -31, -30],
                                      'lon': [180, 181, 182]}, dims=('lat', 'lon'))
    path = tmp_path / 'depth.grd'
    grid.to_netcdf(path, engine='h5netcdf')
    result = slab2.load_slab2_depth(path)
    np.testing.assert_allclose(result.values, -values, equal_nan=True)
    np.testing.assert_array_equal(result.lon, grid.lon)
    np.testing.assert_array_equal(result.lat, grid.lat)
    assert result.attrs['units'] == 'km'
    assert result.attrs['positive'] == 'down'


def test_pygmt_render(tmp_path):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    pytest.importorskip('pygmt')
    grid = xr.DataArray(-np.arange(100, 1000, 100).reshape(3, 3),
                        coords={'lat': [-32, -31, -30], 'lon': [180, 181, 182]},
                        dims=('lat', 'lon'))
    path = tmp_path / 'depth.grd'
    grid.to_netcdf(path, engine='h5netcdf')
    figure = slab2.plot_slab2_depth(path)
    output = tmp_path / 'depth.png'
    figure.savefig(output)
    assert output.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')


def test_age_download_requires_explicit_opt_in(tmp_path):
    with pytest.raises(FileNotFoundError, match='download=True'):
        slab2.load_seafloor_age([169, 188, -44, -14], tmp_path)


def test_age_snapshot_cache_and_region_key(tmp_path, monkeypatch):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    pygmt = pytest.importorskip('pygmt')
    calls = []

    def remote_age(**kwargs):
        calls.append(kwargs)
        return xr.DataArray(np.arange(9).reshape(3, 3) * 10.,
                            coords={'lat': [-32, -31, -30], 'lon': [180, 181, 182]},
                            dims=('lat', 'lon'))

    monkeypatch.setattr(pygmt.datasets, 'load_earth_age', remote_age)
    region = [180, 182, -32, -30]
    downloaded = slab2.load_seafloor_age(region, tmp_path, download=True)
    assert calls == [dict(region=region, resolution='10m', registration='gridline')]
    assert downloaded.attrs['units'] == 'Myr'
    assert '2020GC009214' in downloaded.attrs['citation']
    cached = slab2.load_seafloor_age(region, tmp_path)
    np.testing.assert_array_equal(cached.values, downloaded.values)
    assert len(calls) == 1
    with pytest.raises(FileNotFoundError):
        slab2.load_seafloor_age([179, 182, -32, -30], tmp_path)


def test_combined_age_and_slab_render(tmp_path):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    pytest.importorskip('pygmt')
    coordinates = {'lat': [-32, -31, -30], 'lon': [180, 181, 182]}
    values = -np.arange(100, 1000, 100, dtype=float).reshape(3, 3)
    values[:, 0] = np.nan  # Background must remain visible outside the slab.
    grid = xr.DataArray(values, coords=coordinates, dims=('lat', 'lon'))
    path = tmp_path / 'slab.grd'
    grid.to_netcdf(path, engine='h5netcdf')
    ages = np.arange(9).reshape(3, 3)*20.
    ages[:, 0] = np.nan
    age = xr.DataArray(ages, coords=coordinates, dims=('lat', 'lon'))
    figure = slab2.plot_slab2_depth(path, seafloor_age=age)
    output = tmp_path / 'combined.png'
    figure.savefig(output)
    assert output.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')

    # Two transparent rasters can expose a red GMT/Ghostscript mask colour.
    from matplotlib.image import imread

    pixels = imread(output)
    red_mask = ((pixels[..., 0] > 0.95) & (pixels[..., 1] < 0.05)
                & (pixels[..., 2] < 0.05))
    assert not red_mask.any()


def test_empty_global_plot_rejected():
    with pytest.raises(ValueError, match='at least one'):
        slab2.plot_slab2_global([])


@pytest.mark.parametrize('with_age', [False, True])
def test_global_render_with_longitudes_on_either_side_of_zero(
        tmp_path, with_age, monkeypatch):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    pygmt = pytest.importorskip('pygmt')
    monkeypatch.setattr(pygmt.Figure, 'coast',
                        lambda *args, **kwargs: pytest.fail('Unexpected shorelines'))
    paths = []
    for index, longitudes in enumerate(([178, 180, 182], [-80, -78, -76])):
        values = -np.arange(100, 1000, 100, dtype=float).reshape(3, 3)
        values[0, 0] = np.nan
        grid = xr.DataArray(values, coords={'lat': [-32, -31, -30],
                                            'lon': longitudes}, dims=('lat', 'lon'))
        path = tmp_path / f'slab_{index}.grd'
        grid.to_netcdf(path, engine='h5netcdf')
        paths.append(path)
    age = None
    relief = None
    if with_age:
        ages = np.arange(15, dtype=float).reshape(3, 5)*10
        ages[0, 0] = np.nan
        age = xr.DataArray(ages, coords={'lat': [-65, 0, 65],
                                        'lon': [0, 90, 180, 270, 360]},
                           dims=('lat', 'lon'))
        relief = xr.DataArray(np.linspace(-6000, 5000, 45).reshape(5, 9),
                              coords={'lat': np.linspace(-65, 65, 5),
                                      'lon': np.linspace(0, 360, 9)},
                              dims=('lat', 'lon'))
    boundaries = dict(type='FeatureCollection', features=[
        dict(type='Feature', geometry=dict(type='LineString',
             coordinates=[[179, 10], [-179, 11]]), properties={}),
    ])
    figure = slab2.plot_slab2_global(paths, seafloor_age=age, relief=relief,
                                     plate_boundaries=boundaries)
    output = tmp_path / 'global.png'
    figure.savefig(output)
    from matplotlib.image import imread

    pixels = imread(output)
    assert pixels.shape[1] > pixels.shape[0]
    assert not ((pixels[..., 0] > .95) & (pixels[..., 1] < .05)
                & (pixels[..., 2] < .05)).any()


def test_native_above_sea_level_nodes_keep_signed_depth(tmp_path):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    grid = xr.DataArray([[2.668, -10.], [-20., -100.]],
                        coords={'lat': [18., 19.], 'lon': [-67., -66.]},
                        dims=('lat', 'lon'))
    path = tmp_path / 'mue.grd'
    grid.to_netcdf(path, engine='h5netcdf')
    result = slab2.load_slab2_depth(path)
    assert result.values[0, 0] == pytest.approx(-2.668)
    assert result.values[1, 1] == 100.


def test_relief_snapshot_requires_explicit_download(tmp_path):
    with pytest.raises(FileNotFoundError, match='download=True'):
        slab2.load_earth_relief([0, 360, -65, 65], tmp_path)


def test_relief_snapshot_cache(tmp_path, monkeypatch):
    xr = pytest.importorskip('xarray')
    pytest.importorskip('h5netcdf')
    pygmt = pytest.importorskip('pygmt')
    calls = []

    def remote_relief(**kwargs):
        calls.append(kwargs)
        return xr.DataArray(np.arange(9).reshape(3, 3)*1000. - 4000.,
                            coords={'lat': [-32, -31, -30], 'lon': [180, 181, 182]},
                            dims=('lat', 'lon'))

    monkeypatch.setattr(pygmt.datasets, 'load_earth_relief', remote_relief)
    region = [180, 182, -32, -30]
    downloaded = slab2.load_earth_relief(region, tmp_path, download=True)
    assert calls == [dict(region=region, resolution='10m', registration='gridline')]
    assert downloaded.attrs['units'] == 'm'
    cached = slab2.load_earth_relief(region, tmp_path)
    np.testing.assert_array_equal(cached, downloaded)
    assert len(calls) == 1
