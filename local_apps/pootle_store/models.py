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
import time

from django.db import models, IntegrityError
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import commit_on_success

from translate.storage import base, statsdb, po, poheader
from translate.misc.hash import md5_f

from pootle.__version__ import sver as pootle_version

from pootle_app.lib.util import RelatedManager
from pootle_misc.util import getfromcache, deletefromcache
from pootle_misc.aggregate import group_by_count, max_column
from pootle_misc.baseurl import l

from pootle_store.fields  import TranslationStoreField, MultiStringField
from pootle_store.util import calculate_stats, empty_quickstats
from pootle_store.util import OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED
from pootle_store.filetypes import factory_classes, is_monolingual

# Store States
LOCKED = -1
"""store being modified"""
NEW = 0
"""store just created, not parsed yet"""
PARSED = 1
"""store just parsed, units added but no quality checks where run"""
CHECKED = 2
"""quality checks run"""

############### Quality Check #############

class QualityCheck(models.Model):
    """database cache of results of qualitychecks on unit"""
    objects = RelatedManager()
    name = models.CharField(max_length=64, db_index=True)
    unit = models.ForeignKey("pootle_store.Unit", db_index=True)
    message = models.TextField()
    false_positive = models.BooleanField(default=False, db_index=True)
    def __unicode__(self):
        return self.name

################# Suggestion ################

class Suggestion(models.Model, base.TranslationUnit):
    """suggested translation for unit, provided by users or
    automatically generated after a merge"""
    objects = RelatedManager()
    class Meta:
        unique_together = ('unit', 'target_hash')

    target_f = MultiStringField()
    target_hash = models.CharField(max_length=32, db_index=True)
    unit = models.ForeignKey('pootle_store.Unit')
    user = models.ForeignKey('pootle_profile.PootleProfile', null=True)

    def __unicode__(self):
        return unicode(self.target)

    def _get_target(self):
        return self.target_f

    def _set_target(self, value):
        self.target_f = value
        self.target_hash = md5_f(self.target_f.encode("utf-8")).hexdigest()

    _target = property(_get_target, _set_target)
    _source = property(lambda self: self.unit._source)

############### Unit ####################

def fix_monolingual(oldunit, newunit, monolingual=None):
    """hackish workaround for monolingual files always having only source and no target.

    we compare monolingual unit with corresponding bilingual unit, if
    sources differ assume monolingual source is actually a translation"""

    if monolingual is None:
        monolingual = is_monolingual(type(newunit._store))
    if monolingual and newunit.source != oldunit.source:
        newunit.target = newunit.source
        newunit.source = oldunit.source

def count_words(strings):
    wordcount = 0
    for string in strings:
        wordcount += statsdb.wordcount(string)
    return wordcount


