.. _cache:

Caching System
==============

Pootle uses a caching system to improve performance. It is an essential part of
your Pootle installation. It is based on |Django's caching system|_, and is
used for various things:

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
Pootle is configured with a these named caches:

- ``'default'`` -- all non specified cache data and all Django cache data.
- ``'redis'`` --  all RQ data related and revision counter.
- ``'lru'`` --  all lru cache data.

In large installations you may want to setup separate caches to improve cache
performance.  You can then setup caching parameters for each cache separately.


.. _cache#cache_backends:

Cache Backends
--------------

Django supports :ref:`multiple cache backends <django:setting-up-the-cache>`
(methods of storing cache data).  However, Redis is the only cache backend
supported by Pootle.  We use some custom features of Redis so cannot support
other backends. You can customise the Redis cache settings by overriding the
value of :setting:`CACHES` in your configuration file, an example exists in
file:`90-local.conf.sample`.


.. _Django's caching system: https://docs.djangoproject.com/en/1.10/topics/cache/
.. |Django's caching system| replace:: *Django's caching system*

.. we use | | here and above for italics like :ref: in normal links
   (Django intersphinx objects do not include section titles, must use frags)
