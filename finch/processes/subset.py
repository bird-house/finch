# noqa: D100
import logging
from pathlib import Path
from threading import Lock
from typing import List
from urllib.parse import urlparse

import geopandas as gpd
from clisops.core.average import average_shape
from clisops.core.subset import subset_bbox, subset_gridpoint, subset_shape, subset_time
from pywps import ComplexInput, Process
from pywps.app.exceptions import ProcessError

from . import wpsio
from .utils import (
    RequestInputs,
    dataset_to_netcdf,
    make_metalink_output,
    process_threaded,
    single_input_or_none,
    try_opendap,
    valid_filename,
    write_log,
)

LOGGER = logging.getLogger("PYWPS")


def make_subset_file_name(resource, kind="sub"):
    """Create output file name."""
    if resource.prop == "file":
        p = Path(resource.file)
    elif resource.prop == "url":
        # Inspired by logic from ComplexInput._build_file_name
        # but without the duplicate file name check as it inserts randomness in names
        # See #228
        url_path = urlparse(resource.url).path or ""
        p = Path(url_path) or Path(resource.identifier)
        if not p.suffix:
            p = p.with_suffix(resource.extension)
    else:
        raise NotImplementedError()

    return valid_filename(f"{p.stem}_{kind}{p.suffix}")


def finch_subset_gridpoint(
    process: Process, netcdf_inputs: List[ComplexInput], request_inputs: RequestInputs
) -> List[Path]:
    """Parse wps `request_inputs` based on their name and subset `netcdf_inputs`.

    The expected names of the inputs are as followed (taken from `wpsio.py`):
     - lat: Latitude coordinate, can be a comma separated list of floats
     - lon: Longitude coordinate, can be a comma separated list of floats
     - start_date: Initial date for temporal subsetting.
     - end_date: Final date for temporal subsetting.
    """
    lon_value = request_inputs[wpsio.lon.identifier][0].data
    try:
        longitudes = [float(lon) for lon in lon_value.split(",")]
    except AttributeError:
        longitudes = [float(lon_value)]

    lat_value = request_inputs[wpsio.lat.identifier][0].data
    try:
        latitudes = [float(lat) for lat in lat_value.split(",")]
    except AttributeError:
        latitudes = [float(lat_value)]

    start_date = single_input_or_none(request_inputs, wpsio.start_date.identifier)
    end_date = single_input_or_none(request_inputs, wpsio.end_date.identifier)
    variables = [r.data for r in request_inputs.get("variable", [])]

    n_files = len(netcdf_inputs)
    count = 0

    output_files = []

    lock = Lock()

    def _subset(resource: ComplexInput):
        nonlocal count

        # if not subsetting by time, it's not necessary to decode times
        time_subset = start_date is not None or end_date is not None
        # No chunking needed for a single gridpoint.
        dataset = try_opendap(resource, chunks=False, decode_times=time_subset)

        with lock:
            count += 1
            write_log(
                process,
                f"Subsetting file {count} of {n_files} ({getattr(resource, resource.prop)})",
                subtask_percentage=(count - 1) * 100 // n_files,
            )

        dataset = dataset[variables] if variables else dataset

        subsetted = subset_gridpoint(
            dataset,
            lon=longitudes,
            lat=latitudes,
            start_date=start_date,
            end_date=end_date,
        )

        if "site" in subsetted.dims:
            subsetted = subsetted.rename(site="region")
        else:
            subsetted = subsetted.expand_dims("region")

        if not all(subsetted.dims.values()):
            LOGGER.warning(f"Subset is empty for dataset: {resource.url}")
            return

        p = make_subset_file_name(resource)
        output_filename = Path(process.workdir) / p

        dataset_to_netcdf(subsetted, output_filename)

        output_files.append(output_filename)

    process_threaded(_subset, netcdf_inputs)

    return output_files


def finch_subset_bbox(
    process: Process, netcdf_inputs: List[ComplexInput], request_inputs: RequestInputs
) -> List[Path]:
    """Parse wps `request_inputs` based on their name and subset `netcdf_inputs`.

    The expected names of the request_inputs are as followed (taken from `wpsio.py`):
     - lat0: Latitude coordinate
     - lon0: Longitude coordinate
     - lat1: Latitude coordinate
     - lon1: Longitude coordinate
     - start_date: Initial date for temporal subsetting.
     - end_date: Final date for temporal subsetting.
    """
    lon0 = single_input_or_none(request_inputs, wpsio.lon0.identifier)
    lat0 = single_input_or_none(request_inputs, wpsio.lat0.identifier)
    lon1 = single_input_or_none(request_inputs, wpsio.lon1.identifier)
    lat1 = single_input_or_none(request_inputs, wpsio.lat1.identifier)
    start_date = single_input_or_none(request_inputs, wpsio.start_date.identifier)
    end_date = single_input_or_none(request_inputs, wpsio.end_date.identifier)
    variables = [r.data for r in request_inputs.get("variable", [])]

    nones = [lat1 is None, lon1 is None]
    if any(nones) and not all(nones):
        raise ProcessError("lat1 and lon1 must be both omitted or provided")

    n_files = len(netcdf_inputs)
    count = 0

    output_files = []

    lock = Lock()

    def _subset(resource):
        nonlocal count

        # if not subsetting by time, it's not necessary to decode times
        time_subset = start_date is not None or end_date is not None
        dataset = try_opendap(resource, decode_times=time_subset)

        with lock:
            count += 1
            write_log(
                process,
                f"Subsetting file {count} of {n_files} ({getattr(resource, resource.prop)})",
                subtask_percentage=(count - 1) * 100 // n_files,
            )

        dataset = dataset[variables] if variables else dataset

        try:
            subsetted = subset_bbox(
                dataset,
                lon_bnds=[lon0, lon1],
                lat_bnds=[lat0, lat1],
                start_date=start_date,
                end_date=end_date,
            )
        except ValueError:
            subsetted = False

        if subsetted is False or not all(subsetted.dims.values()):
            LOGGER.warning(f"Subset is empty for dataset: {resource.url}")
            return

        p = make_subset_file_name(resource)
        output_filename = Path(process.workdir) / p

        dataset_to_netcdf(subsetted, output_filename)

        output_files.append(output_filename)

    process_threaded(_subset, netcdf_inputs)

    return output_files


