"""Download published Slab2 grids from the USGS ShakeMap data directory.

Data citation: Hayes (2018), https://doi.org/10.5066/F7PV6JNV.
Grid filenames retain the date provided by USGS. No GMT installation is needed
for downloading; grid loading and plotting are separate operations.
"""

import json
import math
import os
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.client import HTTPException
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

USGS_SLAB2_URL = 'https://apps.usgs.gov/shakemap_geodata/slabs/'
_FIELD_CODES = {'depth': 'dep', 'dip': 'dip', 'strike': 'str', 'uncertainty': 'unc'}


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.names = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for key, value in attrs:
                if key == 'href' and value:
                    self.names.add(value)


def _request(url):
    return Request(url, headers={'User-Agent': 'gdmate-slab2/0.1'})


def _is_grid(path):
    with path.open('rb') as stream:
        header = stream.read(8)
    return (header[:4] in (b'CDF\x01', b'CDF\x02', b'CDF\x05')
            or header == b'\x89HDF\r\n\x1a\n')


def _download(url, destination, timeout):
    temporary = None
    try:
        with urlopen(_request(url), timeout=timeout) as response:
            expected = response.headers.get('Content-Length')
            with NamedTemporaryFile(dir=destination.parent, suffix='.part',
                                    delete=False) as stream:
                temporary = Path(stream.name)
                size = 0
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    size += stream.write(block)
            if expected is not None and size != int(expected):
                raise ValueError(
                    f'incomplete response: expected {expected} bytes, got {size}'
                )
            if not _is_grid(temporary):
                raise ValueError('response is not a NetCDF/HDF5 grid')
        os.replace(temporary, destination)
    except (OSError, ValueError, HTTPException) as error:
        raise RuntimeError(f'Could not download USGS grid {url}: {error}') from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def download_slab2(region, data_dir, *, fields=('depth', 'dip'),
                   overwrite=False, timeout=30):
    """Download Slab2 grids for a three-letter region, e.g. ``'ker'``.

    Parameters
    ----------
    region : str
        USGS region code, e.g. ``'ker'`` (Kermadec) or ``'cas'`` (Cascadia).
    data_dir : str or pathlib.Path
        Local cache directory. Downloads keep their original dated filenames.
    fields : sequence of str
        Any of ``depth``, ``dip``, ``strike``, ``uncertainty``.
    overwrite : bool
        If false, reuse cached grids without network access. If true, download
        again. A failed download preserves any existing destination file.
    timeout : float
        Positive network timeout in seconds for each blocking operation.

    Returns
    -------
    list of dict
        Each record contains ``field``, ``path`` (Path), ``url``, ``size_bytes``
        and ``cached``. Print or retain these records for source provenance.

    Notes
    -----
    Missing grids are located through the official USGS directory listing;
    dates are not guessed. Multiple matching versions raise ValueError rather
    than choosing silently. Cached files and new responses are checked for
    NetCDF/HDF5 signatures; this does not replace full scientific validation.
    Files are published atomically, so interrupted downloads are not cached.
    RuntimeError reports download failures; ValueError reports invalid options
    or unavailable/ambiguous filenames. A multi-file request may leave earlier
    successful downloads cached if a later file fails.
    """
    if not isinstance(region, str) or re.fullmatch(r'[a-z]{3}', region) is None:
        raise ValueError('region must be a three-letter lowercase USGS code')
    if isinstance(fields, str):
        raise ValueError('fields must be a sequence of field names, not a string')
    fields = tuple(dict.fromkeys(fields))
    if not fields or any(field not in _FIELD_CODES for field in fields):
        raise ValueError(f'fields must be selected from {tuple(_FIELD_CODES)}')
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    data_dir = Path(data_dir).expanduser().resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    listing = None
    records = []
    for field in fields:
        pattern = re.compile(
            rf'{region}_slab2_{_FIELD_CODES[field]}_\d{{2}}\.\d{{2}}\.\d{{2}}\.grd'
        )
        cached = sorted(path for path in data_dir.iterdir()
                        if path.is_file() and pattern.fullmatch(path.name))
        if len(cached) > 1 and not overwrite:
            raise ValueError(
                f'Multiple cached versions for {region}/{field} in {data_dir}'
            )
        if not overwrite and cached and _is_grid(cached[0]):
            path, reused = cached[0], True
        else:
            if listing is None:
                listing = _read_listing(timeout)
            matches = sorted(name for name in listing if pattern.fullmatch(name))
            if not matches:
                raise ValueError(
                    f'No USGS grid for {region}/{field} at {USGS_SLAB2_URL}'
                )
            if len(matches) > 1:
                raise ValueError(
                    f'Multiple USGS versions for {region}/{field}: {matches}'
                )
            path, reused = data_dir / matches[0], False
            _download(USGS_SLAB2_URL + path.name, path, timeout)
        records.append(dict(field=field, path=path, url=USGS_SLAB2_URL + path.name,
                            size_bytes=path.stat().st_size, cached=reused))
    return records


