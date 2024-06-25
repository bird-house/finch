Changes
*******

0.12.1 (2024-06-25)
===================
* Replaced `unidecode` with `anyascii` due to a licensing issue.
* Synchronized some dependencies across build systems.
* Added a workaround in ``wps_geoseries_to_netcdf`` to handle a `pandas` v2.0 behaviour change.

0.12.0 (2024-03-25)
===================
* Renamed the installed package from `finch` to `birdhouse-finch`.
* First release of the `birdhouse-finch` package on PyPI.
* Versioning now adheres to SemVer v2.0.0.
* Added a Makefile recipe to the repository to evaluate notebooks while ignoring the output cells.
* Cleaned up documentation to facilitate easier navigation.
* Slightly reorganized the documentation for easier navigation.
* Fast-forwarded the cookiecutter.
* Fixed the ``Manifest.in`` to add all necessary files to wheel.
* Removed references to files that have never existed (`apidoc`).
* Cleaned up the setup code.
* Added more files to be ignored in the `.gitignore` and in the `Manifest.in`.

0.11.4 (2023-12-20)
===================
* Fixed a bug that occurred when fixing a broken cftime-index with newer `cftime` versions.
* Placed pins on xarray and pandas to prevent future errors from changes to frequency codes.

0.11.3 (2023-08-23)
===================
* Updated ReadTheDocs to use the new mambaforge version (`2022.9`).
* Addressed calls in GitHub Action usage that were emitting warnings.
* Updated `MANIFEST.in` to include and exclude the relevant files for the source distribution.
* Modified the `setup.py` to only include the files necessary in the wheel.
* Updated `AUTHORS.rst` to list more contributors.
* Removed namespace file (`__init__.py`) from tests to ensure that they aren't treated like an importable package.
* Updated pre-commit hooks.
* Sorted software requirements for legibility.
* Removed Travis-CI shell script.

0.11.2 (2023-07-27)
===================
* Added a Docker-based testing suite to the GitHub Workflows.
* Added a wider range of Python versions to test against in the GitHub Workflows.
* Migrated conda-build action from mamba-org/provision-with-micromamba to mamba-org/setup-micromamba.
* Cleaned up the Dockerfile. Docker now pip-installs finch directly from the GitHub repository.
* Finch now explicitly supports Python3.11.
* Pinned Python below 3.12 on conda and removed pin on pint for ReadTheDocs builds.
* Added a GitHub Workflow to bump the version number and to create tags from the version bumping process on dispatch.
* Added a pre-commit hook for validating the ReadTheDocs configuration and GitHub Workflows.

0.11.1 (2023-06-19)
===================
* Update to xclim 0.43.0.
* Added xclim yml module support:
    - Added humidex days above calculation via yml module.
    - Reimplmented streamflow indicators via yml module (adjust for xclim 0.41 breaking changes).
* Fixed bug for CanDCS-U6 ensemble "26models" list.
* Passing an empty string to `ensemble_percentiles` in ensemble processes will return the merged un-reduced ensemble. The different members are listed along the `realization` coordinates through raw names allowing for basic distinction between the input members.

0.11.0 (2023-06-13)
===================
* Fixed iter_local when depth > 0 to avoid all files to be considered twice
* Revised documentation configuration on ReadTheDocs to leverage Anaconda (Mambaforge)
* Minor adjustments to dependency configurations
* Removed configuration elements handling from `finch start`. One can still pass custom config files, but all configuration defaults are handled by `finch/default.cfg` and the WSGI function. `jinja2` is not a dependency anymore.

0.10.0 (2022-11-04)
===================
* Generalize ensemble datasets configuration.
    - Datasets usable by ensemble processes are now specified through a YAML file which is pointed to in the configuration.
    - As a consequence processes are generated according to the available variables. Similarly for the allowed values of some inputs on these processes.
    - The output name now includes the dataset name (if a custom name was not specified).
    - ``finch.processes.xclim`` was removed, there is no static module of processes.
    - Input "rcp" has been renamed to "scenario".
    - Input "dataset_name" has been fixed and renamed to "dataset".
