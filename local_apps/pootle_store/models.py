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

from translate.storage import po

#FIXME: move this stuff to pootle_store
from pootle_app.models.directory import Directory

from pootle_store.fields import TranslationStoreField

# custom storage otherwise djago assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

# regexp to parse suggester name from msgidcomment
suggester_regexp = re.compile(r'suggested by (.*)\n')

class Store(models.Model):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""
    is_dir = False
    
    file        = TranslationStoreField(upload_to="fish", max_length=255, storage=fs, db_index=True, null=False)
    pending     = TranslationStoreField(upload_to="fish", max_length=255, storage=fs)
    parent      = models.ForeignKey(Directory, related_name='child_stores', db_index=True)
    pootle_path = models.CharField(max_length=255, null=False, unique=True, db_index=True)
    name        = models.CharField(max_length=128, null=False)

    class Meta:
        ordering = ['pootle_path']
        unique_together = ('parent', 'name')

    def _get_abs_real_path(self):
        return self.file.path

    abs_real_path = property(_get_abs_real_path)

    def _get_real_path(self):
        return self.file.name

    real_path = property(_get_real_path)

    def __unicode__(self):
        return self.name

    def initpending(self):
        """initialize pending translations file if needed"""
        if self.file.store.suggestions_in_format or self.pending:
            # suggestions can be stored in the translation file itself
            # or a pending suggestions file already exists
            return
        
        pending_filename = self.file.path + os.extsep + 'pending' + os.extsep + 'po'
        # check if pending file already exists, just in case it was
        # added outside of pootle
        if not os.path.exists(pending_filename):
            # we'll use tmx because it supports multiple units with
            # the same source text
            store = po.pofile()
            store.savefile(pending_filename)
        self.pending = pending_filename
        self.save()

    def getsuggestions(self, item):
        unit = self.file.getitem(item)
        if self.file.store.suggestions_in_format:
            return unit.getalttrans()
        elif self.pending:
            if not hasattr(self.pending.store, "sourceindex"):
                self.pending.store.makeindex()
            return self.pending.store.findunits(unit.source)
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
            self.initpending()
            newpo = unit.copy()
            if username is not None:
                newpo.msgidcomments.append('"_: suggested by %s\\n"' % username)
            newpo.target = suggtarget
            newpo.markfuzzy(False)
            self.pending.store.addunit(newpo)
            self.pending.savestore()
        self.file.reclassifyunit(item)

    def deletesuggestion(self, item, suggitem, newtrans=None):
        """removes the suggestion from the pending file"""
        
        try:
            suggestion = self.getsuggestions(item)[suggitem]
        except IndexError:
            logging.error('Found an index error attemptine to delete suggestion %d', suggitem)
            return
        
        if self.file.store.suggestions_in_format:
            unit = self.file.getitem(item)
            unit.delalttrans(suggestion)
            self.file.savestore()
            
        else:
            try:
                self.pending.store.units.remove(suggestion)
                self.pending.savestore()
            except ValueError:
                logging.error('Found an index error attempting to delete a suggestion: %s', suggestion)
                return  # TODO: Print a warning for the user.
            
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


def set_store_pootle_path(sender, instance, **kwargs):
    instance.pootle_path = '%s%s' % (instance.parent.pootle_path, instance.name)

models.signals.pre_save.connect(set_store_pootle_path, sender=Store)

class Unit(models.Model):
    #FIXME: why do we have this model, what is it used for
    
    store = models.ForeignKey(Store, related_name='units', db_index=True)
    index = models.IntegerField(db_index=True)
    source = models.TextField()
    #FIXME: what about plurals
    target = models.TextField()
    state = models.CharField(max_length=255, db_index=True)
