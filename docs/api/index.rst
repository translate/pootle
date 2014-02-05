.. _api:

Pootle API
**********

.. versionchanged:: 2.5.1

Pootle provides a REST API for interacting with it using external tools,
allowing those to retrieve data, for example translation stats, or save data to
Pootle, e.g. translations. This reference document is written for those
interested in:

* Developing software to use this API
* Integrating existing software with this API
* Exploring API features in detail


.. _api#enabling-api:

Enabling the Pootle API
=======================

Pootle API is disabled by default. To enable it just install
``django-tastypie`` and put the following line on your custom settings:

.. code-block:: python

  POOTLE_ENABLE_API = True


.. warning::

    If you are running Pootle using Apache with ``mod_wsgi`` you will need to
    enable ``WSGIPassAuthorization On`` as told in
    :ref:`Tastypie authentication docs <tastypie:authentication>`.


.. _api#using:

Pootle API usage
================

In order to interact with Pootle API it is necessary to know how to use it and
some of its particularities.

.. toctree::
   :maxdepth: 1

   using


.. _api#available-resources:

Available resources
===================

The Pootle API exposes a number of resources. Next you have a complete list of
them with data about the accepted HTTP methods, result limits, authentication
requirements or other constraints.

.. note:: You might want to look at the :ref:`Glossary <glossary>` to fully
   understand the resource names used in the API.

.. toctree::
   :maxdepth: 2

   api_language
   api_project
   api_store
   api_suggestion
   api_translation_project
   api_unit
   api_user