* Update to xclim 0.38.0.
* Improved subset_grid_point_dataset & subset_bbox_dataset performance when using local files.

0.9.2 (2022-07-19)
==================
* Fix Finch unable to startup in the Docker image.

0.9.1 (2022-07-07)
==================
* Avoid using a broken version of ``libarchive`` in the Docker image.

0.9.0 (2022-07-06)
==================
* Fix use of ``output_name``, add ``output_format`` to xclim indicators.
* Change all outputs to use ``output`` as the main output field name (instead of ``output_netcdf``).
* Updated to xclim 0.37:

    - Percentile inputs of xclim indicators have been renamed with generic names, excluding an explicit mention to the target percentile.
    - In ensemble processes, these percentiles can now be chosen through ``perc_[var]`` inputs. The default values are inherited from earlier versions of xclim.
* Average shape process downgraded to be single-threaded, as ESMF seems to have issues with multithreading.
* Removed deprecated processes ``subset_ensemble_bbox_BCCAQv2``, ``subset_ensemble_BCCAQv2`` and ``BCCAQv2_heat_wave_frequency_gridpoint``.
* Added ``csv_precision`` to all processes allowing CSV output. When given, it controls the number of decimal places in the output.

0.8.3 (2022-04-21)
==================
* Preserve RCP dimension in ensemble processes, even when only RCP is selected.
* Pin ``dask`` and ``distributed`` at ``2022.1.0``, see https://github.com/Ouranosinc/PAVICS-e2e-workflow-tests/issues/100

0.8.2 (2022-02-07)
==================
* Add ``geoseries_to_netcdf`` process, converting a geojson (like a OGC-API request) to a CF-compliant netCDF.
* Add ``output_name`` argument to most processes (excepted subsetting and averaging processes), to control the name (or prefix) of the output file.
* New dependency ``python-slugify`` to ensure filenames are safe and valid.
* Pinning dask to ``<=2022.1.0`` to avoid a performance issue with ``2022.1.1``.

0.8.0 (2022-01-13)
==================
* Add ``hourly_to_daily`` process, converting hourly data to daily data using a reduction operation (sum, mean, max, min).
* Upgrade to clisops 0.8.0 to accelerate spatial averages over regions.
* Upgrade to xesmf 0.6.2 to fix spatial averaging bug not weighing correctly cells with varing areas.
* Update to PyWPS 4.5.1 to allow the creation of recursive directories for outputs.

Notes
-----
* Upgrading to birdy 0.8.1 will remove annoying warnings when accessing netCDF files from THREDDS.

0.7.7 (2021-11-16)
==================
* Fix Sentry SDK initialization error

0.7.6 (2021-11-16)
==================
* Update to xclim 0.31
* Added `SENTRY_ENV` configuration
* Possibility to pass multiple "rcp" inputs for ensemble processes.
* Writing to netcdf is done only after calling ``load()`` to avoid locks occurring within dask calls to ``to_netcdf`` in multi-processing mode.
* Add an ``average`` parameter to ensemble processes. When true, a spatial average is returned.

0.7.5 (2021-09-07)
==================
* Update to xclim 0.27
* Added ``empirical_quantile_mapping`` process calling ``xclim.sdba.EmpiricalQuantileMapping``.
* Update to PyWPS 4.4.5

0.7.4 (2021-05-04)
==================
* Update to xclim 0.26.
* Default metadata attributes are given through configuration, instead of being hardcoded.
* Inclusion of a list of input dataset urls in ensemble processes.
* Correct ensemble statistics on day-of-year indicators.

0.7.3 (2021-04-13)
==================
* Workaround for clisops shutting down logging
* More flexible chunking
* New subsetting & averaging notebook
* Require xESMF>=0.5.3

