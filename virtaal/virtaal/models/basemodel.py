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


class BaseModel(gobject.GObject):
    """Base class for all models."""

    __gtype_name__ = "BaseModel"

    __gsignals__ = {
        "loaded": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        "saved":  (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    # INITIALIZERS #
    def __init__(self):
        gobject.GObject.__init__(self)


    # ACCESSORS #
    def is_modified(self):
        return False

    # METHODS #
    def loaded(self):
        """Emits the "loaded" signal."""
        self.emit('loaded')

    def saved(self):
        """Emits the "saved" signal."""
        self.emit('saved')
