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

.. _cache#named_caches:

Named Caches
------------
The cache backends are at least configured with a 'default' cache.  If this is
the only cache that exists then all caching is placed into this cache.  The
Pootle cache can also be configured to take advantage of certain named caches.

Current named caches:

- ``'default'`` -- all non specified cache data and all cache data if only one
  cache is defined.
- ``'stats'`` --  all cached data related to overview stats.

In large installations you may want to setup separate caches to improve cache
performance.  You can then setup caching parameters for each cache separately.
In most cases though you will simply use a single 'default' cache.


.. _cache#cache_backends:

Cache Backends
--------------

Django supports |multiple cache backends|_ (methods of storing cache data).
You can specify which backend to use by overriding the value of
:setting:`CACHES` in your configuration file.


.. _cache#memcached:

Memcached
^^^^^^^^^

::

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

::

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': 'unix:/path/to/memcached.sock',
        }
    }

If you don't want Pootle using TCP/IP to access memcached then you can use Unix
sockets.  This is often a situation in hardened installations using SELinux.

You will need to ensure that memcached is running with the ``-s`` option. ::

    memcached -u nobody -s /path/to/memcached.sock -a 0777


.. _cache#database:

Database
^^^^^^^^

::

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'my_cache_table',
        }
    }

|Database caching|_ relies on a table in the main Pootle database for storing
the cached data, which makes it suitable for multiprocessing servers, with the
added benefit that the cached data remains intact after a server reboot
(unlike memcached) but it is considerably slower than memcached.

.. versionchanged:: 2.1.1

This is the default cache backend. On new installs and upgrades the required
database will be created.

Users of older versions need to create the cache tables manually if they would
like to switch to the database cache backend using this :doc:`management command
<commands>`::

    $ pootle createcachetable pootlecache

.. _Django's caching system: http://docs.djangoproject.com/en/dev/topics/cache/
.. |Django's caching system| replace:: *Django's caching system*

.. _multiple cache backends: http://docs.djangoproject.com/en/dev/topics/cache/#setting-up-the-cache
.. |multiple cache backends| replace:: *multiple cache backends*

.. _Database caching: http://docs.djangoproject.com/en/dev/topics/cache/#database-caching
.. |Database caching| replace:: *Database caching*

.. we use | | here and above for italics like :ref: in normal links
   (Django intersphinx objects do not include section titles, must use frags)
