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

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.db.models.signals import pre_save, post_save, post_init, post_delete
from django.db.transaction import commit_on_success


from translate.storage import base, statsdb, po, poheader
from translate.misc.hash import md5_f
from translate.misc.multistring import multistring

from pootle.__version__ import sver as pootle_version

from pootle_app.lib.util import RelatedManager
from pootle_misc.util import getfromcache, deletefromcache
from pootle_misc.aggregate import group_by_count, max_column
from pootle_misc.baseurl import l

from pootle_store.fields  import TranslationStoreField, MultiStringField
from pootle_store.signals import translation_file_updated, post_unit_update
from pootle_store.util import calculate_stats

# Store States
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

def count_words(strings):
    wordcount = 0
    for string in strings:
        wordcount += statsdb.wordcount(string)
    return wordcount

class Unit(models.Model, base.TranslationUnit):
    objects = RelatedManager()
    class Meta:
        ordering = ['store', 'index']
        #unique_together = ('store', 'unitid_hash')

    store = models.ForeignKey("pootle_store.Store", db_index=True, editable=False)
    index = models.IntegerField(db_index=True, editable=False)
    unitid = models.TextField(editable=False)
    unitid_hash = models.CharField(max_length=32, db_index=True, editable=False)

    source_f = MultiStringField(null=True)
    source_hash = models.CharField(max_length=32, db_index=True, editable=False)
    source_wordcount = models.SmallIntegerField(default=0, editable=False)
    source_length = models.SmallIntegerField(db_index=True, default=0, editable=False)

    target_f = MultiStringField(null=True)
    target_wordcount = models.SmallIntegerField(default=0, editable=False)
    target_length = models.SmallIntegerField(db_index=True, default=0, editable=False)

    developer_comment = models.TextField(null=True)
    translator_comment = models.TextField(null=True)
    locations = models.TextField(null=True, editable=False)
    context = models.TextField(null=True, editable=False)
    fuzzy = models.BooleanField(default=False)
    obsolete = models.BooleanField(default=False, editable=False)

    def init_nondb_state(self):
        self._rich_source = None
        self._rich_target = None
        self.unitclass = po.pounit
        self._encoding = 'UTF-8'

    def _get_source(self):
        return self.source_f

    def _set_source(self, value):
        self.source_f = value
        self.source_hash = md5_f(self.source_f.encode("utf-8")).hexdigest()
        self.source_wordcount = count_words(self.source_f.strings)
        self.source_length = len(self.source_f)

    _source = property(_get_source, _set_source)

    def _get_target(self):
        return self.target_f

    def _set_target(self, value):
        self.target_f = value
        self.target_wordcount = count_words(self.target_f.strings)
        self.target_length = len(self.target_f)

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
        return newunit

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self.source)

    def __unicode__(self):
        return unicode(str(self.convert(self.unitclass)).decode(self._encoding))


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
                if not (wordcount == self.target_wordcount == 0):
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
            self.fuzzy = unit.isfuzzy()
            changed = True
        if self.isobsolete() != unit.isobsolete():
            self.obsolete = unit.isobsolete()
            changed = True
        if self.unitid != unit.getid():
            self.unitid = unit.getid()
            self.unitid_hash = md5_f(self.unitid.encode("utf-8")).hexdigest()
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
        return self.locations.split('\n')

    def addlocation(self, location):
        if self.locations is None:
            self.locations = ''
        self.locations += location + "\n"

    def getcontext(self):
        return self.context

    def setcontext(self, value):
        self.context = value

    def isfuzzy(self):
        return self.fuzzy

    def markfuzzy(self, value=True):
        self.fuzzy = value

    def hasplural(self):
        return self.source is not None and len(self.source.strings) > 1

    def isobsolete(self):
        return self.obsolete

    def makeobsolete(self):
        self.obsolete = True

    @classmethod
    def buildfromunit(cls, unit):
        newunit = cls()
        newunit.update(unit)
        return newunit

    def addalttrans(self, txt):
        self.add_suggestion(txt)

    def getalttrans(self):
        return self.get_suggestions()

    def delalttrans(self, alternative):
        alternative.delete()

