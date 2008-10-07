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

import logging

import gobject

from translate.storage.poheader import poheader
from translate.storage import ts2 as ts
from translate.storage import statsdb, factory
from translate.filters import checks
from translate.lang import factory as langfactory

import pan_app
from widgets.entry_dialog import EntryDialog
from mode_selector import ModeSelector


def get_document(obj):
    """See whether obj contains an attribute called 'document'.
    If it does, return the attribute value. Otherwise, see if
    it has a parent (via the attribute 'parent') and ask the
    parent if it contains 'document'. If there is no parent
    and no 'document' attribute, return None."""
    if not hasattr(obj, 'document'):
        if hasattr(obj, 'parent'):
            return get_document(getattr(obj, 'parent'))
        else:
            return None
    else:
        return getattr(obj, 'document')

def compute_nplurals(store):
    def ask_for_language_details():
        def get_content_lang():
            if pan_app.settings.language["contentlang"] != None:
                return pan_app.settings.language["contentlang"]
            else:
                return EntryDialog(_("Please enter the language code for the target language"))

        def ask_for_number_of_plurals():
            while True:
                try:
                    entry = EntryDialog(_("Please enter the number of noun forms (plurals) to use"))
                    return int(entry)
                except ValueError, _e:
                    pass

        def ask_for_plurals_equation():
            return EntryDialog(_("Please enter the plural equation to use"))

        lang     = langfactory.getlanguage(get_content_lang())
        nplurals = lang.nplurals or ask_for_number_of_plurals()
        if nplurals > 1 and lang.pluralequation == "0":
            return nplurals, ask_for_plurals_equation()
        else:
            # Note that if nplurals == 1, the default equation "0" is correct
            return nplurals, lang.pluralequation

    # FIXME this needs to be pushed back into the stores, we don't want to import each format
    if isinstance(store, poheader):
        nplurals, _pluralequation = store.getheaderplural()
        if nplurals is None:
            # Nothing in the header, so let's use the global settings
            settings = pan_app.settings
            nplurals = settings.language["nplurals"]
            pluralequation = settings.language["plural"]
            if not (int(nplurals) > 0 and pluralequation):
                nplurals, pluralequation = ask_for_language_details()
                pan_app.settings.language["nplurals"] = nplurals
                pan_app.settings.language["plural"]   = pluralequation
            store.updateheaderplural(nplurals, pluralequation)
            # If we actually updated something significant, of course the file
            # won't appear changed yet, which is probably what we want.
        return int(nplurals)
    elif isinstance(store, ts.tsfile):
        return store.nplural()
    else:
        return 1

class Document(gobject.GObject):
    """Contains user state about a translate store which stores information like
    GUI-toolkit-independent state (for example bookmarks) and index remappings
    which are needed to"""

    __gtype_name__ = "Document"

    __gsignals__ = {
        "cursor-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, filename, store=None, mode_selector=None):
        gobject.GObject.__init__(self)
        if store:
            self.store = store
        else:
            self.store = factory.getobject(filename)
        if mode_selector is None:
            mode_selector = ModeSelector(self)
        else:
            mode_selector.document = self
        self.stats = statsdb.StatsCache().filestats(filename, checks.UnitChecker(), self.store)
        self._correct_header()
        self.nplurals = compute_nplurals(self.store)
        self.mode = None
        self.mode_cursor = None
        self.mode_selector = mode_selector

        self.set_mode(self.mode_selector.default_mode)
        self.mode_selector.connect('mode-combo-changed', self._on_mode_combo_changed)

    def _correct_header(self):
        """This ensures that the file has a header if it is a poheader type of
        file, and fixes the statistics if we had to add a header."""
        if isinstance(self.store, poheader) and not self.store.header():
            self.store.updateheader(add=True)
            new_stats = {}
            for key, values in self.stats.iteritems():
                new_stats[key] = [value+1 for value in values]
            self.stats = new_stats

    def cursor_changed(self):
        """Emits the "cursor-changed" event, no questions asked."""
        self.emit('cursor-changed')

    def refresh_cursor(self):
        try:
            old_cursor = self.mode_cursor
            if self.mode_cursor != None:
                self.mode_cursor = self.mode.cursor_from_element(self.mode_cursor.deref())
            else:
                self.mode_cursor = self.mode.cursor_from_element()

            if self.mode_cursor.get_pos() < 0:
                try:
                    self.mode_cursor.move(1)
                except IndexError:
                    pass

            if old_cursor and self.mode_cursor and old_cursor.get_pos() != self.mode_cursor.get_pos():
                self.cursor_changed()

            return True
        except IndexError:
            return False

    def set_mode(self, mode):
        logging.debug("Changing document mode to %s" % mode.mode_name)

        self.mode_selector.set_mode(mode)
        self.mode = mode

        self.refresh_cursor()

    def _on_mode_combo_changed(self, _mode_selector, mode):
        self.set_mode(mode)

    def get_source_language(self):
        """Return the current document's source language."""
        candidate = self.store.getsourcelanguage()
        if candidate and not candidate in ['und', 'en', 'en_US']:
            return candidate
        else:
            return pan_app.settings.language["sourcelang"]

    def get_target_language(self):
        """Return the current document's target language."""
        candidate = self.store.gettargetlanguage()
        if candidate and candidate != 'und':
            return candidate
        else:
            return pan_app.settings.language["contentlang"]
