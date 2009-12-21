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

import md5
import os
import logging
import re

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.db.models.signals import pre_save, post_init, post_delete

from translate.storage import base, statsdb, po

from pootle_misc.util import getfromcache, deletefromcache
from pootle_misc.baseurl import l
from pootle_app.models.directory import Directory

from pootle_store.fields  import TranslationStoreField, MultiStringField
from pootle_store.signals import translation_file_updated

############### Unit ####################

class Unit(models.Model, base.TranslationUnit):
    class Meta:
        ordering = ['store', 'index']
        unique_together = ('store', 'index')
        
    store = models.ForeignKey("pootle_store.Store", db_index=True)
    index = models.IntegerField(db_index=True)

    source_f = MultiStringField(null=True)
    target_f = MultiStringField(null=True)

    hash = models.CharField(max_length=32, db_index=True)
    wordcount = models.SmallIntegerField(default=0)
    length = models.SmallIntegerField(db_index=True, default=0)

    developer_comment = models.TextField(null=True)
    translator_comment = models.TextField(null=True)
    locations = models.TextField(null=True)
    context = models.TextField(null=True)
    fuzzy = models.BooleanField(default=False)
    obsolete = models.BooleanField(default=False)
    unitid = models.TextField()

    def init_nondb_state(self):
        self._rich_source = None
        self._rich_target = None
        self.unitclass = po.pounit
        self._encoding = 'UTF-8'
        
    def _get_source(self):
        return self.source_f

    def _set_source(self, value):
        self.source_f = value
        self.hash = md5.md5(self.source_f.encode("utf-8")).hexdigest()
        self.wordcount = statsdb.wordcount(self.source_f)
        self.length = len(self.source_f)
            
    _source = property(_get_source, _set_source)

    def _get_target(self):
        return self.target_f

    def _set_target(self, value):
        self.target_f = value

    _target = property(_get_target, _set_target)
    
    def convert(self, unitclass):
        return unitclass.buildfromunit(self)

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self.source)
    
    def __unicode__(self):
        return unicode(str(self.convert(self.unitclass)).decode(self._encoding))
                       
    def getnotes(self, origin=None):
        if origin == None:
            return self.translator_comment + self.developer_comment
        elif origin == "translator":
            return self.translator_comment
        elif origin in ["programmer", "developer", "source code"]:
            return self.developer_comment
        else:
            raise ValueError("Comment type not valid")

    def addnote(self, text, origin=None, position="append"):
        if not (text and text.strip()):
            return
        if origin in ["programmer", "developer", "source code"]:
            self.developer_comment = text
        else:
            self.translator_comment = text
            
    def getid(self):
        return self.unitid

    def getlocations(self):
        return self.locations

    def addlocation(self, location):
        self.locations.append(location + "\n")

    def getcontext(self):
        return self.context

    def isfuzzy(self):
        return self.fuzzy

    def markfuzzy(self, value=True):
        self.fuzzy = value

    def update(self, unit):
        """update indb translation from file"""
        self.source = unit.source
        self.target = unit.target
        self.developer_comment = unit.getnotes(origin="developer")
        self.translator_comment = unit.getnotes(origin="translator")
        self.locations = "\n".join(unit.getlocations())
        self.context = unit.getcontext()
        self.fuzzy = unit.isfuzzy()
        self.obsolete = unit.isobsolete()
        self.unitid = unit.getid()

        
def init_baseunit(sender, instance, **kwargs):
    instance.init_nondb_state()
post_init.connect(init_baseunit, sender=Unit)

###################### Store ###########################

# custom storage otherwise djago assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

# regexp to parse suggester name from msgidcomment
suggester_regexp = re.compile(r'suggested by (.*) \[[-0-9]+\]')

