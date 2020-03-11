Changes
*******


0.4.x (2020-03-10)
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
