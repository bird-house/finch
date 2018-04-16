.. _configuration:

Configuration
=============

If you want to run on a different hostname or port then change the default values in ``custom.cfg``:

.. code-block:: sh

   $ cd finch
   $ vim custom.cfg
   $ cat custom.cfg
   [settings]
   hostname = localhost
   http-port = 8095

After any change to your ``custom.cfg`` you **need** to run ``make update`` again and restart the ``supervisor`` service:

.. code-block:: sh

  $ make update    # or install
  $ make restart
