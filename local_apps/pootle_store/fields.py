#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Pootle.
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

"""Utility classes for handling translation files."""

import logging
import os
import shutil
import tempfile

from django.conf import settings
from django.core.files import File
from django.db.models.fields.files import FieldFile, FileField
from django.utils.thread_support import currentThread

from translate.storage import factory, statsdb, po
from translate.filters import checks

from pootle_store.signals import translation_file_updated


class TranslationStoreFile(File):
    """A mixin for use alongside django.core.files.base.File, which provides
    additional features for dealing with translation files."""

    _stats = {}
    __statscache = {}

    def _get_statscache(self):
        """reuse statsdb database connection, keep a pool of one connection per thread"""
        current_thread = currentThread()
        if current_thread not in self.__statscache:
            self.__statscache[current_thread] = statsdb.StatsCache(settings.STATS_DB_PATH)
        return self.__statscache[current_thread]

    _statscache = property(_get_statscache)

    #FIXME: figure out what this checker thing is
    checker = None

    def _get_store(self):
        """parse file and return TranslationStore object"""
        if not hasattr(self, "_store"):
            #FIXME: translate.storage.base.parsefile closes file for
            #some weird reason, so we sprinkle with opens to make sure
            #things workout
            self.open()
            self._store = factory.getobject(self)
            self.open()
        return self._store
    store = property(_get_store)

    def _get_filename(self):
        return os.path.basename(self.name)
    filename = property(_get_filename)

    def savestore(self):
        self.store.save()

    def _guess_path(self):
        """Most TranslationStoreFile objects will correspond to
        TranslationStoreField instances and have a known path, however
        standalone instances of TranslationStoreFile can come from in-memory
        files or already open file descriptors with no sure way of obtaining a
        path."""
        #FIXME: is name the best substitute for path?
        return self.name
    path = property(_guess_path)

    def getquickstats(self):
        """Returns the quick statistics (totals only)."""
        if 'quickstats' not in self._stats.setdefault(self.path, {}):
            self._stats[self.path]['quickstats'] = self._statscache.filetotals(self.path, store=self._get_store) # or statsdb.emptyfiletotals()
        return self._stats[self.path]['quickstats']

    def getstats(self):
        """Returns the unit states statistics only."""
        if 'stats' not in self._stats.setdefault(self.path, {}):
            self._stats[self.path]['stats'] = self._statscache.filestatestats(self.path, store=self._get_store)
        return self._stats[self.path]['stats']

    def getcompletestats(self, checker):
        """Return complete stats including quality checks."""
        if 'completestats' not in self._stats.setdefault(self.path, {}):
            self._stats[self.path]['completestats'] =  self._statscache.filestats(self.path, checker, store=self._get_store)
        return self._stats[self.path]['completestats']

    def getunitstats(self):
        if 'unitstats' not in self._stats.setdefault(self.path, {}):
            self._stats[self.path]['unitstats'] = self._statscache.unitstats(self.path, store=self._get_store)
        return self._stats[self.path]['unitstats']

    def reclassifyunit(self, item, checker=checks.StandardUnitChecker()):
        """Reclassifies all the information in the database and self._stats
        about the given unit."""
        unit = self.getitem(item)
        state = self._statscache.recacheunit(self.path, checker, unit)
        #FIXME: can't we use state to update stats cache instead of invalidating it?
        self._stats[self.path] = {}
        return state

    def _get_total(self):
        """Returns a list of translatable unit indices, useful for identifying
        translatable units by their place in translation file (item number)."""
        return self.getstats()['total']
    total = property(_get_total)

    def getitem(self, item):
        """Returns a single unit based on the item number."""
        return self.store.units[self.total[item]]

    def getitemslen(self):
        """The number of items in the file."""
        return self.getquickstats()['total']

    def updateunit(self, item, newvalues, userprefs, languageprefs):
        """Updates a translation with a new target value, comments, or fuzzy
        state."""

        unit = self.getitem(item)

        if newvalues.has_key('target'):
            unit.target = newvalues['target']
        if newvalues.has_key('fuzzy'):
            unit.markfuzzy(newvalues['fuzzy'])
        if newvalues.has_key('translator_comments'):
            unit.removenotes()
            if newvalues['translator_comments']:
                unit.addnote(newvalues['translator_comments'])

        if isinstance(self, po.pofile):
            po_revision_date = time.strftime('%Y-%m-%d %H:%M') + tzstring()
            headerupdates = {'PO_Revision_Date': po_revision_date,
                             'Language': self.languagecode,
                             'X_Generator': self.x_generator}
            if userprefs:
                if getattr(userprefs, 'name', None) and getattr(userprefs, 'email', None):
                    headerupdates['Last_Translator'] = '%s <%s>' % (userprefs.name, userprefs.email)
            self.store.updateheader(add=True, **headerupdates)
            if languageprefs:
                nplurals = getattr(languageprefs, 'nplurals', None)
                pluralequation = getattr(languageprefs, 'pluralequation', None)
                if nplurals and pluralequation:
                    self.store.updateheaderplural(nplurals, pluralequation)
        # If we didn't add a header, savepofile doesn't have to
        # reset the stats, since reclassifyunit will do. This
        # gives us a little speed boost for the common case.
        self.savestore()
        self.reclassifyunit(item)

    def addunit(self, unit):
        """Wrapper around TranslationStore.addunit that updates sourceindex on
        the fly.

        Useful for avoiding rebuilding the index of pending files when new
        suggestions are added."""
        self.store.addunit(unit)
        if hasattr(self.store, "sourceindex"):
            self.store.add_unit_to_index(unit)

    def removeunit(self, unit):
        """Removes a unit from store, updates sourceindex on the fly.

        Useful for avoiding rebuilding index of pending files when suggestions
        are removed."""
        self.store.units.remove(unit)
        if hasattr(self.store, "sourceindex"):
            self.store.remove_unit_from_index(unit)

    def getpomtime(self):
        return statsdb.get_mod_info(self.path)