###################### Translation ################################
    def update_from_form(self, newvalues):
        """update the unit with a new target, value, comments or fuzzy state"""
        if newvalues.has_key('target'):
            if not self.hasplural() and not isinstance(newvalues['target'], basestring):
                self.target = newvalues['target'][0]
            else:
                self.target = newvalues['target']

        if newvalues.has_key('fuzzy'):
            self.markfuzzy(newvalues['fuzzy'])

        if newvalues.has_key('translator_comments'):
            self.addnote(newvalues['translator_comments'],
                         origin="translator", position="replace")

##################### Suggestions #################################
    def get_suggestions(self):
        return self.suggestion_set.all()

    def get_suggestion(self, item, translation):
        translation = multistring(translation)
        try:
            suggestion = self.get_suggestions()[item]
            if suggestion.target == translation:
                return suggestion
        except IndexError:
            pass

        try:
            suggestion = self.suggestion_set.get(target_hash=md5_f(translation.encode("utf-8")).hexdigest())
            return suggestion
        except Suggestion.DoesNotExist:
            pass


    def add_suggestion(self, translation, user=None):
        suggestion = Suggestion(unit=self, user=user)
        suggestion.target = translation
        try:
            suggestion.save()
        except:
            # probably duplicate suggestion
            return None
        return suggestion

    def accept_suggestion(self, item, translation):
        suggestion = self.get_suggestion(item, translation)
        if suggestion is None:
            return
        self.target = suggestion.target
        self.save()
        suggestion.delete()

    def reject_suggestion(self, item, translation):
        suggestion = self.get_suggestion(item, translation)
        if suggestion is None:
            return
        suggestion.delete()

def init_baseunit(sender, instance, **kwargs):
    instance.init_nondb_state()
post_init.connect(init_baseunit, sender=Unit)

def unit_post_save(sender, instance, created, **kwargs):
    if not instance.store.state < CHECKED:
        instance.update_qualitychecks(created)
post_save.connect(unit_post_save, sender=Unit)

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
    state = models.IntegerField(null=False, default=NEW, editable=False)
    class Meta:
        ordering = ['pootle_path']
        unique_together = ('parent', 'name')

    def handle_file_update(self, sender, **kwargs):
        deletefromcache(self, ["getquickstats", "getcompletestats"])

    def _get_abs_real_path(self):
        if self.file:
            return self.file.path

    abs_real_path = property(_get_abs_real_path)

    def _get_real_path(self):
        return self.file.name

    real_path = property(_get_real_path)

    def __unicode__(self):
        return self.pootle_path

    def get_absolute_url(self):
        return l(self.pootle_path)

    def require_units(self):
        """make sure file is parsed and units are created"""
        if self.state < PARSED:
            self.update()
            self.state = PARSED
            self.save()

    @commit_on_success
    def update(self):
        """update db with units from file"""
        if self.state < PARSED:
            # no existing units in db, file hasn't been parsed before
            # no point in merging, add units directly
            for index, unit in enumerate(self.file.store.units):
                if unit.istranslatable():
                    newunit = Unit(store=self, index=index)
                    newunit.update(unit)
                    newunit.save()
            return
        old_ids = set(self.getids())
        new_ids = set(self.file.store.getids())

        obsolete_units = (self.findid(uid) for uid in old_ids - new_ids)
        for unit in obsolete_units:
            unit.delete()

        new_units = (self.file.store.findid(uid) for uid in new_ids - old_ids)
        for unit in new_units:
            newunit = Unit(store=self, index=unit.index)
            newunit.update(unit)
            newunit.save()

        shared_units = ((self.findid(uid), self.file.store.findid(uid)) for uid in old_ids & new_ids)
        for oldunit, unit in shared_units:
            oldunit.index = unit.index
            changed = oldunit.update(unit)
            if changed:
                oldunit.save()

    def require_qualitychecks(self):
        """make sure quality checks are run"""
        if self.state < CHECKED:
            self.update_qualitychecks()
            self.state = CHECKED
            self.save()

    @commit_on_success
    def update_qualitychecks(self):
        for unit in self.units.iterator():
            unit.update_qualitychecks()

    def sync(self):
        """sync file with translations from db"""
        self.file.store.require_index()
        for unit in self.units:
            match = self.file.store.findid(unit.getid())
            if match is not None:
                unit.sync(match)

    def convert(self, fileclass):
        """export to fileclass"""
        output = fileclass()
        output.settargetlanguage(self.translation_project.language.code)
        #FIXME: we should add some headers
        for unit in self.units.iterator():
            output.addunit(unit.convert(output.UnitClass))
        return output

