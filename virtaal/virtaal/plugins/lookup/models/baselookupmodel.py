#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from virtaal.models import BaseModel


class BaseLookupModel(object):
    """The base interface to be implemented by all look-up backend models."""

    description = ""
    """A description of the backend. This will be displayed to users."""
    display_name = None
    """The backend's name, suitable for display."""

    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        """Initialise the model."""
        raise NotImplementedError()


    # METHODS #
    def create_menu_items(self, query, role, srclang, tgtlang):
        """Create the a list C{gtk.MenuItem}s for the given parameters.

        @type  query: basestring
        @param query: The string to use in the look-up.
        @type  query_is_src: bool
        @param query_is_src: C{True} if C{query} is from a source text box. C{False} otherwise.
        @type  srclang: str
        @param srclang: The language code of the source language.
        @type  tgtlang: str
        @param tgtlang: The language code of the target language."""
        raise NotImplementedError()

    def destroy(self):
        pass