class Unit(models.Model, base.TranslationUnit):
    objects = RelatedManager()
    class Meta:
        ordering = ['store', 'index']
        unique_together = ('store', 'unitid_hash')

    store = models.ForeignKey("pootle_store.Store", db_index=True)
    index = models.IntegerField(db_index=True)
    unitid = models.TextField(editable=False)
    unitid_hash = models.CharField(max_length=32, db_index=True, editable=False)

    source_f = MultiStringField(null=True)
    source_hash = models.CharField(max_length=32, db_index=True, editable=False)
    source_wordcount = models.SmallIntegerField(default=0, editable=False)
    source_length = models.SmallIntegerField(db_index=True, default=0, editable=False)

    target_f = MultiStringField(null=True, blank=True)
    target_wordcount = models.SmallIntegerField(default=0, editable=False)
    target_length = models.SmallIntegerField(db_index=True, default=0, editable=False)

    developer_comment = models.TextField(null=True, blank=True)
    translator_comment = models.TextField(null=True, blank=True)
    locations = models.TextField(null=True, editable=False)
    context = models.TextField(null=True, editable=False)

    state = models.IntegerField(null=False, default=UNTRANSLATED, db_index=True)

    mtime = models.DateTimeField(auto_now=True, auto_now_add=True, db_index=True, editable=False)

    def get_mtime(self):
        return self.mtime

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)
        self._rich_source = None
        self._source_updated = False
        self._rich_target = None
        self._target_updated = False
        self._encoding = 'UTF-8'

    def save(self, *args, **kwargs):
        if self._source_updated:
            # update source related fields
            self.source_hash = md5_f(self.source_f.encode("utf-8")).hexdigest()
            self.source_wordcount = count_words(self.source_f.strings)
            self.source_length = len(self.source_f)

        if self._target_updated:
            # update target related fields
            self.target_wordcount = count_words(self.target_f.strings)
            self.target_length = len(self.target_f)
            if self.target_wordcount:
                if self.state == UNTRANSLATED:
                    self.state = TRANSLATED
            elif self.state > FUZZY:
                self.state = UNTRANSLATED

        super(Unit, self).save(*args, **kwargs)

        if settings.AUTOSYNC and self.store.file and self.store.state >= PARSED:
            #FIXME: last translator information is lost
            self.sync(self.getorig())
            self.store.file.savestore()

        if self.store.state >= CHECKED and (self._source_updated or self._target_updated):
            #FIXME: are we sure only source and target affect quality checks?
            self.update_qualitychecks()

        # done processing source/target update remove flag
        self._source_updated = False
        self._target_updated = False

        if self.store.state >= PARSED:
            # updated caches
            store = self.store
            #translation_project = store.translation_project
            #translation_project.update_index(translation_project.indexer, store, self.id)
            deletefromcache(store,
                            ["getquickstats", "getcompletestats", "get_mtime", "has_suggestions"])

    def _get_source(self):
        return self.source_f

    def _set_source(self, value):
        self.source_f = value
        self._source_updated = True

    _source = property(_get_source, _set_source)

    def _get_target(self):
        return self.target_f

    def _set_target(self, value):
        self.target_f = value
        self._target_updated = True

    _target = property(_get_target, _set_target)

    def convert(self, unitclass):
        """convert to a unit of type unitclass retaining as much
        information from the database as the target format can support"""
        newunit = unitclass(self.source)
        newunit.target = self.target
        newunit.markfuzzy(self.isfuzzy())
        locations = self.getlocations()
        if locations:
            newunit.addlocations(locations)
        notes = self.getnotes(origin="developer")
        if notes:
            newunit.addnote(notes, origin="developer")
        notes = self.getnotes(origin="translator")
        if notes:
            newunit.addnote(notes, origin="translator")
        newunit.setid(self.getid())
        newunit.setcontext(self.getcontext())
        if hasattr(newunit, "addalttrans"):
            for suggestion in self.get_suggestions().iterator():
                newunit.addalttrans(suggestion.target, origin=unicode(suggestion.user))
        return newunit

    def get_unit_class(self):
        try:
            return self.store.get_file_class().UnitClass
        except ObjectDoesNotExist:
            return po.pounit

    def __unicode__(self):
        #FIXME: consider using unit id instead?
        return unicode(self.source)

    def __str__(self):
        unitclass = self.get_unit_class()
        return str(self.convert(unitclass))


    def getorig(self):
        unit = self.store.file.store.units[self.index]
        if self.getid() == unit.getid():
            return unit
        #FIXME: if we are here, file changed structure and we need to update indeces
        logging.debug("incorrect unit index %d for %s in file %s", unit.index, unit, unit.store.file)
        self.store.file.store.require_index()
        unit = self.store.file.store.findid(self.getid())
        return unit

    def sync(self, unit):
        """sync in file unit with translations from db"""
        if unit.hasplural():
            unit.target = self.target.strings
        else:
            unit.target = self.target
        unit.addnote(self.getnotes(origin="translator"),
                     origin="translator", position="replace")
        unit.markfuzzy(self.isfuzzy())
        if self.isobsolete():
            unit.makeobsolete()

        if hasattr(unit, 'addalttrans') and self.get_suggestions().count():
            alttranslist = [alttrans.target for alttrans in unit.getalttrans()]
            for suggestion in self.get_suggestions().iterator():
                if suggestion.target in alttranslist:
                    # don't add duplicate suggestion
                    continue
                unit.addalttrans(suggestion.target, unicode(suggestion.user))

    def update(self, unit):
        """update indb translation from file"""
        changed = False
        if self.hasplural() != unit.hasplural():
            self.source = unit.source
            self.target = unit.target
            changed = True
        else:
            if self.source != unit.source:
                self.source = unit.source
                changed = True
            if self.target != unit.target:
                wordcount = self.target_wordcount
                self.target = unit.target
                if not (wordcount == count_words(self.target_f.strings) == 0):
                    #FIXME: we need to do this cause we discard nplurals for empty plurals
                    changed = True
        notes = unit.getnotes(origin="developer")
        if self.developer_comment != notes:
            self.developer_comment = notes
            changed = True
        notes = unit.getnotes(origin="translator")
        if self.translator_comment != notes:
            self.translator_comment = notes
            changed = True
        locations = "\n".join(unit.getlocations())
        if self.locations != locations:
            self.locations = locations
            changed = True
        if self.context != unit.getcontext():
            self.context = unit.getcontext()
            changed = True
        if self.isfuzzy() != unit.isfuzzy():
            self.markfuzzy(unit.isfuzzy())
            changed = True
        if self.isobsolete() != unit.isobsolete():
            if unit.isobsoltete():
                self.makeobsolete()
            else:
                self.resurrect()
            changed = True
        if self.unitid != unit.getid():
            self.unitid = unit.getid()
            self.unitid_hash = md5_f(self.unitid.encode("utf-8")).hexdigest()
            changed = True
        if hasattr(unit, 'getalttrans'):
            for suggestion in unit.getalttrans():
                if suggestion.source == self.source:
                    self.add_suggestion(suggestion.target, touch=False)
                changed = True
        return changed

    def update_qualitychecks(self, created=False):
        """run quality checks and store result in database"""
        if not created:
            self.qualitycheck_set.all().delete()
        if not self.target:
            return
        for name, message in self.store.translation_project.checker.run_filters(self).items():
            self.qualitycheck_set.create(name=name, message=message)

    def get_qualitychecks(self):
        return self.qualitycheck_set.filter(false_positive=False)

