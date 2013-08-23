.. _customization:

Customizing the look
====================

This page lists some things to consider when making changes to the look
and feel of the translation server.


.. _customization#building:

Rebuilding assets after customization
-------------------------------------

.. warning::

   After doing any customization, please execute the following command to
   collect and build static content such as images, CSS and JavaScript files
   that are served by Pootle server.

   .. code-block:: bash

      $ make assets
