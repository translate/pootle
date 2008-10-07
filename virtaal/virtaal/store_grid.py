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

import logging

import gtk
import gobject

from unit_renderer import UnitRenderer
import store_model


COLUMN_NOTE, COLUMN_UNIT, COLUMN_EDITABLE = 0, 1, 2

def make_renderer(grid):
    renderer = UnitRenderer(grid)
    renderer.connect("editing-done", grid._on_cell_edited, grid.get_model())
    renderer.connect("modified", grid._on_modified)
    return renderer

def make_column(renderer):
    column = gtk.TreeViewColumn(None, renderer, unit=COLUMN_UNIT, editable=COLUMN_EDITABLE)
    column.set_expand(True)
    return column


class UnitGrid(gtk.TreeView):
    __gsignals__ = {
        'modified':(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    def add_accelerator_bindings(self):
        self.accel_group = gtk.AccelGroup()
        self._owner.main_window.add_accel_group(self.accel_group)
        self.accel_group.connect_by_path("<Virtaal>/Navigation/Up", self._move_up)
        self.accel_group.connect_by_path("<Virtaal>/Navigation/Down", self._move_down)
        self.accel_group.connect_by_path("<Virtaal>/Navigation/PgUp", self._move_pgup)
        self.accel_group.connect_by_path("<Virtaal>/Navigation/PgDown", self._move_pgdown)

    def enable_tooltips(self):
        if hasattr(self, "set_tooltip_column"):
            self.set_tooltip_column(COLUMN_NOTE)
        self.set_rules_hint(True)

    def install_callbacks(self):
        self.connect('key-press-event', self._on_key_press)
        self.connect("cursor-changed", self._on_cursor_changed)
        self.connect("button-press-event", self._on_button_press)

    def __init__(self, owner):
        gtk.TreeView.__init__(self, store_model.UnitModel(owner.document.store, list(owner.document.mode_cursor)))

        self._owner = owner
        self.document = self._owner.document
        self.set_headers_visible(False)
        #self.set_direction(gtk.TEXT_DIR_LTR)

        # TODO: Is this really necessary?
        if len(self.get_model()) == 0:
            raise ValueError(_("The file did not contain anything to translate."))

        self.renderer = make_renderer(self)
        self.append_column(make_column(self.renderer))
        self.enable_tooltips()

        self.document.connect("cursor-changed", self._on_document_cursor_changed)

        self.install_callbacks()
        self.add_accelerator_bindings()

        gobject.idle_add(self._activate_editing_path,
                         self.get_model().store_index_to_path(self.document.mode_cursor.deref()))

        # This must be changed to a mutex if you ever consider
        # writing multi-threaded code. However, the motivation
        # for this horrid little variable is so dubious that you'd
        # be better off writing better code. I'm sorry to leave it
        # to you.
        self._waiting_for_row_change = 0

    def _on_document_cursor_changed(self, _document):
        # Select and edit the new row indicated by the new cursor position
        path = self.get_model().store_index_to_path(self.document.mode_cursor.deref())
        self._activate_editing_path(path)

    def _activate_editing_path(self, new_path):
        """Activates the given path for editing."""
        # get the index of the translation unit in the translation store
        #self.get_model().set(self.get_model().get_iter(new_path), COLUMN_EDITABLE, True)
        self.get_model().set_editable(new_path)
        def change_cursor():
            self.set_cursor(new_path, self.get_columns()[0], start_editing=True)
            self._waiting_for_row_change -= 1
        self._waiting_for_row_change += 1
        gobject.idle_add(change_cursor, priority=gobject.PRIORITY_DEFAULT_IDLE)

    def _keyboard_move(self, offset):
        # We don't want to process keyboard move events until we have finished updating
        # the display after a move event. So we use this awful, awful, terrible scheme to
        # keep track of pending draw events. In reality, it should be impossible for
        # self._waiting_for_row_change to be larger than 1, but my superstition led me
        # to be safe about it.
        if self._waiting_for_row_change > 0:
            return True

        try:
            self._owner.set_statusbar_message(self.document.mode_cursor.move(offset))
            path = self.get_model().store_index_to_path(self.document.mode_cursor.deref())
            self._activate_editing_path(path)
        except IndexError:
            pass

        return True

    def _move_up(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(-1)

    def _move_down(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(1)

    def _move_pgup(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(-10)

    def _move_pgdown(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(10)

    def _on_button_press(self, widget, event):
        # If the event did not happen in the treeview, but in the
        # editing widget, then the event window will not correspond to
        # the treeview's drawing window. This happens when the
        # user clicks on the edit widget. But if this happens, then
        # we don't want anything to happen, so we return True.
        if event.window != widget.get_bin_window():
            return True
        answer = self.get_path_at_pos(int(event.x), int(event.y))
        if answer is None:
            logging.debug("Not path found at (%d,%d)" % (int(event.x), int(event.y)))
            return True
        old_path, _old_column = self.get_cursor()
        path, _column, _x, _y = answer
        if old_path != path:
            index = self.get_model().path_to_store_index(path)
            if index not in self.document.mode:
                logging.debug("Falling to default")
                from virtaal.modes import MODES
                self.document.set_mode(MODES['Default']) # FIXME: This module should not need to import modes

            self.document.mode_cursor = self.document.mode.cursor_from_element(index)
            self._activate_editing_path(path)
        return True

    def on_configure_event(self, _event, *_user_args):
        path, column = self.get_cursor()

        # Horrible hack.
        # We use set_cursor to cause the editable area to be recreated so that
        # it can be drawn correctly. This has to be delayed (we used idle_add),
        # since calling it immediately after columns_autosize() does not work.
        def reset_cursor():
            if path != None:
                self.set_cursor(path, column, start_editing=True)
            return False

        self.columns_autosize()
        gobject.idle_add(reset_cursor)

        return False

    def _on_modified(self, _widget):
        self.emit("modified")
        return True

    def _on_cell_edited(self, _cell, _path_string, must_advance, _modified, _model):
        if must_advance:
            return self._keyboard_move(1)
        return True

    def _on_cursor_changed(self, _treeview):
        path, _column = self.get_cursor()

        # We defer the scrolling until GTK has finished all its current drawing
        # tasks, hence the gobject.idle_add. If we don't wait, then the TreeView
        # draws the editor widget in the wrong position. Presumably GTK issues
        # a redraw event for the editor widget at a given x-y position and then also
        # issues a TreeView scroll; thus, the editor widget gets drawn at the wrong
        # position.
        def do_scroll():
            self.scroll_to_cell(path, self.get_column(0), True, 0.5, 0.0)
            return False

        gobject.idle_add(do_scroll)
        return True

    def _on_key_press(self, _widget, _event, _data=None):
        # The TreeView does interesting things with combos like SHIFT+TAB.
        # So we're going to stop it from doing this.
        return True