def load_slab2_depth(grid_file):
    """Load a native USGS depth grid as positive-down depth in kilometres.

    Requires xarray and h5netcdf (see environment-pygmt.yml). Native Slab2
    depth values are negative kilometres below sea level. Coordinates and
    missing values are preserved. Nodes above sea level have positive native
    elevations and therefore negative depth; these remain signed, not clipped.
    Rejects empty/all-missing grids.
    """
    grid_file = Path(grid_file)
    if not grid_file.is_file():
        raise FileNotFoundError(grid_file)
    import numpy as np
    import xarray as xr

    with xr.open_dataarray(grid_file, engine='h5netcdf') as source:
        grid = source.load()
    if grid.ndim != 2 or any(size < 2 for size in grid.shape):
        raise ValueError('Slab2 depth must be a 2-D grid with at least 2x2 nodes')
    finite = grid.values[np.isfinite(grid.values)]
    if not finite.size:
        raise ValueError('Expected at least one finite native Slab2 depth')
    depth = -grid
    depth.name = 'slab_surface_depth'
    depth.attrs = dict(grid.attrs, units='km', positive='down',
                       long_name='Slab surface depth')
    return depth


def plot_slab2_depth(grid_file, *, region=None, projection='M15c',
                     contour_interval=100, annotation_interval=200, cmap='batlow',
                     seafloor_age=None, age_max=180):
    """Return a PyGMT slab-depth map with coastline, contours and colour bar.

    ``grid_file`` is a downloaded native USGS depth grid. ``region`` is
    [west, east, south, north] in degrees, or None to use the grid extent.
    Keep the longitude convention of the input grid when specifying bounds.
    Contour and annotation intervals are positive kilometres; depth is shown
    positive downward. PyGMT/GMT/Ghostscript are optional dependencies supplied
    by environment-pygmt.yml. Save the returned Figure with ``savefig``.
    Optional ``seafloor_age`` is a geographic DataArray in Myr, drawn underneath
    the slab with its own grayscale colour bar (young white, old black).
    ``age_max`` sets that colour scale's upper limit in Myr; older ages saturate.
    """
    for interval in (contour_interval, annotation_interval):
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError('Contour and annotation intervals must be positive')
    if not math.isfinite(age_max) or age_max <= 0:
        raise ValueError('age_max must be finite and positive')
    depth = load_slab2_depth(grid_file)
    import pygmt

    if region is None:
        y, x = depth.dims
        region = [float(depth[x].min()), float(depth[x].max()),
                  float(depth[y].min()), float(depth[y].max())]
    figure = pygmt.Figure()
    if seafloor_age is not None:
        _plot_seafloor_age(
            figure, seafloor_age, region, projection, age_max,
            frame=['af', '+tSlab2 depth and seafloor age'],
        )
    maximum = max(contour_interval, math.ceil(float(depth.max()) / contour_interval)
                  * contour_interval)
    pygmt.makecpt(cmap=cmap, series=[0, maximum, contour_interval], continuous=True)
    figure.grdimage(grid=depth, region=region, projection=projection,
                    cmap=True, nan_transparent=True,
                    frame=['af', '+tSlab2 surface depth']
                    if seafloor_age is None else None)
    figure.grdcontour(grid=depth, levels=contour_interval,
                      annotation=annotation_interval, pen='0.5p,gray30')
    figure.coast(shorelines='0.6p,black', resolution='i')
    if seafloor_age is None:
        figure.colorbar(frame=['x+lSlab surface depth', 'y+lkm'])
    else:
        figure.colorbar(position='JBC+w6c/0.25c+h+o0c/1.0c',
                        frame=['x+lSlab surface depth', 'y+lkm'])
    return figure



