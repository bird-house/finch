.. _configuration:

Configuration
=============

Command-line options
--------------------

You can overwrite the default `PyWPS`_ configuration by using command-line options.
See the Finch help which options are available::

    $ finch start --help
    --hostname HOSTNAME        hostname in PyWPS configuration.
    --port PORT                port in PyWPS configuration.

Start service with different hostname and port::

    $ finch start --hostname localhost --port 5001

Use a custom configuration file
-------------------------------

You can overwrite the default `PyWPS`_ configuration by providing your own
PyWPS configuration file (just modifiy the options you want to change).
Use one of the existing ``sample-*.cfg`` files as example and copy them to ``etc/custom.cfg``.

For example change the hostname (*demo.org*) and logging level:

.. code-block:: console

   $ cd finch
   $ vim etc/custom.cfg
   $ cat etc/custom.cfg
   [server]
   url = http://demo.org:5000/wps
   outputurl = http://demo.org:5000/outputs

   [logging]
   level = DEBUG

Start the service with your custom configuration:

.. code-block:: console

   # start the service with this configuration
   $ finch start -c etc/custom.cfg

.. _PyWPS: http://pywps.org/

Content of the configuration file
---------------------------------
Configuration sections and values specific to Finch are:

finch
^^^^^^
:datasets_config: Path to the YAML files defining the available ensemble datasets (see below). The path can be given relative to the "finch/finch/" folder, where `default.cfg` lives.
:default_dataset: Default dataset to use when none is requested. Should be a top-level key of the yaml.
:subset_threads: Number of threads to use when performing the subsetting.

finch:metadata
^^^^^^^^^^^^^^
All fields here are added as string attributes of computed indices, in addition to xclim's attributes.
Finch always adds the following attributes:

:climateindex_package_id: ``https://github.com/Ouranosinc/xclim``
:product: ``derived climate index``


Structure of the dataset configuration file
-------------------------------------------
The configuration value for `finch, datasets_config`, points to a YAML file that defines each ensemble datasets that are available for ensemble processes. These processes and their default values are generated according to the "allowed_values" of the datasets. This means that a user sees _all_ available values in the process's description, but not all are valid depending on the passed `dataset`.

The YAML file must consist in a mapping of dataset name to dataset configuration, the latter having the same structure as this dataclass:

.. autoclass:: finch.processes.utils.DatasetConfiguration

