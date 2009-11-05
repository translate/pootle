#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

import os
import logging
import re

from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache

from translate.storage import po
from translate.misc.multistring import multistring

from pootle_misc.util import getfromcache, deletefromcache
from pootle_misc.baseurl import l
from pootle_app.models.directory import Directory
from pootle_store.fields  import TranslationStoreField
from pootle_store.signals import translation_file_updated

# custom storage otherwise djago assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

# regexp to parse suggester name from msgidcomment
suggester_regexp = re.compile(r'suggested by (.*)')

class Store(models.Model):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""
    is_dir = False

    file        = TranslationStoreField(upload_to="fish", max_length=255, storage=fs, db_index=True, null=False, editable=False)
    pending     = TranslationStoreField(ignore='.pending', upload_to="fish", max_length=255, storage=fs, editable=False)
    tm          = TranslationStoreField(ignore='.tm', upload_to="fish", max_length=255, storage=fs, editable=False)
    parent      = models.ForeignKey(Directory, related_name='child_stores', db_index=True, editable=False)
    pootle_path = models.CharField(max_length=255, null=False, unique=True, db_index=True)
    name        = models.CharField(max_length=128, null=False, editable=False)

    class Meta:
        ordering = ['pootle_path']
        unique_together = ('parent', 'name')

    def handle_file_update(self, sender, **kwargs):
        deletefromcache(self, ["getquickstats", "getcompletestats"])

    def _get_abs_real_path(self):
        return self.file.path

    abs_real_path = property(_get_abs_real_path)

    def _get_real_path(self):
        return self.file.name

    real_path = property(_get_real_path)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return l(self.pootle_path)
    
    @getfromcache
    def getquickstats(self):
        # convert result to normal dicts for later operations
        return dict(self.file.getquickstats())

    @getfromcache
    def getcompletestats(self, checker):
        #FIXME: figure out our own checker?
        stats = {}
        for key, value in self.file.getcompletestats(checker).iteritems():
            stats[key] = len(value)
        return stats

    def initpending(self, create=False):
        """initialize pending translations file if needed"""
        #FIXME: we parse file just to find if suggestions can be
        #stored in format, maybe we should store TranslationStore
        #class and query it for such info
        if self.file.store.suggestions_in_format:
            # suggestions can be stored in the translation file itself
            return

        pending_filename = self.file.path + os.extsep + 'pending'
        if self.pending:
            # pending file already referencing in db, but does it
            # really exist
            if os.path.exists(self.pending.path):
                # pending file exists
                return
            elif create:
                # pending file got deleted recreate
                store = po.pofile()
                #FIXME: we should add more details to headers, maybe
                # copy them from file?
                po.makeheader(charset='UTF-8', encoding='8bit')
                store.savefile(pending_filename)
                return
            else:
                # pending file doesn't exist anymore
                self.pending = None
                self.save()
                
        # check if pending file already exists, just in case it was
        # added outside of pootle
        if not os.path.exists(pending_filename) and create:
            # we only create the file if asked, typically before
            # adding a suggestion
            store = po.pofile()
            store.savefile(pending_filename)

        if os.path.exists(pending_filename):
            self.pending = pending_filename
            self.save()
            translation_file_updated.connect(self.handle_file_update, sender=self.pending)

    def getsuggestions(self, item):
        unit = self.file.getitem(item)
        if self.file.store.suggestions_in_format:
            return unit.getalttrans()
        else:
            self.initpending()
            if self.pending:
                self.pending.store.require_index()
                suggestions = self.pending.store.findunits(unit.source)
                if suggestions is not None:
                    return suggestions
        return []


    def addunitsuggestion(self, unit, newunit, username):
        """adds suggestion for the given unit"""
        if unit.target == newunit.target:
            # duplicate don't add
            # FIXME: should we look up if suggestion already exists in pending file?
            return
            
        if self.file.store.suggestions_in_format:
            unit.addalttrans(newunit.target, origin=username)
        else:
            newunit = self.pending.store.UnitClass.buildfromunit(newunit)
            if username is not None:
                newunit.msgidcomment = 'suggested by %s' % username
            self.pending.addunit(newunit)
                        
            
    def addsuggestion(self, item, suggtarget, username, checker=None):
        """adds a new suggestion for the given item"""
        unit = self.file.getitem(item)
        newpo = unit.copy()
        newpo.target = suggtarget
        newpo.markfuzzy(False)
        
        self.initpending(create=True)
        self.addunitsuggestion(unit, newpo, username)
        
        if self.file.store.suggestions_in_format:
            self.file.savestore()
        else:
            self.pending.savestore()
        if checker is not None:
            self.file.reclassifyunit(item, checker)


    def _deletesuggestion(self, item, suggestion):
        if self.file.store.suggestions_in_format:
            unit = self.file.getitem(item)
            unit.delalttrans(suggestion)
        else:
            try:
                self.pending.removeunit(suggestion)
            except ValueError:
                logging.error('Found an index error attempting to delete a suggestion: %s', suggestion)
                return  # TODO: Print a warning for the user.

    def deletesuggestion(self, item, suggitem, newtrans, checker):
        """removes the suggestion from the pending file"""
        suggestions = self.getsuggestions(item)
        
        try:
            # first try to use index
            suggestion = self.getsuggestions(item)[suggitem]
            if suggestion.hasplural() and suggestion.target.strings == newtrans or \
                   not suggestion.hasplural() and suggestion.target == newtrans[0]:                
                self._deletesuggestion(item, suggestion)
            else:
                # target doesn't match suggested translation, index is
                # incorrect
                raise IndexError
        except IndexError:
            logging.debug('Found an index error attempting to delete suggestion %d\n looking for item by target', suggitem)
            # see if we can find the correct suggestion by searching
            # for target text
            for suggestion in suggestions:
                if suggestion.hasplural() and suggestion.target.strings == newtrans or \
                       not suggestion.hasplural() and suggestion.target == newtrans[0]:
                    self._deletesuggestion(item, suggestion)
                    break

        if self.file.store.suggestions_in_format:
            self.file.savestore()
        else:
            self.pending.savestore()
        self.file.reclassifyunit(item, checker)


    def getsuggester(self, item, suggitem):
        """returns who suggested the given item's suggitem if
        recorded, else None"""

        unit = self.getsuggestions(item)[suggitem]
        if self.file.store.suggestions_in_format:
            return unit.xmlelement.get('origin')

        else:
            suggestedby = suggester_regexp.search(unit.msgidcomment)
            if suggestedby:
                return suggestedby.group(1)
        return None


    def mergefile(self, newfile, username, allownewstrings, suggestions, notranslate, obsoletemissing):
        """make sure each msgid is unique ; merge comments etc from
        duplicates into original"""
        self.file._update_store_cache()
        self.file.store.require_index()
        newfile.require_index()

        old_ids = set(self.file.store.id_index.keys())
        new_ids = set(newfile.id_index.keys())

        if allownewstrings:
            new_units = (newfile.findid(uid) for uid in new_ids - old_ids)
            for unit in new_units:
                self.file.store.addunit(self.file.store.UnitClass.buildfromunit(unit))

        if obsoletemissing:
            old_units = (self.file.store.findid(uid) for uid in old_ids - new_ids)
            for unit in old_units:
                unit.makeobsolete()

        if notranslate or suggestions:
            self.initpending(create=True)
            
        shared_units = ((self.file.store.findid(uid), newfile.findid(uid)) for uid in old_ids & new_ids)        
        for oldunit, newunit in shared_units:
            if not newunit.istranslated():
                continue

            if notranslate or oldunit.istranslated() and suggestions:
                self.addunitsuggestion(oldunit, newunit, username)
            else:
                oldunit.merge(newunit)

        if (suggestions or notranslate) and not self.file.store.suggestions_in_format:
            self.pending.savestore()

        if not isinstance(newfile, po.pofile) or notranslate or suggestions:
            # TODO: We don't support updating the header yet.
            self.file.savestore()
            return

        # Let's update selected header entries. Only the ones
        # listed below, and ones that are empty in self can be
        # updated. The check in header_order is just a basic
        # sanity check so that people don't insert garbage.
        updatekeys = [
            'Content-Type',
            'POT-Creation-Date',
            'Last-Translator',
            'Project-Id-Version',
            'PO-Revision-Date',
            'Language-Team',
            ]
        headerstoaccept = {}
        ownheader = self.file.store.parseheader()
        for (key, value) in newfile.parseheader().items():
            if key in updatekeys or (not key in ownheader
                                     or not ownheader[key]) and key in po.pofile.header_order:
                headerstoaccept[key] = value
            self.file.store.updateheader(add=True, **headerstoaccept)

        # Now update the comments above the header:
        header = self.file.store.header()
        newheader = newfile.header()
        if header is None and not newheader is None:
            header = self.file.store.UnitClass('', encoding=self.encoding)
            header.target = ''
        if header:
            header._initallcomments(blankall=True)
            if newheader:
                for i in range(len(header.allcomments)):
                    header.allcomments[i].extend(newheader.allcomments[i])

        self.file.savestore()


    def inittm(self):
        """initialize translation memory file if needed"""
        if self.tm and os.path.exists(self.tm.path):
            return

        tm_filename = self.file.path + os.extsep + 'tm'
        if os.path.exists(tm_filename):
            self.tm = tm_filename
            self.save()

    def gettmsuggestions(self, item):
        """find all the tmsuggestion items submitted for the given
        item"""

        self.inittm()
        if self.tm:
            unit = self.file.getitem(item)
            locations = unit.getlocations()
            # TODO: review the matching method Can't simply use the
            # location index, because we want multiple matches
            suggestpos = [suggestpo for suggestpo in self.tm.store.units
                          if suggestpo.getlocations() == locations]
            return suggestpos
        return []

def set_store_pootle_path(sender, instance, **kwargs):
    instance.pootle_path = '%s%s' % (instance.parent.pootle_path, instance.name)
models.signals.pre_save.connect(set_store_pootle_path, sender=Store)

def store_post_init(sender, instance, **kwargs):
    translation_file_updated.connect(instance.handle_file_update, sender=instance.file)
    if instance.pending is not None:
        #FIXME: we probably want another method for pending, to avoid
        # invalidating stats that are not affected by suggestions
        translation_file_updated.connect(instance.handle_file_update, sender=instance.pending)
    
models.signals.post_init.connect(store_post_init, sender=Store)

def store_post_delete(sender, instance, **kwargs):
    deletefromcache(instance, ["getquickstats", "getcompletestats"])
models.signals.post_delete.connect(store_post_delete, sender=Store)
