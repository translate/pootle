#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
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

__all__ = ('TreeItem', 'CachedMethods',)

#import threading
from datetime import datetime
from functools import wraps

from translate.filters.decorators import Category

from django.core.cache import cache
from django.utils.encoding import iri_to_uri

from pootle.core.log import timecounterlog
from pootle_misc.util import getfromcache, getfromcachebyname, dictsum
from pootle_misc.checks import get_qualitychecks_by_category, get_qualitychecks


def statslog(function):
    @wraps(function)
    def _statslog(instance, *args, **kwargs):
        start = datetime.now()
        #globals = threading.local()
        result = function(instance, *args, **kwargs)
        end = datetime.now()
        timecounterlog("%s %s (started at %s) executed in %s" % (instance.get_cachekey(), function.__name__, start, end - start))
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


class TreeItem(object):
    children = None
    initialized = False
    _flagged_for_deletion = set()

    def get_children(self):
        """This method will be overridden in descendants"""
        return []

    def get_parent(self):
        """This method will be overridden in descendants"""
        return None

    def get_cachekey(self):
        """This method will be overridden in descendants"""
        raise NotImplementedError('`get_cache_key()` not implemented')

    def _get_total_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_translated_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_fuzzy_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_suggestion_count(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_checks(self):
        """This method will be overridden in descendants"""
        return {}

    def _get_last_action(self):
        """This method will be overridden in descendants"""
        return {'id': 0 , 'mtime': 0, 'snippet': ''}

    def _get_mtime(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_all_checks(self):
        """This method will be overridden in descendants"""
        return {}

    def _get_check_by_name(self, name):
        """This method will be overridden in descendants"""
        return 0

    def initialize_children(self):
        if not self.initialized:
            self.children = self.get_children()
            self.initialized = True

    @getfromcache
    @statslog
    def get_total_wordcount(self):
        """calculate total wordcount statistics"""
        self.initialize_children()
        return (self._get_total_wordcount() +
                self._sum('get_total_wordcount'))

    @getfromcache
    @statslog
    def get_translated_wordcount(self):
        """calculate translated units statistics"""
        self.initialize_children()
        return (self._get_translated_wordcount() +
                self._sum('get_translated_wordcount'))

    @getfromcache
    @statslog
    def get_fuzzy_wordcount(self):
        """calculate untranslated units statistics"""
        self.initialize_children()
        return (self._get_fuzzy_wordcount() +
                self._sum('get_fuzzy_wordcount'))

    @getfromcache
    @statslog
    def get_suggestion_count(self):
        """check if any child store has suggestions"""
        self.initialize_children()
        return (self._get_suggestion_count() +
                self._sum('get_suggestion_count'))

    @getfromcache
    @statslog
    def get_last_action(self):
        """get last action HTML snippet"""
        self.initialize_children()

        return max(
            [self._get_last_action()] +
            [item.get_last_action() for item in self.children],
            key=lambda x: x['mtime'] if 'mtime' in x else 0
        )

    @getfromcache
    @statslog
    def get_mtime(self):
        """get latest modification time"""
        self.initialize_children()
        return max(
            [self._get_mtime()] +
            [item.get_mtime() for item in self.children]
        )

    def _sum(self, name):
        return sum([
            getattr(item, name)() for item in self.children
        ])

    def get_stats(self, include_children=True):
        """get stats for self and - optionally - for children"""
        self.initialize_children()

        result = {
            'total': self.get_total_wordcount(),
            'translated': self.get_translated_wordcount(),
            'fuzzy': self.get_fuzzy_wordcount(),
            'suggestions': self.get_suggestion_count(),
            'lastaction': self.get_last_action(),
            'critical': self.get_critical()
        }

        if include_children:
            result['children'] = {}
            for item in self.children:
                result['children'][item.code] = item.get_stats(False)

        return result

    @getfromcache
    @statslog
    def get_checks(self):
        result = self._get_checks()
        self.initialize_children()
        for item in self.children:
            result = dictsum(result, item.get_checks())

        return result

    def get_all_checks(self):
        result = {}

        self.initialize_children()
        for check in list(get_qualitychecks):
            result[check] = self.get_checks_by_name(check)

        return result

    def get_critical(self):
        check_stats = self.get_checks()

        return sum(map(lambda x: check_stats[x] if x in check_stats else 0,
                       get_qualitychecks_by_category(Category.CRITICAL)))

    def get_critical1(self):
        """Alter implementaion (pick up every check separately)"""
        result = 0

        for check in get_qualitychecks_by_category(Category.CRITICAL):
            result += self.get_checks_by_name(check)

        return result

    @getfromcachebyname
    def get_checks_by_name(self, name):
        result = self._get_check_by_name(name)
        self.initialize_children()
        for item in self.children:
            result += item.get_checks_by_name(name)

        return result

    def get_critical_url(self):
        critical = ','.join(get_qualitychecks_by_category(Category.CRITICAL))
        return self.get_translate_url(check=critical)

    def _delete_from_cache(self, keys):
        parent = self.get_parent()
        if parent:
            parent._delete_from_cache(keys)
        for key in keys:
            cachekey = iri_to_uri(self.get_cachekey() + ":" + key)
            cache.delete(cachekey)

    def update_cache(self):
        self._delete_from_cache(self._flagged_for_deletion)
        self._flagged_for_deletion = set()

    def flag_for_deletion(self, *args):
        for key in args:
            self._flagged_for_deletion.add(key)

    def flush_cache(self, children=True):
        for a in filter(lambda x: x[:2] != '__', dir(CachedMethods)):
            cachekey = iri_to_uri(self.get_cachekey() + ":" +
                                  getattr(CachedMethods, a))
            cache.delete(cachekey)

        if children:
            self.initialize_children()
            for item in self.children:
                item.flush_cache()
