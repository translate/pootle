# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging


__all__ = ('TreeItem', 'CachedTreeItem', 'CachedMethods')


logger = logging.getLogger('stats')


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
    # this is here for models/migrations that have it as a base class
    pass
