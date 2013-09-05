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


def pullmethodname(function):
    def _wrap(instance, *args, **kwargs):
        arg_list = [ a for a in args ]
        arg_list.append(function.__name__)
        return function(instance, *arg_list, **kwargs)
    return _wrap


class TreeItem():
    def get_name(self):
        return ''

    def get_children(self):
        return None

    def _get_children(self, children):
        if children:
            return children
        else:
            return self.get_children()

    @getfromcache
    def get_mtime(self, children=None):
        return max([
            item.get_mtime() for item in self._get_children(children)
        ])

    @getfromcache
    def get_total_wordcount(self, children=None):
        """calculate total wordcount statistics"""
        return self._get_sum_by_attr_name(children, 'get_total_wordcount')

    @getfromcache
    def get_translated_wordcount(self, children=None):
        """calculate translated units statistics"""
        return self._get_sum_by_attr_name(children, 'get_translated_wordcount')

    @getfromcache
    def get_untranslated_wordcount(self, children=None):
        """calculate untranslated units statistics"""
        return self._get_sum_by_attr_name(children, 'get_untranslated_wordcount')

    @getfromcache
    def get_fuzzy_wordcount(self, children=None):
        """calculate untranslated units statistics"""
        return self._get_sum_by_attr_name(children, 'get_fuzzy_wordcount')

    @getfromcache
    def get_suggestion_count(self, children=None):
        """check if any child store has suggestions"""
        return self._get_sum_by_attr_name(children, 'get_suggestion_count')

    def _get_sum_by_attr_name(self, children, name):
        return sum([
            getattr(item, name)() for item in self._get_children(children)
        ])

    def get_stats(self, with_children=True):
        children = self.get_children()
        result = {
            'total': self.get_total_wordcount(children),
            'fuzzy': self.get_fuzzy_wordcount(children),
            'translated': self.get_translated_wordcount(children),
            'untranslated': self.get_untranslated_wordcount(children),
            'suggestions': self.get_suggestion_count(children),
        }
        if with_children:
            result['children'] = {}
            for item in children:
                result['children'][item.get_name] = item.get_stats(False)

    def get_last_action(self):
        try:
            return ''#Submission.get_latest_for_dir(resource_obj) TODO refactor
        except Submission.DoesNotExist:
            return ''