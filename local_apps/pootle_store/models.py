#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import logging
import re

from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache

from translate.storage import po

from pootle_misc.util import getfromcache
from pootle_app.models.directory import Directory
from pootle_store.fields  import TranslationStoreField
from pootle_store.signals import translation_file_updated

# custom storage otherwise djago assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

# regexp to parse suggester name from msgidcomment
suggester_regexp = re.compile(r'suggested by (.*)\n')

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
        path = self.pootle_path
        path_parts = path.split("/")

        # clean project stat cache
        key = "/projects/%s/:getquickstats" % path_parts[2]
        cache.delete(key)
        
        # clean store and directory stat cache
        while path_parts:
            key = path + ":getquickstats"
            cache.delete(key)
            key = path + ":getcompletestats"
            cache.delete(key)
            path_parts = path_parts[:-1]
            path = "/".join(path_parts) + "/"
        
            
    def _get_abs_real_path(self):
        return self.file.path

    abs_real_path = property(_get_abs_real_path)

    def _get_real_path(self):
        return self.file.name

    real_path = property(_get_real_path)
    
    def __unicode__(self):
        return self.name

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
        if self.pending or self.file.store.suggestions_in_format:
            # suggestions can be stored in the translation file itself
            # or a pending suggestions file already exists
            return
        
        pending_filename = self.file.path + os.extsep + 'pending'
        # check if pending file already exists, just in case it was
        # added outside of pootle
        if not os.path.exists(pending_filename) and create:
            # we only create the file if asked, typically before adding a suggestion
            store = po.pofile()
            store.savefile(pending_filename)

        if os.path.exists(pending_filename):
            self.pending = pending_filename
            self.save()

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

    def addsuggestion(self, item, suggtarget, username):
        """adds a new suggestion for the given item"""

        unit = self.file.getitem(item)
        if self.file.store.suggestions_in_format:
            if isinstance(suggtarget, list) and len(suggtarget) > 0:
                suggtarget = suggtarget[0]
            unit.addalttrans(suggtarget, origin=username)
            self.file.savestore()
        else:
            self.initpending(create=True)
            newpo = unit.copy()
            if username is not None:
                newpo.msgidcomments.append('"_: suggested by %s\\n"' % username)
            newpo.target = suggtarget
            newpo.markfuzzy(False)
            self.pending.addunit(newpo)
            self.pending.savestore()
        self.file.reclassifyunit(item)


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

    def deletesuggestion(self, item, suggitem=None, newtrans=None):
        """removes the suggestion from the pending file"""
        if suggitem is not None:
            try:
                suggestions = [self.getsuggestions(item)[suggitem]]
            except IndexError:
                logging.error('Found an index error attemptine to delete suggestion %d', suggitem)
                return
        else:
            suggestions = self.getsuggestions(item)

        for suggestion in suggestions:
            self._deletesuggestion(item, suggestion)
            
        if self.file.store.suggestions_in_format:
            self.file.savestore()
        else:
            self.pending.savestore()
        self.file.reclassifyunit(item)
    
    def getsuggester(self, item, suggitem):
        """returns who suggested the given item's suggitem if
        recorded, else None"""

        unit = self.getsuggestions(item)[suggitem]
        if self.file.store.suggestions_in_format:
            return unit.xmlelement.get('origin')
        
        else:
            suggestedby = suggester_regexp.search(po.unquotefrompo(unit.msgidcomments)).group(1)
            return suggestedby
        return None


    def matchitems(self, newfile, uselocations=False):
        """matches up corresponding items in this pofile with the
        given newfile, and returns tuples of matching poitems
        (None if no match found)"""

        if not hasattr(self.file.store, 'sourceindex'):
            self.file.store.makeindex()
        if not hasattr(newfile, 'sourceindex'):
            newfile.makeindex()
        matches = []
        for newpo in newfile.units:
            if newpo.isheader():
                continue
            foundid = False
            if uselocations:
                newlocations = newpo.getlocations()
                mergedlocations = set()
                for location in newlocations:
                    if location in mergedlocations:
                        continue
                    if location in self.file.store.locationindex:
                        oldpo = self.file.store.locationindex[location]
                        if oldpo is not None:
                            foundid = True
                            matches.append((oldpo, newpo))
                            mergedlocations.add(location)
                            continue
            if not foundid:
                # We can't use the multistring, because it might
                # contain more than two entries in a PO xliff
                # file. Rather use the singular.
                source = unicode(newpo.source)
                oldpo = self.file.store.findunit(source)
                matches.append((oldpo, newpo))

        # find items that have been removed
        matcheditems = set(oldpo for (oldpo, newpo) in matches if oldpo)
        for oldpo in self.file.store.units:
            if not oldpo in matcheditems:
                matches.append((oldpo, None))
        return matches

    def mergeitem(self, po_position, oldpo, newpo, username, suggest=False):
        """merges any changes from newpo into oldpo"""

        unchanged = oldpo.target == newpo.target
        if not suggest and (not oldpo.target or not newpo.target
                            or oldpo.isheader() or newpo.isheader() or unchanged):
            oldpo.merge(newpo)
        else:
            if oldpo in po_position:
                strings = newpo.target #.strings
                self.addsuggestion(po_position[oldpo], strings, username)
            else:
                raise KeyError('Could not find item for merge')

    def mergefile(self, newfile, username, allownewstrings=True, suggestions=False, obseletemissing=True):
        """make sure each msgid is unique ; merge comments etc
        from duplicates into original"""

        self.file._update_store_cache()
        if self.file.store == newfile:
            logging.debug("identical merge: %s", self.file.name)
            return
        
        if not hasattr(self.file.store, 'sourceindex'):
            self.file.store.makeindex()
        translatables = (self.file.store.units[index] for index in self.file.total)
        po_position = dict((unit, position) for (position, unit) in enumerate(translatables))
        matches = self.matchitems(newfile)
        for (oldpo, newpo) in matches:
            if suggestions and oldpo and newpo:
                self.mergeitem(po_position, oldpo, newpo, username, suggest=True)
            elif allownewstrings and oldpo is None:
                self.file.store.addunit(self.file.store.UnitClass.buildfromunit(newpo))
            elif obseletemissing and newpo is None:
                oldpo.makeobsolete()
            elif oldpo and newpo:
                self.mergeitem(po_position, oldpo, newpo, username)
                # we invariably want to get the ids (source
                # locations) from the newpo
                if hasattr(newpo, 'sourcecomments'):
                    oldpo.sourcecomments = newpo.sourcecomments

        if not isinstance(newfile, po.pofile) or suggestions:
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
models.signals.post_init.connect(store_post_init, sender=Store)


class Unit(models.Model):
    #FIXME: why do we have this model, what is it used for
    
    store = models.ForeignKey(Store, related_name='units', db_index=True)
    index = models.IntegerField(db_index=True)
    source = models.TextField()
    #FIXME: what about plurals
    target = models.TextField()
    state = models.CharField(max_length=255, db_index=True)
