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

from pootle_misc.util import getfromcache
from pootle_statistics.models import Submission

class TreeItem():
    children = None
    initialized = False

    def get_name(self):
        """This method will be overridden in descendants"""
        return ''

    def get_children(self):
        """This method will be overridden in descendants"""
        return []

    def _get_total_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_translated_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_untranslated_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_fuzzy_wordcount(self):
        """This method will be overridden in descendants"""
        return 0

    def _get_suggestion_count(self):
        """This method will be overridden in descendants"""
        return 0

    def initialize_children(self):
        if not self.initialized:
            self.children = self.get_children()
            self.initialized = True

    @getfromcache
    def get_total_wordcount(self):
        """calculate total wordcount statistics"""
        self.initialize_children()
        return (self._get_total_wordcount() +
                self._sum('get_total_wordcount'))

    @getfromcache
    def get_translated_wordcount(self):
        """calculate translated units statistics"""
        self.initialize_children()
        return (self._get_translated_wordcount() +
                self._sum('get_translated_wordcount'))

    @getfromcache
    def get_fuzzy_wordcount(self):
        """calculate untranslated units statistics"""
        self.initialize_children()
        return (self._get_fuzzy_wordcount() +
                self._sum('get_fuzzy_wordcount'))

    @getfromcache
    def get_untranslated_wordcount(self):
        """calculate untranslated units statistics"""
        self.initialize_children()
        return (self._get_untranslated_wordcount() +
                self._sum('get_untranslated_wordcount'))

    @getfromcache
    def get_suggestion_count(self):
        """check if any child store has suggestions"""
        self.initialize_children()
        return (self._get_suggestion_count() +
                self._sum('get_suggestion_count'))

    @getfromcache
    def get_last_action(self):
        """get last action HTML snippet"""
        self.initialize_children()

        return max(
            [item.get_last_action() for item in self.children],
            key=lambda x: x.mtime if hasattr(x, 'mtime') else 0
        )

    @getfromcache
    def get_mtime(self):
        """get latest modification time"""
        self.initialize_children()
        return max([
            item.get_mtime() for item in self.children
        ])

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
            'untranslated': self.get_untranslated_wordcount(),
            'suggestions': self.get_suggestion_count(),
            'lastaction': self.get_last_action(),
        }

        if include_children:
            result['children'] = {}
            for item in self.children:
                result['children'][item.get_name()] = item.get_stats(False)

        return result
