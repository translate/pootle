# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict


class Gathered(object):

    def __init__(self, provider):
        self.provider = provider
        self.__results__ = []

    def add_result(self, func, gathered):
        self.__results__.append((func, gathered))


class GatheredDict(Gathered):

    @property
    def results(self):
        gathered = OrderedDict()
        for func_, result in self.__results__:
            if result:
                try:
                    gathered.update(result)
                except TypeError:
                    # Result is ignored if you cant update a dict with it
                    pass
        return gathered

    def get(self, k, default=None):
        try:
            return self[k]
        except KeyError:
            return default

    def keys(self):
        return self.results.keys()

    def values(self):
        return [self[k] for k in self.results]

    def items(self):
        return [(k, self[k]) for k in self.results]

    def __contains__(self, k):
        return k in self.results

    def __getitem__(self, k):
        return self.results[k]

    def __iter__(self):
        for k in self.results.keys():
            yield k


class GatheredList(Gathered):

    @property
    def results(self):
        gathered = []
        for func_, result in self.__results__:
            if isinstance(result, (list, tuple)):
                gathered.extend(result)
        return gathered

    def __iter__(self):
        for item in self.results:
            yield item
