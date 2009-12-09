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

import logging

from basemodel import BaseModel


class UndoModel(BaseModel):
    """Simple model representing an undo history."""

    # INITIALIZERS #
    def __init__(self, controller):
        self.controller = controller

        super(UndoModel, self).__init__()
        self.index = -1
        self.recording = False
        self.undo_stack = []


    # METHODS #
    def clear(self):
        """Clear the undo stack and reset the index pointer."""
        self.undo_stack = []
        self.index = -1

    def head(self):
        """Get the undo info currently pointed to by C{self.index}."""
        return self.undo_stack[self.index]

    def move(self, offset=1):
        """Move the cursor (C{self.index}) by C{offset}."""
        newindex = self.index + offset
        if not (0 < newindex < len(self.undo_stack)):
            raise IndexError

        self.index = newindex
        return self.undo_stack[self.index]

    def peek(self, index=None, offset=None):
        """Peek at the item at C{index} or C{offset} positions away without
            moving the cursor (C{self.index}) there."""
        if index is not None:
            return self.undo_stack[index]
        if offset is not None:
            return self.undo_stack[self.index + offset]

    def pop(self, permanent=False):
        if not self.undo_stack or not (0 <= self.index < len(self.undo_stack)):
            return None

        if not permanent:
            self.index -= 1
            return self.undo_stack[self.index+1]

        # self.index does not necessarily point to the last element in the list, so we have
        # to throw away the rest of the list first.
        self.undo_stack = self.undo_stack[:self.index]
        item = self.undo_stack.pop()
        self.index = len(self.undo_stack) - 1
        return item

    def push(self, undo_dict):
        """Push an undo-action onto the undo stack.
            @type  undo_dict: dict
            @param undo_dict: A dictionary containing undo information with the
                following keys:
                 - "action": Value is a callable that is called (with the "unit"
                   value, to effect the undo).
                 - "unit": Value is the unit on which the undo-action is applicable.
                 - "targetn": The index of the target on which the undo is applicable.
                 - "cursorpos": The position of the cursor after the undo."""
        for key in ('action', 'unit', 'targetn', 'cursorpos'):
            if not key in undo_dict:
                raise ValueError('Invalid undo dictionary!')

        if self.recording:
            self.undo_stack[-1].append(undo_dict)
        else:
            if self.index < 0:
                self.undo_stack = []
            if self.index != len(self.undo_stack) - 1:
                self.undo_stack = self.undo_stack[:self.index+1]
            self.undo_stack.append(undo_dict)
        self.index = len(self.undo_stack) - 1

    def record_start(self):
        if self.recording:
            raise Exception('Undo already recording.')

        if self.index < 0:
            self.undo_stack = []
        if self.index != len(self.undo_stack) - 1:
            self.undo_stack = self.undo_stack[:self.index]

        self.undo_stack.append([])
        self.index = len(self.undo_stack) - 1
        self.recording = True

    def record_stop(self):
        if not self.recording:
            raise Exception("Undo can't stop recording if it was not recording in the first place.")

        self.recording = False
