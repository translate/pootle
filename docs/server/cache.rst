.. _cache:

Caching System
**************

Pootle uses a caching system to improve performance. It is an essential part
of :doc:`optimizing <optimization>` your Pootle installation. It is based on
Django's caching system, and is used for various things:

- To serve cached (possibly slightly outdated) versions of most pages to
  anonymous users to reduce their impact on server performance.

- To cache bits of the user interface, even for logged in users. Data will not
  be out of date but Pootle still tries to use cache to reduce impact on server
  performance.

- To store the result of expensive calculations like translation statistics.

- To keep track of last update timestamps to avoid unnecessary file operations
  (for example don't attempt to save translations before a download if there
  are no new translations).

Without a well functioning cache system, Pootle could be slow.


.. _cache#cache_backends:

Cache backends
--------------

Django supports multiple cache backends (methods of storing cache data). You
specify which backend to use by changing the value of ``CACHE_BACKEND`` in the
`localsettings.py` file.


.. _cache#memcached:

Memcached
^^^^^^^^^

::

    CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

Memcached is the recommended cache backend, it provides the best performance.
And works fine with multiprocessing servers like Apache. It requires the
`python-memcached` package and a running memcached server. Due to extra
dependencies it is not enabled by default.


.. _cache#memcached_on_unix_sockets:

Memcached on Unix sockets
"""""""""""""""""""""""""

::

    CACHE_BACKEND = 'memcached:unix:/path/to/memcached.sock'

If you don't want Pootle using TCP/IP to access memcached then you can use Unix
sockets.  This is often a situation in hardened installations using SELinux.

You will need to ensure that memcached is running with the ``-s`` option. ::

    memcached -u nobody -s /path/to/memcached.sock -a 0777


.. _cache#database:

Database
^^^^^^^^

::

    CACHE_BACKEND = 'db://pootlecache?max_entries=65536&cull_frequency=16'

Database caching relies on a table in the main Pootle database for storing the
cached data, which makes it suitable for multiprocessing servers, with the
added benefit that the cached data remains intact after a server reboot (unlike
memcached) but it is considerably slower than memcached.

.. versionchanged:: 2.1.1

This is the default cache backend. On new installs and upgrades the required
database will be created.

Users of older versions need to create the cache tables manually if they would
like to switch to the database cache backend using this :doc:`manage.py command
<commands>`::

    ./manage.py createcachetable pootlecache


.. _cache#local_memory:

Local memory
^^^^^^^^^^^^

::

    CACHE_BACKEND = 'locmem:///?max_entries=4096&cull_frequency=5'


.. deprecated:: 2.1

The default was to use this less efficient but simpler memory cache backend.
That default is not suitable at all for multiprocess servers like
:doc:`apache`.

Since it uses in-process memory, it is impossible to update cache across all
processes leading to translation statistics being different for each process,
which often results in users seeing different values on consecutive requests, a
problem easily solved by switching to memcached.

There is little reason to continue using local memory.
