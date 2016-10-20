# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from django.conf import settings
from django.core.cache import cache as default_cache, caches
from django.core.cache.backends.base import InvalidCacheBackendError
from django.core.exceptions import ImproperlyConfigured


PERSISTENT_STORES = ('redis',)


def make_method_key(model, method, key):
    """Creates a cache key for model's `method` method.

    :param model: A model instance
    :param method: Method name to cache
    :param key: a unique key to identify the object to be cached
    """
    prefix = 'method-cache'

    if isinstance(model, basestring):
        name = model
    else:
        name = (model.__name__
                if hasattr(model, '__name__')
                else model.__class__.__name__)

    key = make_key(**key) if isinstance(key, dict) else key
    return u':'.join([prefix, name, method, key])


def make_key(*args, **kwargs):
    """Creates a cache key with key-value pairs from a dict."""
    return ':'.join([
        '%s=%s' % (k, v) for k, v in sorted(kwargs.iteritems())
    ])


def get_cache(cache=None):
    """Return ``cache`` or the 'default' cache if ``cache`` is not specified or
    ``cache`` is not configured.

    :param cache: The name of the requested cache.
    """
    try:
        # Check for proper Redis persistent backends
        # FIXME: this logic needs to be a system sanity check
        if (cache in PERSISTENT_STORES and
                (cache not in settings.CACHES or 'RedisCache' not in
                 settings.CACHES[cache]['BACKEND'] or
                 settings.CACHES[cache].get('TIMEOUT', '') is not None)):
            raise ImproperlyConfigured(
                'Pootle requires a Redis-backed caching backend for %r '
                'with `TIMEOUT: None`. Please review your settings.' % cache
            )

        return caches[cache]
    except InvalidCacheBackendError:
        return default_cache
