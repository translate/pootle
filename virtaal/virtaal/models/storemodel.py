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

import os
import gobject
import logging
import time
from translate.storage import factory, statsdb
from translate.filters import checks
from translate.convert import pot2po

from translate.storage import ts2 as ts
from translate.storage.poheader import poheader, tzstring

from virtaal.common import pan_app

from basemodel import BaseModel


class StoreModel(BaseModel):
    """
    This model represents a translation store/file. It is basically a wrapper
    for the C{translate.storage.store} class. It is mostly based on the old
    C{Document} class from Virtaal's pre-MVC days.
    """

    __gtype_name__ = "StoreModel"

    # INITIALIZERS #
    def __init__(self, filename, controller):
        super(StoreModel, self).__init__()
        self.controller = controller
        self.load_file(filename)


    # SPECIAL METHODS #
    def __getitem__(self, index):
        """Alias for C{get_unit}."""
        return self.get_unit(index)

    def __len__(self):
        if not self._trans_store:
            return -1
        return len(self._valid_units)


    # ACCESSORS #
    def get_filename(self):
        return self._trans_store and self._trans_store.filename or None

    def get_source_language(self):
        """Return the current store's source language."""
        candidate = self._trans_store.units[0].getsourcelanguage()
        # If we couldn't get the language from the first unit, try the store
        if candidate is None:
            candidate = self._trans_store.getsourcelanguage()
        if candidate and not candidate in ['und', 'en', 'en_US']:
            return candidate

    def set_source_language(self, langcode):
        self._trans_store.setsourcelanguage(langcode)

    def get_target_language(self):
        """Return the current store's target language."""
        candidate = self._trans_store.units[0].gettargetlanguage()
        # If we couldn't get the language from the first unit, try the store
        if candidate is None:
            candidate = self._trans_store.gettargetlanguage()
        if candidate and candidate != 'und':
            return candidate

    def set_target_language(self, langcode):
        self._trans_store.settargetlanguage(langcode)

    def get_unit(self, index):
        """Get a specific unit by index."""
        return self._trans_store.units[self._valid_units[index]]

    def get_units(self):
        # TODO: Add caching
        """Return the current store's (filtered) units."""
        return [self._trans_store.units[i] for i in self._valid_units]

    # METHODS #
    def load_file(self, filename):
        # Adapted from Document.__init__()
        if not os.path.exists(filename):
            raise IOError(_('The file "%s" does not exist.') % filename)
        if not os.path.isfile(filename):
            raise IOError(_('"%s" is not a usable file.') % filename)
        logging.info('Loading file %s' % (filename))
        self._trans_store = factory.getobject(filename)
        self.filename = filename
        self.stats = statsdb.StatsCache().filestats(filename, checks.UnitChecker(), self._trans_store)
        self._correct_header(self._trans_store)
        self._get_valid_units()
        self.nplurals = self._compute_nplurals(self._trans_store)

    def save_file(self, filename=None):
        self._update_header()
        if filename is None:
            filename = self.filename
        if filename == self.filename:
            self._trans_store.save()
        else:
            self._trans_store.savefile(filename)
        self.stats = statsdb.StatsCache().filestats(filename, checks.UnitChecker(), self._trans_store)
        self._get_valid_units()

    def update_file(self, filename):
        # Adapted from Document.__init__()
        newstore = factory.getobject(filename)
        oldfilename = self._trans_store.filename

        #get a copy of old stats before we convert
        oldstats = statsdb.StatsCache().filestats(oldfilename, checks.UnitChecker(), self._trans_store)

        self._trans_store = pot2po.convert_stores(newstore, self._trans_store, fuzzymatching=False)

        #FIXME: ugly tempfile hack, can we please have a pure store implementation of statsdb
        import tempfile
        import os
        tempfd, tempfilename = tempfile.mkstemp()
        os.write(tempfd, str(self._trans_store))
        self.stats = statsdb.StatsCache().filestats(tempfilename, checks.UnitChecker(), self._trans_store)
        os.close(tempfd)
        os.remove(tempfilename)

        self.controller.compare_stats(oldstats, self.stats)

        # store filename or else save is confused
        self._trans_store.filename = oldfilename
        self._get_valid_units()
        self._correct_header(self._trans_store)
        self.nplurals = self._compute_nplurals(self._trans_store)

    def _compute_nplurals(self, store):
        # Copied as-is from Document._compute_nplurals()
        # FIXME this needs to be pushed back into the stores, we don't want to import each format
        if isinstance(store, poheader):
            nplurals, _pluralequation = store.getheaderplural()
            if nplurals is None:
                return
            return int(nplurals)
        elif isinstance(store, ts.tsfile):
            return store.nplural()

    def _correct_header(self, store):
        """This ensures that the file has a header if it is a poheader type of
        file, and fixes the statistics if we had to add a header."""
        # Copied as-is from Document._correct_header()
        if isinstance(store, poheader) and not store.header():
            store.updateheader(add=True)
            new_stats = {}
            for key, values in self.stats.iteritems():
                new_stats[key] = [value+1 for value in values]
            self.stats = new_stats

    def _get_valid_units(self):
        self._valid_units = self.stats['total']

        if not self.stats['total']:
            return

        # Adjust stats
        index_start = self.stats['total'][0]
        for key in self.stats:
            self.stats[key] = [(i - index_start) for i in self.stats[key]]

    def _update_header(self):
        """Make sure that headers are complete and update with current time (if applicable)."""
        # This method comes from Virtaal 0.2's main_window.py:Virtaal._on_file_save().
        # It makes sure that, if we are working with a PO file, that all header info is present.
        if isinstance(self._trans_store, poheader):
            name = self.controller.main_controller.get_translator_name()
            email = self.controller.main_controller.get_translator_email()
            team = self.controller.main_controller.get_translator_team()
            if name is None or email is None or team is None:
                # User cancelled
                raise Exception('Save cancelled.')
            pan_app.settings.translator["name"] = name
            pan_app.settings.translator["email"] = email
            pan_app.settings.translator["team"] = team
            pan_app.settings.write()

            header_updates = {}
            header_updates["PO_Revision_Date"] = time.strftime("%Y-%m-%d %H:%M") + tzstring()
            header_updates["X_Generator"] = pan_app.x_generator
            if name or email:
                header_updates["Last_Translator"] = u"%s <%s>" % (name, email)
                self._trans_store.updatecontributor(name, email)
            if team:
                header_updates["Language-Team"] = team
            header_updates["Language"] = self.controller.main_controller.lang_controller.target_lang.code
            if self.controller.main_controller.lang_controller.target_lang.plural:
                self._trans_store.updateheaderplural(self.controller.main_controller.lang_controller.target_lang.nplurals, self.controller.main_controller.lang_controller.target_lang.plural)
            self._trans_store.updateheader(add=True, **header_updates)