def load_seafloor_age(region, data_dir, *, resolution='10m', download=False):
    """Load a local snapshot of GMT's EarthByte seafloor-age grid in Myr.

    ``region`` is [west, east, south, north] in degrees. The snapshot filename
    includes bounds, resolution and gridline registration to avoid reusing a
    different region. Set ``download=True`` to permit a missing snapshot to be
    fetched through PyGMT (which also caches the original GMT dataset under
    ~/.gmt/server). Existing local snapshots are reused without network access.
    Requires the optional PyGMT environment for downloading, and xarray/h5netcdf
    for loading. Dataset reference: Seton et al. (2020),
    https://doi.org/10.1029/2020GC009214. This may differ from older age models
    used in published figures. Source and retrieval metadata are saved in the
    local NetCDF snapshot; remote GMT datasets can change over time.
    """
    return _load_earth_snapshot('age', region, data_dir, resolution, download)



def _read_listing(timeout):
    try:
        with urlopen(_request(USGS_SLAB2_URL), timeout=timeout) as response:
            parser = _Links()
            parser.feed(response.read().decode('utf-8'))
            return parser.names
    except (OSError, ValueError, HTTPException) as error:
        raise RuntimeError(
            f'Could not read USGS listing {USGS_SLAB2_URL}: {error}'
        ) from error


def list_slab2_regions(*, field='depth', timeout=30):
    """Discover sorted region codes with the requested grid in the USGS listing.

    Requires network access. ``field`` uses the same names as download_slab2.
    Only complete dated grid filenames in the official directory are accepted.
    Availability refers to that directory, not every format in the data release.
    """
    if field not in _FIELD_CODES:
        raise ValueError(f'field must be selected from {tuple(_FIELD_CODES)}')
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    pattern = re.compile(
        rf'([a-z]{{3}})_slab2_{_FIELD_CODES[field]}_\d{{2}}\.\d{{2}}\.\d{{2}}\.grd'
    )
    regions = sorted({match.group(1) for name in _read_listing(timeout)
                      if (match := pattern.fullmatch(name))})
    if not regions:
        raise ValueError(f'No USGS {field} grids found at {USGS_SLAB2_URL}')
    return regions


