.. _optimization:

Optimization
============

With a few extra steps, you can support more users and more data.  Here are
some tips for performance tuning on your Pootle installation.

- Ensure that Pootle runs under a webserver like :doc:`Apache <apache>`,
  :doc:`Nginx <nginx>` or a `fastcgi server
  <http://cleverdevil.org/computing/24/python-fastcgi-wsgi-and-lighttpd>`_. 

   - If you really can't install under another web server, at least install
     `cherrypy <http://www.cherrypy.org>`_ which Pootle will automatically use.
     This will help a little bit with performance.

- Be sure to use a proper database server like :ref:`MySQL
  <installation#mysql>` instead of the default SQLite.  You can :doc:`migrate
  an existing installation <database_migration>` if you already have data you
  don't want to lose.

- Install :doc:`memcached <cache>` and enable it in the settings file.

- Install the latest recommended version of all dependencies. Django and the
  Translate Toolkit might affect performance.  Later versions of Pootle should
  also give better performance.  You can :doc:`upgrade <upgrading>` to newer
  versions of Pootle easily.

- Ensure :setting:`LIVE_TRANSLATION` is disabled.

- Ensure :setting:`DEBUG` mode is disabled.

- Ensure that the ``zip`` and ``unzip`` commands are installed on your
  server.  These can improve the performance during upload and download
  of large ZIP files.

- Ensure that you have an :doc:`indexing engine <indexing>` installed with its
  Python bindings. This will improve the performance of searching in big
  projects.  PyLucene should perform better, although it might be harder to
  install.

- Ensure that you have python-levenshtein installed. This will improve the
  performance when updating from templates.

- Increase the cache timeout for users who are not logged in.

- Increase your parse pool size if you have enough memory available.

- Enable ``'django.contrib.sessions.backends.cached_db'``.

- Disable swap on the server.  Things should be configured so that physical
  memory of the server is never exceeded. Swapping is bound to seriously
  degrade the user experience.


.. _optimization#apache:

Apache
------

For Apache, review your server settings so that you don't support too many or
too few clients.  Supporting too many clients increase memory usage, and can
actually reduce performance.

No specific settings can be recommended, since this depends heavily on your
users, your files, and your hardware. However the default value for the
``MaxClient`` directive (usually 256) is almost always too high. Experiment
with values between 10 and 80.


.. _optimization#mysql:

MySQL
-----

If using MySQL backend, for smaller installations it is suggested to go with
MyISAM backend (which might result in smaller memory usage and better
performance). If high concurrency is expected, InnoDB is suggested to avoid
locking issues.


.. _optimization#fast_po_implementation:

Fast PO implementation
----------------------

If you want better performance for your PO based operations, you can try to
enable the fast PO implementation available since Translate Toolkit 1.5.0.
This implementation will be used if ``USECPO=2`` is available in the operating
system environment variables.  Note that this is different from the Apache
environment variables.

Your PO files will have to have character encodings specified, and be perfectly
valid PO files (no duplicate messages or other format errors). Be sure to test
this extensively before you migrate your live server to this setup.
