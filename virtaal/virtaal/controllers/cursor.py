#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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
import logging
from bisect import bisect_left

from virtaal.common import GObjectWrapper


class Cursor(GObjectWrapper):
    """
    Manages the current position in an arbitrary model.

    NOTE: Assigning to C{self.pos} causes the "cursor-changed" signal
    to be emitted.
    """

    __gtype_name__ = "Cursor"

    __gsignals__ = {
        "cursor-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "cursor-empty": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }


    # INITIALIZERS #
    def __init__(self, model, indices, circular=True):
        """Constructor.
            @type  model: anything
            @param model: The model (usually a collection) to which the cursor is applicable.
            @type  indices: ordered collection
            @param indices: The valid values for C{self.index}."""
        GObjectWrapper.__init__(self)

        self.model = model
        self._indices = indices
        self.circular = circular

        self._pos = 0


    # ACCESSORS #
    def _get_pos(self):
        return self._pos
    def _set_pos(self, value):
        if value == self._pos:
            return # Don't unnecessarily move the cursor (or emit 'cursor-changed', more specifically)
        if value >= len(self.indices):
            self._pos = len(self.indices) - 1
        elif value < 0:
            self._pos = 0
        else:
            self._pos = value
        self.emit('cursor-changed')
    pos = property(_get_pos, _set_pos)

    def _get_index(self):
        l_indices = len(self._indices)
        if l_indices < 1:
            return -1
        if self.pos >= l_indices:
            return l_indices - 1
        return self._indices[self.pos]
    def _set_index(self, index):
        """Move the cursor to the cursor to the position specified by C{index}.
            @type  index: int
            @param index: The index that the cursor should point to."""
        self.pos = bisect_left(self._indices, index)
    index = property(_get_index, _set_index)

    def _get_indices(self):
        return self._indices
    def _set_indices(self, value):
        oldindex = self.index
        oldpos = self.pos

        self._indices = list(value)

        self.index = oldindex
        if len(self._indices) == 0:
            self.emit('cursor-empty')
        if oldpos == self.pos and oldindex != self.index:
            self.emit('cursor-changed')
    indices = property(_get_indices, _set_indices)

    # METHODS #
    def deref(self):
        """Dereference the cursor to the item in the model that the cursor is
            currently pointing to.

            @returns: C{self.model[self.index]}, or C{None} if any error occurred."""
        try:
            return self.model[self.index]
        except Exception:
            logging.debug('Unable to dereference cursor')
            return None

    def force_index(self, index):
        """Force the cursor to move to the given index, even if it is not in the
            C{self.indices} list.
            This should only be used when absolutely necessary. Be prepared to
            deal with the consequences of using this method."""
        oldindex = self.index
        if index not in self.indices:
            newindices = list(self.indices)
            insert_pos = bisect_left(self.indices, index)
            if insert_pos == len(self.indices):
                newindices.append(index)
            else:
                newindices.insert(insert_pos, index)
            self.indices = newindices
        self.index = index

    def move(self, offset):
        """Move the cursor C{offset} positions down.
            The cursor will wrap around to the beginning if C{circular=True}
            was given when the cursor was created."""
        # FIXME: Possibly contains off-by-one bug(s)
        if 0 <= self.pos + offset < len(self._indices):
            self.pos += offset
        elif self.circular:
            if self.pos + offset >= 0:
                self.pos = self.pos + offset - len(self._indices)
            elif self.pos + offset < 0:
                self.pos = self.pos + offset + len(self._indices)
        else:
            raise IndexError()
