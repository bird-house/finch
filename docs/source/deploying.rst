.. _deploying:

Deployment
==========

Start Finch PyWPS service
-------------------------

After successful installation, you can start the service using the ``finch`` command-line:

.. code-block:: console

   $ finch --help  # show help
   $ finch start  # start service with default configuration

   OR

   $ finch start --daemon  # start service as daemon
   loading configuration
   forked process id: 42

The deployed WPS service is available by default on port 5000:

http://localhost:5000/wps?service=WPS&version=1.0.0&request=GetCapabilities.

Once the service is running, a `pywps.pid` file is created in the current directory.
This file contains the process ID of the running ``finch`` service.

Alternatively, you can find which process uses a given port using the following command (here for port 5000):

.. code-block:: console

   $ netstat -nlp | grep :5000

Check the log files for errors:

.. code-block:: console

   $ tail -f  pywps.log

Stopping the ``finch`` daemon:

.. code-block:: console

   $ finch stop

Changing the default port
+++++++++++++++++++++++++

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

Starting Finch WPS the lazy way (from sources)
++++++++++++++++++++++++++++++++++++++++++++++

If `finch` is running from a clone of the GitHub source code repository, you can alternatively simply use the ``Makefile`` to start and stop the service:

.. code-block:: console

   $ make start
   $ make status
   $ tail -f pywps.log
   $ make stop

If you wish to always run Finch from the Makefile, you can set the URL and port via environment variables:

.. code-block:: console

   $ export WPS_URL=http://localhost:9876  # to set a particular URL:port

Deploying Finch from a Docker container
---------------------------------------

Running Finch as a Docker service is very simple:

.. code-block:: console

   $ docker run -p 5000:5000 birdhouse/finch

This will start Finch mapped to port 5000, allowing you to access Finch at http://localhost:5000.

Using Ansible to deploy Finch WPS
---------------------------------

Ansible can also be used to deploy `finch` on your system. See the `Ansible playbook example`_ for more information.

.. _Ansible playbook example: http://ansible-wps-playbook.readthedocs.io/en/latest/index.html
