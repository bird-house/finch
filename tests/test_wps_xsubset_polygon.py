import geojson
import xarray as xr

from _utils import execute_process, shapefile_zip, wps_input_file, wps_literal_input

poly = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[0.5, 0], [2.5, 0], [2.5, 2.5], [0.5, 2.5], [0.5, 0]]],
    },
}


def test_wps_subsetpoly(client, netcdf_datasets):
    # --- given ---
    identifier = "subset_polygon"
    inputs = [
        wps_input_file("resource", f"file://{netcdf_datasets['tasmin']}"),
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("start_date", "2000"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    ds = xr.open_dataset(outputs[0])
    assert list(ds.lat.values) == [0, 1, 2]
    assert list(ds.lon.values) == [1, 2]


def test_wps_subsetpoly_shapefile(client, netcdf_datasets):
    # --- given ---
    identifier = "subset_polygon"
    poly = shapefile_zip()
    inputs = [
        wps_input_file("resource", f"file://{netcdf_datasets['tasmin']}"),
        wps_input_file("shape", poly),
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("start_date", "2000"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    ds = xr.open_dataset(outputs[0])
    assert list(ds.lat.values) == [0, 1, 2]
    assert list(ds.lon.values) == [1, 2]
