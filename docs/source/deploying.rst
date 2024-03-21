.. _deploying:

Deploying Finch
===============

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

.. note:: Remember the process ID (PID) so you can stop the service with ``kill PID``.

You can find which process uses a given port using the following command (here for port 5000):

.. code-block:: console

   $ netstat -nlp | grep :5000

Check the log files for errors:

.. code-block:: console

   $ tail -f  pywps.log


You can overwrite the default `PyWPS`_ configuration by using command-line options.
See the Finch help for which options are available:

.. code-block:: console

    $ finch start --help
    --hostname HOSTNAME        hostname in PyWPS configuration.
    --port PORT                port in PyWPS configuration.

Start service with different hostname and port

.. code-block:: console

    $ finch start --hostname localhost --port 5001

.. _PyWPS: http://pywps.org/


... or do it the lazy way (from sources)
++++++++++++++++++++++++++++++++++++++++

If `finch` is running from a clone of the GitHub source code repository, you can alternatively simply use the ``Makefile`` to start and stop the service:

.. code-block:: console

   $ make start
   $ make status
   $ tail -f pywps.log
   $ make stop

Deploying Finch from a Docker container
---------------------------------------

Running Finch as a Docker service is very simple:

.. code-block:: console

   $ docker run -p 5000:5000 birdhouse/finch

This will start Finch on port 5000, allow you to access Finch at http://localhost:5000.

Use Ansible to deploy Finch on your System
------------------------------------------

Use the `Ansible playbook`_ for PyWPS to deploy Finch on your system.

.. _Ansible playbook: http://ansible-wps-playbook.readthedocs.io/en/latest/index.html
