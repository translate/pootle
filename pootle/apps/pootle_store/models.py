#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import datetime
import logging
import os
import re
import time
from hashlib import md5
from itertools import chain

from translate.filters.decorators import Category
from translate.storage import base

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import models, DatabaseError, IntegrityError
from django.db.models.signals import post_delete, post_save, pre_delete
from django.db.transaction import commit_on_success
from django.utils import timezone, tzinfo
from django.utils.translation import ugettext_lazy as _

from taggit.managers import TaggableManager

from pootle.core.managers import RelatedManager
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_misc.aggregate import group_by_count_extra, max_column
from pootle_misc.baseurl import l
from pootle_misc.checks import check_names
from pootle_misc.util import (cached_property, getfromcache, deletefromcache,
                              datetime_min)
from pootle_statistics.models import SubmissionFields, SubmissionTypes
from pootle_store.fields import (TranslationStoreField, MultiStringField,
                                 PLURAL_PLACEHOLDER, SEPARATOR)
from pootle_store.filetypes import factory_classes, is_monolingual
from pootle_store.util import (calculate_stats, empty_quickstats,
                               OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED)
from pootle_tagging.models import ItemWithGoal


#
# Store States
#

# Store being modified
LOCKED = -1
# Store just created, not parsed yet
NEW = 0
# Store just parsed, units added but no quality checks were run
PARSED = 1
# Quality checks run
CHECKED = 2


############### Quality Check #############

class QualityCheck(models.Model):
    """Database cache of results of qualitychecks on unit."""
    name = models.CharField(max_length=64, db_index=True)
    unit = models.ForeignKey("pootle_store.Unit", db_index=True)
    category = models.IntegerField(null=False, default=Category.NO_CATEGORY)
    message = models.TextField()
    false_positive = models.BooleanField(default=False, db_index=True)

    objects = RelatedManager()

    @property
    def display_name(self):
        return check_names.get(self.name, self.name)

    def __unicode__(self):
        return self.name


################# Suggestion ################

class SuggestionManager(RelatedManager):
    def get_by_natural_key(self, target_hash, unitid_hash, pootle_path):
        return self.get(target_hash=target_hash, unit__unitid_hash=unitid_hash,
                 unit__store__pootle_path=pootle_path)


class Suggestion(models.Model, base.TranslationUnit):
    """Suggested translation for a :cls:`~pootle_store.models.Unit`, provided
    by users or automatically generated after a merge.
    """
    target_f = MultiStringField()
    target_hash = models.CharField(max_length=32, db_index=True)
    unit = models.ForeignKey('pootle_store.Unit')
    user = models.ForeignKey('pootle_profile.PootleProfile', null=True)

    translator_comment_f = models.TextField(null=True, blank=True)

    objects = SuggestionManager()

    class Meta:
        unique_together = ('unit', 'target_hash')

    def natural_key(self):
        return (self.target_hash, self.unit.unitid_hash,
                self.unit.store.pootle_path)
    natural_key.dependencies = ['pootle_store.Unit', 'pootle_store.Store']

    ############################ Properties ###################################

    @property
    def _target(self):
        return self.target_f

    @_target.setter
    def _target(self, value):
        self.target_f = value
        self._set_hash()

    @property
    def _source(self):
        return self.unit._source

    @property
    def translator_comment(self):
        return self.translator_comment_f

    @translator_comment.setter
    def translator_comment(self, value):
        self.translator_comment_f = value
        self._set_hash()

    ############################ Methods ######################################

    def __unicode__(self):
        return unicode(self.target)

    def _set_hash(self):
        string = self.translator_comment_f
        if string:
            string = self.target_f + SEPARATOR + string
        else:
            string = self.target_f
        self.target_hash = md5(string.encode("utf-8")).hexdigest()


################################ Signal handlers ##############################

def delete_votes(sender, instance, **kwargs):
    # Since votes are linked by ContentType and not foreign keys, referential
    # integrity is not kept, and we have to ensure we remove any votes manually
    # when a suggestion is removed
    from voting.models import Vote
    from django.contrib.contenttypes.models import ContentType
    ctype = ContentType.objects.get_for_model(instance)
    Vote.objects.filter(content_type=ctype,
                        object_id=instance._get_pk_val()).delete()

post_delete.connect(delete_votes, sender=Suggestion)


############### Unit ####################

def fix_monolingual(oldunit, newunit, monolingual=None):
    """Hackish workaround for monolingual files always having only source and
    no target.

    We compare monolingual unit with corresponding bilingual unit, if sources
    differ assume monolingual source is actually a translation.
    """
    if monolingual is None:
        monolingual = is_monolingual(type(newunit._store))

    if monolingual and newunit.source != oldunit.source:
        newunit.target = newunit.source
        newunit.source = oldunit.source


def count_words(strings):
    from translate.storage import statsdb
    wordcount = 0

    for string in strings:
        wordcount += statsdb.wordcount(string)

    return wordcount


def stringcount(string):
    try:
        return len(string.strings)
    except AttributeError:
        return 1


class UnitManager(RelatedManager):

    def get_by_natural_key(self, unitid_hash, pootle_path):
        return self.get(unitid_hash=unitid_hash,
                        store__pootle_path=pootle_path)

    def get_for_path(self, pootle_path, profile):
        """Returns units that fall below the `pootle_path` umbrella.

        :param pootle_path: An internal pootle path.
        :param profile: The user profile who is accessing the units.
        """
        lang, proj, dir_path, filename = split_pootle_path(pootle_path)

        units_qs = super(UnitManager, self).get_query_set().filter(
            state__gt=OBSOLETE,
        )

        # /projects/<project_code>/translate/*
        if lang is None and proj is not None:
            units_qs = units_qs.extra(
                where=[
                    '`pootle_store_store`.`pootle_path` LIKE %s',
                    '`pootle_store_store`.`pootle_path` NOT LIKE %s',
                ], params=[''.join(['/%/', proj ,'/%']), '/templates/%']
            )
        # /<lang_code>/<project_code>/translate/*
        # /<lang_code>/translate/*
        # /translate/*
        else:
            units_qs = units_qs.filter(
                store__pootle_path__startswith=pootle_path,
            )

        return units_qs