##################### TranslationUnit ############################

    def getnotes(self, origin=None):
        if origin == None:
            notes = ''
            if self.translator_comment is not None:
                notes += self.translator_comment
            if self.developer_comment is not None:
                notes += self.developer_comment
            return notes
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

    def setid(self, value):
        self.unitid = value
        self.unitid_hash = md5_f(self.unitid.encode("utf-8")).hexdigest()

    def getlocations(self):
        if self.locations is None:
            return []
        return filter(None, self.locations.split('\n'))

    def addlocation(self, location):
        if self.locations is None:
            self.locations = ''
        self.locations += location + "\n"

    def getcontext(self):
        return self.context

    def setcontext(self, value):
        self.context = value

    def isfuzzy(self):
        return self.state == FUZZY

    def markfuzzy(self, value=True):
        if self.state <= OBSOLETE:
            return

        if value:
            self.state = FUZZY
        elif self.state <= FUZZY:
            if count_words(self.target_f.strings):
                self.state = TRANSLATED
            else:
                self.state = UNTRANSLATED

    def hasplural(self):
        return self.source is not None and len(self.source.strings) > 1

    def isobsolete(self):
        return self.state == OBSOLETE

    def makeobsolete(self):
        if self.state > OBSOLETE:
            self.state = OBSOLETE

    def resurrect(self):
        if self.state > OBSOLETE:
            return

        if count_words(self.target_f.strings):
            self.state = TRANSLATED
        else:
            self.state = UNTRANSLATED

    def istranslated(self):
        return self.state >= TRANSLATED

    @classmethod
    def buildfromunit(cls, unit):
        newunit = cls()
        newunit.update(unit)
        return newunit

    def addalttrans(self, txt, origin=None):
        self.add_suggestion(txt, user=origin)

    def getalttrans(self):
        return self.get_suggestions()

    def delalttrans(self, alternative):
        alternative.delete()

    def merge(self, unit, overwrite=False, comments=True, authoritative=False):
        changed = False
        if comments:
            notes = unit.getnotes(origin="translator")
            if notes and self.translator_comment != notes:
                self.translator_comment = notes
                changed = True

        if not bool(unit.target):
            # no translation in new unit bail out
            return changed

        if bool(self.target) and not overwrite:
            # won't replace existing translation unless overwrite is
            # true
            return changed

        if self.istranslated() and not unit.istranslated():
            # current translation more trusted
            return changed

        self.target = unit.target
        if self.source != unit.source:
            self.markfuzzy()
        else:
            self.markfuzzy(unit.isfuzzy())
        changed = True

        return changed

