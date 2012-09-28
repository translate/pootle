.. _indexing:

Text indexing for Pootle
========================

Pootle provides :doc:`searching </features/searching>` functionality, which
is a great way to do searches over all files in a project. If there are many
strings to search through, then performance can be slow, but installing a
text indexing library will speed things up, allowing searching even in very
large projects.


.. _indexing#supported_indexing_engines:

Supported indexing engines
--------------------------

The following indexing engines are supported:

- `Lucene <http://lucene.apache.org/>`_:  This should be the fastest, but is
  not packaged for many Linux distributions, and is a bit harder to build.

- `Xapian <http://xapian.org>`_ (v1.0 or higher): Note that you need at least
  `version 1.0.13
  <http://svn.xapian.org/*checkout*/tags/1.0.13/xapian-bindings/NEWS>`_ to run
  under Apache with mod_wsgi or mod_python.


.. _indexing#usage:

Pootle's usage of the indexing engine
-------------------------------------

The indexing database helps to speed up
:doc:`search queries </features/searching>` performed from the Pootle interface.


.. _indexing#administration:

Installation
------------

If you want to use an indexing engine to speed up text searches, then you need
to install one of the supported indexing engines and its Python binding.

The indexing engine will be used, as soon as the required Python bindings are
available.

See below for details.


.. _indexing#lucene:

Lucene
^^^^^^

- Install the `PyLucene <http://pylucene.osafoundation.org/>`_ package

  - For debian: follow this `Howto
    <https://systemausfall.org/wikis/howto/pyluceneondebian>`_


.. _indexing#xapian:

Xapian
^^^^^^

- Install the `Python bindings for Xapian
  <http://xapian.org/docs/bindings/python/>`_

  - For debian: ``apt-get install python-xapian xapian-tools``

The Xapian tools packaged is required for the *xapian-check* command which
is used to determines whether the Xapian version is compatable with Pootle.


.. _indexing#debugging:

Debugging
---------

If you want to check which indexing engines are currently detected on your
system you can execute the self-tests of the indexing engine interface of
Pootle::

    python translate/search/indexing/test_indexers.py

This will display the installed engines and check if they work as expected.

.. note:: Please file a `bug report
   <http://bugs.locamotion.org/enter_bug.cgi?product=Pootle&component=Pootle>`_
   if you encounter any errors when running these tests.

The actual test for xapian is ``xapian-check --version``.
