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

"""This provides the data structure for keeping the undo data."""

import collections

import pan_app
from support.partial import partial


class BoundedQueue(collections.deque):
    def __init__(self, get_size):
        super(BoundedQueue, self).__init__()
        self.current_pos = 0
        self.get_size = get_size

    def push(self, item):
        while len(self) > self.get_size():
            self.popleft()
        self.append(item)


def add_undo_to_buffer(buf):
    buf.__undo_stack = BoundedQueue(lambda: pan_app.settings.undo['depth'])
    buf.insert_handler = buf.connect("insert-text",  on_insert_text,  buf.__undo_stack)
    buf.delete_handler = buf.connect("delete-range", on_delete_range, buf.__undo_stack)
    return buf

def block_change_signals(buf):
    buf.handler_block(buf.insert_handler)
    buf.handler_block(buf.delete_handler)

def unblock_change_signals(buf):
    buf.handler_unblock(buf.insert_handler)
    buf.handler_unblock(buf.delete_handler)

def execute_without_signals(buf, action):
    block_change_signals(buf)
    result = action()
    unblock_change_signals(buf)
    return result

def undo(undo_list):
    if len(undo_list) > 0:
        action = undo_list.pop()
        return action()
    return False

def on_delete_range(buf, start_iter, end_iter, undo_list):
    offset = start_iter.get_offset()
    text = buf.get_text(start_iter, end_iter)

    def undo():
        buf.delete_selection(False, True)
        start_iter = buf.get_iter_at_offset(offset)
        execute_without_signals(buf, partial(buf.insert, start_iter, text))
        buf.place_cursor(start_iter)
        return True

    undo_list.push(undo)
    return True

def on_insert_text(buf, iter, text, length, undo_list):
    # some weird zero length events waste our time; let's ignore them
    if length < 1:
        return True
    offset = iter.get_offset()

    def undo():
        buf.delete_selection(False, True)
        start_iter = buf.get_iter_at_offset(offset)
        end_iter = buf.get_iter_at_offset(offset + length)
        execute_without_signals(buf, partial(buf.delete, start_iter, end_iter))
        buf.place_cursor(start_iter)
        return True

    undo_list.push(undo)
    return True

def merge_actions(buf, position):
    """Combine the last two undo actions into one. This is useful when we are
    replacing all the buffer contents and such events are seen as a delete
    followed by an insert.

        @type  buf: gtk.TextBuffer
        @param buf: the buffer where the undo actions should be merged
        @type  position: int
        @param position: the wanted position of the cursor if these "two"
            events are to be undone
    """
    if hasattr(buf, '__undo_stack'):
        undostack = buf.__undo_stack
        if len(undostack) > 1:
            undos = (undostack.pop(), undostack.pop())
            def undo():
                undos[0]() and undos[1]()
                buf.place_cursor(buf.get_iter_at_offset(position))
                return True

        else:
            action = undostack.pop()
            def undo():
                action()
                buf.place_cursor(buf.get_iter_at_offset(position))
                return True

        undostack.push(undo)
