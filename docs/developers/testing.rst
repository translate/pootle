.. _testing:

Testing
=======

.. warning::

   Work in progress. For now only Python testing is being added. Future
   coverage will include JavaScript code too.

Pootle tests use the full-featured `pytest testing tool
<http://pytest.org/latest/>`_ and its integration with Django via
`pytest-django <http://pytest-django.readthedocs.org/en/latest/>`_.

The entire test suite can be executed from a checkout by running ``make
test``. This will create a new virtual environment, install the required
dependencies and run the tests.

However, if you're developing you can simply run

.. code-block:: console

    $ py.test

from the root of the repository. Note that you need to install the testing
requirements into your virtualenv first (*requirements/tests.txt*).

.. note::

    Since the test runner automatically sets the :setting:`DEBUG` setting to
    ``False``, the static assets need to be collected before running the view
    tests. You can run ``make assets`` for building them.

The ``py.test`` runner command offers several options which are extended
by plugins as well. Check `its documentation <http://pytest.org/latest/>`_
for further details.


Settings for Tests
------------------

Some testing-specific settings are loaded from the *tests/settings.py*
file and override any previous setting you might have set in the
*settings/\*.conf* files.


Writing Tests
-------------

Writing new tests is easy. Just write a function whose name starts with
``test_`` and place it in an appropriate module under the *tests/*
subdirectory.

You'll need to use plain Python assertions in test functions. Check
pytest's documentation for `more information on assertions
<http://pytest.org/latest/assert.html>`_.

In order to use a fixture, you simply need to reference its name as a
function argument. Pytest does the rest of the magic. There are `other
ways to reference and use fixtures
<http://pytest.org/latest/fixture.html>`_ as well, but most of the time
you'll find yourself passing them as function arguments.

What to Test
^^^^^^^^^^^^

You'll usually want to test model behavior. These tests should test one
function or method in isolation. If you end up needing to test for
multiple things, then you might need to split the function/method into
more specific units. This allows to structure the code better.

When testing models, it's a suggested practice to avoid DB access because
it makes the tests run slower, so think twice if your test actually needs
DB access. At the same time, pytest-django encourages you to follow these
best practices and disables DB access by default. If your test needs DB
access, you need to explicitly request it by using the
`@`pytest.mark.django_db marker
<http://pytest-django.readthedocs.org/en/latest/helpers.html#pytest-mark-django-db-request-database-access>`_.

While testing views/integration tests can also help catch regressions,
they're slower to run and end up in less useful failures, so better to
write fewer of these.


Fixtures
--------

Pootle tests include some pytest fixtures you can reuse. They're located
in *tests/fixtures/* and are loaded when the test runner is being set up.

If you have a fixture which is very specific you can place it in a usual
``conftest.py`` file in its proper context, whereas the aforementioned
directory is meant to be for storing shared or general-purpose fixtures.

Model Fixtures
^^^^^^^^^^^^^^

Model fixtures are stored under *tests/fixtures/models/*, and they are
basically factory functions returning an instance of the desired model.
Note that these might depend on other fixtures too.

For now these model fixtures require DB access, but since that's not what
every single test might need, we might want to combine this with other
more complete solutions like `factory_boy
<https://factoryboy.readthedocs.org/en/latest/>`_ in the future.
