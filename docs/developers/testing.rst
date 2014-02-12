.. _testing:

Testing
=======

.. warning::

   Work in progress. For now only Python testing is being added. Future
   coverage will include JavaScript code too.

Pootle's unit tests use the py.test Python test suite and its integration
with Django is done using `pytest-django <http://pytest.org/latest/>`_.

The entire test suite can be executed from a checkout by running:

.. code-block:: bash

    $ make test

This will create a new virtual environment, install the required
dependencies and run the test suite. Alternatively, if you have setup a
development environment, you can install the testing requirements
(*requirements/tests.txt*) and simply run ``py.test tests/`` from the root
of the repository.

The py.test runner offers several options, check `its documentation
<http://pytest.org/latest/>`_ for further details.

Settings for Tests
------------------

In short, you can place testing-specific settings both in the
*90-tests.conf* and *90-tests-local.conf* files within the
*pootle/settings/* directory. Other *90-\*.conf* files will be ignored.

.. note:: *90-tests.conf* doesn't contain any database settings, and you
   are encouraged to set those in *90-tests-local.conf*. If nothing is
   specified SQLite will be used by default, which might not actually be what
   you want to run the tests against.

In further detail, Pootle's test runner will use the usual
``pootle.settings`` module for settings. This module ensures that all
files in the *pootle/settings/* directory are read and interpreted in
order.

In testing environments, the needs might differ from other environments,
so the settings module will have a slightly different behavior:

- All *.conf* files will be read from *pootle/settings/* as usual
- The usual custom settings named as *90-\*.conf* will be ignored
- *90-tests.conf* and *90-tests-local.conf* will be taken into account
