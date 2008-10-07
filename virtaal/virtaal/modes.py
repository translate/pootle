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


class BidiIterator(object):
    def __init__(self, itr):
        self.itr  = iter(itr)
        self.hist = []
        self.pos  = -1

    def next(self):
        if self.pos < len(self.hist) - 1:
            val = self.hist[self.pos]
            self.pos += 1
            return val
        else:
            self.hist.append(self.itr.next())
            self.pos += 1
            return self.hist[-1]

    def prev(self):
        if self.pos > -1:
            val = self.hist[self.pos]
            self.pos -= 1
            return val
        else:
            raise StopIteration()

    def __iter__(self):
        return self


class BaseMode(UnionSetEnumerator):
    """Interface for other modes."""
    mode_name = 'BaseMode'
    user_name = '' # Sublcasses should mark this for translation with _()
    widgets = []

    def __init__(self):
        raise NotImplementedError()

    def selected(self, document):
        """Signals that this mode has just been selected by the given document.
            @type  document: virtaal.document.Document
            @param document: The document for which this mode was selected."""
        raise NotImplementedError()

    def unit_changed(self, editor):
        """The selected unit has just changed.
            @type  editor: virtaal.unit_editor.UnitEditor
            @param editor: The unit editor of the newly selected unit."""
        raise NotImplementedError()

    def unselected(self):
        """Signals that this mode is unselected."""
        raise NotImplementedError()


class DefaultMode(BaseMode):
    mode_name = "Default"
    user_name = _("All")
    widgets = []

    def __init__(self):
        UnionSetEnumerator.__init__(self)

    def selected(self, document):
        """This mode has just been selected, so we update this instance to match all units."""
        UnionSetEnumerator.__init__(self, SortedSet(document.stats['total']))

    def unit_changed(self, editor):
        """This mode has nothing to do with selected units."""
        pass

    def unselected(self):
        """This mode has nothing to do when unselected."""
        pass


class QuickTranslateMode(BaseMode):
    mode_name = "Quick Translate"
    user_name = _("Incomplete")
    widgets = []

    def __init__(self):
        UnionSetEnumerator.__init__(self)

    def selected(self, document):
        """This mode has just been selected, so we update this instance to match all fuzzy/untranslated units."""
        UnionSetEnumerator.__init__(self, SortedSet(document.stats['fuzzy']), SortedSet(document.stats['untranslated']))

    def unit_changed(self, editor):
        """This mode has nothing to do with selected units."""
        pass

    def unselected(self):
        """This mode has nothing to do when unselected."""
        pass


from virtaal.search_mode import SearchMode

MODES = dict( (klass.mode_name, klass()) for klass in globals().itervalues() if hasattr(klass, 'mode_name') and klass != BaseMode )
