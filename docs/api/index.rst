.. _api:

Pootle API
**********

Pootle provides a REST API for interacting with it using external tools,
allowing those to retrieve data, for example translation stats, or save data to
Pootle, e.g. translations. This reference document is written for those
interested in:

* Developing software to use this API
* Integrating existing software with this API
* Exploring API features in detail


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
   understand the API.

.. toctree::
   :maxdepth: 2

   api_language
   api_project
   api_store
   api_suggestion
   api_translation_project
   api_unit
