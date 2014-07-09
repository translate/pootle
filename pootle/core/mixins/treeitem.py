#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
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

from translate.filters.decorators import Category

from django.core.cache import cache
from django.utils.encoding import iri_to_uri

from pootle_misc.util import (getfromcache, getfromcachebyname, dictsum,
                              get_cached_value, set_cached_value, datetime_min)
from pootle_misc.checks import get_qualitychecks_by_category


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

    @classmethod
    def get_all(self):
        return [getattr(self, x) for x in
                filter(lambda x: x[:2] != '__' and x != 'get_all', dir(self))]


class TreeItem(object):
    def __init__(self, *args, **kwargs):
        self.children = None
        self.initialized = False
        self._flagged_for_deletion = set()
        super(TreeItem, self).__init__()

    def get_children(self):
        """This method will be overridden in descendants"""
        return []

    def get_parents(self):
        """This method will be overridden in descendants"""
        return []

    def get_cachekey(self):
        """This method will be overridden in descendants"""
        raise NotImplementedError('`get_cachekey()` not implemented')

    def _get_total_wordcount(self, goal=None):
        """This method will be overridden in descendants"""
        return 0

    def _get_translated_wordcount(self, goal=None):
        """This method will be overridden in descendants"""
        return 0

    def _get_fuzzy_wordcount(self, goal=None):
        """This method will be overridden in descendants"""
        return 0

    def _get_suggestion_count(self, goal=None):
        """This method will be overridden in descendants"""
        return 0

    def _get_critical_error_unit_count(self, goal=None):
        """This method will be overridden in descendants"""
        return 0

    def _get_next_goal_count(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_checks(self):
        """This method will be overridden in descendants"""
        return {'unit_count': 0, 'checks': {}}

    def _get_last_action(self, goal=None):
        """This method will be overridden in descendants"""
        return {'id': 0, 'mtime': 0, 'snippet': ''}

    def _get_mtime(self):
        """This method will be overridden in descendants"""
        return datetime_min

    def _get_last_updated(self, goal=None):
        """This method will be overridden in descendants"""
        return {'id': 0, 'creation_time': 0, 'snippet': ''}

    def initialize_children(self):
        if not self.initialized:
            self.children = self.get_children()
            self.initialized = True

    def get_total_wordcount(self, goal=None):
        """calculate total wordcount statistics"""
        self.initialize_children()
        return (self._get_total_wordcount(goal) +
                self._sum('get_total_wordcount', goal))

    def get_translated_wordcount(self, goal=None):
        """calculate translated units statistics"""
        self.initialize_children()
        return (self._get_translated_wordcount(goal) +
                self._sum('get_translated_wordcount', goal))

    def get_fuzzy_wordcount(self, goal=None):
        """calculate untranslated units statistics"""
        self.initialize_children()
        return (self._get_fuzzy_wordcount(goal) +
                self._sum('get_fuzzy_wordcount', goal))

    def get_suggestion_count(self, goal=None):
        """check if any child store has suggestions"""
        self.initialize_children()
        return (self._get_suggestion_count(goal) +
                self._sum('get_suggestion_count', goal))

    def get_critical_error_unit_count(self, goal=None):
        """Calculate number of units with critical errors."""
        self.initialize_children()
        return (self._get_critical_error_unit_count(goal) +
                self._sum('get_critical_error_unit_count', goal))

    def get_next_goal_count(self):
        """Calculate next goal untranslated statistics."""
        return self._get_next_goal_count()

    def get_last_action(self, goal=None):
        """get last action HTML snippet"""
        self.initialize_children()

        return max(
            [self._get_last_action(goal)] +
            [item.get_last_action(goal) for item in self.get_progeny(goal)],
            key=lambda x: x['mtime'] if 'mtime' in x else 0
        )

    @getfromcache
    def get_mtime(self):
        """get latest modification time"""
        self.initialize_children()
        return max(
            [self._get_mtime()] +
            [item.get_mtime() for item in self.children]
        )

    def get_last_updated(self, goal=None):
        """get last updated"""
        self.initialize_children()
        return max(
            [self._get_last_updated(goal)] +
            [item.get_last_updated(goal) for item in self.get_progeny(goal)],
            key=lambda x: x['creation_time'] if 'creation_time' in x else 0
        )

    def _sum(self, name, goal=None):
        return sum([
            getattr(item, name)(goal) for item in self.get_progeny(goal)
        ])

    def get_stats(self, include_children=True, goal=None):
        """get stats for self and - optionally - for children"""
        self.initialize_children()

        result = self.get_self_stats(goal)

        if include_children:
            result['children'] = {}
            children = self.get_children_for_stats(goal)
            for item in children:
                code = (self._get_code(item) if hasattr(self, '_get_code')
                                             else item.code)
                result['children'][code] = item.get_stats(False, goal)

        return result

    def get_children_for_stats(self, goal=None):
        """Get children for calculating the stats.

        Children means first level descendants.

        This method is meant to be extended for those child models that allow
        drilling down in a goal.
        """
        return self.children

    def get_progeny(self, goal=None):
        """Get progeny for calculating the stats.

        Progeny means descendants for all levels.

        This method is meant to be extended for those child models that allow
        drilling down in a goal.
        """
        return self.children

    def get_self_stats(self, goal=None):
        """Get stats for self.

        This method is meant to be extended for those child models that require
        different stats when drilling down in a goal.
        """
        return {
            'total': self.get_total_wordcount(),
            'translated': self.get_translated_wordcount(),
            'fuzzy': self.get_fuzzy_wordcount(),
            'suggestions': self.get_suggestion_count(),
            'critical': self.get_critical_error_unit_count(),
            'nextGoal': self.get_next_goal_count(),
            'lastupdated': self.get_last_updated(),
            'lastaction': self.get_last_action(),
        }

    @getfromcache
    def get_checks(self):
        result = self._get_checks()
        self.initialize_children()
        for item in self.children:
            item_res = item.get_checks()
            result['checks'] = dictsum(result['checks'], item_res['checks'])
            result['unit_count'] += item_res['unit_count']

        return result

    def get_critical_url(self):
        critical = ','.join(get_qualitychecks_by_category(Category.CRITICAL))
        return self.get_translate_url(check=critical)

    def get_next_goal_url(self):
        return ''

    def _delete_from_cache(self, keys):
        itemkey = self.get_cachekey()
        for key in keys:
            cachekey = iri_to_uri(itemkey + ":" + key)
            cache.delete(cachekey)

        parents = self.get_parents()
        for p in parents:
            p._delete_from_cache(keys)

    def update_cache(self):
        self._delete_from_cache(self._flagged_for_deletion)
        self._flagged_for_deletion = set()

    def flag_for_deletion(self, *args):
        for key in args:
            self._flagged_for_deletion.add(key)

    def flush_cache(self, children=True):
        for name in CachedMethods.get_all():
            cachekey = iri_to_uri(self.get_cachekey() + ":" + name)
            cache.delete(cachekey)

        if children:
            self.initialize_children()
            for item in self.children:
                item.flush_cache()

    def set_last_action(self, last_action):
        set_cached_value(self, 'get_last_action', last_action)
        parents = self.get_parents()
        for p in parents:
            pla = get_cached_value(p, 'get_last_action')
            if pla and pla['mtime'] < last_action['mtime']:
                p.set_last_action(last_action)
