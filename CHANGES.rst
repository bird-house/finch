Changes
*******

0.7.6 (unreleased)
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
