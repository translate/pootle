# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
from datetime import datetime
from functools import wraps

from django.utils.encoding import iri_to_uri

from pootle.core.cache import get_cache
from pootle.core.url_helpers import get_all_pootle_paths


__all__ = ('TreeItem', 'CachedTreeItem', 'CachedMethods')


logger = logging.getLogger('stats')
cache = get_cache('stats')


def statslog(function):
    @wraps(function)
    def _statslog(instance, *args, **kwargs):
        start = datetime.now()
        result = function(instance, *args, **kwargs)
        end = datetime.now()
        logger.info("%s(%s)\t%s\t%s", function.__name__, ', '.join(args),
                    end - start, instance.get_cachekey())
        return result
    return _statslog


class NoCachedStats(Exception):
    pass


class CachedMethods(object):
    """Cached method names."""

    CHECKS = 'get_checks'
    WORDCOUNT_STATS = 'get_wordcount_stats'
    LAST_ACTION = 'get_last_action'
    SUGGESTIONS = 'get_suggestion_count'
    MTIME = 'get_mtime'
    LAST_UPDATED = 'get_last_updated'

    # Check refresh_stats command when add a new CachedMethod

    @classmethod
    def get_all(cls):
        return [getattr(cls, x) for x in
                filter(lambda x: x[:2] != '__' and x != 'get_all', dir(cls))]


class TreeItem(object):
    def __init__(self, *args, **kwargs):
        self._children = None
        self.initialized = False
        super(TreeItem, self).__init__()

    def get_children(self):
        """This method will be overridden in descendants"""
        return []

    def set_children(self, children):
        self._children = children
        self.initialized = True

    def get_parents(self):
        """This method will be overridden in descendants"""
        return []

    def get_cachekey(self):
        """This method will be overridden in descendants"""
        raise NotImplementedError('`get_cachekey()` not implemented')

    def initialize_children(self):
        if not self.initialized:
            self._children = self.get_children()
            self.initialized = True

    @property
    def children(self):
        if not self.initialized:
            self.initialize_children()
        return self._children

    def get_critical_url(self, **kwargs):
        return self.get_translate_url(check_category='critical', **kwargs)


class CachedTreeItem(TreeItem):

    def __init__(self, *args, **kwargs):
        self._dirty_cache = set()
        super(CachedTreeItem, self).__init__()

    # # # # # # #  Update stats in Redis Queue Worker process # # # # # # # #

    def all_pootle_paths(self):
        """Get cache_key for all parents (to the Language and Project)
        of current TreeItem
        """
        return get_all_pootle_paths(self.get_cachekey())

    def can_be_updated(self):
        """This method will be overridden in descendants"""
        return True

    def set_cached_value(self, name, value):
        key = iri_to_uri(self.get_cachekey() + ":" + name)
        return cache.set(key, value, None)

    def get_cached_value(self, name):
        key = iri_to_uri(self.get_cachekey() + ":" + name)
        return cache.get(key)

    @statslog
    def update_cached(self, name):
        """calculate stat value and update cached value"""
        self.set_cached_value(name, self._calc(name))

    def get_cached(self, name):
        """get stat value from cache"""
        result = self.get_cached_value(name)
        if result is None:

            msg = u"cache miss %s for %s(%s)" % (name, self.get_cachekey(),
                                                 self.__class__)
            logger.info(msg)
            raise NoCachedStats(msg)

        return result