##################### Suggestions #################################
    def get_suggestions(self):
        return self.suggestion_set.select_related('user').all()

    def add_suggestion(self, translation, user=None, touch=True):
        if translation == self.target:
            return None

        suggestion = Suggestion(unit=self, user=user)
        suggestion.target = translation
        try:
            suggestion.save()
            if touch:
                self.save()
        except:
            # probably duplicate suggestion
            return None
        return suggestion

    def accept_suggestion(self, suggid):
        try:
            suggestion = self.suggestion_set.get(id=suggid)
        except Suggestion.DoesNotExist:
            return False

        self.target = suggestion.target
        self.save()
        suggestion.delete()
        if settings.AUTOSYNC and self.file:
            #FIXME: update alttrans
            self.sync(self.getorig())
            self.store.updateheader(suggestion.user)
            self.file.savestore()
        return True

    def reject_suggestion(self, suggid):
        try:
            suggestion = self.suggestion_set.get(id=suggid)
        except Suggestion.DoesNotExist:
            return False
        suggestion.delete()
        # update timestamp
        self.save()
        return True

    def get_terminology(self):
        """get terminology suggestions"""
        matcher = self.store.translation_project.gettermmatcher()
        if matcher is not None:
            result = matcher.matches(self.source)
        else:
            result = []
        return result

###################### Store ###########################

x_generator = "Pootle %s" % pootle_version

# custom storage otherwise djago assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

# regexp to parse suggester name from msgidcomment
suggester_regexp = re.compile(r'suggested by (.*) \[[-0-9]+\]')