class TranslationStoreFieldFile(FieldFile, TranslationStoreFile):
    """FieldFile is the File-like object of a FileField, that is found in a
    TranslationStoreField."""

    _store_cache = {}

    # redundant redefinition of path to be the same as defined in
    # FieldFile, added here for clarity since TranslationStoreFile
    # uses a different method
    path = property(FieldFile._get_path)

    def _get_store(self):
        """Get translation store from dictionary cache, populate if store not
        already cached."""
        #FIXME: when do we detect that file changed?
        if self.path not in self._store_cache:
            self._update_store_cache()
        return self._store_cache[self.path][0]

    def _update_store_cache(self):
        """Add translation store to dictionary cache, replace old cached
        version if needed."""
        mod_info = self.getpomtime()

        if self.path not in self._store_cache or self._store_cache[self.path][1] != mod_info:
            logging.debug("cache miss for %s", self.path)
            self._store_cache[self.path] = (factory.getobject(self.path, ignore=self.field.ignore), mod_info)
            self._stats[self.path] = {}
            translation_file_updated.send(sender=self, path=self.path)

    def _touch_store_cache(self):
        """Update stored mod_info without reparsing file."""
        if self.path not in self._store_cache:
            return self._update_store_cache()

        mod_info = self.getpomtime()
        self._store_cache[self.path] = (self._store_cache[self.path][0], mod_info)
        #FIXME: should we track pomtime for stats cache as well
        self._stats[self.path] = {}
        translation_file_updated.send(sender=self, path=self.path)

    def _delete_store_cache(self):
        """Remove translation store from dictionary cache."""
        if self.path in self._store_cache:
            del(self._store_cache[self.path])
        self._stats[self.path] = {}

    store = property(_get_store)

    def savestore(self):
        """Saves to temporary file then moves over original file. This
        way we avoid the need for locking."""
        tmpfile, tmpfilename = tempfile.mkstemp(suffix=self.filename)
        self.store.savefile(tmpfilename)
        shutil.move(tmpfilename, self.path)
        self._touch_store_cache()

    def save(self, name, content, save=True):
        #FIXME: implement save to tmp file then move instead of directly saving
        super(TranslationStoreFieldFile, self).save(name, content, save)
        self._delete_store_cache()

    def delete(self, save=True):
        self._delete_store_cache()
        super(TranslationStoreFieldFile, self).delete(save)


class TranslationStoreField(FileField):
    """This is the field class to represent a FileField in a model that
    represents a translation store."""

    attr_class = TranslationStoreFieldFile

    #def formfield(self, **kwargs):
    #    defaults = {'form_class': FileField}
    #    defaults.update(kwargs)
    #    return super(TranslationStoreField, self).formfield(**defaults)

    def __init__(self, ignore=None, **kwargs):
        """ignore: postfix to be stripped from filename when trying to
        determine file format for parsing, useful for .pending files"""
        self.ignore = ignore
        super(TranslationStoreField, self).__init__(**kwargs)
