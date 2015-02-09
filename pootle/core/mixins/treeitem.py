#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Zuza Software Foundation
# Copyright 2013-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59

__all__ = ('TreeItem', 'CachedTreeItem', 'CachedMethods')

import logging

from datetime import datetime
from functools import wraps

from translate.filters.decorators import Category

from django.conf import settings
from django.core.urlresolvers import set_script_prefix
from django.utils.encoding import force_unicode, iri_to_uri

from django_rq import job
from django_rq.queues import get_connection

from pootle.core.cache import get_cache
from pootle.core.log import log
from pootle.core.url_helpers import get_all_pootle_paths, split_pootle_path
from pootle_misc.checks import get_qualitychecks_by_category
from pootle_misc.util import datetime_min, dictsum


POOTLE_DIRTY_TREEITEMS = 'pootle:dirty:treeitems'
POOTLE_REFRESH_STATS = 'pootle:refresh:stats'


logger = logging.getLogger('stats')
cache = get_cache('stats')


def statslog(function):
    @wraps(function)
    def _statslog(instance, *args, **kwargs):
        start = datetime.now()
        result = function(instance, *args, **kwargs)
        end = datetime.now()
        logger.info("%s(%s)\t%s\t%s" % (function.__name__, ', '.join(args), end - start,
                                        instance.get_cachekey()))
        return result
    return _statslog


class CachedMethods(object):
    """Cached method names."""
    CHECKS = 'get_checks'
    TOTAL = 'get_total_wordcount'
    TRANSLATED = 'get_translated_wordcount'
    FUZZY = 'get_fuzzy_wordcount'
    LAST_ACTION = 'get_last_action'
    SUGGESTIONS = 'get_suggestion_count'
    MTIME = 'get_mtime'
    LAST_UPDATED = 'get_last_updated'

    # Check refresh_stats command when add a new CachedMethod

    @classmethod
    def get_all(self):
        return [getattr(self, x) for x in
                filter(lambda x: x[:2] != '__' and x != 'get_all', dir(self))]


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

    def get_parents(self):
        """This method will be overridden in descendants"""
        return []

    def get_cachekey(self):
        """This method will be overridden in descendants"""
        raise NotImplementedError('`get_cachekey()` not implemented')

    @classmethod
    def _get_total_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    @classmethod
    def _get_translated_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    @classmethod
    def _get_fuzzy_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    @classmethod
    def _get_suggestion_count(self):
        """This method will be overridden in descendants"""
        return 0

    @classmethod
    def _get_checks(self):
        """This method will be overridden in descendants"""
        return {'unit_critical_error_count': 0, 'checks': {}}

    @classmethod
    def _get_last_action(self):
        """This method will be overridden in descendants"""
        return {'id': 0, 'mtime': 0, 'snippet': ''}

    @classmethod
    def _get_mtime(self):
        """This method will be overridden in descendants"""
        return datetime_min

    @classmethod
    def _get_last_updated(self):
        """This method will be overridden in descendants"""
        return {'id': 0, 'creation_time': 0, 'snippet': ''}

    def is_dirty(self):
        """Checks if any of children is registered as dirty"""
        return any(map(lambda x: x.is_dirty(), self.children))

    def initialize_children(self):
        if not self.initialized:
            self._children = self.get_children()
            self.initialized = True

    @property
    def children(self):
        if not self.initialized:
            self.initialize_children()
        return self._children

    def _calc_sum(self, name, from_update):
        self.initialize_children()
        method = getattr(self, '_%s' % name)
        return (method() +
                sum([item.get_cached(name, from_update)
                     for item in self.children]))

    def _calc_last_action(self, from_update):
        self.initialize_children()

        return max(
            [self._get_last_action()] +
            [item.get_cached(CachedMethods.LAST_ACTION, from_update)
             for item in self.children],
            key=lambda x: x['mtime'] if 'mtime' in x else 0
        )

    def _calc_mtime(self, from_update):
        """get latest modification time"""
        self.initialize_children()
        return max(
            [self._get_mtime()] +
            [item.get_cached(CachedMethods.MTIME, from_update)
             for item in self.children]
        )

    def _calc_last_updated(self, from_update):
        """get last updated"""
        self.initialize_children()
        return max(
            [self._get_last_updated()] +
            [item.get_cached(CachedMethods.LAST_UPDATED, from_update)
             for item in self.children],
            key=lambda x: x['creation_time'] if 'creation_time' in x else 0
        )

    def _calc_checks(self, from_update):
        result = self._get_checks()
        self.initialize_children()
        for item in self.children:
            item_res = item.get_cached(CachedMethods.CHECKS, from_update)
            result['checks'] = dictsum(result['checks'], item_res['checks'])
            result['unit_critical_error_count'] += item_res['unit_critical_error_count']

        return result

    def _calc(self, name, from_update=False):
        if name == CachedMethods.TOTAL:
            return self._calc_sum(CachedMethods.TOTAL, from_update)
        elif name == CachedMethods.TRANSLATED:
            return self._calc_sum(CachedMethods.TRANSLATED, from_update)
        elif name == CachedMethods.FUZZY:
            return self._calc_sum(CachedMethods.FUZZY, from_update)
        elif name == CachedMethods.SUGGESTIONS:
            return self._calc_sum(CachedMethods.SUGGESTIONS, from_update)
        elif name == CachedMethods.LAST_ACTION:
            return self._calc_last_action(from_update)
        elif name == CachedMethods.LAST_UPDATED:
            return self._calc_last_updated(from_update)
        elif name == CachedMethods.CHECKS:
            return self._calc_checks(from_update)
        elif name == CachedMethods.MTIME:
            return self._calc_mtime(from_update)

        return None

    def get_critical_url(self, **kwargs):
        critical = ','.join(get_qualitychecks_by_category(Category.CRITICAL))
        return self.get_translate_url(check=critical, **kwargs)

    def get_stats(self, include_children=True):
        """get stats for self and - optionally - for children"""
        self.initialize_children()

        result = {
            'total': self._calc(CachedMethods.TOTAL),
            'translated': self._calc(CachedMethods.TRANSLATED),
            'fuzzy': self._calc(CachedMethods.FUZZY),
            'suggestions': self._calc(CachedMethods.SUGGESTIONS),
            'lastaction': self._calc(CachedMethods.LAST_ACTION),
            'critical': self.get_error_unit_count(),
            'lastupdated': self._calc(CachedMethods.LAST_UPDATED),
            'is_dirty': self.is_dirty(),
        }

        if include_children:
            result['children'] = {}
            for item in self.children:
                code = (self._get_code(item) if hasattr(self, '_get_code')
                                             else item.code)
                result['children'][code] = item.get_stats(False)

        return result

    def get_error_unit_count(self):
        check_stats = self._calc(CachedMethods.CHECKS)

        return check_stats.get('unit_critical_error_count', 0)

    def get_checks(self):
        return self._calc(CachedMethods.CHECKS)['checks']


