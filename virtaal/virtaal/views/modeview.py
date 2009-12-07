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

from virtaal.common import GObjectWrapper

from baseview import BaseView


class ModeView(GObjectWrapper, BaseView):
    """
    Manages the mode selection on the GUI and communicates with its associated
    C{ModeController}.
    """

    __gtype_name__ = 'ModeView'
    __gsignals__ = {
        "mode-selected":  (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    }

    # INITIALIZERS #
    def __init__(self, controller):
        GObjectWrapper.__init__(self)

        self.controller = controller
        self._build_gui()
        self._load_modes()

    def _build_gui(self):
        # Get the mode container from the main controller
        # We need the *same* glade.XML instance as used by the MainView, because we need
        # the gtk.Table as already added to the main window. Loading the Glade file again
        # would create a new main window with a different gtk.Table.
        gladegui = self.controller.main_controller.view.gui # FIXME: Is this acceptable?
        self.mode_box = gladegui.get_widget('mode_box')

        self.cmb_modes = gtk.combo_box_new_text()
        self.cmb_modes.connect('changed', self._on_cmbmode_change)

        self.lbl_mode = gtk.Label()
        #l10n: This refers to the 'mode' that determines how Virtaal moves
        #between units.
        self.lbl_mode.set_markup_with_mnemonic(_('N_avigation:'))
        self.lbl_mode.props.xpad = 3
        self.lbl_mode.set_mnemonic_widget(self.cmb_modes)

        self.mode_box.attach(self.lbl_mode, 0, 1, 0, 1, xoptions=0, yoptions=0)
        self.mode_box.attach(self.cmb_modes, 1, 2, 0, 1, xoptions=0, yoptions=0)

    def _load_modes(self):
        self.displayname_index = {}
        i = 0
        for name in self.controller.modes:
            displayname = self.controller.modenames[name]
            self.cmb_modes.append_text(displayname)
            self.displayname_index[displayname] = i
            i += 1


    # METHODS #
    def remove_mode_widgets(self, widgets):
        if not widgets:
            return

        # Remove previous mode's widgets
        if self.cmb_modes.get_active() > -1:
            for w in self.mode_box.get_children():
                if w in widgets:
                    self.mode_box.remove(w)

    def select_mode(self, displayname):
        if displayname in self.displayname_index:
            self.cmb_modes.set_active(self.displayname_index[displayname])
        else:
            raise ValueError('Unknown mode specified: %s' % (mode_name))

    def show(self):
        self.mode_box.show_all()

    # EVENT HANDLERS #
    def _on_cmbmode_change(self, combo):
        self.emit('mode-selected', combo.get_active_text())