######################## TranslationStore #########################

    def _get_units(self):
        self.require_units()
        return self.unit_set.order_by('index')
    units=property(_get_units)

    def addunit(self, unit, index=None):
        if index is None:
            index = max_column(self.units, 'index', -1) + 1

        newunit = Unit(store=self, index=index)
        newunit.update(unit)
        newunit.save()

        self.file.addunit(self.file.store.UnitClass.buildfromunit(unit))

    def findunit(self, source):
        # find using hash instead of index
        source_hash = md5_f(source.encode("utf-8")).hexdigest()
        try:
            return self.units.get(source_hash=source_hash)
        except Unit.DoesNotExist:
            return None

    def findid(self, id):
        unitid_hash = md5_f(id.encode("utf-8")).hexdigest()
        try:
            return self.units.get(unitid_hash=unitid_hash)
        except Unit.DoesNotExist:
            return None

    def getids(self):
        return self.units.values_list('unitid', flat=True)

    suggestions_in_format = True

############################### Stats ############################

    @getfromcache
    def getquickstats(self):
        """calculate translation statistics"""
        return calculate_stats(self.units)

    @getfromcache
    def getcompletestats(self):
        """report result of quality checks"""
        self.require_qualitychecks()
        queryset = QualityCheck.objects.filter(unit__store=self)
        return group_by_count(queryset, 'name')

    def has_suggestions(self):
        """check if any unit in store has suggestions"""
        return Suggestion.objects.filter(unit__store=self).count() > 0

################################ Translation #############################

    def getitem(self, item):
        """Returns a single unit based on the item number."""
        return self.units[item]

    @commit_on_success
    def mergefile(self, newfile, username, allownewstrings, suggestions, notranslate, obsoletemissing):
        """make sure each msgid is unique ; merge comments etc from
        duplicates into original"""
        old_ids = set(self.getids())
        new_ids = set(newfile.getids())

        if allownewstrings:
            new_units = (newfile.findid(uid) for uid in new_ids - old_ids)
            for unit in new_units:
                self.addunit(unit)

        if obsoletemissing:
            old_units = (self.findid(uid) for uid in old_ids - new_ids)
            for unit in old_units:
                unit.makeobsolete()
                unit.save()

        if notranslate or suggestions:
            self.initpending(create=True)

        shared_units = ((self.findid(uid), newfile.findid(uid)) for uid in old_ids & new_ids)
        for oldunit, newunit in shared_units:
            if not newunit.istranslated():
                continue

            if notranslate or oldunit.istranslated() and suggestions:
                self.addunitsuggestion(oldunit, newunit, username)
            else:
                oldunit.merge(newunit)
                oldunit.save()

        if (suggestions or notranslate) and not self.file.store.suggestions_in_format:
            self.pending.savestore()

        self.sync()
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

    def updateunit(self, item, newvalues, user=None):
        """Updates a translation with a new target value, comments, or fuzzy
        state."""
        # operation replaces file, make sure we have latest copy
        oldstats = self.getquickstats()
        self.file._update_store_cache()

        unit = self.getitem(item)
        unit.update_from_form(newvalues)
        unit.save()

        unit.sync(unit.getorig())
        had_header = self.updateheader(user)
        self.file.savestore()
        newstats = self.getquickstats()
        post_unit_update.send(sender=self, oldstats=oldstats, newstats=newstats)


############################ Translation Memory ##########################

    def inittm(self):
        """initialize translation memory file if needed"""
        if self.tm and os.path.exists(self.tm.path):
            return
        if not self.file:
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


############################## Suggestions #################################

    def initpending(self, create=False):
        """initialize pending translations file if needed"""
        #FIXME: we parse file just to find if suggestions can be
        #stored in format, maybe we should store TranslationStore
        #class and query it for such info
        if self.file.store.suggestions_in_format:
            # suggestions can be stored in the translation file itself
            return
        pending_name = os.extsep.join(self.file.name.split(os.extsep)[:-1] + ['po', 'pending'])
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

    def addsuggestion(self, item, suggtarget, username):
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
            self.initpending(create=True)
            newpo = self.pending.store.UnitClass.buildfromunit(unit)
            newpo.target = suggtarget
            newpo.markfuzzy(False)
            self.addunitsuggestion(unit, newpo, username)
            self.pending.savestore()

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

    def deletesuggestion(self, item, suggitem, newtrans):
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

########################### Signals ###############################

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
