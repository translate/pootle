.. _cache:

Caching System
==============

Pootle uses a caching system to improve performance. It is an essential part
of :doc:`optimizing <optimization>` your Pootle installation. It is based on
|Django's caching system|_, and is used for various things:

- To serve cached (possibly slightly outdated) versions of most pages to
  anonymous users to reduce their impact on server performance.

- To cache bits of the user interface, even for logged in users. Data will not
  be out of date but Pootle still tries to use the cache to reduce the impact
  on server performance.

- To store the result of expensive calculations like translation statistics.

- To keep track of last update timestamps to avoid unnecessary and expensive
  file operations (for example don't attempt to save translations before a
  download if there are no new translations).

Without a well functioning cache system, Pootle could be slow.


.. _cache#cache_backends:

Cache Backends
--------------

Django supports :ref:`multiple cache backends <django:setting-up-the-cache>`
(methods of storing cache data). You can specify which backend to use by
overriding the value of :setting:`CACHES` in your configuration file.


.. _cache#memcached:

Memcached
^^^^^^^^^

.. code-block:: python

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

:ref:`Memcached <django:memcached>` is the **recommended cache backend**, it
provides the best performance.  And works fine with multiprocessing servers
like Apache. It requires the `python-memcached` package and a running
memcached server. Due to extra dependencies it is not enabled by default.


.. _cache#memcached_on_unix_sockets:

Memcached on Unix sockets
"""""""""""""""""""""""""

.. code-block:: python

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': 'unix:/path/to/memcached.sock',
        }
    }

If you don't want Pootle using TCP/IP to access memcached then you can use Unix
sockets.  This is often a situation in hardened installations using SELinux.

You will need to ensure that memcached is running with the ``-s`` option:

.. code-block:: bash

    $ memcached -u nobody -s /path/to/memcached.sock -a 0777


.. _cache#database:

Database
^^^^^^^^

.. code-block:: python

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'my_cache_table',
        }
    }

:ref:`Database caching <django:database-caching>` relies on a table in the main
Pootle database for storing the cached data, which makes it suitable for
multiprocessing servers, with the added benefit that the cached data remains
intact after a server reboot (unlike memcached) but it is considerably slower
than memcached.

.. versionchanged:: 2.1.1

This is the default cache backend. On new installs and upgrades the required
database will be created.

Users of older versions need to create the cache tables manually if they would
like to switch to the database cache backend using this :doc:`management
command <commands>`:

.. code-block:: bash

    $ pootle createcachetable pootlecache


.. _Django's caching system: http://docs.djangoproject.com/en/dev/topics/cache/
.. |Django's caching system| replace:: *Django's caching system*

.. we use | | here and above for italics like :ref: in normal links
   (Django intersphinx objects do not include section titles, must use frags)
