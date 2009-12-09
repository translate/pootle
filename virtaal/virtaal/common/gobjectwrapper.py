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


class GObjectWrapper(gobject.GObject):
    """
    A wrapper for GObject sub-classes that provides some more powerful signal-
    handling.
    """

    # INITIALIZERS #
    def __init__(self):
        gobject.GObject.__init__(self)
        self._all_signals = gobject.signal_list_names(self.__gtype_name__)
        self._enabled_signals = list(self._all_signals)


    # METHODS #
    def disable_signals(self, signals=[]):
        """Disable all or specified signals."""
        if signals:
            for sig in signals:
                if sig in self._enabled_signals:
                    self._enabled_signals.remove(sig)
        else:
            self._enabled_signals = []

    def enable_signals(self, signals=[]):
        """Enable all or specified signals."""
        if signals:
            for sig in signals:
                if sig not in self._enabled_signals:
                    self._enabled_signals.append(sig)
        else:
            self._enabled_signals = list(self._all_signals) # Enable all signals

    def emit(self, signame, *args):
        if signame in self._enabled_signals:
            #logging.debug('emit("%s", %s)' % (signame, ','.join([repr(arg) for arg in args])))
            gobject.GObject.emit(self, signame, *args)
