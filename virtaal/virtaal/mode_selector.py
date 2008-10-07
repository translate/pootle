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
import gtk
import logging

import virtaal.modes


class ModeSelector(gtk.HBox):
    """A composite widget for selecting modes."""

    __gtype_name__ = "ModeSelector"

    __gsignals__ = {
        "mode-combo-changed":  (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    DEFAULT_MODE_NAME = 'Default'

    def __init__(self, document):
        gtk.HBox.__init__(self)
        self.document = document

        # Add mode-selection combo box
        self.cmb_modes = gtk.combo_box_new_text()
        self.cmb_modes.connect('changed', self._on_cmbmode_change)
        self.lbl_mode = gtk.Label()
        self.lbl_mode.set_markup_with_mnemonic(_('_Mode: '))
        self.lbl_mode.set_mnemonic_widget(self.cmb_modes)
        self.pack_start(self.lbl_mode, expand=False)
        self.pack_start(self.cmb_modes, expand=False)

        self.mode_names = {} # mode_name to mode instance map
        self.mode_index = {} # mode instance to index (in cmb_modes) map
        i = 0
        self.default_mode = None
        self.current_mode = None

        for mode in virtaal.modes.MODES.itervalues():
            self.cmb_modes.append_text(mode.user_name)
            self.mode_names[mode.user_name] = mode
            self.mode_index[mode] = i
            i += 1

            if mode.mode_name == self.DEFAULT_MODE_NAME:
                self.default_mode = mode

    def cursor_changed(self, grid):
        """Indirect handler for C{Virtaal.store_grid}'s "cursor-changed" event.

            This method gets the C{UnitEditor} object for the newly selected
            unit and passes it on to all modes' C{handle_unit()} methods. It
            should only be called by a direct handler of the "cursor-changed"
            event.

            @type  grid: UnitGrid
            @param grid: The unit grid object that emitted the original signal.
            """
        self.current_mode.unit_changed(grid.renderer.get_editor(grid))

    def select_mode_by_name(self, mode_name):
        if mode_name in self.mode_names:
            self.cmb_modes.set_active(self.mode_index[self.mode_names[mode_name]])
        else:
            raise ValueError('Unknown mode specified.')

    def set_mode(self, mode):
        # Remove previous mode's widgets
        if self.cmb_modes.get_active() > -1:
            for w in self.get_children():
                if w is not self.cmb_modes and w is not self.lbl_mode:
                    self.remove(w)

        # Select new mode and add its widgets
        self.cmb_modes.set_active(self.mode_index[mode])
        # The line above is needed to make sure that the combo is updated for direct calls to this method.
        for w in mode.widgets:
            if w.get_parent() is None:
                self.pack_start(w, expand=False, padding=2)

        self.show_all()
        mode.selected(self.document)

        if self.current_mode:
            self.current_mode.unselected()
        self.current_mode = mode

    def _on_cmbmode_change(self, combo):
        self.emit('mode-combo-changed', self.mode_names[combo.get_active_text()])
