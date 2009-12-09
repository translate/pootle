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

from virtaal.common import GObjectWrapper
from virtaal.modes  import modeclasses
from virtaal.views  import ModeView

from basecontroller import BaseController


class ModeController(BaseController):
    """
    Contains logic for switching and managing unit selection modes.

    In the context of modes, models always represent a specific mode. So it's
    not strictly a data model (as it contains its own logic), but it is the
    standard type of object that is manipulated and handled by this controller
    and C{ModeView} objects.
    """

    __gtype_name__ = 'ModeController'
    __gsignals__ = {
        'mode-selected': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }
    default_mode_name = 'Default'

    # INITIALIZERS #
    def __init__(self, main_controller):
        GObjectWrapper.__init__(self)

        self.main_controller = main_controller
        self.main_controller.mode_controller = self

        self._init_modes()
        self.view = ModeView(self)
        self.view.connect('mode-selected', self._on_mode_selected)

        self.current_mode = None
        self.view.select_mode(self.modenames[self.default_mode_name])

    def _init_modes(self):
        self.modes = {}
        self.modenames = {}

        for modeclass in modeclasses:
            newmode = modeclass(self)
            self.modes[newmode.name] = newmode
            self.modenames[newmode.name] = newmode.display_name


    # ACCESSORS #
    def get_mode_by_display_name(self, displayname):
        candidates = [mode for name, mode in self.modes.items() if mode.display_name == displayname]
        if candidates:
            return candidates[0]


    # METHODS #
    def refresh_mode(self):
        if not self.current_mode:
            self.select_default_mode()
        else:
            self.select_mode(self.current_mode)

    def select_default_mode(self):
        self.select_mode_by_name(self.default_mode_name)

    def select_mode_by_display_name(self, displayname):
        self.select_mode(self.get_mode_by_display_name(displayname))

    def select_mode_by_name(self, name):
        self.select_mode(self.modes[name])

    def select_mode(self, mode):
        if self.current_mode:
            self.view.remove_mode_widgets(self.current_mode.widgets)
            self.current_mode.unselected()

        self.current_mode = mode
        self._ignore_mode_change = True
        self.view.select_mode(self.modenames[mode.name])
        self._ignore_mode_change = False
        self.view.show()
        self.current_mode.selected()
        logging.info('Mode selected: %s' % (self.current_mode.name))
        self.emit('mode-selected', self.current_mode)

    # EVENT HANDLERS #
    def _on_mode_selected(self, _modeview, modename):
        if not getattr(self, '_ignore_mode_change', True):
            self.select_mode(self.get_mode_by_display_name(modename))
