#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

import datetime
import logging
import os
import re
from hashlib import md5
from itertools import chain

from translate.filters.decorators import Category
from translate.storage import base

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import models, transaction, DatabaseError, IntegrityError
from django.template.defaultfilters import escape, truncatechars
from django.utils import dateformat, timezone, tzinfo
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pootle.core.log import (MUTE_QUALITYCHECK, STORE_ADDED, STORE_DELETED,
                             UNIT_ADDED, UNIT_DELETED, UNIT_OBSOLETE,
                             UNMUTE_QUALITYCHECK, action_log, store_log)
from pootle.core.managers import RelatedManager
from pootle.core.mixins import CachedMethods, TreeItem
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_misc.aggregate import max_column
from pootle_misc.checks import check_names
from pootle_misc.util import datetime_min
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)

from .caching import unit_delete_cache, unit_update_cache
from .fields import (MultiStringField, TranslationStoreField,
                     PLURAL_PLACEHOLDER, SEPARATOR)
from .filetypes import factory_classes, is_monolingual
from .signals import translation_submitted
from .util import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED


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

    def pending(self):
        return self.get_queryset().filter(state=SuggestionStates.PENDING)


class SuggestionStates(object):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


class Suggestion(models.Model, base.TranslationUnit):
    """Suggested translation for a :cls:`~pootle_store.models.Unit`, provided
    by users or automatically generated after a merge.
    """
    target_f = MultiStringField()
    target_hash = models.CharField(max_length=32, db_index=True)
    unit = models.ForeignKey('pootle_store.Unit')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='suggestions',
        db_index=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='reviews',
        db_index=True,
    )
    translator_comment_f = models.TextField(null=True, blank=True)
    state = models.CharField(
        max_length=16,
        default=SuggestionStates.PENDING,
        null=False,
        choices=(
            (SuggestionStates.PENDING, _('Pending')),
            (SuggestionStates.ACCEPTED, _('Accepted')),
            (SuggestionStates.REJECTED, _('Rejected')),
        ),
        db_index=True,
    )
    creation_time = models.DateTimeField(
        db_index=True,
        null=True,
    )
    review_time = models.DateTimeField(null=True, db_index=True)

    objects = SuggestionManager()

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

    def save(self, *args, **kwargs):
        if not self.id:
            self.unit.store.suggestion_count += 1
            self.unit.store.save()
            self.unit.store.translation_project.suggestion_count += 1
            self.unit.store.translation_project.save()
        super(Suggestion, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.state == SuggestionStates.PENDING:
            self.unit.decrease_suggestion_count()
        super(Suggestion, self).delete(*args, **kwargs)


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


def stringcount(string):
    try:
        return len(string.strings)
    except AttributeError:
        return 1


class UnitManager(RelatedManager):
    def get_for_path(self, pootle_path, user, permission_code="view"):
        """Returns units that fall below the `pootle_path` umbrella.

        :param pootle_path: An internal pootle path.
        :param user: The user who is accessing the units.
        :param permission_code: The permission code to check units for.
        """
        lang, proj, dir_path, filename = split_pootle_path(pootle_path)

        units_qs = super(UnitManager, self).get_queryset().filter(
            state__gt=OBSOLETE,
            store__translation_project__project__disabled=False,
            store__translation_project__directory__obsolete=False,
        )

        # /projects/<project_code>/translate/*
        if lang is None and proj is not None:
            if dir_path and filename:
                units_path = ''.join(['/%/', proj, '/', dir_path, filename])
            elif dir_path:
                units_path = ''.join(['/%/', proj, '/', dir_path, '%'])
            elif filename:
                units_path = ''.join(['/%/', proj, '/', filename])
            else:
                units_path = ''.join(['/%/', proj, '/%'])
        # /projects/translate/*
        elif lang is None and proj is None:
            units_path = '/%'
        # /<lang_code>/<project_code>/translate/*
        # /<lang_code>/translate/*
        else:
            units_path = ''.join([pootle_path, '%'])

        units_qs = units_qs.extra(
            where=[
                'pootle_store_store.pootle_path LIKE %s',
                'pootle_store_store.pootle_path NOT LIKE %s',
            ], params=[units_path, '/templates/%']
        )

        # Non-superusers are limited to the projects they have access to
        if not user.is_superuser:
            from pootle_project.models import Project
            user_projects = Project.accessible_by_user(user)
            units_qs = units_qs.filter(
                store__translation_project__project__code__in=user_projects,
            )

        return units_qs


class Unit(models.Model, base.TranslationUnit):
    store = models.ForeignKey("pootle_store.Store", db_index=True)
    index = models.IntegerField(db_index=True)
    unitid = models.TextField(editable=False)
    unitid_hash = models.CharField(
        max_length=32,
        db_index=True,
        editable=False,
    )
    source_f = MultiStringField(null=True)
    source_hash = models.CharField(
        max_length=32,
        db_index=True,
        editable=False,
    )
    source_wordcount = models.SmallIntegerField(default=0, editable=False)
    source_length = models.SmallIntegerField(
        db_index=True,
        default=0,
        editable=False,
    )
    target_f = MultiStringField(null=True, blank=True)
    target_wordcount = models.SmallIntegerField(default=0, editable=False)
    target_length = models.SmallIntegerField(
        db_index=True,
        default=0,
        editable=False,
    )
    developer_comment = models.TextField(null=True, blank=True)
    translator_comment = models.TextField(null=True, blank=True)
    locations = models.TextField(null=True, editable=False)
    context = models.TextField(null=True, editable=False)
    state = models.IntegerField(
        null=False,
        default=UNTRANSLATED,
        db_index=True,
    )
    revision = models.IntegerField(
        null=False,
        default=0,
        db_index=True,
        blank=True,
    )

    # Metadata
    creation_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        editable=False,
        null=True,
    )
    mtime = models.DateTimeField(
        auto_now=True,
        auto_now_add=True,
        db_index=True,
        editable=False,
    )

    # unit translator
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name='submitted',
    )
    submitted_on = models.DateTimeField(db_index=True, null=True)
    commented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name='commented',
    )
    commented_on = models.DateTimeField(db_index=True, null=True)

    # reviewer: who has accepted suggestion or removed FUZZY
    # None if translation has been submitted by approved translator
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name='reviewed',
    )
    reviewed_on = models.DateTimeField(db_index=True, null=True)

    objects = UnitManager()

    class Meta:
        ordering = ['store', 'index']
        unique_together = ('store', 'unitid_hash')
        get_latest_by = 'mtime'

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

    @property
    def has_critical_failures(self):
        return QualityCheck.objects.filter(
            unit=self,
            category=Category.CRITICAL,
            false_positive=False,
        ).exists()

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

    def delete(self, *args, **kwargs):
        action_log(user='system', action=UNIT_DELETED,
            lang=self.store.translation_project.language.code,
            unit=self.id,
            translation='')

        unit_delete_cache(self)

        super(Unit, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        created = self.id is None

        if not hasattr(self, '_log_user'):
            self._log_user = 'system'
        if created:
            self._save_action = UNIT_ADDED

        unit_update_cache(self)

        if self.id:
            if hasattr(self, '_save_action'):
                action_log(user=self._log_user, action=self._save_action,
                    lang=self.store.translation_project.language.code,
                    unit=self.id, translation=self.target_f
                )

        super(Unit, self).save(*args, **kwargs)

        if created:
            # This is caching that can't be done before saving the Unit to
            # allow these other objects to refer to it.
            self.store.last_unit = self
            self.store.translation_project.last_unit = self
            self.store.last_unit.save()
            self.store.translation_project.last_unit.save()

        if hasattr(self, '_save_action') and self._save_action == UNIT_ADDED:
            action_log(user=self._log_user, action=self._save_action,
                lang=self.store.translation_project.language.code,
                unit=self.id,
                translation=self.target_f
            )

        if self._source_updated or self._target_updated:
            # Update quality checks
            self.update_qualitychecks()

        # done processing source/target update remove flag
        self._source_updated = False
        self._target_updated = False

        # update cache only if we are updating a single unit
        if self.store.state >= PARSED:
            self.store.flag_for_deletion(CachedMethods.MTIME)
            self.store.update_cache()

    def get_absolute_url(self):
        lang, proj, dir, fn = split_pootle_path(self.store.pootle_path)
        return reverse('pootle-tp-overview', args=[lang, proj, dir, fn])

    def get_translate_url(self):
        lang, proj, dir, fn = split_pootle_path(self.store.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            '#unit=', unicode(self.id),
        ])

    def get_mtime(self):
        return self.mtime

    def is_accessible_by(self, user):
        """Returns `True` if the current unit is accessible by `user`."""
        if user.is_superuser:
            return True

        from pootle_project.models import Project
        user_projects = Project.accessible_by_user(user)
        return self.store.translation_project.project.code in user_projects

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
        unit_notes = unit.getnotes(origin="translator")
        if unit_notes != (self_notes or ''):
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

    def update(self, unit, user=None):
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
                    self.add_suggestion(suggestion.target, user=user, touch=False)

                changed = True

        return changed

    def update_qualitychecks(self, keep_false_positives=False):
        """Run quality checks and store result in the database."""
        existing = []

        # Calculate quality checks for the unit and update critical counts.
        had_failures = self.has_critical_failures

        checks = self.qualitycheck_set.all()
        if keep_false_positives:
            existing = set(checks.filter(false_positive=True) \
                                 .values_list('name', flat=True))
            checks = checks.filter(false_positive=False)

        if checks.count() > 0:
            self.store.flag_for_deletion(CachedMethods.CHECKS)
            # all checks should be recalculated
            checks.delete()

        # no checks if unit is untranslated
        if not self.target:
            return

        qc_failures = self.store.translation_project.checker \
                                .run_filters(self, categorised=True)

        for name in qc_failures.iterkeys():
            if name == 'fuzzy' or name in existing:
                # keep false-positive checks
                continue

            message = qc_failures[name]['message']
            category = qc_failures[name]['category']

            self.qualitycheck_set.create(name=name, message=message,
                                         category=category)

            self.store.flag_for_deletion(CachedMethods.CHECKS)

        # XXX we can probably figure that out from the code above
        has_failures_now = self.has_critical_failures

        if has_failures_now and not had_failures:
            self.store.failing_critical_count += 1
            self.store.save()
            self.store.translation_project.failing_critical_count += 1
            self.store.translation_project.save()
        elif not has_failures_now and had_failures:
            self.store.failing_critical_count -= 1
            self.store.save()
            self.store.translation_project.failing_critical_count -= 1
            self.store.translation_project.save()

    def get_qualitychecks(self):
        return self.qualitycheck_set.all()

    def get_active_qualitychecks(self):
        return self.qualitycheck_set.filter(false_positive=False)

    # FIXME: This is a hackish implementation needed due to the underlying
    # lame model definitions
    def get_reviewer(self):
        """Retrieve reviewer information for the current unit.

        :return: In case the current unit's status is an effect of accepting a
            suggestion, the reviewer user is returned.
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
                return getattr(last_submission.suggestion, 'reviewer',
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

        if value != (self.state == FUZZY):
            # when Unit toggles its FUZZY state the number of translated words
            # also changes
            self.store.flag_for_deletion(CachedMethods.FUZZY,
                                         CachedMethods.TRANSLATED,
                                         CachedMethods.LAST_ACTION)

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
            # when Unit becomes obsolete the cache should be updated
            unit_delete_cache(self)
            self._save_action = UNIT_OBSOLETE

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
        return self.suggestion_set.pending().select_related('user').all()

    def add_suggestion(self, translation, user=None, touch=True):
        if not filter(None, translation):
            return None

        if translation == self.target:
            return None

        if user is None:
            user = get_user_model().objects.get_system_user()

        suggestion = Suggestion(
            unit=self,
            user=user,
            state=SuggestionStates.PENDING,
            translation_project=self.store.translation_project,
        )
        suggestion.target = translation
        try:
            suggestion.save()

            sub = Submission(
                creation_time=timezone.now(),
                translation_project=self.store.translation_project,
                submitter=user,
                unit=self,
                type=SubmissionTypes.SUGG_ADD,
                suggestion=suggestion,
            )
            sub.save()

            self.store.flag_for_deletion(CachedMethods.SUGGESTIONS)
            if touch:
                self.save()
        except:
            # probably duplicate suggestion
            return None

        return suggestion

    def accept_suggestion(self, suggestion, translation_project, reviewer):
        old_state = self.state
        old_target = self.target
        self.target = suggestion.target

        if suggestion.user_id is not None:
            suggestion_user = suggestion.user
        else:
            User = get_user_model()
            suggestion_user = User.objects.get_nobody_user()

        current_time = timezone.now()
        self.submitted_by = suggestion_user
        self.submitted_on = current_time

        self._log_user = reviewer
        self.store.flag_for_deletion(CachedMethods.SUGGESTIONS,
                                     CachedMethods.LAST_ACTION)
        # Update timestamp
        self.save()

        suggestion.state = SuggestionStates.ACCEPTED
        suggestion.reviewer = reviewer
        suggestion.review_time = current_time
        suggestion.save()

        self.decrease_suggestion_count()

        create_subs = {}
        # assume the target changed
        create_subs[SubmissionFields.TARGET] = [old_target, self.target]
        # check if the state changed
        if old_state != self.state:
            create_subs[SubmissionFields.STATE] = [old_state, self.state]

        for field in create_subs:
            kwargs = {
                'creation_time': current_time,
                'translation_project': translation_project,
                'submitter': reviewer,
                'unit': self,
                'field': field,
                'type': SubmissionTypes.SUGG_ACCEPT,
                'old_value': create_subs[field][0],
                'new_value': create_subs[field][1],
            }
            if field == SubmissionFields.TARGET:
                kwargs['suggestion'] = suggestion

            sub = Submission(**kwargs)
            sub.save()

        if suggestion_user:
            translation_submitted.send(sender=translation_project,
                                       unit=self, user=suggestion_user)

    def reject_suggestion(self, suggestion, translation_project, reviewer):
        suggestion.state = SuggestionStates.REJECTED
        suggestion.review_time = timezone.now()
        suggestion.reviewer = reviewer
        suggestion.save()

        sub = Submission(
            creation_time=suggestion.review_time,
            translation_project=translation_project,
            submitter=reviewer,
            unit=self,
            type=SubmissionTypes.SUGG_REJECT,
            suggestion=suggestion,
        )
        sub.save()

        self.store.flag_for_deletion(CachedMethods.SUGGESTIONS,
                                     CachedMethods.LAST_ACTION)
        # Update timestamp
        self.save()

        self.decrease_suggestion_count()

    def decrease_suggestion_count(self):
        self.store.suggestion_count -= 1
        self.store.save()
        self.store.translation_project.suggestion_count -= 1
        self.store.translation_project.save()

    def toggle_qualitycheck(self, check_id, false_positive, user):
        check = self.qualitycheck_set.get(id=check_id)

        if check.false_positive == false_positive:
            return

        check.false_positive = false_positive
        check.save()

        has_other_critical_failures = QualityCheck.objects.filter(
            unit=self,
            category=Category.CRITICAL,
            false_positive=False,
        ).exclude(id=check_id).exists()

        self.store.flag_for_deletion(CachedMethods.CHECKS,
                                     CachedMethods.LAST_ACTION)
        self._log_user = user
        if false_positive:
            self._save_action = MUTE_QUALITYCHECK
            if not has_other_critical_failures:
                self.store.failing_critical_count -= 1
                self.store.translation_project.failing_critical_count -= 1
                self.store.save()
                self.store.translation_project.save()
        else:
            self._save_action = UNMUTE_QUALITYCHECK
            if not has_other_critical_failures:
                self.store.failing_critical_count += 1
                self.store.translation_project.failing_critical_count += 1
                self.store.save()
                self.store.translation_project.save()

        # create submission
        self.submitted_on = timezone.now()
        self.submitted_by = user
        self.save()
        if false_positive:
            sub_type = SubmissionTypes.MUTE_CHECK
        else:
            sub_type = SubmissionTypes.UNMUTE_CHECK

        sub = Submission(
            creation_time=self.submitted_on,
            translation_project=self.store.translation_project,
            submitter=user,
            field=SubmissionFields.NONE,
            unit=self,
            type=sub_type,
            quality_check=check
        )
        sub.save()

    def get_terminology(self):
        """get terminology suggestions"""
        matcher = self.store.translation_project.gettermmatcher()
        if matcher is not None:
            result = matcher.matches(self.source)
        else:
            result = []
        return result

    def get_last_updated_message(self):
        unit = {
            'source': escape(truncatechars(self, 50)),
            'url': self.get_translate_url(),
        }

        action_bundle = {
            'action': _(
                '<i><a href="%(url)s">%(source)s</a></i>&nbsp;'
                'added',
                unit
            ),
            "date": self.creation_time,
            "isoformat_date": self.creation_time.isoformat(),
        }
        return mark_safe(
            '<time class="extra-item-meta js-relative-date"'
            '    title="%(date)s" datetime="%(isoformat_date)s">&nbsp;'
            '</time>&nbsp;'
            u'<span class="action-text">%(action)s</span>'
            % action_bundle)


###################### Store ###########################

# custom storage otherwise django assumes all files are uploads headed to
# media dir
fs = FileSystemStorage(location=settings.PODIRECTORY)

# regexp to parse suggester name from msgidcomment
suggester_regexp = re.compile(r'suggested by (.*) \[[-0-9]+\]')


class Store(models.Model, TreeItem, base.TranslationStore):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""

    file = TranslationStoreField(
        upload_to="fish",
        max_length=255,
        storage=fs,
        db_index=True,
        null=False,
        editable=False,
    )
    parent = models.ForeignKey(
        'pootle_app.Directory',
        related_name='child_stores',
        db_index=True,
        editable=False,
    )
    translation_project = models.ForeignKey(
        'pootle_translationproject.TranslationProject',
        related_name='stores',
        db_index=True,
        editable=False,
    )
    pootle_path = models.CharField(
        max_length=255,
        null=False,
        unique=True,
        db_index=True,
        verbose_name=_("Path"),
    )
    name = models.CharField(max_length=128, null=False, editable=False)
    file_mtime = models.DateTimeField(default=datetime_min)
    state = models.IntegerField(
        null=False,
        default=NEW,
        editable=False,
        db_index=True,
    )
    creation_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        editable=False,
        null=True,
    )
    last_sync_revision = models.IntegerField(db_index=True, null=True)
    obsolete = models.BooleanField(default=False)

    UnitClass = Unit
    Name = "Model Store"
    is_dir = False

    objects = RelatedManager()

    class Meta:
        ordering = ['pootle_path']
        unique_together = ('parent', 'name')

    ############################ Properties ###################################

    @property
    def code(self):
        return self.name.replace('.', '-')

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
        return self.pootle_path.split(u'/', 2)[-1]

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

    def __init__(self, *args, **kwargs):
        super(Store, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.pootle_path)

    def __str__(self):
        storeclass = self.get_file_class()
        store = self.convert(storeclass)
        return str(store)

    def save(self, *args, **kwargs):
        created = not self.id
        self.pootle_path = self.parent.pootle_path + self.name
        super(Store, self).save(*args, **kwargs)
        if created:
            # new unit
            store_log(user='system', action=STORE_ADDED,
                      path=self.pootle_path, store=self.id)

        if hasattr(self, '_units'):
            index = self.max_index() + 1
            for i, unit in enumerate(self._units):
                unit.store = self
                unit.index = index + i
                unit.save()

        if self.state >= PARSED:
            self.update_cache()

    def delete(self, *args, **kwargs):
        store_log(user='system', action=STORE_DELETED,
                  path=self.pootle_path, store=self.id)
        for unit in self.unit_set.iterator():
            action_log(user='system', action=UNIT_DELETED,
                       lang=self.translation_project.language.code,
                       unit=unit.id, translation='')

        super(Store, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return reverse('pootle-tp-overview', args=[lang, proj, dir, fn])

    def get_translate_url(self, **kwargs):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            get_editor_filter(**kwargs),
        ])

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

    @transaction.atomic
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

    @transaction.atomic
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

        if not self.file:
            # This will always happen for pootle-terminology.po, don't warn
            if not self.pootle_path.endswith("pootle-terminology.po"):
                logging.warning(u"Attempted to update a non-existing file",
                                self.pootle_path)
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
                    # Use the same (parent) object since units will accumulate
                    # the list of cache attributes to clear in the parent Store
                    # object
                    unit.store = self
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

            if update_translation or modified_since:
                modified_units = set()

                if modified_since:
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
                system = get_user_model().objects.get_system_user()
                for unit in self.findid_bulk(common_dbids):
                    # Use the same (parent) object since units will accumulate
                    # the list of cache attributes to clear in the parent Store
                    # object
                    unit.store = self
                    newunit = store.findid(unit.getid())
                    old_target_f = unit.target_f
                    old_unit_state = unit.state

                    if (monolingual and not
                        self.translation_project.is_template_project):
                        fix_monolingual(unit, newunit, monolingual)

                    changed = unit.update(newunit, user=system)

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
                        create_subs = {}

                        if unit._target_updated:
                            create_subs[SubmissionFields.TARGET] = \
                                [old_target_f, unit.target_f]

                        # Set unit fields if submission should be created
                        if create_subs:
                            unit.submitted_by = system
                            unit.submitted_on = timezone.now()
                        unit.save()
                        # check unit state after saving
                        if old_unit_state != unit.state:
                            create_subs[SubmissionFields.STATE] = [old_unit_state,
                                                                   unit.state]

                        # Create Submission after unit saved
                        for field in create_subs:
                            sub = Submission(
                                creation_time=unit.submitted_on,
                                translation_project=self.translation_project,
                                submitter=system,
                                unit=unit,
                                field=field,
                                type=SubmissionTypes.SYSTEM,
                                old_value=create_subs[field][0],
                                new_value=create_subs[field][1]
                            )
                            sub.save()
        finally:
            # Unlock store
            self.state = old_state
            if (update_structure and
                (update_translation or modified_since)):
                self.sync_time = timezone.now()
            self.save()

    #TODO process cache for _get_checks
    def require_qualitychecks(self):
        """make sure quality checks are run"""
        if self.state < CHECKED:
            self.update_qualitychecks()

    @transaction.atomic
    def update_qualitychecks(self, keep_false_positives=False):
        logging.debug(u"Updating quality checks for %s", self.pootle_path)
        for unit in self.units.iterator():
            unit.update_qualitychecks(keep_false_positives)

        if self.state < CHECKED:
            self.state = CHECKED
            self.save()

    def sync(self, update_structure=False, update_translation=False,
             conservative=True, create=False, user=None, skip_missing=False,
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
                self.update_store_header(user)
                self.file.savestore()
                self.sync_time = self.get_mtime()

                self.save()
            return

        if conservative and self.translation_project.is_template_project:
            # don't save to templates
            return

        logging.info(u"Syncing %s", self.pootle_path)
        self.require_dbid_index(update=True)
        disk_store = self.file.store
        old_ids = set(disk_store.getids())
        new_ids = set(self.dbid_index.keys())

        file_changed = False

        if update_structure:
            obsolete_units = (disk_store.findid(uid)
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
            self.update_store_header(user)
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

    def addunit(self, unit, index=None, user=None):
        if index is None:
            index = self.max_index() + 1

        newunit = self.UnitClass(store=self, index=index)
        newunit.update(unit, user=user)

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

    ### TreeItem

    def get_parents(self):
        if self.parent.is_translationproject():
            return [self.translation_project]
        else:
            return [self.parent]

    def get_cachekey(self):
        return self.pootle_path

    def get_total_wordcount(self):
        return self.total_wordcount

    def get_translated_wordcount(self):
        return self.translated_wordcount

    def get_fuzzy_wordcount(self):
        return self.fuzzy_wordcount

    def get_suggestion_count(self):
        return self.suggestion_count

    def get_critical_error_unit_count(self):
        return self.failing_critical_count

    def _get_checks(self):
        try:
            self.require_qualitychecks()
            queryset = QualityCheck.objects.filter(unit__store=self,
                                                   unit__state__gt=UNTRANSLATED,
                                                   false_positive=False)

            queryset = queryset.values('unit', 'name').order_by('unit')

            saved_unit = None
            result = {
                'unit_count': 0,
                'checks': {},
            }
            for item in queryset:
                if item['unit'] != saved_unit or saved_unit is None:
                    saved_unit = item['unit']
                    # assumed all checks are critical and should be counted
                    result['unit_count'] += 1
                if item['name'] in result['checks']:
                    result['checks'][item['name']] += 1
                else:
                    result['checks'][item['name']] = 1

            return result
        except Exception as e:
            logging.info(u"Error getting quality checks for %s\n%s",
                         self.name, e)
            return {'unit_count': 0, 'checks': {}}

    def _get_mtime(self):
        return max_column(self.unit_set.all(), 'mtime', datetime_min)

    def get_last_updated(self):
        if self.last_unit is None:
            return {'id': 0, 'creation_time': 0, 'snippet': ''}

        creation_time = dateformat.format(self.last_unit.creation_time, 'U')
        return {
            'id': self.last_unit.id,
            'creation_time': int(creation_time),
            'snippet': self.last_unit.get_last_updated_message()
        }

    def get_last_action(self):
        if self.last_submission is None:
            return {'id': 0, 'mtime': 0, 'snippet': ''}

        mtime = dateformat.format(self.last_submission.creation_time, 'U')
        return {
            'id': self.last_submission.unit.id,
            'mtime': int(mtime),
            'snippet': self.last_submission.get_submission_message()
        }

    ### /TreeItem

    ############################ Translation #############################

    def getitem(self, item):
        """Returns a single unit based on the item number."""
        return self.units[item]

    @transaction.atomic
    def mergefile(self, newfile, user, allownewstrings, suggestions,
                  notranslate, obsoletemissing):
        """Merges :param:`newfile` with the current store.

        :param newfile: The file that will be merged into the current store.
        :param user: A :cls:`~accounts.models.User` User instance.
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
                    self.addunit(unit)

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
                        oldunit.add_suggestion(newunit.target, user)
                    else:
                        changed = oldunit.merge(newunit, overwrite=True)
                        if changed:
                            oldunit.save()

            if allownewstrings or obsoletemissing:
                self.sync(update_structure=True, update_translation=True,
                          conservative=False, create=False, user=user)

        finally:
            # Unlock store
            self.state = old_state
            self.save()

    def update_store_header(self, user=None):
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
            if user is None:
                try:
                    submission = self.translation_project.submission_set \
                                     .filter(creation_time=mtime).latest()
                    submitter = submission.submitter

                    if submitter is not None:
                        if submitter.username != 'nobody':
                            user = submitter
                except ObjectDoesNotExist:
                    try:
                        submission = self.translation_project.submission_set \
                                                             .latest()
                        mtime = min(submission.creation_time, mtime)
                        submitter = submission.submitter

                        if submitter is not None:
                            if submitter.username != 'nobody':
                                user = submitter
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
                                       (int(dateformat.format(mtime, 'U')),
                                        mtime.microsecond)),
                    }
            if user is not None and user.is_authenticated():
                headerupdates['Last_Translator'] = '%s <%s>' % \
                        (user.full_name or user.username, user.email)
            else:
                #FIXME: maybe insert settings.TITLE or domain here?
                headerupdates['Last_Translator'] = 'Anonymous Pootle User'
            disk_store.updateheader(add=True, **headerupdates)

            if language.nplurals and language.pluralequation:
                disk_store.updateheaderplural(language.nplurals,
                                              language.pluralequation)
