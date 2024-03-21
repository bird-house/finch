.. _installation:

Installation
============

.. contents::
    :local:
    :depth: 1

Development Installation (GitHub)
---------------------------------

Check out code from the Finch GitHub repo and start the installation:

.. code-block:: console

   $ git clone https://github.com/bird-house/finch.git
   $ cd finch

Create Conda environment named `finch`:

.. code-block:: console

   $ conda env create -f environment.yml
   $ source activate finch

Install Finch app:

.. code-block:: console

   $ python -m pip install -e .
   OR
   $ make install

For development you can use this command:

.. code-block:: console

  $ pip install -e .[dev]
  OR
  $ make develop

Install from PyPI
-----------------

.. note::

   As of Winter 2024, `finch` is available as a PyPI-based package for testing and evaluation purposes. For a production server, we recommend installing `finch` either from GitHub sources or deploying Finch as a Docker service.

To install the latest release from PyPI:

.. code-block:: console

   $ python -m pip install birdhouse-finch

Install from Conda
------------------

.. note::

   `finch` is not yet available on conda-forge. But we are working on making this package available soon!

Start Finch PyWPS service
-------------------------

After successful installation you can start the service using the ``finch`` command-line.

.. code-block:: console

   $ finch --help  # show help
   $ finch start  # start service with default configuration

   OR

   $ finch start --daemon  # start service as daemon
   loading configuration
   forked process id: 42

The deployed WPS service is by default available on port 5000:

http://localhost:5000/wps?service=WPS&version=1.0.0&request=GetCapabilities.

.. NOTE:: Remember the process ID (PID) so you can stop the service with ``kill PID``.

You can find which process uses a given port using the following command (here for port 5000):

.. code-block:: console

   $ netstat -nlp | grep :5000

Check the log files for errors:

.. code-block:: console

   $ tail -f  pywps.log

... or do it the lazy way (from sources)
++++++++++++++++++++++++++++++++++++++++

If `finch` is running from the GitHub source code repository, you can alternatively simply use the ``Makefile`` to start and stop the service:

.. code-block:: console

  $ make start
  $ make status
  $ tail -f pywps.log
  $ make stop

Deploying Finch from a Docker container
---------------------------------------

For production environments, we suggest running Finch as a Docker service.

.. code-block:: console

   $ docker run -p 5000:5000 birdhouse/finch

Use Ansible to deploy Finch on your System
------------------------------------------

Use the `Ansible playbook`_ for PyWPS to deploy Finch on your system.

.. _Ansible playbook: http://ansible-wps-playbook.readthedocs.io/en/latest/index.html
