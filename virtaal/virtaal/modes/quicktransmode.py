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

from virtaal.support.set_enumerator import UnionSetEnumerator
from virtaal.support.sorted_set import SortedSet

from basemode import BaseMode


class QuickTranslateMode(BaseMode):
    """Quick translate mode - Include only untranslated and fuzzy units."""

    name = 'QuickTranslate'
    display_name = _("Incomplete")
    widgets = []

    # INITIALIZERS #
    def __init__(self, controller):
        """Constructor.
            @type  controller: virtaal.controllers.ModeController
            @param controller: The ModeController that managing program modes."""
        self.controller = controller


    # METHODS #
    def selected(self):
        cursor = self.controller.main_controller.store_controller.cursor
        if not cursor or not cursor.model:
            return

        indices = list(UnionSetEnumerator(
            SortedSet(cursor.model.stats['untranslated']),
            SortedSet(cursor.model.stats['fuzzy'])
        ).set)

        if not indices:
            self.controller.select_default_mode()
            return

        cursor.indices = indices

    def unselected(self):
        pass