def plot_slab2_global(grid_files, *, central_longitude=180, latitude_bounds=(-65, 65),
                      projection_width='24c', cmap='batlow',
                      seafloor_age=None, age_max=180, relief=None,
                      relief_shading=True, shorelines=False,
                      plate_boundaries=None, boundary_pen='0.6p,black'):
    """Return a global PyGMT map of native Slab2 depth grids on one colour scale.

    Longitudes are handled by GMT's geographic projection, including grids
    supplied in either -180..180 or 0..360 coordinates. The default equidistant
    cylindrical map is Pacific-centred, spanning 0..360 degrees and +/-65
    latitude. Depth is positive-down km. Each grid is drawn independently with
    transparent missing values; grids are not merged or resampled by this helper.
    For overlapping grids the later entry is drawn on top. Optional
    ``seafloor_age`` is a geographic DataArray in Myr, drawn underneath with a
    separate grayscale colour bar from 0 to ``age_max`` Myr (default 180).
    Optional ``relief`` is a geographic elevation DataArray in metres, drawn
    below the age/slab layers. Relief-derived illumination shades relief when
    ``relief_shading`` is true. Age overprints relief without illumination wherever
    age data are present. Shoreline outlines default to off;
    set ``shorelines=True`` to restore them. Optional ``plate_boundaries``
    is a PB2002 GeoJSON FeatureCollection drawn on top with ``boundary_pen``.
    """
    files = list(grid_files)
    if not files:
        raise ValueError('Provide at least one Slab2 depth grid')
    if (not math.isfinite(central_longitude) or len(latitude_bounds) != 2
            or not all(math.isfinite(value) for value in latitude_bounds)
            or not -90 <= latitude_bounds[0] < latitude_bounds[1] <= 90):
        raise ValueError('Map centre and latitude bounds must be finite and valid')
    if not math.isfinite(age_max) or age_max <= 0:
        raise ValueError('age_max must be finite and positive')
    grids = [load_slab2_depth(path) for path in files]
    maximum = max(100, math.ceil(max(float(grid.max()) for grid in grids)/100)*100)
    import pygmt

    region = [central_longitude - 180, central_longitude + 180, *latitude_bounds]
    projection = f'Q{central_longitude}/{projection_width}'
    figure = pygmt.Figure()
    title = ('Global Slab2 surface depth' if seafloor_age is None
             else 'Global Slab2 depth and seafloor age')
    figure.basemap(region=region, projection=projection,
                   frame=['xa60f30', 'ya30f15', f'+t{title}'])
    intensity = None
    if relief is not None:
        relief = relief.copy()
        relief.encoding.pop('source', None)
        relief.gmt.registration = 0
        relief.gmt.gtype = 1
        if relief_shading:
            intensity = pygmt.grdgradient(relief, azimuth=315, normalize='t0.5')
        pygmt.makecpt(cmap='gray', series=[-8000, 8000, 1000], continuous=True)
        figure.grdimage(grid=relief, cmap=True, shading=intensity)
    if seafloor_age is not None:
        age_intensity = None
        if intensity is not None:
            # Match the age grid even when its chosen resolution differs.
            age_intensity = _grid_on_nodes(intensity, seafloor_age)
            # Age overprints ocean relief; retain terrain shading only in gaps.
            age_intensity = age_intensity.where(seafloor_age.isnull(), 0)
            age_intensity.gmt.registration = 0
            age_intensity.gmt.gtype = 1
        _plot_seafloor_age(
            figure, seafloor_age, region, projection, age_max,
            colorbar_position='JBC+w12c/0.35c+h+o0c/2.7c',
            shading=age_intensity, relief=relief,
        )
    pygmt.makecpt(cmap=cmap, series=[0, maximum, 100],
                  continuous=True, background=True)
    for grid in grids:
        grid.gmt.registration = 0
        grid.gmt.gtype = 1
        figure.grdimage(grid=grid, cmap=True, nan_transparent=True)
    if shorelines:
        figure.coast(shorelines='0.4p,black', resolution='l')
    if plate_boundaries is not None:
        from gdmate.plate_boundaries import plate_boundary_segments

        for segment in plate_boundary_segments(plate_boundaries):
            figure.plot(data=segment, pen=boundary_pen)
    figure.colorbar(position='JBC+w12c/0.35c+h+o0c/1.2c',
                    frame=['xa100f50+lSlab surface depth', 'y+lkm'])
    return figure



