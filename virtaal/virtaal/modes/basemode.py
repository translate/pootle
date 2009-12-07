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


class BaseMode(object):
    """Interface for other modes."""
    name = 'BaseMode'
    """The internal name of the mode."""
    display_name = ''
    """Sublcasses should mark this for translation with _()"""
    widgets = []

    # INITIALIZERS #
    def __init__(self, mode_controller):
        raise NotImplementedError()


    # METHODS #
    def selected(self):
        """Signals that this mode has just been selected by the given document."""
        raise NotImplementedError()

    def unselected(self):
        """This is run right before the mode is unselected."""
        raise NotImplementedError()
