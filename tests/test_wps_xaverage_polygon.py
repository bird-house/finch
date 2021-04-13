import geojson
import pytest
import xarray as xr
from tests.utils import execute_process, shapefile_zip, wps_input_file, wps_literal_input


def test_wps_averagepoly(client, netcdf_datasets):
    # --- given ---
    identifier = "average_polygon"
    poly = {
        "type": "Feature",
        "id": "apolygon",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0.5, 0], [2.5, 0], [2.5, 2.5], [0.5, 2.5]]],
        },
    }
    inputs = [
        wps_input_file("resource", f"file://{netcdf_datasets['tasmin']}"),
        wps_literal_input("shape", geojson.dumps(poly)),
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("start_date", "2000"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

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
    outputs = execute_process(client, identifier, inputs, output_names=["output"])

    # --- then ---
    ds = xr.open_dataset(outputs[0])

    assert ds.geom.size == 1
    assert ds.FID.values == [0]


def test_dap(client):
    identifier = "average_polygon"
    nc_file = "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/testdata/xclim/NRCANdaily" \
              "/nrcan_canada_daily_tasmin_1990.nc"
    poly = '{"type": "FeatureCollection", "features": [{"id": "0", "type": "Feature", "properties": {}, "geometry": ' \
            '{"type": "Polygon", "coordinates": [[[-73.8578, 50.2016], [-73.3993, 51.6116], [-71.2542, 52.0625], [-72.1262, 50.9916], [-73.8578, 50.2016]]]}, "bbox": [-73.8578, 50.2016, -71.2542, 52.0625]}], "bbox": [-73.8578, 50.2016, -71.2542, 52.0625]}'

    inputs = [
        wps_input_file("resource", nc_file),
        wps_literal_input("shape", poly),
        wps_literal_input("variable", "tasmin"),
        wps_literal_input("start_date", "1990-06-01"),
        wps_literal_input("end_date", "1990-06-05"),
    ]

    # --- when ---
    outputs = execute_process(client, identifier, inputs, output_names=["output"])
    ds = xr.open_dataset(outputs[0])
    assert ds.tasmin.mean().data > 200
