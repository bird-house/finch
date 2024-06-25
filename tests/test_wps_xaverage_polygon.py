import geojson
import pytest
import xarray as xr

from _utils import execute_process, shapefile_zip, wps_input_file, wps_literal_input


def test_wps_averagepoly(client, netcdf_datasets):
    # --- given ---
    identifier = "average_polygon"
    poly = {
        "type": "Feature",
        "id": "apolygon",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0.5, 0], [2.5, 0], [2.5, 2.5], [0.5, 2.5], [0.5, 0]]],
        },
    }
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
    assert ds.geom.size == 1
    assert ds.id.values == ["apolygon"]


@pytest.mark.parametrize("tolerance", ["0", "0.1"])
def test_wps_averagepoly_shapefile(client, netcdf_datasets, tolerance):
    # --- given ---
    identifier = "average_polygon"
    poly = shapefile_zip()
    inputs = [
        wps_input_file("resource", f"file://{netcdf_datasets['tasmin']}"),
        wps_input_file("shape", poly),
        wps_literal_input("tolerance", tolerance),
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("start_date", "2000"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs)

    # --- then ---
    ds = xr.open_dataset(outputs[0])

    assert ds.geom.size == 1
    assert ds.FID.values == [0]
