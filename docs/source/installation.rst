.. _installation:

Installation
============

.. contents::
    :local:
    :depth: 1

Install from PyPI
-----------------

.. note::

   As of Winter 2024, `finch` is available as a PyPI-based package for testing and evaluation purposes. For a production server, we recommend deploying Finch as a Docker service.

To install the latest release from PyPI:

.. code-block:: console

   $ python -m pip install birdhouse-finch

Install from Docker
-------------------

The easiest way to deploy Finch is to use the Docker image. The Docker image is available on Docker Hub as `birdhouse/finch`.

.. code-block:: console

   $ docker pull birdhouse/finch:latest

Development Installation (GitHub)
---------------------------------

Check out code from the Finch GitHub repo and start the installation:

.. code-block:: console

   $ git clone https://github.com/bird-house/finch.git
   $ cd finch

Create Conda environment named `finch`, this includes the development and documentation dependencies :

.. code-block:: console

   $ conda env create -f environment.yml
   $ conda activate finch

Install `finch` app:

.. code-block:: console

   $ python -m pip install -e .
   OR
   $ make install


Install from Conda
------------------

.. note::

   `finch` is not yet available on conda-forge. We are not working on making this package available soon.
