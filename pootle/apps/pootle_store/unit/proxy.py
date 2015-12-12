# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_store.fields import to_python as multistring_to_python


class UnitProxy(object):
    """Wraps a values Unit dictionary"""

    @property
    def source(self):
        return multistring_to_python(self.unit["source_f"])

    @property
    def target(self):
        return multistring_to_python(self.unit["target_f"])

    def __init__(self, unit):
        self.unit = unit

    def __getattr__(self, k):
        try:
            return self.__dict__["unit"][k] or ""
        except KeyError:
            return self.__getattribute__(k)

    def getlocations(self):
        if self.locations is None:
            return []
        return filter(None, self.locations.split('\n'))

    def hasplural(self):
        return (
            self.source is not None
            and (len(self.source.strings) > 1
                 or getattr(self.source, "plural", None)))