def extract_shp(path):
    """Return a geopandas-compatible path to the shapefile stored in a zip archive.

    If multiple shapefiles are included, return only the first one found.

    Parameters
    ----------
    path : Path
      Path to zip archive holding shapefile.

    Returns
    -------
    str
      zip:///<path to zip file>!<relative path to shapefile>
    """
    from zipfile import ZipFile

    z = ZipFile(path)

    fn = next(filter(lambda x: x.endswith(".shp"), z.namelist()))
    z.close()

    return f"zip://{path.absolute()}!{fn}"


def finch_average_shape(
    process: Process,
    netcdf_inputs: List[ComplexInput],
    request_inputs: RequestInputs,
) -> List[Path]:
    """Parse wps `request_inputs` based on their name and average `netcdf_inputs`.

    The expected names of the request_inputs are as followed (taken from `wpsio.py`):
     - shape: Polygon contour to average the data over.
     - start_date: Initial date for temporal subsetting.
     - end_date: Final date for temporal subsetting.
    """
    shp = Path(request_inputs[wpsio.shape.identifier][0].file)
    if shp.suffix == ".zip":
        shp = extract_shp(shp)

    start_date = single_input_or_none(request_inputs, wpsio.start_date.identifier)
    end_date = single_input_or_none(request_inputs, wpsio.end_date.identifier)
    tolerance = single_input_or_none(request_inputs, wpsio.tolerance.identifier)
    variables = [r.data for r in request_inputs.get("variable", [])]

    shape = gpd.read_file(shp)
    if tolerance > 0:
        shape["geometry"] = shape.simplify(tolerance)

    n_files = len(netcdf_inputs)
    count = 0

    output_files = []

    for resource in netcdf_inputs:
        # if not subsetting by time, it's not necessary to decode times
        time_subset = start_date is not None or end_date is not None
        dataset = try_opendap(
            resource, decode_times=time_subset, chunk_dims=["time", "realization"]
        )

        count += 1
        write_log(
            process,
            f"Averaging file {count} of {n_files} ({getattr(resource, resource.prop)})",
            subtask_percentage=(count - 1) * 100 // n_files,
        )

        dataset = dataset[variables] if variables else dataset

        if time_subset:
            dataset = subset_time(dataset, start_date=start_date, end_date=end_date)
        averaged = average_shape(dataset, shape)

        if not all(averaged.dims.values()):
            LOGGER.warning(f"Average is empty for dataset: {resource.url}")
            return

        p = make_subset_file_name(resource, kind="avg")
        output_filename = Path(process.workdir) / p

        dataset_to_netcdf(averaged, output_filename)

        output_files.append(output_filename)

    return output_files


def finch_subset_shape(
    process: Process,
    netcdf_inputs: List[ComplexInput],
    request_inputs: RequestInputs,
) -> List[Path]:
    """Parse wps `request_inputs` based on their name and subset `netcdf_inputs`.

    The expected names of the request_inputs are as followed (taken from `wpsio.py`):
     - shape: Polygon contour to subset the data with.
     - start_date: Initial date for temporal subsetting.
     - end_date: Final date for temporal subsetting.
    """
    shp = Path(request_inputs[wpsio.shape.identifier][0].file)
    if shp.suffix == ".zip":
        shp = extract_shp(shp)

    start_date = single_input_or_none(request_inputs, wpsio.start_date.identifier)
    end_date = single_input_or_none(request_inputs, wpsio.end_date.identifier)
    variables = [r.data for r in request_inputs.get("variable", [])]

    n_files = len(netcdf_inputs)
    count = 0

    output_files = []

    lock = Lock()

    def _subset(resource):
        nonlocal count

        # if not subsetting by time, it's not necessary to decode times
        time_subset = start_date is not None or end_date is not None
        dataset = try_opendap(resource, decode_times=time_subset)

        with lock:
            count += 1
            write_log(
                process,
                f"Subsetting file {count} of {n_files} ({getattr(resource, resource.prop)})",
                subtask_percentage=(count - 1) * 100 // n_files,
            )

        dataset = dataset[variables] if variables else dataset

        subsetted = subset_shape(
            dataset,
            shape=shp,
            start_date=start_date,
            end_date=end_date,
        )

        if not all(subsetted.dims.values()):
            LOGGER.warning(f"Subset is empty for dataset: {resource.url}")
            return

        p = make_subset_file_name(resource)
        output_filename = Path(process.workdir) / p

        dataset_to_netcdf(subsetted, output_filename)

        output_files.append(output_filename)

    process_threaded(_subset, netcdf_inputs)

    return output_files


def common_subset_handler(
    process: Process, request, response, subset_function
):  # noqa: D103
    assert subset_function in [
        finch_subset_bbox,
        finch_subset_gridpoint,
        finch_subset_shape,
        finch_average_shape,
    ]

    write_log(process, "Processing started", process_step="start")

    output_files = subset_function(
        process,
        netcdf_inputs=request.inputs["resource"],
        request_inputs=request.inputs,
    )
    metalink = make_metalink_output(process, output_files)

    response.outputs["output"].file = metalink.files[0].file
    response.outputs["ref"].data = metalink.xml

    write_log(process, "Processing finished successfully", process_step="done")

    return response
