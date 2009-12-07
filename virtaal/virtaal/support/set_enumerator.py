#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Zuza Software Foundation
#
# This file is part of Virtaal.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import gobject
from bisect import bisect_left

from virtaal.support.sorted_set import SortedSet


# FIXME: Add docstrings!

class UnionSetEnumerator(gobject.GObject):
    __gtype_name__ = "UnionSetEnumerator"

    __gsignals__ = {
        "remove": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_PYOBJECT)),
        "add":    (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_PYOBJECT))
    }

    def __init__(self, *sets):
        gobject.GObject.__init__(self)

        if len(sets) > 0:
            self.sets = sets
            self.set = reduce(lambda big_set, set: big_set.union(set), sets[1:], sets[0])
        else:
            self.sets = [SortedSet([])]
            self.set = SortedSet([])

    #cursor = property(lambda self: self._current_element, _set_cursor)

    def __len__(self):
        return len(self.set.data)

    def __contains__(self, element):
        try:
            return element in self.set
        except IndexError:
            return False

    def _before_add(self, _src, _pos, element):
        if element not in self.set:
            self.set.add(element)
            cursor_pos = bisect_left(self.set.data, element)
            self.emit('add', self, cursor_pos, element)

    def _before_remove(self, _src, _pos, element):
        if element in self.set:
            self.set.remove(element)
            self.emit('remove', self, bisect_left(self.set.data, element), element)

    def cursor_from_element(self, element=None):
        if element != None:
            return Cursor(self, bisect_left(self.set.data, element))
        else:
            return Cursor(self)

    def remove(self, element):
        for set_ in self.sets:
            set_.remove(element)
