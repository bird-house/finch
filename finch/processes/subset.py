import logging
from pathlib import Path
from typing import List
from threading import Lock

from pywps import Process, ComplexInput
from pywps.app.exceptions import ProcessError
from xclim.subset import subset_gridpoint, subset_bbox
import xarray as xr

from finch.processes.utils import (
    RequestInputs,
    single_input_or_none,
    try_opendap,
    process_threaded,
    write_log,
)

LOGGER = logging.getLogger("PYWPS")


def finch_subset_gridpoint(process: Process, inputs: RequestInputs) -> List[Path]:
    """Parse wps inputs based on their name and execute the correct subset function.
    
    The expected names of the inputs are as followed (taken from `wpsio.py`):
     - resource: ComplexInput files to subset.
     - lat: Latitude coordinate, can be a comma separated list of floats
     - lon: Longitude coordinate, can be a comma separated list of floats
     - start_date: Initial date for temporal subsetting.
     - end_date: Final date for temporal subsetting.
    """

    lon_value = inputs["lon"][0].data
    try:
        longitudes = [float(l) for l in lon_value.split(",")]
    except AttributeError:
        longitudes = [float(lon_value)]

    lat_value = inputs["lat"][0].data
    try:
        latitudes = [float(l) for l in lat_value.split(",")]
    except AttributeError:
        latitudes = [float(lat_value)]

    start_date = single_input_or_none(inputs, "start_date")
    end_date = single_input_or_none(inputs, "end_date")
    variables = [r.data for r in inputs.get("variable", [])]

    n_files = len(inputs["resource"])
    count = 0

    output_files = []

    lock = Lock()

    def _subset(resource: ComplexInput):
        nonlocal count

        # if not subsetting by time, it's not necessary to decode times
        time_subset = start_date is not None or end_date is not None
        dataset = try_opendap(resource, decode_times=time_subset)

        with lock:
            count += 1
            write_log(
                process,
                f"Subsetting file {count} of {n_files}",
                subtask_percentage=(count - 1) * 100 // n_files,
            )

        dataset = dataset[variables] if variables else dataset

        subsets = []
        for longitude, latitude in zip(longitudes, latitudes):
            subset = subset_gridpoint(
                dataset,
                lon=longitude,
                lat=latitude,
                start_date=start_date,
                end_date=end_date,
            )
            subsets.append(subset)

        subsetted = xr.concat(subsets, dim="region")

        if not all(subsetted.dims.values()):
            LOGGER.warning(f"Subset is empty for dataset: {resource.url}")
            return

        p = Path(resource._file or resource._build_file_name(resource.url))
        output_filename = Path(process.workdir) / (p.stem + "_sub" + p.suffix)

        subsetted.to_netcdf(output_filename)

        output_files.append(output_filename)

    process_threaded(_subset, inputs["resource"])

    return output_files


def finch_subset_bbox(process: Process, inputs: RequestInputs) -> List[Path]:
    """Parse wps inputs based on their name and execute the correct subset function.
    
    The expected names of the inputs are as followed (taken from `wpsio.py`):
     - resource: ComplexInput files to subset.
     - lat0: Latitude coordinate
     - lon0: Longitude coordinate
     - lat1: Latitude coordinate
     - lon1: Longitude coordinate
     - start_date: Initial date for temporal subsetting.
     - end_date: Final date for temporal subsetting.
    """
    lon0 = single_input_or_none(inputs, "lon0")
    lat0 = single_input_or_none(inputs, "lat0")
    lon1 = single_input_or_none(inputs, "lon1")
    lat1 = single_input_or_none(inputs, "lat1")
    start_date = single_input_or_none(inputs, "start_date")
    end_date = single_input_or_none(inputs, "end_date")
    variables = [r.data for r in inputs.get("variable", [])]

    nones = [lat1 is None, lon1 is None]
    if any(nones) and not all(nones):
        raise ProcessError("lat1 and lon1 must be both omitted or provided")

    n_files = len(inputs["resource"])
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
                f"Subsetting file {count} of {n_files}",
                subtask_percentage=(count - 1) * 100 // n_files,
            )

        dataset = dataset[variables] if variables else dataset

        subsetted = subset_bbox(
            dataset,
            lon_bnds=[lon0, lon1],
            lat_bnds=[lat0, lat1],
            start_date=start_date,
            end_date=end_date,
        )

        if not all(subsetted.dims.values()):
            LOGGER.warning(f"Subset is empty for dataset: {resource.url}")
            return

        p = Path(resource._file or resource._build_file_name(resource.url))
        output_filename = Path(process.workdir) / (p.stem + "_sub" + p.suffix)

        subsetted.to_netcdf(output_filename)

        output_files.append(output_filename)

    process_threaded(_subset, inputs["resource"])

    return output_files
