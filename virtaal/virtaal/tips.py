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

"""These are some tips that are displayed to the user."""

from gettext import gettext as _


tips = [
    _("At the end of a translation, simply press <Enter> to continue with the next one."),
    _("To copy the original string into the target field, simply press <Alt+Down>."),
    #_("When editing a fuzzy translation, the fuzzy marker will automatically be removed."),
    # l10n: Refer to the translation of "Fuzzy" to find the appropriate shortcut key to recommend
    _("To mark the current translation as fuzzy, simply press <Alt+U>."),
    _("Use Ctrl+Up or Ctrl+Down to move between translations."),
    _("Use Ctrl+PgUp or Ctrl+PgDown to move in large steps between translations."),
]
