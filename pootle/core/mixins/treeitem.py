# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging


__all__ = ('TreeItem', 'CachedTreeItem')


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