class Store(models.Model, base.TranslationStore):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""
    objects = RelatedManager()
    UnitClass = Unit
    Name = "Model Store"
    is_dir = False

    file = TranslationStoreField(upload_to="fish", max_length=255, storage=fs, db_index=True, null=False, editable=False)
    pending = TranslationStoreField(ignore='.pending', upload_to="fish", max_length=255, storage=fs, editable=False)
    tm = TranslationStoreField(ignore='.tm', upload_to="fish", max_length=255, storage=fs, editable=False)
    parent = models.ForeignKey('pootle_app.Directory', related_name='child_stores', db_index=True, editable=False)
    translation_project = models.ForeignKey('pootle_translationproject.TranslationProject', related_name='stores', db_index=True, editable=False)
    pootle_path = models.CharField(max_length=255, null=False, unique=True, db_index=True, verbose_name=_("Path"))
    name = models.CharField(max_length=128, null=False, editable=False)
    state = models.IntegerField(null=False, default=NEW, editable=False, db_index=True)
    class Meta:
        ordering = ['pootle_path']
        unique_together = ('parent', 'name')

    def save(self, *args, **kwargs):
        self.pootle_path = self.parent.pootle_path + self.name
        super(Store, self).save(*args, **kwargs)
        if hasattr(self, '_units'):
            index = self.max_index() + 1
            for i, unit in enumerate(self._units):
                unit.store = self
                unit.index = index + i
                unit.save()
        if self.state >= PARSED:
            #if self.translation_project:
                # update search index
                #self.translation_project.update_index(self.translation_project.indexer, self)
            # new units, let's flush cache
            deletefromcache(self, ["getquickstats", "getcompletestats", "get_mtime", "has_suggestions"])

    def delete(self, *args, **kwargs):
        super(Store, self).delete(*args, **kwargs)
        deletefromcache(self, ["getquickstats", "getcompletestats", "get_mtime", "has_suggestions"])

    @getfromcache
    def get_mtime(self):
        return max_column(self.units, 'mtime', None)

    def _get_abs_real_path(self):
        if self.file:
            return self.file.path

    abs_real_path = property(_get_abs_real_path)

    def _get_real_path(self):
        return self.file.name

    real_path = property(_get_real_path)

    def get_absolute_url(self):
        return l(self.pootle_path)

    def require_units(self):
        """make sure file is parsed and units are created"""
        if self.state < PARSED and self.unit_set.count() == 0:
            self.update(update_structure=True, update_translation=True, conservative=False)


    def require_dbid_index(self, update=False):
        """build a quick mapping index between unit ids and database ids"""
        if update or not hasattr(self, "dbid_index"):
            self.dbid_index = dict(self.units.values_list('unitid', 'id'))

    def findid_bulk(self, ids):
        chunks = 200
        for i in xrange(0, len(ids), chunks):
            units = self.units.filter(id__in=ids[i:i+chunks])
            for unit in units.iterator():
                yield unit

    @commit_on_success
    def update(self, update_structure=False, update_translation=False, conservative=True):
        """update db with units from file"""
        if self.state == LOCKED:
            # file currently being updated
            #FIXME: shall we idle wait for lock to be released first? what about stale locks?
            logging.info("attemped to update %s while locked", self.pootle_path)
            return

        if self.state < PARSED:
            logging.debug("Parsing %s", self.pootle_path)
            # no existing units in db, file hasn't been parsed before
            # no point in merging, add units directly
            oldstate = self.state
            self.state = LOCKED
            self.save()
            try:
                for index, unit in enumerate(self.file.store.units):
                    if unit.istranslatable():
                        self.addunit(unit, index)
            except:
                # something broke, delete any units that got created
                # and return store state to its original value
                self.unit_set.all().delete()
                self.state = oldstate
                self.save()
                raise

            self.state = PARSED
            self.save()
            return

        # lock store
        logging.debug("Updating %s", self.pootle_path)
        oldstate = self.state
        self.state = LOCKED
        self.save()
        try:
            monolingual = is_monolingual(type(self.file.store))
            self.require_dbid_index(update=True)
            old_ids = set(self.dbid_index.keys())
            new_ids = set(self.file.store.getids())

            if update_structure:
                obsolete_dbids = [self.dbid_index.get(uid) for uid in old_ids - new_ids]
                for unit in self.findid_bulk(obsolete_dbids):
                    if not unit.istranslated() or not conservative:
                        #FIXME: make obselete instead?
                        unit.delete()

                new_units = (self.file.store.findid(uid) for uid in new_ids - old_ids)
                for unit in new_units:
                    self.addunit(unit, unit.index)

            if update_translation:
                shared_dbids = [self.dbid_index.get(uid) for uid in old_ids & new_ids]

                for unit in self.findid_bulk(shared_dbids):
                    newunit = self.file.store.findid(unit.getid())
                    if monolingual and not self.translation_project.is_template_project:
                        fix_monolingual(unit, newunit, monolingual)
                    changed = unit.update(newunit)
                    if update_structure and unit.index != newunit.index:
                        unit.index = newunit.index
                        changed = True
                    if changed:
                        unit.save()
        finally:
            # unlock store
            self.state = oldstate
            self.save()

    def require_qualitychecks(self):
        """make sure quality checks are run"""
        if self.state < CHECKED:
            self.update_qualitychecks()
            # new qualitychecks, let's flush cache
            deletefromcache(self, ["getcompletestats"])

    @commit_on_success
    def update_qualitychecks(self):
        logging.debug("Updating quality checks for %s", self.pootle_path)
        for unit in self.units.iterator():
            unit.update_qualitychecks()

        if self.state < CHECKED:
            self.state = CHECKED
            self.save()

    def sync(self, update_structure=False, update_translation=False, conservative=True, create=False):
        """sync file with translations from db"""
        if not self.file:
            if create:
                # file doesn't exist let's create it
                logging.debug("Creating file %s", self.pootle_path)
                storeclass = self.get_file_class()
                store_path = os.path.join(self.translation_project.abs_real_path, self.name)
                store = self.convert(storeclass)
                store.savefile(store_path)
                self.file = store_path
                self.save()
            return

        logging.debug("Syncing %s", self.pootle_path)
        self.require_dbid_index(update=True)
        old_ids = set(self.file.store.getids())
        new_ids = set(self.dbid_index.keys())

        if update_structure:
            obsolete_units = (self.file.store.findid(uid) for uid in old_ids - new_ids)
            for unit in obsolete_units:
                if not unit.istranslated():
                    del unit
                elif not conservative:
                    unit.makeobsolete()
                    if not unit.isobsolete():
                        del unit

            new_dbids = [self.dbid_index.get(uid) for uid in new_ids - old_ids]
            for unit in self.findid_bulk(new_dbids):
                newunit = unit.convert(self.file.store.UnitClass)
                self.file.store.addunit(newunit)

        monolingual = is_monolingual(type(self.file.store))

        if update_translation:
            shared_dbids = [self.dbid_index.get(uid) for uid in old_ids & new_ids]
            for unit in self.findid_bulk(shared_dbids):
                #FIXME: use a better mechanism for handling states and different formats
                if monolingual and not unit.istranslated():
                    continue
                match = self.file.store.findid(unit.getid())
                if match is not None:
                    unit.sync(match)

        #FIXME update headers here
        self.file.savestore()

    def get_file_class(self):
        try:
            return self.translation_project.project.get_file_class()
        except ObjectDoesNotExist:
            if self.name:
                name, ext = os.path.splitext(self.name)
                return factory_classes[ext]
        return factory_classes['po']

    def convert(self, fileclass):
        """export to fileclass"""
        logging.debug("Converting %s to %s", self.pootle_path, fileclass)
        output = fileclass()
        try:
            output.settargetlanguage(self.translation_project.language.code)
        except ObjectDoesNotExist:
            pass
        #FIXME: we should add some headers
        for unit in self.units.iterator():
            output.addunit(unit.convert(output.UnitClass))
        return output

    def __unicode__(self):
        return unicode(self.pootle_path)

    def __str__(self):
        storeclass = self.get_file_class()
        store = self.convert(storeclass)
        return str(store)

