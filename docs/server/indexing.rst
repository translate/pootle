.. _indexing:

Text indexing for Pootle
========================

Pootle provides :doc:`searching <../features/searching>` functionality, which
is a great way to do searches over all files in a project. If there are many
strings to search through, this can be slow, but installing a text indexing
library will speed things up, allowing searching even in very large projects.


.. _indexing#supported_indexing_engines:

Supported indexing engines
--------------------------

For now the current indexing engines are supported:

- `Lucene <http://lucene.apache.org/>`_:  This should be the fastest, but is
  not packaged on many distributions, and is a bit harder to build.

- `Xapian <http://xapian.org>`_ (v1.0 or higher): Note that you need at least
  `version 1.0.13
  <http://svn.xapian.org/*checkout*/tags/1.0.13/xapian-bindings/NEWS>`_ to run
  under Apache with mod_wsgi or mod_python.

.. _indexing#usage:

Usage
-----

The indexing databases help to speed up search queries via the Pootle
interface. See :doc:`../features/searching` for details.


.. _indexing#administration:

Administration
--------------

If you want to use an indexing engine to speed up text searches, then you need
to install any of the supported indexing engines and its python binding.

The indexing engines will be used, as soon as the required python bindings are
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

- Install the `python bindings for Xapian
  <http://xapian.org/docs/bindings/python/>`_

  - For debian: ``apt-get install python-xapian xapian-tools``

Xapian tools is needed for *xapian-check* which determines whether the version
is OK to use or not.


.. _indexing#debugging:

Debugging
---------

If you want to check, which indexing engines are currently detected in your
system, you can execute the self-tests of the indexing engine interface of
Pootle::

    python translate/search/indexing/test_indexers.py

This will display the installed engines and check, if they work as expected.
Please file a `bug report
<http://bugs.locamotion.org/enter_bug.cgi?product=Pootle&component=Pootle>`_ if
you encounter any errors when running these tests.

The actual test for xapian is ``xapian-check --version``.
