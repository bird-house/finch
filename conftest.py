# noqa: D100


def pytest_collectstart(collector):  # noqa: D103
    if collector.fspath and collector.fspath.ext == ".ipynb":
        collector.skip_compare += (
            "text/html",
            "application/javascript",
        )