######################## TranslationStore #########################

    suggestions_in_format = True

    def _get_units(self):
        if hasattr(self, '_units'):
            return self._units

        self.require_units()
        return self.unit_set.filter(state__gt=OBSOLETE).order_by('index').select_related('store__translation_project')
    units=property(_get_units)

    def max_index(self):
        """Largest unit index"""
        return max_column(self.unit_set.all(), 'index', -1)

    def addunit(self, unit, index=None):
        if index is None:
            index = self.max_index() + 1

        newunit = Unit(store=self, index=index)
        newunit.update(unit)
        if self.id:
            newunit.save()
        else:
            # we can't save the unit if the store is not in the
            # database already, so let's keep it in temporary list
            if not hasattr(self, '_units'):
                class FakeQuerySet(list):
                    def iterator(self):
                        return self.__iter__()
                self._units = FakeQuerySet()
            self._units.append(newunit)

    def findunit(self, source):
        # find using hash instead of index
        source_hash = md5_f(source.encode("utf-8")).hexdigest()
        try:
            return self.units.get(source_hash=source_hash)
        except Unit.DoesNotExist:
            return None

    def findid(self, id):
        if hasattr(self, "id_index"):
            return self.id_index.get(id, None)

        unitid_hash = md5_f(id.encode("utf-8")).hexdigest()
        try:
            return self.units.get(unitid_hash=unitid_hash)
        except Unit.DoesNotExist:
            return None

    def getids(self, filename=None):
        if hasattr(self, "_units"):
            self.makeindex()
        if hasattr(self, "id_index"):
            return self.id_index.keys()
        elif hasattr(self, "dbid_index"):
            return self.dbid_index.values()
        else:
            return self.units.values_list('unitid', flat=True)

    def header(self):
        #FIXME: we should store some metadata in db
        if self.file and hasattr(self.file, 'header'):
            return self.file.header()

############################### Stats ############################

    @getfromcache
    def getquickstats(self):
        """calculate translation statistics"""
        try:
            return calculate_stats(self.units)
        except IntegrityError:
            logging.info("Duplicate IDs in %s", self.abs_real_path)
        except base.ParseError, e:
            logging.info("Failed to parse %s\n%s", self.abs_real_path, e)
        except (IOError, OSError), e:
            logging.info("Can't access %s\n%s", self.abs_real_path, e)
        stats = {}
        stats.update(empty_quickstats)
        stats['errors'] += 1
        return stats

    @getfromcache
    def getcompletestats(self):
        """report result of quality checks"""
        self.require_qualitychecks()
        queryset = QualityCheck.objects.filter(unit__store=self, unit__state__gt=UNTRANSLATED, false_positive=False)
        return group_by_count(queryset, 'name')

    @getfromcache
    def has_suggestions(self):
        """check if any unit in store has suggestions"""
        return Suggestion.objects.filter(unit__store=self, unit__state__gt=OBSOLETE).count()

