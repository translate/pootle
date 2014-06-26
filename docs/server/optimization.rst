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


Caching
^^^^^^^

Fast and efficient caching avoids hitting the DB when it's not really needed.
Adjust the :setting:`CACHES` setting accordingly.

`python-memcached <http://www.tummy.com/software/python-memcached/>`_ Efficient
caching.


Indexing Engines
^^^^^^^^^^^^^^^^

Installing an :doc:`indexing engine <indexing>` will speed-up searches. Pootle
will automatically pick one from any of the available engines.

`Xapian <http://xapian.org/docs/bindings/python/>`_
  Python bindings for Xapian [#f1]_.

`PyLucene <https://lucene.apache.org/pylucene/>`_
  Python bindings for Lucene.


.. rubric:: Note

.. [#f1] Xapian versions before 1.0.13 are incompatible with Apache; Pootle will
  detect Xapian version and disable indexing when running under *mod_wsgi* if
  needed.

  Checking for Xapian relies on the `xapian-check` command, which is found in
  the `xapian-tools` package in Debian-based systems.


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

zip and unzip
  Fast (un)compression of file archives.

`python-Levenshtein <https://pypi.python.org/pypi/python-Levenshtein/>`_
  Provides speed-up when updating against templates.

`iso-codes <http://packages.debian.org/unstable/source/iso-codes>`_
  Enables translated language and country names.

`raven <http://raven.readthedocs.org/>`_
  Enables logging server exceptions to a `Sentry server
  <http://sentry.readthedocs.org/en/latest/>`_. If installed and configured,
  Pootle will automatically use the raven client.

`python-ldap <http://www.python-ldap.org/>`_
  Enables :ref:`LDAP authentication <authentication#ldap>`. Be sure to check the
  :ref:`LDAP settings <settings#ldap>`.


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

- Install :doc:`memcached <cache>` and enable it in the settings file.

- Install the latest recommended version of all dependencies. Django and the
  Translate Toolkit might affect performance.  Later versions of Pootle should
  also give better performance.  You can :doc:`upgrade <upgrading>` to newer
  versions of Pootle easily.

- Ensure :setting:`DEBUG` mode is disabled.

- Ensure that the ``zip`` and ``unzip`` commands are installed on your
  server.  These can improve the performance during upload and download
  of large ZIP files.

- Ensure that you have an :doc:`indexing engine <indexing>` installed with its
  Python bindings. This will improve the performance of searching in big
  projects. PyLucene should perform better, although it might be harder to
  install.

- Ensure that you have python-levenshtein installed. This will improve the
  performance when updating against templates.

- Increase the cache timeout for users who are not logged in.

- Increase your :setting:`PARSE_POOL_SIZE` if you have enough memory available.

- Enable ``'django.contrib.sessions.backends.cached_db'``.

- Disable swap on the server.  Things should be configured so that physical
  memory of the server is never exceeded. Swapping is bound to seriously
  degrade the user experience.

- Ensure gzip compression is enabled on your web server. For Apache,
  `mod_deflate <https://httpd.apache.org/docs/2.4/mod/mod_deflate.html>`_
  handles this. Also see `nginx wiki <http://wiki.nginx.org/HttpGzipModule>`_.


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

Using MySQL is well tested and recommended. You can :doc:`migrate your current
database <database_migration>` if you already have data you don't want to lose.

If using MySQL backend, for smaller installations it is suggested to go with
`MyISAM backend
<https://dev.mysql.com/doc/refman/5.6/en/myisam-storage-engine.html>`_ (which
might result in smaller memory usage and better performance). If high
concurrency is expected, `InnoDB
<https://dev.mysql.com/doc/refman/5.6/en/innodb-storage-engine.html>`_ is
suggested to avoid locking issues.


.. _optimization#fast_po_implementation:

Fast PO implementation
^^^^^^^^^^^^^^^^^^^^^^

If you want better performance for your PO based operations, you can try to
enable the fast PO implementation. This implementation will be used if
``USECPO=2`` is available in the operating system environment variables. Note
that this is different from the web server's environment variables.

Your PO files will have to have character encodings specified, and be perfectly
valid PO files (no duplicate messages or other format errors). Be sure to test
this extensively before you migrate your live server to this setup.
