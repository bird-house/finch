.. _devguide:

Developer Guide
===============

.. contents::
    :local:
    :depth: 1

.. warning:: To create new processes, refer to the examples found in Emu_.

.. _Emu: https://github.com/bird-house/emu

Building the docs
-----------------

First install dependencies for the documentation:

.. code-block:: shell

   $ make develop

Run the Sphinx docs generator:

.. code-block:: shell

   $ make docs

.. _testing:

Running tests
-------------

Run tests using pytest_.

First activate the ``finch`` Conda environment and install ``pytest``.

.. code-block:: shell

   $ source activate finch
   $ pip install -e ".[dev]"  # if not already installed
   # or
   $ make develop

Run quick tests (skip slow and online):

.. code-block:: shell

   $ pytest -m 'not slow and not online'"

Run all tests:

.. code-block:: shell

   $ pytest

Check code formatting compliance:

.. code-block:: shell

   $ pre-commit run --all-files

.. _pytest: https://docs.pytest.org/en/latest/

Run tests the lazy way
----------------------

Do the same as above using the ``Makefile``.

.. code-block:: shell

   $ make test
   $ make test-all
   $ make lint

Updating the Conda environment
------------------------------

To update the `conda` specification file for building identical environments_ on a specific operating system:

.. note:: You should perform this regularly within your Pull Requests on your target OS and architecture (64-bit Linux).

.. code-block:: console

   $ conda env create -f environment.yml
   $ source activate finch
   $ make clean
   $ make install
   $ conda list -n finch --explicit > spec-file.txt

.. _environments: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#building-identical-conda-environments

Preparing Finch releases
------------------------

In order to prepare a new release version of finch, perform the following steps in a new branch:

#. Update ``CHANGES.rst`` with the release notes for the next version.
#. Run `$ bump-my-version bump { patch | minor | major }` to update the version numbers.
#. Run `$ bump-my-version bump release` to create a new release commit.
#. Push your changes to GitHub.
#. Open a Pull Request with an appropriate title and description (e.g. "Prepare release v1.2.3").
#. Wait for the CI workflows to complete.
#. Merge the Pull Request into the ``main`` branch.
#. Tag the commit with the new version number:
    - Run `$ git tag -a v1.2.3 -m "Release v1.2.3"`.
    - Push the tag to GitHub with `$ git push origin v1.2.3`.
#. Create a new release on GitHub using the newly tagged commit with the same version number as the tag:
    - The release title should be the same as the tag name.
    - The release description should be the same as the release notes in ``CHANGES.rst``.