class CachedTreeItem(TreeItem):
    def __init__(self, *args, **kwargs):
        self._dirty_cache = set()
        super(CachedTreeItem, self).__init__()

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
        self.set_cached_value(name, self._calc(name, from_update=True))

    def get_cached(self, name, from_update=False):
        """get stat value from cache"""
        result = self.get_cached_value(name)
        if result is None:
            logger.error(
                "cache miss %s for %s(%s)" % (name,
                                              self.get_cachekey(),
                                              self.__class__),
            )
            if not from_update or settings.DEBUG:
                # get initial (empty, zero) value
                result = getattr(CachedTreeItem, '_%s' % name)()

        return result

    def get_checks(self):
        return self.get_cached(CachedMethods.CHECKS)['checks']

    def get_stats(self, include_children=True):
        """get stats for self and - optionally - for children"""
        self.initialize_children()

        result = {
            'total': self.get_cached(CachedMethods.TOTAL),
            'translated': self.get_cached(CachedMethods.TRANSLATED),
            'fuzzy': self.get_cached(CachedMethods.FUZZY),
            'suggestions': self.get_cached(CachedMethods.SUGGESTIONS),
            'lastaction': self.get_cached(CachedMethods.LAST_ACTION),
            'critical': self.get_error_unit_count(),
            'lastupdated': self.get_cached(CachedMethods.LAST_UPDATED),
            'is_dirty': self.is_dirty(),
        }

        if include_children:
            result['children'] = {}
            for item in self.children:
                code = (self._get_code(item) if hasattr(self, '_get_code')
                                             else item.code)
                result['children'][code] = item.get_stats(False)

        return result

    def refresh_stats(self, include_children=True, cached_methods=None):
        """refresh cached stats for self and for children"""
        self.initialize_children()

        if include_children:
            for item in self.children:
                # note that refresh_stats for a Store object does nothing
                item.refresh_stats(cached_methods=cached_methods)

        if cached_methods is None:
            cached_methods = CachedMethods.get_all()

        for name in cached_methods:
            self.update_cached(name)

    def get_error_unit_count(self):
        check_stats = self.get_cached(CachedMethods.CHECKS)

        return check_stats.get('unit_critical_error_count', 0)

    def is_dirty(self):
        """Checks if current TreeItem is registered as dirty"""
        return self.get_dirty_score() > 0 or self.is_being_refreshed()

    def mark_dirty(self, *args):
        """Mark cached method names for this TreeItem as dirty"""
        for key in args:
            self._dirty_cache.add(key)

    def mark_all_dirty(self):
        """Mark all cached method names for this TreeItem as dirty"""
        all_cache_methods = CachedMethods.get_all()
        self._dirty_cache = set(all_cache_methods)

    def _clear_cache(self, keys, parents=True, children=False):
        itemkey = self.get_cachekey()
        for key in keys:
            cachekey = iri_to_uri(itemkey + ":" + key)
            cache.delete(cachekey)
        if keys:
            log("%s deleted from %s cache" % (keys, itemkey))

        if parents:
            parents = self.get_parents()
            for p in parents:
                p._clear_cache(keys, parents=parents, children=False)

        if children:
            self.initialize_children()
            for item in self.children:
                item._clear_cache(keys, parents=False, children=True)

    def clear_dirty_cache(self, parents=True, children=False):
        self._clear_cache(self._dirty_cache,
                          parents=parents, children=children)
        self._dirty_cache = set()

    def clear_all_cache(self, children=True, parents=True):
        all_cache_methods = CachedMethods.get_all()
        self.mark_dirty(*all_cache_methods)
        self.clear_dirty_cache(children=children, parents=parents)

    ################ Update stats in Redis Queue Worker process ###############

    def all_pootle_paths(self):
        """Get cache_key for all parents (to the Language and Project)
        of current TreeItem
        """
        return get_all_pootle_paths(self.get_cachekey())

    def is_being_refreshed(self):
        """Checks if current TreeItem is being refreshed"""
        r_con = get_connection()
        path = r_con.get(POOTLE_REFRESH_STATS)

        if path is not None:
            if path == '/':
                return True

            lang, prj, dir, file = split_pootle_path(path)
            key = self.get_cachekey()

            return key in path or path in key or key in '/projects/%s/' % prj

        return False

    def register_all_dirty(self):
        """Register current TreeItem and all parent paths as dirty
        (should be called before RQ job adding)
        """
        r_con = get_connection()
        for p in self.all_pootle_paths():
            r_con.zincrby(POOTLE_DIRTY_TREEITEMS, p)

    def unregister_all_dirty(self):
        """Unregister current TreeItem and all parent paths as dirty
        (should be called from RQ job procedure after cache is updated)
        """
        r_con = get_connection()
        for p in self.all_pootle_paths():
            r_con.zincrby(POOTLE_DIRTY_TREEITEMS, p, -1)

    def unregister_dirty(self):
        """Unregister current TreeItem as dirty
        (should be called from RQ job procedure after cache is updated)
        """
        r_con = get_connection()
        r_con.zincrby(POOTLE_DIRTY_TREEITEMS, self.get_cachekey(), -1)

    def get_dirty_score(self):
        r_con = get_connection()
        return r_con.zscore(POOTLE_DIRTY_TREEITEMS, self.get_cachekey())

    def update_dirty_cache(self):
        """Add a RQ job which updates dirty cached stats of current TreeItem
        to the default queue
        """
        _dirty = self._dirty_cache.copy()
        if _dirty:
            self._dirty_cache = set()
            self.register_all_dirty()
            update_cache.delay(self, _dirty)

    def update_all_cache(self):
        """Add a RQ job which updates all cached stats of current TreeItem
        to the default queue
        """
        self.mark_all_dirty()
        self.update_dirty_cache()

    def _update_cache(self, keys):
        """Update dirty cached stats of current TreeItem"""
        if self.can_be_updated():
            # children should be recalculated to avoid using of obsolete directories
            # or stores which could be saved in `children` property
            self.initialized = False
            self.initialize_children()
            for key in keys:
                self.update_cached(key)
            for p in self.get_parents():
                p._update_cache(keys)

            self.unregister_dirty()
        else:
            logger.warning('Cache for %s object cannot be updated.' % self)
            self.unregister_all_dirty()

    def update_parent_cache(self):
        """Update dirty cached stats for a all parents of the current TreeItem"""
        all_cache_methods = CachedMethods.get_all()
        for p in self.get_parents():
            p.register_all_dirty()
            update_cache.delay(p, all_cache_methods)

    def init_cache(self):
        """Set initial values for all cached method for the current TreeItem"""
        for method_name in CachedMethods.get_all():
            method = getattr(CachedTreeItem, '_%s' % method_name)
            self.set_cached_value(method_name, method())


@job
def update_cache(instance, keys):
    """RQ job"""
    # The script prefix needs to be set here because the generated
    # URLs need to be aware of that and they are cached. Ideally
    # Django should take care of setting this up, but it doesn't yet:
    # https://code.djangoproject.com/ticket/16734
    script_name = (u'/' if settings.FORCE_SCRIPT_NAME is None
                        else force_unicode(settings.FORCE_SCRIPT_NAME))
    set_script_prefix(script_name)
    instance._update_cache(keys)