class Unit(models.Model, base.TranslationUnit):
    store = models.ForeignKey("pootle_store.Store", db_index=True)
    index = models.IntegerField(db_index=True)
    unitid = models.TextField(editable=False)
    unitid_hash = models.CharField(max_length=32, db_index=True,
            editable=False)

    source_f = MultiStringField(null=True)
    source_hash = models.CharField(max_length=32, db_index=True,
            editable=False)
    source_wordcount = models.SmallIntegerField(default=0, editable=False)
    source_length = models.SmallIntegerField(db_index=True, default=0,
            editable=False)

    target_f = MultiStringField(null=True, blank=True)
    target_wordcount = models.SmallIntegerField(default=0, editable=False)
    target_length = models.SmallIntegerField(db_index=True, default=0,
            editable=False)

    developer_comment = models.TextField(null=True, blank=True)
    translator_comment = models.TextField(null=True, blank=True)
    locations = models.TextField(null=True, editable=False)
    context = models.TextField(null=True, editable=False)

    state = models.IntegerField(null=False, default=UNTRANSLATED, db_index=True)

    # Metadata
    mtime = models.DateTimeField(auto_now=True, auto_now_add=True,
                                 db_index=True, editable=False)

    submitted_by = models.ForeignKey('pootle_profile.PootleProfile', null=True,
            db_index=True, related_name='submitted')
    submitted_on = models.DateTimeField(auto_now_add=True, db_index=True,
            null=True)

    commented_by = models.ForeignKey('pootle_profile.PootleProfile', null=True,
            db_index=True, related_name='commented')
    commented_on = models.DateTimeField(auto_now_add=True, db_index=True,
            null=True)

    objects = UnitManager()

    class Meta:
        ordering = ['store', 'index']
        unique_together = ('store', 'unitid_hash')
        get_latest_by = 'mtime'

    def natural_key(self):
        return (self.unitid_hash, self.store.pootle_path)
    natural_key.dependencies = ['pootle_store.Store']

    ############################ Properties ###################################

    @property
    def _source(self):
        return self.source_f

    @_source.setter
    def _source(self, value):
        self.source_f = value
        self._source_updated = True

    @property
    def _target(self):
        return self.target_f

    @_target.setter
    def _target(self, value):
        self.target_f = value
        self._target_updated = True

    ############################ Methods ######################################

    def __unicode__(self):
        # FIXME: consider using unit id instead?
        return unicode(self.source)

    def __str__(self):
        unitclass = self.get_unit_class()
        return str(self.convert(unitclass))

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
            self.source_hash = md5(self.source_f.encode("utf-8")).hexdigest()
            self.source_wordcount = count_words(self.source_f.strings)
            self.source_length = len(self.source_f)

        if self._target_updated:
            # update target related fields
            self.target_wordcount = count_words(self.target_f.strings)
            self.target_length = len(self.target_f)
            if filter(None, self.target_f.strings):
                if self.state == UNTRANSLATED:
                    self.state = TRANSLATED
            elif self.state > FUZZY:
                self.state = UNTRANSLATED

        super(Unit, self).save(*args, **kwargs)

        if (settings.AUTOSYNC and self.store.file and
            self.store.state >= PARSED and
            (self._target_updated or self._source_updated)):
            #FIXME: last translator information is lost
            self.sync(self.getorig())
            self.store.update_store_header()
            self.store.file.savestore()

        if (self.store.state >= CHECKED and
            (self._source_updated or self._target_updated)):
            #FIXME: are we sure only source and target affect quality checks?
            self.update_qualitychecks()

        # done processing source/target update remove flag
        self._source_updated = False
        self._target_updated = False

        if self.store.state >= PARSED:
            # updated caches
            store = self.store
            deletefromcache(store, ["getquickstats", "getcompletestats",
                                    "get_mtime", "get_suggestion_count"])

    def get_absolute_url(self):
        return l(self.store.pootle_path)

    def get_translate_url(self):
        lang, proj, dir, fn = split_pootle_path(self.store.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            '#unit=', unicode(self.id),
        ])

    def get_mtime(self):
        return self.mtime

    def convert(self, unitclass):
        """Convert to a unit of type :param:`unitclass` retaining as much
        information from the database as the target format can support."""
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
                newunit.addalttrans(suggestion.target,
                                    origin=unicode(suggestion.user))

        if self.isobsolete():
            newunit.makeobsolete()

        return newunit

    def get_unit_class(self):
        try:
            return self.store.get_file_class().UnitClass
        except ObjectDoesNotExist:
            from translate.storage import po
            return po.pounit

    def getorig(self):
        unit = self.store.file.store.units[self.index]
        if self.getid() == unit.getid():
            return unit

        # FIXME: if we are here, file changed structure and we need to update
        # indexes
        logging.debug(u"Incorrect unit index %d for %s in file %s",
                      unit.index, unit, unit.store.file)

        self.store.file.store.require_index()
        unit = self.store.file.store.findid(self.getid())

        return unit

    def sync(self, unit):
        """Sync in file unit with translations from the DB."""
        changed = False

        if not self.isobsolete() and unit.isobsolete():
            unit.resurrect()
            changed = True

        if unit.target != self.target:
            if unit.hasplural():
                nplurals = self.store.translation_project.language.nplurals
                target_plurals = len(self.target.strings)
                strings = self.target.strings
                if target_plurals < nplurals:
                    strings.extend([u'']*(nplurals - target_plurals))
                if unit.target.strings != strings:
                    unit.target = strings
                    changed = True
            else:
                unit.target = self.target
                changed = True

        self_notes = self.getnotes(origin="translator")
        if unit.getnotes(origin="translator") != self_notes or '':
            unit.addnote(self_notes, origin="translator", position="replace")
            changed = True

        if unit.isfuzzy() != self.isfuzzy():
            unit.markfuzzy(self.isfuzzy())
            changed = True

        if hasattr(unit, 'addalttrans') and self.get_suggestions().count():
            alttranslist = [alttrans.target for alttrans in unit.getalttrans()]
            for suggestion in self.get_suggestions().iterator():
                if suggestion.target in alttranslist:
                    # don't add duplicate suggestion
                    continue
                unit.addalttrans(suggestion.target, unicode(suggestion.user))
                changed = True

        if self.isobsolete() and not unit.isobsolete():
            unit.makeobsolete()
            changed = True

        return changed

    def update(self, unit):
        """Update in-DB translation from the given :param:`unit`.

        :rtype: bool
        :return: True if the new :param:`unit` differs from the current unit.
            Two units differ when any of the fields differ (source, target,
            translator/developer comments, locations, context, status...).
        """
        changed = False

        if (self.source != unit.source or
            len(self.source.strings) != stringcount(unit.source) or
            self.hasplural() != unit.hasplural()):

            if unit.hasplural() and len(unit.source.strings) == 1:
                self.source = [unit.source, PLURAL_PLACEHOLDER]
            else:
                self.source = unit.source

            changed = True

        if (self.target != unit.target or
            len(self.target.strings) != stringcount(unit.target)):
            notempty = filter(None, self.target_f.strings)
            self.target = unit.target

            if filter(None, self.target_f.strings) or notempty:
                #FIXME: we need to do this cause we discard nplurals
                # for empty plurals
                changed = True

        notes = unit.getnotes(origin="developer")

        if (self.developer_comment != notes and
            (self.developer_comment or notes)):
            self.developer_comment = notes or None
            changed = True

        notes = unit.getnotes(origin="translator")

        if (self.translator_comment != notes and
            (self.translator_comment or notes)):
            self.translator_comment = notes or None
            changed = True

        locations = "\n".join(unit.getlocations())
        if self.locations != locations and (self.locations or locations):
            self.locations = locations or None
            changed = True

        context = unit.getcontext()
        if self.context != unit.getcontext() and (self.context or context):
            self.context = context or None
            changed = True

        if self.isfuzzy() != unit.isfuzzy():
            self.markfuzzy(unit.isfuzzy())
            changed = True

        if self.isobsolete() != unit.isobsolete():
            if unit.isobsolete():
                self.makeobsolete()
            else:
                self.resurrect()

            changed = True

        if self.unitid != unit.getid():
            self.unitid = unicode(unit.getid()) or unicode(unit.source)
            self.unitid_hash = md5(self.unitid.encode("utf-8")).hexdigest()
            changed = True

        if hasattr(unit, 'getalttrans'):
            for suggestion in unit.getalttrans():
                if suggestion.source == self.source:
                    self.add_suggestion(suggestion.target, touch=False)

                changed = True

        return changed

    def update_qualitychecks(self, created=False, keep_false_positives=False):
        """Run quality checks and store result in the database."""
        existing = []

        if not created:
            checks = self.qualitycheck_set.all()

            if keep_false_positives:
                existing = set(checks.filter(false_positive=True) \
                                     .values_list('name', flat=True))
                checks = checks.filter(false_positive=False)

            checks.delete()

        if not self.target:
            return

        qc_failures = self.store.translation_project.checker \
                                .run_filters(self, categorised=True)

        for name in qc_failures.iterkeys():
            if name == 'isfuzzy' or name in existing:
                continue

            message = qc_failures[name]['message']
            category = qc_failures[name]['category']

            self.qualitycheck_set.create(name=name, message=message,
                                         category=category)

    def get_qualitychecks(self):
        return self.qualitycheck_set.filter(false_positive=False)

    # FIXME: This is a hackish implementation needed due to the underlying
    # lame model definitions
    def get_reviewer(self):
        """Retrieve reviewer information for the current unit.

        :return: In case the current unit's status is an effect of accepting a
            suggestion, the reviewer profile is returned.
            Otherwise, returns ``None``, indicating that the current unit's
            status is an effect of any other actions.
        """
        if self.submission_set.count():
            # Find the latest submission changing either the target or the
            # unit's state and return the reviewer attached to it in case the
            # submission type was accepting a suggestion
            last_submission = self.submission_set.filter(
                    field__in=[SubmissionFields.TARGET, SubmissionFields.STATE]
                ).latest()
            if last_submission.type == SubmissionTypes.SUGG_ACCEPT:
                return getattr(last_submission.from_suggestion, 'reviewer',
                               None)

        return None

    ################# TranslationUnit ############################

    def getnotes(self, origin=None):
        if origin is None:
            notes = ''
            if self.translator_comment is not None:
                notes += self.translator_comment
            if self.developer_comment is not None:
                notes += self.developer_comment
            return notes
        elif origin == "translator":
            return self.translator_comment or ''
        elif origin in ["programmer", "developer", "source code"]:
            return self.developer_comment or ''
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
        self.unitid_hash = md5(self.unitid.encode("utf-8")).hexdigest()

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
            if filter(None, self.target_f.strings):
                self.state = TRANSLATED
            else:
                self.state = UNTRANSLATED

    def hasplural(self):
        return (self.source is not None and
                (len(self.source.strings) > 1
                or hasattr(self.source, "plural") and
                self.source.plural))

    def isobsolete(self):
        return self.state == OBSOLETE

    def makeobsolete(self):
        if self.state > OBSOLETE:
            self.state = OBSOLETE

    def resurrect(self):
        if self.state > OBSOLETE:
            return

        if filter(None, self.target_f.strings):
            self.state = TRANSLATED
        else:
            self.state = UNTRANSLATED

    def istranslated(self):
        if self._target_updated and not self.isfuzzy():
            return bool(filter(None, self.target_f.strings))
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

    def fuzzy_translate(self, matcher):
        candidates = matcher.matches(self.source)
        if candidates:
            match_unit = candidates[0]
            changed = self.merge(match_unit, authoritative=True)
            if changed:
                return match_unit


    def merge(self, merge_unit, overwrite=False, comments=True,
              authoritative=False):
        """Merges :param:`merge_unit` with the current unit.

        :param merge_unit: The unit that will be merged into the current unit.
        :param overwrite: Whether to replace the existing translation or not.
        :param comments: Whether to merge translator comments or not.
        :param authoritative: Not used. Kept for Toolkit API consistenty.
        :return: True if the current unit has been changed.
        """
        changed = False

        if comments:
            notes = merge_unit.getnotes(origin="translator")

            if notes and self.translator_comment != notes:
                self.translator_comment = notes
                changed = True

        # No translation in merge_unit: bail out
        if not bool(merge_unit.target):
            return changed

        # Won't replace existing translation unless overwrite is True
        if bool(self.target) and not overwrite:
            return changed

        # Current translation more trusted
        if self.istranslated() and not merge_unit.istranslated():
            return changed

        if self.target != merge_unit.target:
            self.target = merge_unit.target

            if self.source != merge_unit.source:
                self.markfuzzy()
            else:
                self.markfuzzy(merge_unit.isfuzzy())

            changed = True
        elif self.isfuzzy() != merge_unit.isfuzzy():
            self.markfuzzy(merge_unit.isfuzzy())
            changed = True

        return changed

    ################# Suggestions #################################
    def get_suggestions(self):
        return self.suggestion_set.select_related('user').all()

    def add_suggestion(self, translation, user=None, touch=True):
        if not filter(None, translation):
            return None

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
        self.state = TRANSLATED

        self.submitted_by = suggestion.user
        self.submitted_on = timezone.now()

        # It is important to first delete the suggestion before calling
        # ``save``, otherwise the quality checks won't be properly updated
        # when saving the unit.
        suggestion.delete()
        self.save()

        if settings.AUTOSYNC and self.file:
            #FIXME: update alttrans
            self.sync(self.getorig())
            self.store.update_store_header(profile=suggestion.user)
            self.file.savestore()

        return True

    def reject_suggestion(self, suggid):
        try:
            suggestion = self.suggestion_set.get(id=suggid)
        except Suggestion.DoesNotExist:
            return False

        suggestion.delete()
        # Update timestamp
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