################################ Translation #############################

    def getitem(self, item):
        """Returns a single unit based on the item number."""
        return self.units[item]

    @commit_on_success
    def mergefile(self, newfile, username, allownewstrings, suggestions, notranslate, obsoletemissing):
        """make sure each msgid is unique ; merge comments etc from
        duplicates into original"""

        monolingual = is_monolingual(type(newfile))
        if self.state == LOCKED:
            # file currently being updated
            #FIXME: shall we idle wait for lock to be released first? what about stale locks?
            logging.info("attemped to merge %s while locked", self.pootle_path)
            return

        # must be done before locking the file in case it wasn't already parsed
        self.require_units()
        logging.debug("merging %s", self.pootle_path)

        # lock store
        oldstate = self.state
        self.state = LOCKED
        self.save()
        try:
            self.require_dbid_index(update=True)
            old_ids = set(self.dbid_index.keys())
            if issubclass(self.translation_project.project.get_file_class(),  newfile.__class__):
                new_ids = set(newfile.getids())
            else:
                new_ids = set(newfile.getids(self.name))

            if (not monolingual or self.translation_project.is_template_project) and allownewstrings:
                new_units = (newfile.findid(uid) for uid in new_ids - old_ids)
                for unit in new_units:
                    self.addunit(unit)

            if obsoletemissing:
                obsolete_dbids = [self.dbid_index.get(uid) for uid in old_ids - new_ids]
                for unit in self.findid_bulk(obsolete_dbids):
                    if unit.istranslated():
                        unit.makeobsolete()
                        unit.save()
                    else:
                        unit.delete()

            shared_dbids = [self.dbid_index.get(uid) for uid in old_ids & new_ids]
            for oldunit in self.findid_bulk(shared_dbids):
                newunit = newfile.findid(oldunit.getid())
                if monolingual and not self.translation_project.is_template_project:
                    fix_monolingual(oldunit, newunit, monolingual)
                if notranslate or oldunit.istranslated() and suggestions:
                    if newunit.istranslated():
                        #FIXME: add a user argument
                        oldunit.add_suggestion(newunit.target, None)
                else:
                    changed = oldunit.merge(newunit)
                    if changed:
                        oldunit.save()

            self.sync(update_structure=True, update_translation=True, conservative=False, create=False)

        finally:
            # unlock store
            self.state = oldstate
            self.save()


    def updateheader(self, user=None):
        had_header = False
        if isinstance(self.file.store, po.pofile):
            had_header = self.file.store.header()
            po_revision_date = time.strftime('%Y-%m-%d %H:%M') + poheader.tzstring()
            headerupdates = {'PO_Revision_Date': po_revision_date,
                             'X_Generator': x_generator}

            language = self.translation_project.language
            headerupdates['Language'] = language.code
            if language.nplurals and language.pluralequation:
                self.file.store.updateheaderplural(language.nplurals, language.pluralequation)

            if user is not None and user.is_authenticated():
                headerupdates['Last_Translator'] = '%s <%s>' % (user.first_name or user.username, user.email)
            else:
                #FIXME: maybe insert settings.TITLE or domain here?
                headerupdates['Last_Translator'] = 'Anonymous Pootle User'

            self.file.store.updateheader(add=True, **headerupdates)
        return had_header

############################## Pending Files #################################

    def init_pending(self):
        """initialize pending translations file if needed"""
        if self.pending:
            # pending file already referenced in db, but does it
            # really exist
            if os.path.exists(self.pending.path):
                # pending file exists
                return
            else:
                # pending file doesn't exist anymore
                self.pending = None
                self.save()

        pending_name = os.extsep.join(self.file.name.split(os.extsep)[:-1] + ['po', 'pending'])
        pending_path = os.path.join(settings.PODIRECTORY, pending_name)

        # check if pending file already exists, just in case it was
        # added outside of pootle
        if os.path.exists(pending_path):
            self.pending = pending_name
            self.save()

    def import_pending(self):
        """import suggestions from legacy .pending files, into database"""
        self.init_pending()
        if not self.pending:
            return

        for sugg in [sugg for sugg in self.pending.store.units if sugg.istranslatable() and sugg.istranslated()]:
            if not sugg.istranslatable() or not sugg.istranslated():
                continue
            unit = self.findunit(sugg.source)
            if unit:
                suggester = self.getsuggester_from_pending(sugg)
                unit.add_suggestion(sugg.target, suggester, touch=False)
                self.pending.store.units.remove(sugg)
        if len(self.pending.store.units) >  1:
            self.pending.savestore()
        else:
            self.pending.delete()
            self.pending = None
            self.save()

    def getsuggester_from_pending(self, unit):
        """returns who suggested the given item's suggitem if
        recorded, else None"""
        suggestedby = suggester_regexp.search(unit.msgidcomment)
        if suggestedby:
            username = suggestedby.group(1)
            from pootle_profile.models import PootleProfile
            try:
                return PootleProfile.objects.get(user__username=username)
            except PootleProfile.DoesNotExist:
                pass
        return None
