.. _optimization:

Optimization
============

This page lists extra optional software you can install to improve Pootle's
performance. Some configuration tips are given too.


.. _optimization#optional_software:

Optional Software
-----------------

By installing optional software you can gain performance and extra features.


Database Backends
^^^^^^^^^^^^^^^^^

You should really switch to a real database backend in production environments.
Adjust the :setting:`DATABASES` setting accordingly.

`MySQL-python <http://mysql-python.sourceforge.net/>`_
  MySQL adapter for Python.

`Psycopg2 <http://initd.org/psycopg/>`_
  PostgreSQL adapter for Python.


Web Servers
^^^^^^^^^^^

You should really run Pootle behind a :ref:`real web server <web>`, at least to
serve static content. For generating the dynamic content, you can also use
alternative WSGI servers that might better suit your environment.

`Apache <http://httpd.apache.org/>`_
  Apache web server.

`Nginx <http://nginx.org/>`_
  Ngninx web server.

`gunicorn <http://gunicorn.org/>`_
  Python WSGI HTTP server.


Speed-ups and Extras
^^^^^^^^^^^^^^^^^^^^

`iso-codes <https://packages.debian.org/unstable/source/iso-codes>`_
  Enables translated language and country names.

`raven <http://raven.readthedocs.org/en/latest/>`_
  Enables logging server exceptions to a `Sentry server
  <http://sentry.readthedocs.org/en/latest/>`_. If installed and configured,
  Pootle will automatically use the raven client.


.. _optimization#tips:

Tips
----

With a few extra steps, you can support more users and more data.  Here are
some tips for performance tuning on your Pootle installation.

- Ensure that Pootle runs under a proper :doc:`web server <web>`.

- Be sure to use a proper database server like :ref:`MySQL
  <optimization#mysql>` instead of the default SQLite.  You can :doc:`migrate
  an existing installation <database_migration>` if you already have data you
  don't want to lose.

- Install the latest recommended version of all dependencies. Django and the
  Translate Toolkit might affect performance.  Later versions of Pootle should
  also give better performance.  You can :doc:`upgrade <upgrading>` to newer
  versions of Pootle easily.

- Ensure :setting:`DEBUG` mode is disabled.

- Increase the cache timeout for users who are not logged in.

- Increase your :setting:`PARSE_POOL_SIZE` if you have enough memory available.

- Enable ``'django.contrib.sessions.backends.cached_db'``.

- Disable swap on the server.  Things should be configured so that physical
  memory of the server is never exceeded. Swapping is bound to seriously
  degrade the user experience.

- Ensure gzip compression is enabled on your web server. For Apache,
  `mod_deflate <https://httpd.apache.org/docs/2.4/mod/mod_deflate.html>`_ and
  for Nginx, `ngx_http_gzip_module
  <http://nginx.org/en/docs/http/ngx_http_gzip_module.html>`_.


.. _optimization#apache:

Apache
^^^^^^

For Apache, review your server settings so that you don't support too many or
too few clients. Supporting too many clients increases memory usage, and can
actually reduce performance.

No specific settings can be recommended, since this depends heavily on your
users, your files, and your hardware. However the default value for the
``MaxClient`` directive (usually 256) is almost always too high. Experiment
with values between 10 and 80.


.. _optimization#mysql:

MySQL
^^^^^

Using MySQL with `InnoDB backend
<https://dev.mysql.com/doc/refman/5.6/en/innodb-storage-engine.html>`_ is well
tested. MyISAM is no longer supported. You can :doc:`migrate your current
database <database_migration>` if you already have data you don't want to lose.