# custom storage otherwise djago assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

# regexp to parse suggester name from msgidcomment
suggester_regexp = re.compile(r'suggested by (.*) \[[-0-9]+\]')


class StoreManager(RelatedManager):
    def get_by_natural_key(self, pootle_path):
        return self.get(pootle_path=pootle_path)


class Store(models.Model, base.TranslationStore):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""

    file = TranslationStoreField(upload_to="fish", max_length=255, storage=fs,
            db_index=True, null=False, editable=False)

    # Deprecated
    pending = TranslationStoreField(ignore='.pending', upload_to="fish",
            max_length=255, storage=fs, editable=False)
    tm = TranslationStoreField(ignore='.tm', upload_to="fish", max_length=255,
            storage=fs, editable=False)

    parent = models.ForeignKey('pootle_app.Directory',
            related_name='child_stores', db_index=True, editable=False)

    translation_project_fk = 'pootle_translationproject.TranslationProject'
    translation_project = models.ForeignKey(translation_project_fk,
            related_name='stores', db_index=True, editable=False)

    pootle_path = models.CharField(max_length=255, null=False, unique=True,
            db_index=True, verbose_name=_("Path"))
    name = models.CharField(max_length=128, null=False, editable=False)

    sync_time = models.DateTimeField(default=datetime_min)
    state = models.IntegerField(null=False, default=NEW, editable=False,
            db_index=True)

    tags = TaggableManager(blank=True, verbose_name=_("Tags"),
                           help_text=_("A comma-separated list of tags."))
    goals = TaggableManager(blank=True, verbose_name=_("Goals"),
                            through=ItemWithGoal,
                            help_text=_("A comma-separated list of goals."))

    UnitClass = Unit
    Name = "Model Store"
    is_dir = False

    objects = StoreManager()

    class Meta:
        ordering = ['pootle_path']
        unique_together = ('parent', 'name')

    def natural_key(self):
        return (self.pootle_path,)
    natural_key.dependencies = ['pootle_app.Directory']

    ############################ Properties ###################################

    @property
    def tag_like_objects(self):
        """Return the tag like objects applied to this store.

        Tag like objects can be either tags or goals.
        """
        return list(chain(self.tags.all().order_by("name"),
                          self.goals.all().order_by("name")))

    @property
    def abs_real_path(self):
        if self.file:
            return self.file.path

    @property
    def real_path(self):
        return self.file.name

    @property
    def is_terminology(self):
        """Is this a project specific terminology store?"""
        #TODO: Consider if this should check if the store belongs to a
        # terminology project. Probably not, in case this might be called over
        # several files in a project.
        return self.name.startswith('pootle-terminology')

    @property
    def units(self):
        if hasattr(self, '_units'):
            return self._units

        self.require_units()
        return self.unit_set.filter(state__gt=OBSOLETE).order_by('index') \
                            .select_related('store__translation_project')

    @units.setter
    def units(self, value):
        """Null setter to avoid tracebacks if :meth:`TranslationStore.__init__`
        is called.
        """
        pass

    ############################ Cached properties ############################

    @cached_property
    def path(self):
        """Returns just the path part omitting language and project codes.

        If the `pootle_path` of a :cls:`Store` object `store` is
        `/af/project/dir1/dir2/file.po`, `store.path` will return
        `dir1/dir2/file.po`.
        """
        return u'/'.join(self.pootle_path.split(u'/')[3:])

    ############################ Methods ######################################

    @classmethod
    def _get_mtime_from_header(cls, store):
        mtime = None
        from translate.storage import poheader
        if isinstance(store, poheader.poheader):
            try:
                _mtime = store.parseheader().get('X-POOTLE-MTIME', None)
                if _mtime:
                    mtime = datetime.datetime.fromtimestamp(float(_mtime))
                    if settings.USE_TZ:
                        # Africa/Johanesburg - pre-2.1 default
                        tz = tzinfo.FixedOffset(120)
                        mtime = timezone.make_aware(mtime, tz)
                    else:
                        mtime -= datetime.timedelta(hours=2)
            except Exception as e:
                logging.debug("failed to parse mtime: %s", e)
        return mtime

    def __unicode__(self):
        return unicode(self.pootle_path)

    def __str__(self):
        storeclass = self.get_file_class()
        store = self.convert(storeclass)
        return str(store)

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
            # new units, let's flush cache
            deletefromcache(self, ["getquickstats", "getcompletestats",
                                   "get_mtime", "get_suggestion_count"])

    def delete(self, *args, **kwargs):
        super(Store, self).delete(*args, **kwargs)
        deletefromcache(self, ["getquickstats", "getcompletestats",
                               "get_mtime", "get_suggestion_count"])

    def get_absolute_url(self):
        return l(self.pootle_path)

    def get_translate_url(self, **kwargs):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            get_editor_filter(**kwargs),
        ])

    @getfromcache
    def get_mtime(self):
        return max_column(self.unit_set.all(), 'mtime', datetime_min)

    def require_units(self):
        """Make sure file is parsed and units are created."""
        if self.state < PARSED and self.unit_set.count() == 0:
            if (self.file and is_monolingual(type(self.file.store)) and
                not self.translation_project.is_template_project):
                self.translation_project \
                    .update_against_templates(pootle_path=self.pootle_path)
            else:
                self.parse()

    def require_dbid_index(self, update=False, obsolete=False):
        """build a quick mapping index between unit ids and database ids"""
        if update or not hasattr(self, "dbid_index"):
            units = self.unit_set.all()
            if not obsolete:
                units = units.filter(state__gt=OBSOLETE)
            self.dbid_index = dict(units.values_list('unitid', 'id'))

    def findid_bulk(self, ids):
        chunks = 200
        for i in xrange(0, len(ids), chunks):
            units = self.unit_set.filter(id__in=ids[i:i+chunks])
            for unit in units.iterator():
                yield unit

    def get_matcher(self):
        """builds a TM matcher from current translations and obsolete units"""
        from translate.search import match
        #FIXME: should we cache this?
        matcher = match.matcher(
            self,
            max_candidates=1,
            max_length=settings.FUZZY_MATCH_MAX_LENGTH,
            min_similarity=settings.FUZZY_MATCH_MIN_SIMILARITY,
            usefuzzy=True
        )
        matcher.extendtm(self.unit_set.filter(state=OBSOLETE))
        matcher.addpercentage = False
        return matcher

    def clean_stale_lock(self):
        if self.state != LOCKED:
            return

        mtime = max_column(self.unit_set.all(), 'mtime', None)
        if mtime is None:
            #FIXME: we can't tell stale locks if store has no units at all
            return

        delta = timezone.now() - mtime
        if delta.days or delta.seconds > 2 * 60 * 60:
            logging.warning("Found stale lock in %s, something went wrong "
                            "with a previous operation on the store",
                            self.pootle_path)

            # lock been around for too long, assume it is stale
            if QualityCheck.objects.filter(unit__store=self).exists():
                # there are quality checks, assume we are checked
                self.state = CHECKED
            else:
                # there are units assumed we are parsed
                self.state = PARSED

            return True

        return False

    @commit_on_success
    def parse(self, store=None):
        self.clean_stale_lock()

        if self.state == LOCKED:
            # File currently being updated
            # FIXME: shall we idle wait for lock to be released first? what
            # about stale locks?
            logging.info(u"Attemped to update %s while locked",
                         self.pootle_path)
            return

        if store is None:
            store = self.file.store

        if self.state < PARSED:
            logging.debug(u"Parsing %s", self.pootle_path)
            # no existing units in db, file hasn't been parsed before
            # no point in merging, add units directly
            old_state = self.state
            self.state = LOCKED
            self.save()
            try:
                for index, unit in enumerate(store.units):
                    if unit.istranslatable():
                        try:
                            self.addunit(unit, index)
                        except IntegrityError as e:
                            logging.warning(u'Data integrity error while '
                                            u'importing unit %s:\n%s',
                                            unit.getid(), e)
            except:
                # Something broke, delete any units that got created
                # and return store state to its original value
                self.unit_set.all().delete()
                self.state = old_state
                self.save()
                raise

            self.state = PARSED
            self.sync_time = self.get_mtime()
            self.save()
            return

    def _remove_obsolete(self, source):
        """Removes an obsolete unit from the DB. This will usually be used
        after fuzzy matching.
        """
        obsolete_unit = self.findunit(source, obsolete=True)
        if obsolete_unit:
            obsolete_unit.delete()

    @commit_on_success
    def update(self, update_structure=False, update_translation=False,
               store=None, fuzzy=False, only_newer=False, modified_since=0):
        """Update DB with units from file.

        :param update_structure: Whether to update store's structure by marking
            common DB units as obsolete and adding new units.
        :param update_translation: Whether to update existing translations or
            not.
        :param store: The target :class:`~pootle_store.models.Store`. If unset,
            the current file will be used as a target.
        :param fuzzy: Whether to perform fuzzy matching or not.
        :param only_newer: Whether to update only the files that changed on
            disk after the last sync.
        :param modified_since: Don't update translations that have been
            modified since the given change ID.
        """
        self.clean_stale_lock()

        if self.state == LOCKED:
            # File currently being updated
            # FIXME: Shall we idle wait for lock to be released first?
            # What about stale locks?
            logging.info(u"Attempted to update %s while locked",
                         self.pootle_path)
            return
        elif self.state < PARSED:
            # File has not been parsed before
            logging.debug(u"Attempted to update unparsed file %s",
                          self.pootle_path)
            self.parse(store=store)
            return

        if only_newer:
            disk_mtime = datetime.datetime \
                                 .fromtimestamp(self.file.getpomtime()[0])
            if settings.USE_TZ:
                tz = timezone.get_default_timezone()
                disk_mtime = timezone.make_aware(disk_mtime, tz)

            if disk_mtime <= self.sync_time:
                # The file on disk wasn't changed since the last sync
                logging.debug(u"File didn't change since last sync, skipping "
                              u"%s", self.pootle_path)
                return

        if store is None:
            store = self.file.store

        # Lock store
        logging.debug(u"Updating %s", self.pootle_path)
        old_state = self.state
        self.state = LOCKED
        self.save()

        try:
            if fuzzy:
                matcher = self.get_matcher()

            monolingual = is_monolingual(type(store))

            # Force a rebuild of the unit ID <-> DB ID index and get IDs for
            # in-DB (old) and on-disk (new) stores
            self.require_dbid_index(update=True, obsolete=True)
            old_ids = set(self.dbid_index.keys())
            new_ids = set(store.getids())

            if update_structure:
                # Remove old units or make them obsolete if they were already
                # translated
                obsolete_dbids = [self.dbid_index.get(uid)
                                  for uid in old_ids - new_ids]
                for unit in self.findid_bulk(obsolete_dbids):
                    if unit.istranslated():
                        unit.makeobsolete()
                        unit.save()
                    else:
                        unit.delete()

                # Add new units to the store
                new_units = (store.findid(uid) for uid in new_ids - old_ids)
                for unit in new_units:
                    newunit = self.addunit(unit, unit.index)

                    # Fuzzy match non-empty target strings
                    if fuzzy and not filter(None, newunit.target.strings):
                        match_unit = newunit.fuzzy_translate(matcher)
                        if match_unit:
                            newunit.save()
                            self._remove_obsolete(match_unit.source)

                    # Update quality checks for the new unit in case they were
                    # calculated for the store before
                    if old_state >= CHECKED:
                        newunit.update_qualitychecks(created=True)

            if update_translation or modified_since:
                modified_units = set()

                if modified_since:
                    from pootle_statistics.models import Submission
                    self_unit_ids = set(self.dbid_index.values())

                    try:
                        modified_units = set(Submission.objects.filter(
                                id__gt=modified_since,
                                unit__id__in=self_unit_ids,
                        ).values_list('unit', flat=True).distinct())
                    except DatabaseError as e:
                        # SQLite might barf with the IN operator over too many
                        # values
                        modified_units = set(Submission.objects.filter(
                                id__gt=modified_since,
                        ).values_list('unit', flat=True).distinct())
                        modified_units &= self_unit_ids

                common_dbids = set(self.dbid_index.get(uid) \
                                   for uid in old_ids & new_ids)

                # If some units have been modified since a given change ID,
                # keep them safe and avoid overwrites
                if modified_units:
                    common_dbids -= modified_units

                common_dbids = list(common_dbids)
                for unit in self.findid_bulk(common_dbids):
                    newunit = store.findid(unit.getid())

                    if (monolingual and not
                        self.translation_project.is_template_project):
                        fix_monolingual(unit, newunit, monolingual)

                    changed = unit.update(newunit)

                    # Unit's index within the store might have changed
                    if update_structure and unit.index != newunit.index:
                        unit.index = newunit.index
                        changed = True

                    # Fuzzy match non-empty target strings
                    if fuzzy and not filter(None, unit.target.strings):
                        match_unit = unit.fuzzy_translate(matcher)
                        if match_unit:
                            changed = True
                            self._remove_obsolete(match_unit.source)

                    if changed:
                        do_checks = unit._source_updated or unit._target_updated
                        unit.save()
                        if do_checks and old_state >= CHECKED:
                            unit.update_qualitychecks()
        finally:
            # Unlock store
            self.state = old_state
            if (update_structure and
                (update_translation or modified_since)):
                self.sync_time = timezone.now()
            self.save()

    def require_qualitychecks(self):
        """make sure quality checks are run"""
        if self.state < CHECKED:
            self.update_qualitychecks()
            # new qualitychecks, let's flush cache
            deletefromcache(self, ["getcompletestats"])

    @commit_on_success
    def update_qualitychecks(self):
        logging.debug(u"Updating quality checks for %s", self.pootle_path)
        for unit in self.units.iterator():
            unit.update_qualitychecks()

        if self.state < CHECKED:
            self.state = CHECKED
            self.save()

    def sync(self, update_structure=False, update_translation=False,
             conservative=True, create=False, profile=None, skip_missing=False,
             modified_since=0):
        """Sync file with translations from DB."""
        if skip_missing and not self.file.exists():
            return

        if (not modified_since and conservative and
            self.sync_time >= self.get_mtime()):
            return

        if not self.file:
            if create:
                # File doesn't exist let's create it
                logging.debug(u"Creating file %s", self.pootle_path)

                storeclass = self.get_file_class()
                store_path = os.path.join(
                    self.translation_project.abs_real_path, self.name
                )
                store = self.convert(storeclass)
                store.savefile(store_path)

                self.file = store_path
                self.update_store_header(profile=profile)
                self.file.savestore()
                self.sync_time = self.get_mtime()

                self.save()
            return

        if conservative and self.translation_project.is_template_project:
            # don't save to templates
            return

        logging.debug(u"Syncing %s", self.pootle_path)
        self.require_dbid_index(update=True)
        disk_store = self.file.store
        old_ids = set(disk_store.getids())
        new_ids = set(self.dbid_index.keys())

        file_changed = False

        if update_structure:
            obsolete_units = (disk_store.findid(uid) \
                              for uid in old_ids - new_ids)
            for unit in obsolete_units:
                if not unit.istranslated():
                    del unit
                elif not conservative:
                    unit.makeobsolete()

                    if not unit.isobsolete():
                        del unit

                file_changed = True

            new_dbids = [self.dbid_index.get(uid) for uid in new_ids - old_ids]
            for unit in self.findid_bulk(new_dbids):
                newunit = unit.convert(disk_store.UnitClass)
                disk_store.addunit(newunit)
                file_changed = True

        monolingual = is_monolingual(type(disk_store))

        if update_translation:
            modified_units = set()

            if modified_since:
                from pootle_statistics.models import Submission
                self_unit_ids = set(self.dbid_index.values())

                try:
                    modified_units = set(Submission.objects.filter(
                            id__gt=modified_since,
                            unit__id__in=self_unit_ids,
                    ).values_list('unit', flat=True).distinct())
                except DatabaseError as e:
                    # SQLite might barf with the IN operator over too many
                    # values
                    modified_units = set(Submission.objects.filter(
                            id__gt=modified_since,
                    ).values_list('unit', flat=True).distinct())
                    modified_units &= self_unit_ids

            common_dbids = set(self.dbid_index.get(uid) \
                               for uid in old_ids & new_ids)

            if modified_units:
                common_dbids &= modified_units

            common_dbids = list(common_dbids)
            for unit in self.findid_bulk(common_dbids):
                # FIXME: use a better mechanism for handling states and
                # different formats
                if monolingual and not unit.istranslated():
                    continue

                match = disk_store.findid(unit.getid())
                if match is not None:
                    changed = unit.sync(match)
                    if changed:
                        file_changed = True

        if file_changed:
            self.update_store_header(profile=profile)
            self.file.savestore()

        self.sync_time = timezone.now()
        self.save()

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
        logging.debug(u"Converting %s to %s", self.pootle_path, fileclass)
        output = fileclass()
        try:
            output.settargetlanguage(self.translation_project.language.code)
        except ObjectDoesNotExist:
            pass
        #FIXME: we should add some headers
        for unit in self.units.iterator():
            output.addunit(unit.convert(output.UnitClass))
        return output

    #################### TranslationStore #########################

    suggestions_in_format = True

    def max_index(self):
        """Largest unit index"""
        return max_column(self.unit_set.all(), 'index', -1)

    def addunit(self, unit, index=None):
        if index is None:
            index = self.max_index() + 1

        newunit = self.UnitClass(store=self, index=index)
        newunit.update(unit)

        if self.id:
            newunit.save()
        else:
            # We can't save the unit if the store is not in the
            # database already, so let's keep it in temporary list
            if not hasattr(self, '_units'):
                class FakeQuerySet(list):
                    def iterator(self):
                        return self.__iter__()

                self._units = FakeQuerySet()

            self._units.append(newunit)

        return newunit

    def findunits(self, source, obsolete=False):
        if not obsolete and hasattr(self, "sourceindex"):
            return super(Store, self).findunits(source)

        # find using hash instead of index
        source_hash = md5(source.encode("utf-8")).hexdigest()
        units = self.unit_set.filter(source_hash=source_hash)
        if obsolete:
            units = units.filter(state=OBSOLETE)
        else:
            units = units.filter(state__gt=OBSOLETE)
        if units.count():
            return units

    def findunit(self, source, obsolete=False):
        units = self.findunits(source, obsolete)
        if units:
            return units[0]

    def findid(self, id):
        if hasattr(self, "id_index"):
            return self.id_index.get(id, None)

        unitid_hash = md5(id.encode("utf-8")).hexdigest()
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
        if self.file and hasattr(self.file.store, 'header'):
            return self.file.store.header()

    ########################### Stats ############################

    @getfromcache
    def getquickstats(self):
        """calculate translation statistics"""
        try:
            return calculate_stats(self.units)
        except IntegrityError:
            logging.info(u"Duplicate IDs in %s", self.abs_real_path)
        except base.ParseError as e:
            logging.info(u"Failed to parse %s\n%s", self.abs_real_path, e)
        except (IOError, OSError) as e:
            logging.info(u"Can't access %s\n%s", self.abs_real_path, e)
        stats = {}
        stats.update(empty_quickstats)
        stats['errors'] += 1
        return stats

    @getfromcache
    def getcompletestats(self):
        """report result of quality checks"""
        try:
            self.require_qualitychecks()
            queryset = QualityCheck.objects.filter(unit__store=self,
                                                   unit__state__gt=UNTRANSLATED,
                                                   false_positive=False)
            return group_by_count_extra(queryset, 'name', 'category')
        except Exception as e:
            logging.info(u"Error getting quality checks for %s\n%s",
                         self.name, e)
            return {}

    @getfromcache
    def get_suggestion_count(self):
        """Check if any unit in the store has suggestions"""
        return Suggestion.objects.filter(unit__store=self,
                                         unit__state__gt=OBSOLETE).count()


    ############################ Translation #############################

    def getitem(self, item):
        """Returns a single unit based on the item number."""
        return self.units[item]

    @commit_on_success
    def mergefile(self, newfile, profile, allownewstrings, suggestions,
                  notranslate, obsoletemissing):
        """Merges :param:`newfile` with the current store.

        :param newfile: The file that will be merged into the current store.
        :param profile: A :cls:`~pootle_profile.models.PootleProfile` user
            profile.
        :param allownewstrings: Whether to add or not units from
            :param:`newfile` not present in the current store.
        :param suggestions: Try to add conflicting units as suggestions in case
            the new file's modified time is unknown or older that the in-DB
            unit).
        :param notranslate: Don't translate/merge in-DB units but rather add
            them as suggestions.
        :param obsoletemissing: Whether to remove or not units present in the
            current store but not in :param:`newfile`.
        """
        if not newfile.units:
            return

        monolingual = is_monolingual(type(newfile))
        self.clean_stale_lock()

        # Must be done before locking the file in case it wasn't already parsed
        self.require_units()

        if self.state == LOCKED:
            # File currently being updated
            # FIXME: shall we idle wait for lock to be released first? what
            # about stale locks?
            logging.info(u"Attemped to merge %s while locked", self.pootle_path)
            return

        logging.debug(u"Merging %s", self.pootle_path)

        # Lock store
        old_state = self.state
        self.state = LOCKED
        self.save()

        if suggestions:
            mtime = self._get_mtime_from_header(newfile)
        else:
            mtime = None

        try:
            self.require_dbid_index(update=True, obsolete=True)
            old_ids = set(self.dbid_index.keys())
            if issubclass(self.translation_project.project.get_file_class(),
                          newfile.__class__):
                new_ids = set(newfile.getids())
            else:
                new_ids = set(newfile.getids(self.name))

            if ((not monolingual or
                 self.translation_project.is_template_project) and
                allownewstrings):
                new_units = (newfile.findid(uid) for uid in new_ids - old_ids)
                for unit in new_units:
                    newunit = self.addunit(unit)
                    if old_state >= CHECKED:
                        newunit.update_qualitychecks(created=True)

            if obsoletemissing:
                obsolete_dbids = [self.dbid_index.get(uid)
                                  for uid in old_ids - new_ids]
                for unit in self.findid_bulk(obsolete_dbids):
                    if unit.istranslated():
                        unit.makeobsolete()
                        unit.save()
                    else:
                        unit.delete()

            common_dbids = [self.dbid_index.get(uid)
                            for uid in old_ids & new_ids]
            for oldunit in self.findid_bulk(common_dbids):
                newunit = newfile.findid(oldunit.getid())

                if (monolingual and
                    not self.translation_project.is_template_project):
                    fix_monolingual(oldunit, newunit, monolingual)

                if newunit.istranslated():
                    if (notranslate or suggestions and
                        oldunit.istranslated() and
                        (not mtime or mtime < oldunit.mtime)):
                        oldunit.add_suggestion(newunit.target, profile)
                    else:
                        changed = oldunit.merge(newunit, overwrite=True)
                        if changed:
                            do_checks = (oldunit._source_updated or
                                         oldunit._target_updated)
                            oldunit.save()

                            if do_checks and old_state >= CHECKED:
                                oldunit.update_qualitychecks()

            if allownewstrings or obsoletemissing:
                self.sync(update_structure=True, update_translation=True,
                          conservative=False, create=False, profile=profile)

        finally:
            # Unlock store
            self.state = old_state
            self.save()


    def update_store_header(self, profile=None):
        language = self.translation_project.language
        source_language = self.translation_project.project.source_language
        disk_store = self.file.store
        disk_store.settargetlanguage(language.code)
        disk_store.setsourcelanguage(source_language.code)

        from translate.storage import poheader
        if isinstance(disk_store, poheader.poheader):
            mtime = self.get_mtime()
            if mtime is None:
                mtime = timezone.now()
            if profile is None:
                try:
                    submission = self.translation_project.submission_set \
                                     .filter(creation_time=mtime).latest()
                    submitter = submission.submitter

                    if submitter is not None:
                        if submitter.user.username != 'nobody':
                            profile = submitter
                except ObjectDoesNotExist:
                    try:
                        submission = self.translation_project.submission_set \
                                                             .latest()
                        mtime = min(submission.creation_time, mtime)
                        submitter = submission.submitter

                        if submitter is not None:
                            if submitter.user.username != 'nobody':
                                profile = submitter
                    except ObjectDoesNotExist:
                        pass

            po_revision_date = mtime.strftime('%Y-%m-%d %H:%M') + \
                               poheader.tzstring()
            from pootle.__version__ import sver as pootle_version
            x_generator = "Pootle %s" % pootle_version
            headerupdates = {
                    'PO_Revision_Date': po_revision_date,
                    'X_Generator': x_generator,
                    'X_POOTLE_MTIME': ('%s.%06d' %
                                       (int(time.mktime(mtime.timetuple())),
                                        mtime.microsecond)),
                    }
            if profile is not None and profile.user.is_authenticated():
                headerupdates['Last_Translator'] = '%s <%s>' % \
                        (profile.user.first_name or profile.user.username,
                         profile.user.email)
            else:
                #FIXME: maybe insert settings.TITLE or domain here?
                headerupdates['Last_Translator'] = 'Anonymous Pootle User'
            disk_store.updateheader(add=True, **headerupdates)

            if language.nplurals and language.pluralequation:
                disk_store.updateheaderplural(language.nplurals,
                                              language.pluralequation)


    ########################## Pending Files #################################
    # The .pending files are deprecated since Pootle 2.1.0, but support for
    # them are kept here to be able to do migrations from older Pootle
    # versions.

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

        pending_name = os.extsep.join(self.file.name.split(os.extsep)[:-1] + \
                       ['po', 'pending'])
        pending_path = os.path.join(settings.PODIRECTORY, pending_name)

        # check if pending file already exists, just in case it was
        # added outside of pootle
        if os.path.exists(pending_path):
            self.pending = pending_name
            self.save()

    @commit_on_success
    def import_pending(self):
        """import suggestions from legacy .pending files, into database"""
        self.init_pending()
        if not self.pending:
            return

        for sugg in [sugg for sugg in self.pending.store.units
                     if sugg.istranslatable() and sugg.istranslated()]:
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


################################ Signal handlers ##############################

# NOTE: for some strange reason it was impossible to use m2m_changed signal.
def flush_goal_stats_for_tp_cache(sender, instance, **kwargs):
    """Flush goal stats for a TP if the goal is (un)applied to a store."""
    # Make sure that the signal was sent when (un)applying a goal to a store.
    if isinstance(instance.content_object, Store):
        goal = instance.tag
        store_path = instance.content_object.pootle_path
        goal.delete_cache_for_path(store_path)

post_save.connect(flush_goal_stats_for_tp_cache, sender=Store.goals.through)
pre_delete.connect(flush_goal_stats_for_tp_cache, sender=Store.goals.through)
