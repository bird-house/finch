# noqa: D100
import logging
from pathlib import Path
from urllib.parse import urlparse

import cf_xarray.geometry as cfgeo
import geopandas as gpd
import numpy as np
import xarray as xr
from pywps import FORMATS, ComplexInput, ComplexOutput, LiteralInput

from . import wpsio
from .utils import (
    dataset_to_netcdf,
    log_file_path,
    single_input_or_none,
    update_history,
    valid_filename,
    write_log,
)
from .wps_base import FinchProcess

LOGGER = logging.getLogger("PYWPS")


class GeoseriesToNetcdfProcess(FinchProcess):
    """Convert a geospatial series to a CF-compliant netCDF."""

    def __init__(self):
        inputs = [
            ComplexInput(
                "resource",
                "Geospatial series",
                abstract="Series of geographical features, or an url which requests such a series (ex: OGC-API)",
                supported_formats=[FORMATS.GEOJSON],
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                "index_dim",
                "Index dimension",
                abstract="Name of the column in the data to be converted into the index dimension.",
                data_type="string",
                min_occurs=1,
                max_occurs=1,
            ),
            LiteralInput(
                "feat_dim",
                "Feature dimension",
                abstract=(
                    "Name of a column in the data to be used as the coordinate and of "
                    " the 'feature' dimension. Each geometry must be different along and only along this dimension."
                ),
                data_type="string",
                default="",
                min_occurs=0,
                max_occurs=1,
            ),
            LiteralInput(
                "squeeze",
                "Squeeze variables",
                abstract="Squeeze variables that are replicated along one of the dimensions.",
                data_type="boolean",
                default=False,
                min_occurs=0,
                max_occurs=1,
            ),
            # LiteralInput(
            #     "grid_mapping",
            #     "Grid mapping",
            #     abstract="Name of the grid mapping of the data, only longitude_latitude supported.",
            #     data_type="string",
            #     default="longitude_latitude",
            #     min_occurs=0,
            #     max_occurs=1,
            # ),
            wpsio.output_name,
        ]

        outputs = [
            ComplexOutput(
                "output",
                "Geospatial series as netCDF",
                abstract="The geospatial series as a 2 dimension netCDF.",
                as_reference=True,
                supported_formats=[FORMATS.NETCDF],
            ),
            wpsio.output_log,
        ]

        super().__init__(
            self._handler,
            identifier="geoseries_to_netcdf",
            version="0.1",
            title="Convert a geospatial series to a CF-compliant netCDF.",
            abstract=(
                "Reshapes a geospatial series with a features dimensions and "
                "converts into the netCDf format, following CF convetions."
            ),
            inputs=inputs,
            outputs=outputs,
            status_supported=True,
            store_supported=True,
        )

        self.status_percentage_steps = {
            "start": 5,
            "downloaded": 25,
            "converted": 75,
            "done": 99,
        }

    def _handler(self, request, response):
        write_log(self, "Processing started", process_step="start")

        # --- Process inputs ---
        geo_url = request.inputs["resource"][0].url
        index_dim = request.inputs["index_dim"][0].data
        feat_dim = request.inputs["feat_dim"][0].data
        squeeze = request.inputs["squeeze"][0].data
        grid_map = "longitude_latitude"  # request.inputs['grid_mapping'][0].data

        # Open URL
        gdf = gpd.read_file(geo_url)
        write_log(self, "Geoseries downloaded", process_step="downloaded")

        # Try casting all columns
        gdf = _maybe_cast(gdf)

        # Set index and convert to xr
        ds = gdf.set_index(index_dim).to_xarray()

        # FIXME: This is a workaround for changes to behaviour in pandas v2.0.0
        # Convert datetime64[xyz] coordinates to np.datetime64[ns]
        # Needed to correct the LOCAL_DATE encoding
        if ds[index_dim].dtype.kind == "M":
            ds[index_dim] = ds[index_dim].astype(np.datetime64)

        # Reshape geometries
        ds = cfgeo.reshape_unique_geometries(ds)

        # Convert shapely objects to CF-style
        coords = cfgeo.shapely_to_cf(ds.geometry, grid_mapping=grid_map)
        if coords.features.size == coords.node.size:
            # Then it's only single points, we can drop 'node'
            coords = coords.drop_dims("node")

        ds = xr.merge([ds.drop_vars("geometry"), coords])

        # feat dim
        if feat_dim:
            feat = _maybe_squeeze(ds[feat_dim], index_dim)
            if feat.ndim == 2:
                raise ValueError(
                    "'feat_dim' was given but it cannot be squeezed along the index dimension."
                )
            ds[feat_dim] = feat
            ds = ds.drop_vars("features").rename(features=feat_dim).set_coords(feat_dim)

        # squeeze
        if squeeze:
            for dim in [feat_dim, index_dim]:
                for name, var in ds.data_vars.items():
                    if dim in var.dims:
                        try:
                            ds[name] = _maybe_squeeze(var, dim)
                        except KeyError:
                            print(ds)
                            raise

        write_log(self, "Geoseries converted to CF dataset", process_step="converted")

        host = urlparse(geo_url).netloc
        if host is None:
            source = "geospatial series data"
        else:
            source = f"data downloaded from {host}"
        ds.attrs["history"] = update_history(
            f"Converted {source} to a CF-compliant Dataset.", ds
        )

        # Write to disk
        filename = valid_filename(
            single_input_or_none(request.inputs, "output_name") or "geoseries"
        )
        output_file = Path(self.workdir) / f"{filename}.nc"
        dataset_to_netcdf(ds, output_file)

        # Fill response
        response.outputs["output"].file = str(output_file)
        response.outputs["output_log"].file = str(log_file_path(self))


def _maybe_cast(dataframe):
    """Try to cast string columns to common dtypes."""
    for col in dataframe.columns:
        # Only cast string columns
        if isinstance(dataframe[col][0], str):
            for dtype in ["datetime64[ns]", "int", "float"]:
                try:
                    dataframe[col] = dataframe[col].astype(dtype)
                    break
                except ValueError:
                    pass
    return dataframe


def _maybe_squeeze(da, dim):
    if da.dtype == object:
        # we can't use the fill method to handle NaNs, unsuported for objects
        # we assume we are handling strings, with "" or np.NaN as invalid objects.
        can_squeeze = np.apply_along_axis(
            lambda arr: len(set(np.unique(arr)) - {""}) == 1,
            da.get_axis_num(dim),
            da.fillna("").values,
        ).all()
        if can_squeeze:
            return da.max(dim)
        return da

    # else : int, float or datetime
    da_filled = da.ffill(dim).bfill(dim)
    if (da_filled.isel({dim: 0}) == da_filled).all():
        return da_filled.isel({dim: 0}, drop=True)
    return da
