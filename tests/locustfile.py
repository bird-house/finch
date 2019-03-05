from locust import HttpLocust, TaskSet


def post_ice_days(l):
    data = {
        "inputs": [
            {
                "id": "tasmax",
                "href": "https://github.com/Ouranosinc/xclim/raw/master/tests/testdata/NRCANdaily/nrcan_canada_daily_tasmax_1990.nc"
            },
            {
                "id": "freq",
                "data": "YS"
            }
        ],
        "response": "document",
        "mode": "auto",
        "outputs": [
            {
                "transmissionMode": "reference",
                "id": "output_netcdf"
            }
        ]
    }
    l.client.post("/providers/finch/processes/tx_max/jobs", json=data, verify=False)


class UserBehavior(TaskSet):
    tasks = {
        post_ice_days: 1,
    }


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 900
    max_wait = 1100