class Store(models.Model, base.TranslationStore):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""
    UnitClass = Unit
    Name = "Model Store"
    is_dir = False

    file = TranslationStoreField(upload_to="fish", max_length=255, storage=fs, db_index=True, null=False, editable=False)
    pending = TranslationStoreField(ignore='.pending', upload_to="fish", max_length=255, storage=fs, editable=False)
    tm = TranslationStoreField(ignore='.tm', upload_to="fish", max_length=255, storage=fs, editable=False)
    parent = models.ForeignKey(Directory, related_name='child_stores', db_index=True, editable=False)
    pootle_path = models.CharField(max_length=255, null=False, unique=True, db_index=True, verbose_name=_("Path"))
    name = models.CharField(max_length=128, null=False, editable=False)

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

        pending_name = self.file.name + os.extsep + 'pending'
        pending_path = os.path.join(settings.PODIRECTORY, pending_name)
        if self.pending:
            # pending file already referencing in db, but does it
            # really exist
            if os.path.exists(self.pending.path):
                # pending file exists
                self.pending._update_store_cache()
                return
            elif not create:
                # pending file doesn't exist anymore
                self.pending = None
                self.save()

        # check if pending file already exists, just in case it was
        # added outside of pootle
        if not os.path.exists(pending_path) and create:
            # we only create the file if asked, typically before
            # adding a suggestion
            store = po.pofile()
            store.updateheader(add=True, **store.makeheaderdict(charset='UTF-8', encoding='8bit'))
            store.savefile(pending_path)

        if os.path.exists(pending_path):
            self.pending = pending_name
            self.save()
            self.pending._update_store_cache()
            translation_file_updated.connect(self.handle_file_update, sender=self.pending)

    def getsuggestions_unit(self, unit):
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
    
    def getsuggestions(self, item):
        unit = self.getitem(item)
        return self.getsuggestions_unit(unit)


    def suggestion_is_unique(self, unit, newtarget):
        """check for duplicate suggestions"""
        if unit.target == newtarget:
            return False

        for suggestion in self.getsuggestions_unit(unit):
            if suggestion.target == newtarget:
                return False

        return True
    
    def addunitsuggestion(self, unit, newunit, username):
        """adds suggestion for the given unit"""
        if not self.suggestion_is_unique(unit, newunit.target):
            return

        if self.file.store.suggestions_in_format:
            unit.addalttrans(newunit.target, origin=username)
        else:
            newunit = self.pending.store.UnitClass.buildfromunit(newunit)
            if username is not None:
                newunit.msgidcomment = 'suggested by %s [%d]' % (username, hash(newunit.target))
            self.pending.addunit(newunit)


    def addsuggestion(self, item, suggtarget, username, checker=None):
        """adds a new suggestion for the given item"""
        unit = self.getitem(item)
        
        if self.file.store.suggestions_in_format:
            # probably xliff, which can't do unit copies and doesn't
            # need a unit to add suggestions anyway. so let's shortcut
            # and insert suggestion here
            if self.suggestion_is_unique(unit, suggtarget):
                unit.addalttrans(suggtarget, origin=username)
                self.file.savestore()
        else:
            newpo = unit.copy()
            newpo.target = suggtarget
            newpo.markfuzzy(False)

            self.initpending(create=True)
            self.addunitsuggestion(unit, newpo, username)
            self.pending.savestore()
        
        if checker is not None:
            self.file.reclassifyunit(item, checker)


    def _deletesuggestion(self, item, suggestion):
        if self.file.store.suggestions_in_format:
            unit = self.getitem(item)
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
            header = self.file.store.UnitClass('', encoding=self.file.store._encoding)
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
            unit = self.getitem(item)
            locations = unit.getlocations()
            # TODO: review the matching method. We can't simply use the
            # location index, because we want multiple matches.
            suggestpos = [suggestpo for suggestpo in self.tm.store.units
                          if suggestpo.getlocations() == locations]
            return suggestpos
        return []

    def _get_units(self):
        return self.unit_set.order_by('index')
    units=property(_get_units)

    def update(self):
        """update db with units from file"""
        for index, unit in enumerate(self.file.store.units):
            if unit.istranslatable():
                newunit, created = Unit.objects.get_or_create(store=self, index=index)
                newunit.update(unit)
                newunit.save()
    def output(self, file=None):
        if file is None:
            file = self.file
        store = factory.getobject(self.file)
        self.require_index()
        for unit in store.units:
            uid = unit.getid()
            match =  self.id_index.get(uid, None)
            if match is not None:
                unit.merge(match)
        print store
        
        
    def getitem(self, item):
        """Returns a single unit based on the item number."""
        return self.units[item]


def set_store_pootle_path(sender, instance, **kwargs):
    instance.pootle_path = '%s%s' % (instance.parent.pootle_path, instance.name)
pre_save.connect(set_store_pootle_path, sender=Store)

def store_post_init(sender, instance, **kwargs):
    translation_file_updated.connect(instance.handle_file_update, sender=instance.file)
    if instance.pending is not None:
        #FIXME: we probably want another method for pending, to avoid
        # invalidating stats that are not affected by suggestions
        translation_file_updated.connect(instance.handle_file_update, sender=instance.pending)

post_init.connect(store_post_init, sender=Store)

def store_post_delete(sender, instance, **kwargs):
    deletefromcache(instance, ["getquickstats", "getcompletestats"])
post_delete.connect(store_post_delete, sender=Store)
