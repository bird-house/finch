from locust import HttpLocust, TaskSet


def post_ice_days(loc):
    url = "https://github.com/Ouranosinc/xclim/raw/master/tests/testdata/NRCANdaily/nrcan_canada_daily_tasmax_1990.nc"
    data = {
        "inputs": [{"id": "tasmax", "href": url}, {"id": "freq", "data": "YS"}],
        "response": "document",
        "mode": "auto",
        "outputs": [{"transmissionMode": "reference", "id": "output_netcdf"}],
    }
    loc.client.post("/providers/finch/processes/tx_max/jobs", json=data, verify=False)


class UserBehavior(TaskSet):
    tasks = {
        post_ice_days: 1,
    }


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 900
    max_wait = 1100
