.. _testing:

Testing
=======

.. warning::

   This page needs expanding and updating.

This page contains notes about Pootle's unit tests and how they should be used,
interpreted and expanded. See the `Translate Toolkit docs
<http://translate.readthedocs.org/projects/translate-toolkit/en/latest/development/testing.html>`_
for notes on writing tests.

Pootle's unit tests use the Django testing framework, and can be executed with::

    $ python manage.py test  pootle_store pootle_app pootle_translationproject

Although you can run tests for all applications, several of the external
applications are not passing their tests which renders this less useful.

Tests could be run with ``py.test`` using `pytest-django
<https://pypi.python.org/pypi/pytest-django/>`_
or alternately by adding a `django-pytest
<https://github.com/buchuki/django-pytest#readme>`_
app to Pootle (conceivably both could be done) - however this is not currently
supported or implemented.