0.7.2 (2021-04-01)
==================
* Add `data_validation` and `cf_compliance` arguments for ensemble xclim processes.

0.7.1 (2021-03-25)
==================
* Add `data_validation` and `cf_compliance` arguments for xclim processes.
* Skip `data_validation` checks for the BCCAQv2HeatWave process.


0.7.0 (2021-03-15)
==================

* Add new process averaging gridded fields over a polygon using xESMF
* Update to xclim 0.24, allowing for considerable simplification of the indicator process building mechanism
* Update to PyWPS 4.4

0.6.1 (2021-01-26)
==================

* Add partial support for xclim 0.23 with new indicators
* Add support for land indicators
* Add support for multivariate indicators
* Upgrade PyWPS to 4.2.10
* Fix bug in variable name inference
* Add support for non-standard variable name (univariate case only)

0.6.0 (2021-01-12)
==================

* fix to chunk regions of subsetted files
* use `cruft` to propagate changes from the birdhouse cookiecutter
* catch documentation build error earlier since doc build is part of regular CI build
* catch tutorial notebooks out of sync with code earlier since also part of regular CI build
* use mock imports to facilitate building docs
* add partial support for xclim v0.21
* add support for shapefiles in `subset_shape`

0.5.2 (2020-03-25)
==================

* fix to remove realization coordinate from ensembles
* added chunk datasets for local files also
* update xclim to == 0.15.2

0.5.1 (2020-03-18)
==================

* fix local bccaqv2 files filtering

0.5.0 (2020-03-18)
==================

* update xclim to 0.15.0
* add french translation of processes abstract and descriptions

0.4.1 (2020-03-12)
==================

* fix #103 (drs_filename) add defaults when `project_id` is unknown
* drs_filenames: use dash instead of underscores in variable names
* fix #80 frequency attrs of computed datasets

0.4.0 (2020-03-10)
==================

* Add ensembles processes
* Allow ensemble process to specify which models are included
* Accept multiple files for processing
* Update from latest cookie-cutter template
* Add grid point indicator processes
* Add ensemble bbox processes
* Add support for percentiles inputs
* Update xclim to 0.14
* Pin PyWPS to 4.2.4
* Add DODS to supported formats for resources

0.3.x (2020-01-17)
==================

* Extract common inputs and outputs to wpsio.py
* Speed up CSV creation
* Explicitly close thread pool
* Tests for CSV conversion
* Added subset_shape process
* Pin PyWPS to ~4.2.3
* Add start and end date to bccaqv2 subset
* Identifier DAP link by header
* Datetime fix when replacing hour to 12
* deprecate lon0 and lat0 for SubsetGridPointBCCAQV2Process
* change point subset processes to accept a comma separated list of floats for multiple grid cells

0.2.7 (2019-12-09)
==================

* Fix for segmentation fault in libnetcdf (pin version to 4.6.2 until a fix is released)

0.2.6 (2019-12-04)
==================

* Notebooks are tested by Travis-CI
* Bug fix
* Update `xclim` to >= 0.12.2
* Update `pywps` to > 4.2.3

0.2.5 (2019-10-03)
==================

* Add test for DAP input to subsetting
* Update notebook to run on the Jenkins test suite

0.2.3 (2019-05-27)
==================

* Allow creating CSV output
* Keep global attributes when computing indices
* Add BCCAQV2HeatWave process
* Add basic usage notebook

0.2.1 (2019-05-06)
==================

* Require Python>=3.6
* Fix percentages in status update
* Improve loggin

0.2 (2019-05-02)
================

* Added subset_gridpoint process
* Support DAP links
* Added bounding box subsetting
* Threshold arguments passed as strings with units
* Added test for heat_wave_frequency
* Use sentry to monitor error messages
* Include Dockerfile
* Use processes instead of threads

0.1 (2018-11-15)
================

* First release.
