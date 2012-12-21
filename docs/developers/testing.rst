.. _testing:

Unit Testing
============

.. warning::

   This page needs updating.

This page contains notes about Pootle's unit tests and how they should be used,
interpreted and expanded. You might also want to check the `testing guidelines
<http://translate.sourceforge.net/wiki/developers/testing_guidelines>`_.

Pootle's unit tests use the Django testing framekwork, and can be executed with::

    $ python manage.py test pootle_app

Although you can run tests for all applications, several of the external
applications are not passing their tests which renders this less useful.

These can be run with *py.test* if you have the correct plugin for *py.test*
installed. `More information
<http://codespeak.net/py/dist/test/plugin/django.html>`_.
