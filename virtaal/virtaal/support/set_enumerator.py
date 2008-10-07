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

class Cursor(gobject.GObject):
    __gtype_name__ = "Cursor"

    def __init__(self, union_set, pos=-1):
        gobject.GObject.__init__(self)
        if pos >= len(union_set):
            # TODO: Push new status message: 'End of page reached, continuing at the top'
            pos = 0
        self.union_set = union_set
        self.union_set.connect('add', self._on_add)
        self.union_set.connect('remove', self._on_remove)
        self._pos = pos

    def _on_add(self, _src, cursor_pos, _element):
        if self._pos >= cursor_pos:
            self._pos += 1

    def _on_remove(self, _src, cursor_pos, _element):
        if self._pos >= cursor_pos:
            self._pos -= 1

    def _assert_valid_index(self, index):
        if not 0 <= index < len(self.union_set):
            raise IndexError()

    def move(self, offset):
        newpos = self._pos + offset
        statusmsg = ''
        try:
            self._assert_valid_index(newpos)
        except IndexError:
            if newpos < 0:
                newpos += len(self.union_set)
                statusmsg = _('Top of page reached, continuing at the bottom')
            else:
                # If we get here, newpos > len(self.union_set.set.data)
                newpos -= len(self.union_set.set.data)
                statusmsg = _('End of page reached, continuing at the top')
        self._pos = newpos
        return statusmsg

    def deref(self, index=None):
        if index == None:
            index = self._pos
        self._assert_valid_index(index)
        return self.union_set.set.data[index]

    def get_pos(self):
        return self._pos

    def __iter__(self):
        def iterator():
            for element in self.union_set.set.data:
                yield element

        return iterator()


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
            for set_ in self.sets:
                set_.connect('before-add', self._before_add)
                set_.connect('before-remove', self._before_remove)
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
