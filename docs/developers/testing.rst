.. _testing:

Testing
=======

.. warning::

   This page needs expanding and updating.

This page contains notes about Pootle's unit tests and how they should be used,
interpreted and expanded. See the :ref:`Translate Toolkit testing docs
<toolkit:testing>` for notes on writing tests.

Pootle's unit tests use the Django testing framework, and can be executed with:

.. code-block:: bash

    $ python manage.py test pootle_store pootle_app pootle_translationproject

Although you can run tests for all applications, several of the external
applications are not passing their tests which renders this less useful.

Tests could be run with ``py.test`` using `pytest-django`_ or alternately by
adding a `django-pytest`_ app to Pootle (conceivably both could be done) - however
this is not currently supported or implemented.

.. _pytest-django: http://pypi.python.org/pypi/pytest-django/

.. _django-pytest: http://github.com/buchuki/django-pytest#readme