def _plot_seafloor_age(figure, seafloor_age, region, projection, age_max, *,
                        frame=None, colorbar_position='JBC+w6c/0.25c+h+o0c/2.6c',
                        shading=None, relief=None):
    """Draw the shared age layer with a white missing-data background."""
    import pygmt

    if seafloor_age.attrs.get('gmt_dataset', '').endswith('_g'):
        # Snapshots explicitly use geographic, gridline-registered nodes.
        seafloor_age = seafloor_age.copy()
        seafloor_age.encoding.pop('source', None)
        seafloor_age.gmt.registration = 0
        seafloor_age.gmt.gtype = 1
    with pygmt.config(COLOR_NAN='white'):
        if relief is None:
            pygmt.makecpt(cmap='gray', reverse=True,
                          series=[0, age_max, age_max / 9],
                          continuous=True, background=True)
            figure.grdimage(grid=seafloor_age, region=region, projection=projection,
                            cmap=True, frame=frame, shading=shading)
        else:
            # One grayscale raster avoids stacked NaN-mask artefacts in exports.
            terrain_gray = (_grid_on_nodes(relief, seafloor_age).clip(-8000, 8000)
                            + 8000) / 16000
            age_gray = 1 - seafloor_age.clip(0, age_max) / age_max
            background = age_gray.where(seafloor_age.notnull(), terrain_gray)
            background.gmt.registration = 0
            background.gmt.gtype = 1
            pygmt.makecpt(cmap='gray', series=[0, 1, 0.1], continuous=True)
            figure.grdimage(grid=background, region=region, projection=projection,
                            cmap=True, frame=frame, shading=shading)
            # The colour bar describes age, not the normalised background raster.
            pygmt.makecpt(cmap='gray', reverse=True,
                          series=[0, age_max, age_max / 9],
                          continuous=True, background=True)
    figure.colorbar(position=colorbar_position,
                    frame=['xa60f20+lSeafloor age', 'y+lMa'])



def load_earth_relief(region, data_dir, *, resolution='10m', download=False):
    """Load a cached GMT IGPP topography/bathymetry snapshot in metres.

    Uses the same bounds, coarse resolution choices and explicit download
    opt-in as load_seafloor_age. Positive elevations are above sea level;
    negative elevations are bathymetry. GMT's source cache and the local NetCDF
    snapshot retain the downloaded data for later offline use. Source title,
    URL, resolution, bounds and retrieval time are recorded in the snapshot.
    """
    return _load_earth_snapshot('relief', region, data_dir, resolution, download)


def _load_earth_snapshot(kind, region, data_dir, resolution, download):
    """Share validation and atomic snapshot caching for GMT Earth datasets."""
    bounds = tuple(float(value) for value in region)
    if (len(bounds) != 4 or not all(math.isfinite(value) for value in bounds)
            or not 0 < bounds[1] - bounds[0] <= 360
            or not -90 <= bounds[2] < bounds[3] <= 90):
        raise ValueError('region must contain finite ordered geographic bounds')
    resolutions = ('01d', '30m', '20m', '15m', '10m', '06m', '05m',
                   '04m', '03m', '02m', '01m')
    if resolution not in resolutions:
        raise ValueError(f'resolution must be selected from {resolutions}')
    key = '_'.join(str(value) for value in bounds)
    path = (Path(data_dir).expanduser().resolve()
            / f'earth_{kind}_{resolution}_g_{key}.nc')
    if path.is_file():
        import xarray as xr

        with xr.open_dataarray(path, engine='h5netcdf') as source:
            return source.load()
    if not download:
        raise FileNotFoundError(f'{path}: set download=True to fetch Earth {kind}')
    import pygmt

    loader = getattr(pygmt.datasets, f'load_earth_{kind}')
    grid = loader(
        region=list(bounds), resolution=resolution, registration='gridline')
    grid.attrs.update(
        units='Myr' if kind == 'age' else 'm',
        source=f'https://www.generic-mapping-tools.org/remote-datasets/earth-{kind}.html',
        citation=('Seton et al. (2020), https://doi.org/10.1029/2020GC009214'
                  if kind == 'age' else grid.attrs.get('title', 'IGPP Earth Relief')),
        gmt_dataset=f'@earth_{kind}_{resolution}_g',
        requested_region=json.dumps(bounds),
        downloaded_utc=datetime.now(timezone.utc).isoformat(),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, suffix='.nc', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        grid.to_netcdf(temporary, engine='h5netcdf')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return grid



def _grid_on_nodes(grid, reference):
    """Interpolate a geographic grid to reference coordinates and dimension names."""
    y, x = grid.dims
    ay, ax = reference.dims
    result = grid.interp({y: reference[ay].values, x: reference[ax].values})
    names = {old: new for old, new in ((y, ay), (x, ax)) if old != new}
    if names:
        result = result.rename(names)
    result.gmt.registration = 0
    result.gmt.gtype = 1
    return result
