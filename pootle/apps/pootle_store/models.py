#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime
import difflib
import logging
import operator
import os

from hashlib import md5

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models, transaction, IntegrityError
from django.db.models import F
from django.template.defaultfilters import escape, truncatechars
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from translate.filters.decorators import Category
from translate.storage import base

from pootle.core.log import (TRANSLATION_ADDED, TRANSLATION_CHANGED,
                             TRANSLATION_DELETED, UNIT_ADDED, UNIT_DELETED,
                             UNIT_OBSOLETE, UNIT_RESURRECTED,
                             STORE_ADDED, STORE_OBSOLETE, STORE_DELETED,
                             MUTE_QUALITYCHECK, UNMUTE_QUALITYCHECK,
                             action_log, store_log, log)
from pootle.core.mixins import CachedMethods, CachedTreeItem
from pootle.core.models import Revision
from pootle.core.storage import PootleFileSystemStorage
from pootle.core.search import SearchBroker
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle.core.utils import dateformat
from pootle.core.utils.timezone import datetime_min, make_aware
from pootle_misc.aggregate import max_column
from pootle_misc.checks import check_names, run_given_filters, get_checker
from pootle_misc.util import import_func
from pootle_statistics.models import (SubmissionFields,
                                      SubmissionTypes, Submission)

from .fields import (TranslationStoreField, MultiStringField,
                     PLURAL_PLACEHOLDER, SEPARATOR)
from .filetypes import factory_classes
from .util import OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED, get_change_str


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

class QualityCheckManager(models.Manager):

    def get_queryset(self):
        """Mimics `select_related(depth=1)` behavior. Pending review."""
        return (
            super(QualityCheckManager, self).get_queryset().select_related(
                'unit',
            )
        )


class QualityCheck(models.Model):
    """Database cache of results of qualitychecks on unit."""
    name = models.CharField(max_length=64, db_index=True)
    unit = models.ForeignKey("pootle_store.Unit", db_index=True)
    category = models.IntegerField(null=False, default=Category.NO_CATEGORY)
    message = models.TextField()
    false_positive = models.BooleanField(default=False, db_index=True)

    objects = QualityCheckManager()

    def __unicode__(self):
        return self.name

    @property
    def display_name(self):
        return check_names.get(self.name, self.name)

    @classmethod
    def delete_unknown_checks(cls):
        unknown_checks = QualityCheck.objects \
            .exclude(name__in=check_names.keys())
        unknown_checks.delete()

################# Suggestion ################

class SuggestionManager(models.Manager):

    def get_queryset(self):
        """Mimics `select_related(depth=1)` behavior. Pending review."""
        return (
            super(SuggestionManager, self).get_queryset().select_related(
                'unit', 'user', 'reviewer',
            )
        )

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                             related_name='suggestions', db_index=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                 related_name='reviews', db_index=True)

    translator_comment_f = models.TextField(null=True, blank=True)

    state_choices = [
        (SuggestionStates.PENDING, _('Pending')),
        (SuggestionStates.ACCEPTED, _('Accepted')),
        (SuggestionStates.REJECTED, _('Rejected')),
    ]
    state = models.CharField(max_length=16, default=SuggestionStates.PENDING,
                             null=False, choices=state_choices, db_index=True)

    creation_time = models.DateTimeField(db_index=True, null=True)
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
    def translator_comment(self, value):
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


############### Unit ####################

wordcount_f = import_func(settings.POOTLE_WORDCOUNT_FUNC)

def count_words(strings):
    wordcount = 0

    for string in strings:
        wordcount += wordcount_f(string)

    return wordcount

def stringcount(string):
    try:
        return len(string.strings)
    except AttributeError:
        return 1


TMServer = SearchBroker()


class UnitManager(models.Manager):

    def get_queryset(self):
        """Mimics `select_related(depth=1)` behavior. Pending review."""
        return (
            super(UnitManager, self).get_queryset().select_related(
                'store', 'submitted_by', 'commented_by', 'reviewed_by',
            )
        )

    def get_for_path(self, pootle_path, user):
        """Returns units that fall below the `pootle_path` umbrella.

        :param pootle_path: An internal pootle path.
        :param user: The user who is accessing the units.
        """
        lang, proj, dir_path, filename = split_pootle_path(pootle_path)

        units_qs = super(UnitManager, self).get_queryset().filter(
            state__gt=OBSOLETE,
            store__translation_project__project__disabled=False,
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
    revision = models.IntegerField(null=False, default=0, db_index=True, blank=True)

    # Metadata
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    mtime = models.DateTimeField(auto_now=True, auto_now_add=True,
                                 db_index=True, editable=False)

    # unit translator
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
            db_index=True, related_name='submitted')
    submitted_on = models.DateTimeField(db_index=True, null=True)

    commented_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
            db_index=True, related_name='commented')
    commented_on = models.DateTimeField(db_index=True, null=True)

    # reviewer: who has accepted suggestion or removed FUZZY
    # None if translation has been submitted by approved translator
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
            db_index=True, related_name='reviewed')
    reviewed_on = models.DateTimeField(db_index=True, null=True)

    objects = UnitManager()
    simple_objects = models.Manager()

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

    ######################### Class & static methods ##########################

    @classmethod
    def max_revision(cls):
        """Returns the max revision number across all units."""
        return max_column(cls.objects.all(), 'revision', 0)

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
        self._state_updated = False
        self._comment_updated = False
        self._auto_translated = False
        self._encoding = 'UTF-8'

    # should be called to flag the store cache for a deletion
    # before the unit will be deleted
    def flag_store_before_going_away(self):
        self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS)

        if self.suggestion_set.pending().count() > 0:
            self.store.mark_dirty(CachedMethods.SUGGESTIONS)

        if self.get_qualitychecks().filter(false_positive=False):
            self.store.mark_dirty(CachedMethods.CHECKS)

        # Check if unit currently being deleted is the one referenced in
        # last_action
        la = self.store.get_cached_value(CachedMethods.LAST_ACTION)
        if not la or 'id' not in la or la['id'] == self.id:
            self.store.mark_dirty(CachedMethods.LAST_ACTION)
        # and last_updated
        lu = self.store.get_cached_value(CachedMethods.LAST_UPDATED)
        if not lu or 'id' not in lu or lu['id'] == self.id:
            self.store.mark_dirty(CachedMethods.LAST_UPDATED)

    def delete(self, *args, **kwargs):
        action_log(user='system', action=UNIT_DELETED,
            lang=self.store.translation_project.language.code,
            unit=self.id,
            translation='',
            path=self.store.pootle_path)

        self.flag_store_before_going_away()

        super(Unit, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not hasattr(self, '_log_user'):
            User = get_user_model()
            self._log_user = User.objects.get_system_user()

        if not self.id:
            self._save_action = UNIT_ADDED
            self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS,
                                  CachedMethods.LAST_UPDATED)

        if self._source_updated:
            # update source related fields
            self.source_hash = md5(self.source_f.encode("utf-8")).hexdigest()
            self.source_length = len(self.source_f)
            self.update_wordcount(auto_translate=True)

        if self._target_updated:
            # update target related fields
            self.target_wordcount = count_words(self.target_f.strings)
            self.target_length = len(self.target_f)
            self.store.mark_dirty(CachedMethods.LAST_ACTION)
            if filter(None, self.target_f.strings):
                if self.state == UNTRANSLATED:
                    self.state = TRANSLATED
                    self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS)

                    if not hasattr(self, '_save_action'):
                        self._save_action = TRANSLATION_ADDED
                else:
                    if not hasattr(self, '_save_action'):
                        self._save_action = TRANSLATION_CHANGED
            else:
                self._save_action = TRANSLATION_DELETED
                # if it was TRANSLATED then set to UNTRANSLATED
                if self.state > FUZZY:
                    self.state = UNTRANSLATED
                    self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS)

        # Updating unit from the .po file set its revision property to
        # a new value (the same for all units during its store updated)
        # since that change doesn't require further sync but note that
        # auto_translated units require further sync
        revision = kwargs.pop('revision', None)
        if revision is not None and not self._auto_translated:
            self.revision = revision
        elif self._target_updated or self._state_updated or self._comment_updated:
            self.revision = Revision.incr()

        if self.id and hasattr(self, '_save_action'):
            action_log(user=self._log_user, action=self._save_action,
                lang=self.store.translation_project.language.code,
                unit=self.id,
                translation=self.target_f,
                path=self.store.pootle_path
            )

        if (self._state_updated and self.state == TRANSLATED and
            self._save_action == TRANSLATION_CHANGED and
            not self._target_updated):
            # set reviewer data if FUZZY has been removed only and
            # translation hasn't been updated
            self.reviewed_on = timezone.now()
            self.reviewed_by = self._log_user
        elif self.state == FUZZY:
            # clear reviewer data if unit has been marked as FUZZY
            self.reviewed_on = None
            self.reviewed_by = None
        elif self.state == UNTRANSLATED:
            # clear reviewer and translator data if translation
            # has been deleted
            self.reviewed_on = None
            self.reviewed_by = None
            self.submitted_by = None
            self.submitted_on = None

        super(Unit, self).save(*args, **kwargs)

        if hasattr(self, '_save_action') and self._save_action == UNIT_ADDED:
            # just added FUZZY unit
            if self.state == FUZZY:
                self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS)

            action_log(user=self._log_user, action=self._save_action,
                lang=self.store.translation_project.language.code,
                unit=self.id,
                translation=self.target_f,
                path=self.store.pootle_path
            )

            self.add_initial_submission()

        if self._source_updated or self._target_updated:
            self.update_qualitychecks()
            if self.istranslated():
                self.update_tmserver()

        # done processing source/target update remove flag
        self._source_updated = False
        self._target_updated = False
        self._state_updated = False
        self._comment_updated = False
        self._auto_translated = False

        # update cache only if we are updating a single unit
        if self.store.state >= PARSED:
            self.store.mark_dirty(CachedMethods.MTIME)
            self.store.update_dirty_cache()

    def get_absolute_url(self):
        lang, proj, dir, fn = split_pootle_path(self.store.pootle_path)
        return reverse('pootle-tp-browse', args=[lang, proj, dir, fn])

    def get_translate_url(self):
        lang, proj, dir, fn = split_pootle_path(self.store.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            '#unit=', unicode(self.id),
        ])

    def get_search_locations_url(self, **kwargs):
        lang, proj, dir, fn = split_pootle_path(self.store.pootle_path)

        return u''.join([
            reverse('pootle-project-translate', args=[proj, dir, fn]),
            get_editor_filter(search=self.locations, sfields='locations'),
        ])

    def get_screenshot_url(self):
        prefix = self.store.translation_project.project.screenshot_search_prefix
        if prefix:
            return prefix + urlquote(self.source_f)

    def get_mtime(self):
        return self.mtime

    def is_accessible_by(self, user):
        """Returns `True` if the current unit is accessible by `user`."""
        if user.is_superuser:
            return True

        from pootle_project.models import Project
        user_projects = Project.accessible_by_user(user)
        return self.store.translation_project.project.code in user_projects

    def add_initial_submission(self):
        if self.istranslated() or self.isfuzzy():
            Submission.objects.create(
                creation_time=self.creation_time,
                translation_project=self.store.translation_project,
                submitter=self._log_user,
                unit=self,
                store=self.store,
                type=SubmissionTypes.UNIT_CREATE,
                field=SubmissionFields.TARGET,
                new_value=self.target,
            )

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
            if self_notes != '':
                unit.addnote(self_notes, origin="translator", position="replace")
            else:
                unit.removenotes()
            changed = True

        if unit.isfuzzy() != self.isfuzzy():
            unit.markfuzzy(self.isfuzzy())
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

        if user is None:
            User = get_user_model()
            user = User.objects.get_system_user()

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
            self._comment_updated = True

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
                self.resurrect(unit.isfuzzy())

            changed = True

        if self.unitid != unit.getid():
            self.unitid = unicode(unit.getid()) or unicode(unit.source)
            self.unitid_hash = md5(self.unitid.encode("utf-8")).hexdigest()
            changed = True

        return changed

    def update_wordcount(self, auto_translate=False):
        """Updates the source wordcount for a unit.

        :param auto_translate: when set to `True`, it will copy the
            source string into the target field.
        """
        self.source_wordcount = count_words(self.source_f.strings)

        if self.source_wordcount == 0:
            # We can't set the actual wordcount to zero since the unit
            # will essentially disappear from statistics thus for such
            # units set word count to 1
            self.source_wordcount = 1

            if (auto_translate
                and not bool(filter(None, self.target_f.strings))):
                # auto-translate untranslated strings
                self.target = self.source
                self.state = FUZZY
                self._auto_translated = True

    def update_qualitychecks(self, keep_false_positives=False,
                             check_names=None, existing=None):
        """Run quality checks and store result in the database.

        :param keep_false_positives: when set to `False`, it will activate
            (unmute) any existing false positive checks.
        :param check_names: list of quality check names to update, use
            `None` to update all quality checks.
        :param existing: if existing checks were calculated before, they
            can be passed `None` to calculate existing checks during
            updating.
        :return: `True` if quality checks were updated or `False` if they
            left unchanged.
        """
        unmute_list = []
        result = False

        if existing is None:
            checks = self.qualitycheck_set.all()
            if check_names:
                checks = checks.filter(name__in=check_names)

            existing = {}
            for check in checks.values('name', 'false_positive', 'id'):
                existing[check['name']] = {
                    'false_positive': check['false_positive'],
                    'id': check['id'],
                }

        # no checks if unit is untranslated
        if not self.target:
            if existing:
                self.store.mark_dirty(CachedMethods.CHECKS)
                self.qualitycheck_set.all().delete()
                return True

            return False

        checker = get_checker(self)
        if check_names is None:
            qc_failures = checker.run_filters(self, categorised=True)
        else:
            qc_failures = run_given_filters(checker, self, check_names)

        for name in qc_failures.iterkeys():
            if name in existing:
                # keep false-positive checks if check is active
                if existing[name]['false_positive'] and not keep_false_positives:
                    unmute_list.append(name)
                del existing[name]
                continue

            message = qc_failures[name]['message']
            category = qc_failures[name]['category']

            self.qualitycheck_set.create(name=name, message=message,
                                         category=category)

            self.store.mark_dirty(CachedMethods.CHECKS)
            result = True

        if not keep_false_positives and unmute_list:
            self.qualitycheck_set.filter(name__in=unmute_list) \
                                 .update(false_positive=False)

        # delete inactive checks
        if existing:
            self.store.mark_dirty(CachedMethods.CHECKS)
            self.qualitycheck_set.filter(name__in=existing).delete()

        return result or bool(unmute_list) or bool(existing)

    def get_qualitychecks(self):
        return self.qualitycheck_set.all()

    def get_active_qualitychecks(self):
        return self.qualitycheck_set.filter(false_positive=False)

##################### TranslationUnit ############################

    def update_tmserver(self):
        obj = {
            'id': self.id,
            # 'revision' must be an integer for statistical queries to work
            'revision': self.revision,
            'project': self.store.translation_project.project.fullname,
            'path': self.store.pootle_path,
            'source': self.source,
            'target': self.target,
            'username': '',
            'fullname': '',
            'email_md5': '',
        }

        if self.submitted_by:
            obj.update({
                'username': self.submitted_by.username,
                'fullname': self.submitted_by.full_name,
                'email_md5': md5(self.submitted_by.email).hexdigest(),
            })

        TMServer.update(self.store.translation_project.language.code, obj)

    def get_tm_suggestions(self):
        return TMServer.search(self)

##################### TranslationUnit ############################

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
            self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS,
                                  CachedMethods.LAST_ACTION)
            self._state_updated = True
            # that's additional check
            # but leave old value in case _save_action is set
            if not hasattr(self, '_save_action'):
                self._save_action = TRANSLATION_CHANGED

        if value:
            self.state = FUZZY
        elif self.state <= FUZZY:
            if filter(None, self.target_f.strings):
                self.state = TRANSLATED
            else:
                self.state = UNTRANSLATED
                # that's additional check
                # but leave old value in case _save_action is set
                if not hasattr(self, '_save_action'):
                    self._save_action = TRANSLATION_DELETED

    def hasplural(self):
        return (self.source is not None and
                (len(self.source.strings) > 1
                or hasattr(self.source, "plural") and
                self.source.plural))

    def isobsolete(self):
        return self.state == OBSOLETE

    def makeobsolete(self):
        if self.state > OBSOLETE:
            # when Unit becomes obsolete the cache flags should be updated
            self.flag_store_before_going_away()
            self._state_updated = True
            self._save_action = UNIT_OBSOLETE

            self.state = OBSOLETE
            self.index = 0

    def resurrect(self, is_fuzzy=False):
        if self.state > OBSOLETE:
            return

        if filter(None, self.target_f.strings):
            # when Unit toggles its OBSOLETE state the number of translated words
            # or fuzzy words also changes
            if is_fuzzy:
                self.state = FUZZY
            else:
                self.state = TRANSLATED
        else:
            self.state = UNTRANSLATED

        self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS)
        self._state_updated = True
        self._save_action = UNIT_RESURRECTED

    def istranslated(self):
        if self._target_updated and not self.isfuzzy():
            return bool(filter(None, self.target_f.strings))
        return self.state >= TRANSLATED

    @classmethod
    def buildfromunit(cls, unit):
        newunit = cls()
        newunit.update(unit)
        return newunit

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

##################### Suggestions #################################
    def get_suggestions(self):
        return self.suggestion_set.pending().select_related('user').all()

    def add_suggestion(self, translation, user=None, touch=True,
                       similarity=None, mt_similarity=None):
        """Adds a new suggestion to the unit.

        :param translation: suggested translation text
        :param user: user who is making the suggestion. If it's ``None``,
            the ``system`` user will be used.
        :param touch: whether to update the unit's timestamp after adding
            the suggestion or not.
        :param similarity: human similarity for the new suggestion.
        :param mt_similarity: MT similarity for the new suggestion.

        :return: a tuple ``(suggestion, created)`` where ``created`` is a
            boolean indicating if the suggestion was successfully added.
            If the suggestion already exists it's returned as well.
        """
        if not filter(None, translation):
            return (None, False)

        if translation == self.target:
            return (None, False)

        if user is None:
            User = get_user_model()
            user = User.objects.get_system_user()

        try:
            suggestion = Suggestion.objects.pending().get(
                unit=self,
                user=user,
                target_f=translation,
            )
            return (suggestion, False)
        except Suggestion.DoesNotExist:
            suggestion = Suggestion(
                unit=self,
                user=user,
                state=SuggestionStates.PENDING,
                creation_time=timezone.now(),
            )
            suggestion.target = translation
            suggestion.save()

            sub = Submission(
                creation_time=suggestion.creation_time,
                translation_project=self.store.translation_project,
                submitter=user,
                unit=self,
                store=self.store,
                type=SubmissionTypes.SUGG_ADD,
                suggestion=suggestion,
                similarity=similarity,
                mt_similarity=mt_similarity,
            )
            sub.save()

            self.store.mark_dirty(CachedMethods.SUGGESTIONS,
                                  CachedMethods.LAST_ACTION)
            if touch:
                self.save()

        return (suggestion, True)

    def accept_suggestion(self, suggestion, translation_project, reviewer):
        # Save for later
        old_state = self.state
        old_target = self.target

        # Update some basic attributes so we can create submissions. Note
        # these do not conflict with `ScoreLog`'s interests, so it's safe
        self.target = suggestion.target
        if self.state == FUZZY:
            self.state = TRANSLATED

        if suggestion.user_id is not None:
            suggestion_user = suggestion.user
        else:
            User = get_user_model()
            suggestion_user = User.objects.get_nobody_user()

        current_time = timezone.now()
        suggestion.state = SuggestionStates.ACCEPTED
        suggestion.reviewer = reviewer
        suggestion.review_time = current_time
        suggestion.save()

        create_subs = {}
        create_subs[SubmissionFields.TARGET] = [old_target, self.target]
        if old_state != self.state:
            create_subs[SubmissionFields.STATE] = [old_state, self.state]
            self.store.mark_dirty(CachedMethods.WORDCOUNT_STATS)

        for field in create_subs:
            kwargs = {
                'creation_time': current_time,
                'translation_project': translation_project,
                'submitter': reviewer,
                'unit': self,
                'store': self.store,
                'field': field,
                'type': SubmissionTypes.SUGG_ACCEPT,
                'old_value': create_subs[field][0],
                'new_value': create_subs[field][1],
            }
            if field == SubmissionFields.TARGET:
                kwargs['suggestion'] = suggestion

            sub = Submission(**kwargs)
            sub.save()

        # FIXME: remove such a dependency on `ScoreLog`
        # Update current unit instance's attributes
        # important to set these attributes after saving Submission
        # because in the `ScoreLog` we need to access the unit's certain
        # attributes before it was saved
        self.submitted_by = suggestion_user
        self.submitted_on = current_time
        self.reviewed_by = reviewer
        self.reviewed_on = self.submitted_on
        self._log_user = reviewer

        self.store.mark_dirty(CachedMethods.SUGGESTIONS,
                              CachedMethods.LAST_ACTION)
        # Update timestamp
        self.save()

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
            store=self.store,
            type=SubmissionTypes.SUGG_REJECT,
            suggestion=suggestion,
        )
        sub.save()

        self.store.mark_dirty(CachedMethods.SUGGESTIONS,
                              CachedMethods.LAST_ACTION)
        # Update timestamp
        self.save()


    def toggle_qualitycheck(self, check_id, false_positive, user):
        check = self.qualitycheck_set.get(id=check_id)

        if check.false_positive == false_positive:
            return

        check.false_positive = false_positive
        check.save()

        self.store.mark_dirty(CachedMethods.CHECKS,
                              CachedMethods.LAST_ACTION)
        self._log_user = user
        if false_positive:
            self._save_action = MUTE_QUALITYCHECK
        else:
            self._save_action = UNMUTE_QUALITYCHECK

        # create submission
        if false_positive:
            sub_type = SubmissionTypes.MUTE_CHECK
        else:
            sub_type = SubmissionTypes.UNMUTE_CHECK

        sub = Submission(creation_time=timezone.now(),
            translation_project=self.store.translation_project,
            submitter=user,
            field=SubmissionFields.NONE,
            unit=self,
            store=self.store,
            type=sub_type,
            quality_check=check
        )
        sub.save()

        # update timestamp
        # log user action
        self.save()

    def get_terminology(self):
        """get terminology suggestions"""
        matcher = self.store.translation_project.gettermmatcher()
        if matcher is not None:
            result = matcher.matches(self.source)
        else:
            result = []
        return result

    def get_last_updated_info(self):
        unit = {
            'source': truncatechars(self, 50),
            'url': self.get_translate_url(),
            'id': self.id,
        }

        return {
            "display_datetime": dateformat.format(self.creation_time),
            "iso_datetime": self.creation_time.isoformat(),
            "creation_time": int(dateformat.format(self.creation_time, 'U')),
            "unit": unit,
        }


###################### Store ###########################


# Needed to alter storage location in tests
fs = PootleFileSystemStorage()


class StoreManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        """Mimics `select_related(depth=1)` behavior. Pending review."""
        return super(StoreManager, self).get_queryset() \
                                        .select_related(
                                            'parent',
                                            'translation_project',
                                        )

    def live(self):
        """Filters non-obsolete stores."""
        return self.filter(obsolete=False)


class Store(models.Model, CachedTreeItem, base.TranslationStore):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""
    UnitClass = Unit
    Name = "Model Store"
    is_dir = False

    file = TranslationStoreField(max_length=255, storage=fs,
            db_index=True, null=False, editable=False)

    parent = models.ForeignKey('pootle_app.Directory',
            related_name='child_stores', db_index=True, editable=False)

    translation_project_fk = 'pootle_translationproject.TranslationProject'
    translation_project = models.ForeignKey(translation_project_fk,
            related_name='stores', db_index=True, editable=False)

    pootle_path = models.CharField(max_length=255, null=False, unique=True,
            db_index=True, verbose_name=_("Path"))
    name = models.CharField(max_length=128, null=False, editable=False)

    file_mtime = models.DateTimeField(default=datetime_min)
    state = models.IntegerField(null=False, default=NEW, editable=False,
            db_index=True)
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    last_sync_revision = models.IntegerField(db_index=True, null=True)
    obsolete = models.BooleanField(default=False)

    objects = StoreManager()

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
        """is this a project specific terminology store?"""
        #TODO: Consider if this should check if the store belongs to a
        # terminology project. Probably not, in case this might be called over
        # several files in a project.
        return self.name.startswith('pootle-terminology')

    @property
    def parent_vfolder_treeitems(self):
        if 'virtualfolder' in settings.INSTALLED_APPS:
            return self.parent_vf_treeitems.all()

        return []

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

    ############################ Methods ######################################

    @cached_property
    def path(self):
        """Returns just the path part omitting language and project codes.

        If the `pootle_path` of a :cls:`Store` object `store` is
        `/af/project/dir1/dir2/file.po`, `store.path` will return
        `dir1/dir2/file.po`.
        """
        return self.pootle_path.split(u'/', 2)[-1]

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
            store_log(user='system', action=STORE_ADDED,
                      path=self.pootle_path, store=self.id)

        if hasattr(self, '_units'):
            index = self.max_index() + 1
            revision = None
            if created:
                revision = Revision.incr()
            for i, unit in enumerate(self._units):
                unit.store = self
                unit.index = index + i
                unit.save(revision=revision)

        if self.state >= PARSED:
            self.update_dirty_cache()

    def delete(self, *args, **kwargs):
        parents = self.get_parents()

        store_log(user='system', action=STORE_DELETED,
                  path=self.pootle_path, store=self.id)

        lang = self.translation_project.language.code
        for unit in self.unit_set.iterator():
            action_log(user='system', action=UNIT_DELETED, lang=lang,
                       unit=unit.id, translation='', path=self.pootle_path)

        super(Store, self).delete(*args, **kwargs)

        self.clear_all_cache(parents=False, children=False)
        for p in parents:
            p.update_all_cache()

    def makeobsolete(self):
        """Make this store and all its units obsolete."""
        store_log(user='system', action=STORE_OBSOLETE,
                  path=self.pootle_path, store=self.id)

        lang = self.translation_project.language.code
        unit_query = self.unit_set.filter(state__gt=OBSOLETE)
        unit_ids = unit_query.values_list('id', flat=True)
        for unit_id in unit_ids:
            action_log(user='system', action=UNIT_OBSOLETE, lang=lang,
                       unit=unit_id, translation='', path=self.pootle_path)
        unit_query.update(state=OBSOLETE, index=0)
        self.obsolete = True
        self.save()
        self.clear_all_cache(parents=False, children=False)

    def get_absolute_url(self):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return reverse('pootle-tp-browse', args=[lang, proj, dir, fn])

    def get_translate_url(self, **kwargs):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            get_editor_filter(**kwargs),
        ])

    def require_units(self):
        """Make sure file is parsed and units are created."""
        if self.state < PARSED and self.unit_set.count() == 0:
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
                revision = Revision.incr()
                for index, unit in enumerate(store.units):
                    if unit.istranslatable():
                        try:
                            self.addunit(unit, index, revision=revision)
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
            self.last_sync_revision = revision
            self.mark_all_dirty()
            self.save()
            return

    def get_file_mtime(self):
        disk_mtime = datetime.datetime \
                     .fromtimestamp(self.file.getpomtime()[0])
        # set microsecond to 0 for comparing with a time value without microseconds
        disk_mtime = make_aware(disk_mtime.replace(microsecond=0))

        return disk_mtime

    def update_index(self, start, delta):
        op = operator.add if delta > 0 else operator.sub
        Unit.objects.filter(store_id=self.id, index__gte=start).update(
            index=op(F('index'), delta)
        )

    def mark_units_obsolete(self, uids_to_obsolete, revision=None):
        """Marks a bulk of units as obsolete.

        :param uids_to_obsolete: UIDs of the units to be marked as obsolete.
        :return: The number of units marked as obsolete.
        """
        obsoleted = 0
        for unit in self.findid_bulk(uids_to_obsolete):
            # Use the same (parent) object since units will
            # accumulate the list of cache attributes to clear
            # in the parent Store object
            unit.store = self
            if not unit.isobsolete():
                unit.makeobsolete()
                unit.save(revision=revision)
                obsoleted += 1

        return obsoleted

    def remove_modified_units(self, unit_ids):
        """Returns a list of UIDs excluding those which have been modified since
        the last sync.

        :param unit_ids: set of UIDs for this store.
        :return: set of UIDs.
        """
        # Get units that were modified after last sync
        filter_by = {'store': self}
        if self.last_sync_revision is not None:
            filter_by.update({'revision__gt': self.last_sync_revision})

        # If a dbunit is obsolete then the dbunit should be resurrected in any
        # case
        modified_units = set(
            Unit.objects.filter(**filter_by).exclude(state=OBSOLETE)
                        .values_list('id', flat=True).distinct()
        )

        # If some units have been modified since last sync keep them safe
        unit_ids -= modified_units

        return unit_ids

    def update_units(self, store, uids_to_update, uid_index_map, user,
                     revision=None):
        """Updates existing units in the store.

        :param uids_to_update: UIDs of the units to be updated.
        :param uid_index_map: dictionary of DB ID to index mappings.
        :param user: attribute specific changes to this user.
        :param revision: set updated unit revision to this value.
        :return: The number of units that were actually updated.
        """
        updated = 0

        uids_to_update = list(uids_to_update)
        for unit in self.findid_bulk(uids_to_update):
            # Use the same (parent) object since units will accumulate
            # the list of cache attributes to clear in the parent Store
            # object
            unit.store = self
            uid = unit.getid()
            newunit = store.findid(uid)

            # FIXME: `old_unit = copy.copy(unit)?`
            old_target = unit.target_f
            old_state = unit.state

            changed = unit.update(newunit, user=user)

            if uid in uid_index_map:
                unit.index = uid_index_map[uid]['index']
                changed = True

            if changed:
                updated += 1
                current_time = timezone.now()

                self.record_submissions(unit, old_target, old_state,
                                        current_time, user)

                # FIXME: extreme implicit hazard
                if unit._comment_updated:
                    unit.commented_by = user
                    unit.commented_on = current_time

                # Set unit fields if target was updated
                # FIXME: extreme implicit hazard
                if unit._target_updated:
                    unit.submitted_by = user
                    unit.submitted_on = current_time
                    unit.reviewed_on = None
                    unit.reviewed_by = None

                unit.save(revision=revision)

        return updated

    def record_submissions(self, unit, old_target, old_state, current_time, user):
        """Records all applicable submissions for `unit`.

        EXTREME HAZARD: this relies on implicit `._<field>_updated` members
        being available in `unit`. Let's look into replacing such members with
        something saner (#3895).
        """
        create_subs = {}

        # FIXME: extreme implicit hazard
        if unit._target_updated:
            create_subs[SubmissionFields.TARGET] = [
                old_target,
                unit.target_f,
            ]

        # FIXME: extreme implicit hazard
        if unit._state_updated:
            create_subs[SubmissionFields.STATE] = [
                old_state,
                unit.state,
            ]

        # FIXME: extreme implicit hazard
        if unit._comment_updated:
            create_subs[SubmissionFields.COMMENT] = [
                '',
                unit.translator_comment or '',
            ]

        # Create Submission after unit saved
        for field in create_subs:
            sub = Submission(
                creation_time=current_time,
                translation_project=self.translation_project,
                submitter=user,
                unit=unit,
                store=unit.store,
                field=field,
                type=SubmissionTypes.SYSTEM,
                old_value=create_subs[field][0],
                new_value=create_subs[field][1]
            )
            # FIXME: we can store these objects in a list and
            # `bulk_create()` them in a single go
            sub.save()

    def update(self, overwrite=False, store=None, only_newer=False):
        """Update DB with units from file.

        :param overwrite: Whether to update all existing translations or
            keep safe units that updated after the last sync.
        :param store: an optional source `Store` instance from TTK. If unset,
            the current DB store's FS store will be used as a source.
        :param only_newer: Whether to update only the files that changed on
            disk after the last sync.
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

        disk_mtime = self.get_file_mtime()
        if only_newer and disk_mtime == self.file_mtime:
            # The file on disk wasn't changed since the last sync
            logging.debug(u"File didn't change since last sync, skipping "
                          u"%s" % self.pootle_path)
            return

        if store is None:
            store = self.file.store

        # Lock store
        logging.debug(u"Updating %s", self.pootle_path)
        old_state = self.state
        self.state = LOCKED
        self.save()

        update_revision = Revision.incr()
        try:
            changes = {
                'obsolete': 0,
                'updated': 0,
                'added': 0,
            }

            old_unitid_list = []  # unitid list for comparing (DB)
            old_unitids = {}  # unitids dict (DB)
            old_unitid_set = set()
            old_obsolete_unitid_set = set()  # obsolete unitids in DB
            update_unitids = {}

            unit_values = self.unit_set.order_by('index').values_list(
                'unitid', 'state', 'id', 'index',
            )
            for (unitid, state, dbid, index) in unit_values:
                if state == OBSOLETE:
                    old_obsolete_unitid_set.add(unitid)
                else:
                    old_unitid_list.append(unitid)
                old_unitids[unitid] = {'dbid': dbid, 'index': index}
                old_unitid_set.add(unitid)

            new_unitid_list = sorted(store.getids(),
                                     key=lambda x: store.findid(x).index)
            new_unitid_set = set(new_unitid_list)

            User = get_user_model()
            system = User.objects.get_system_user()

            common_dbids = set()

            def insert(i1, j1, j2, offset):
                # Add new units to the store
                new_units = (store.findid(uid) for uid in new_unitid_list[j1:j2])
                for index, unit in enumerate(new_units):
                    new_unit_index = i1 + index + 1 + offset
                    uid = unit.getid()
                    if uid not in old_unitid_set:
                        self.addunit(unit, new_unit_index, user=system,
                                     revision=update_revision)
                        changes['added'] += 1
                    else:
                        update_unitids[uid] = {'dbid': old_unitids[uid]['dbid'],
                                               'index': new_unit_index}

            sm = difflib.SequenceMatcher(None, old_unitid_list, new_unitid_list)
            offset = 0
            for (tag, i1, i2, j1, j2) in sm.get_opcodes():
                current_offset = offset
                if tag == 'delete':
                    continue
                elif tag == 'insert':
                    previous_index = 0
                    if i1 > 0:
                        previous = old_unitids[old_unitid_list[i1 - 1]]
                        previous_index = previous['index']
                    if i1 < len(old_unitid_list):
                        next = old_unitids[old_unitid_list[i1]]
                        delta = j2 - j1
                        if previous_index + delta >= next['index']:
                            delta = next['index'] - previous_index + delta - 1
                            self.update_index(start=next['index'] + current_offset, delta=delta)
                            offset += delta
                    insert(previous_index, j1, j2, current_offset)
                elif tag == 'replace':
                    i1_index = old_unitids[old_unitid_list[i1 - 1]]['index']
                    i2_index = old_unitids[old_unitid_list[i2 - 1]]['index']
                    delta = j2 - j1 - i2_index + i1_index
                    if delta > 0:
                        self.update_index(start=i2_index + current_offset, delta=delta)
                        offset += delta
                    insert(i1_index, j1, j2, current_offset)
                else:
                    common_dbids.update(set(old_unitids[uid]['dbid']
                                            for uid in old_unitid_list[i1:i2]))

            # Step N-1: mark obsolete units as such

            obsolete_dbids = [old_unitids[uid]['dbid']
                              for uid in old_unitid_set -
                                         old_obsolete_unitid_set -
                                         new_unitid_set]
            changes['obsolete'] = \
                self.mark_units_obsolete(obsolete_dbids,
                                         revision=update_revision)


            # Step N: update existing units

            update_dbids = set([x['dbid'] for x in update_unitids.values()])
            common_dbids.update(update_dbids)

            # Optimization: only go through unchanged units since the last sync
            if not overwrite:
                common_dbids = self.remove_modified_units(common_dbids)

            changes['updated'] = self.update_units(store, common_dbids,
                                                   update_unitids, system,
                                                   revision=update_revision)

            self.file_mtime = disk_mtime

            if (filter(lambda x: changes[x] > 0, changes) and
                store == self.file.store):
                if self.last_sync_revision is not None:
                    changes['unsynced'] = \
                        self.increment_unsynced_unit_revision(update_revision)

                self.last_sync_revision = update_revision

        finally:
            # Unlock store
            self.state = old_state
            self.save()
            if filter(lambda x: changes[x] > 0, changes):
                log(u"[update] %s units in %s [revision: %d]" % (
                    get_change_str(changes), self.pootle_path,
                    self.get_max_unit_revision())
                )

    def increment_unsynced_unit_revision(self, update_revision):
        filter_by = {
            'store': self,
            'revision__gt': self.last_sync_revision,
            'revision__lt': update_revision,
            'state__gt': OBSOLETE,
        }
        count = 0
        for unit in Unit.simple_objects.filter(**filter_by):
            unit.save(revision=Revision.incr())
            count += 1

        return count

    def serialize(self):
        from django.core.cache import caches

        if self.is_terminology:
            raise NotImplementedError("Cannot serialize terminology stores")

        cache = caches["exports"]
        rev = self.get_max_unit_revision()
        path = self.pootle_path

        ret = cache.get(path, version=rev)
        if not ret:
            storeclass = self.get_file_class()
            store = self.convert(storeclass)
            if hasattr(store, "updateheader"):
                # FIXME We need those headers on import
                # However some formats just don't support setting metadata
                store.updateheader(add=True, X_Pootle_Path=path)
                store.updateheader(add=True, X_Pootle_Revision=rev)

            ret = str(store)
            cache.set(path, ret, version=rev)

        return ret

    def sync(self, update_structure=False, conservative=True,
             user=None, skip_missing=False, only_newer=True):
        """Sync file with translations from DB."""
        if skip_missing and not self.file.exists():
            return

        last_revision = self.get_max_unit_revision()

        #TODO only_newer -> not force
        if (only_newer and self.file.exists() and
            self.last_sync_revision >= last_revision):
            logging.info(u"[sync] No updates for %s after [revision: %d]" %
                (self.pootle_path, self.last_sync_revision))
            return

        if not self.file.exists() and not skip_missing:
            # File doesn't exist let's create it
            logging.debug(u"Creating file %s", self.pootle_path)

            # FIXME: put this is a `create_file()` method
            storeclass = self.get_file_class()
            store_path = os.path.join(
                self.translation_project.abs_real_path, self.name
            )
            store = self.convert(storeclass)
            store.savefile(store_path)
            log(u"Created file for %s [revision: %d]" %
                (self.pootle_path, last_revision))

            self.file = store_path
            self.update_store_header(user=user)
            self.file.savestore()
            self.file_mtime = self.get_file_mtime()
            self.last_sync_revision = last_revision

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
        changes = {
            'obsolete': 0,
            'deleted': 0,
            'updated': 0,
            'added': 0,
        }

        if update_structure:
            obsolete_units = (disk_store.findid(uid)
                              for uid in old_ids - new_ids)
            for unit in obsolete_units:
                if not unit.istranslated():
                    del unit
                elif not conservative:
                    changes['obsolete'] += 1
                    unit.makeobsolete()

                    if not unit.isobsolete():
                        changes['deleted'] += 1
                        del unit

                file_changed = True

            new_dbids = [self.dbid_index.get(uid) for uid in new_ids - old_ids]
            for unit in self.findid_bulk(new_dbids):
                newunit = unit.convert(disk_store.UnitClass)
                disk_store.addunit(newunit)
                changes['added'] += 1
                file_changed = True

        # Get units modified after last sync and before this sync started
        filter_by = {
            'revision__lte': last_revision,
            'store': self,
        }
        # Sync all units if first sync
        if self.last_sync_revision is not None:
            filter_by.update({'revision__gt': self.last_sync_revision})

        modified_units = set(Unit.objects.filter(**filter_by)
                                 .values_list('id', flat=True).distinct())

        common_dbids = set(self.dbid_index.get(uid)
                           for uid in old_ids & new_ids)

        if conservative:
            # Sync only modified units
            common_dbids &= modified_units

        common_dbids = list(common_dbids)

        for unit in self.findid_bulk(common_dbids):
            match = disk_store.findid(unit.getid())
            if match is not None:
                changed = unit.sync(match)
                if changed:
                    changes['updated'] += 1
                    file_changed = True

        #TODO conservative -> not overwrite
        if file_changed or not conservative:
            self.update_store_header(user=user)
            self.file.savestore()
            self.file_mtime = self.get_file_mtime()

            log(u"[sync] File saved; %s units in %s [revision: %d]" %
                (get_change_str(changes), self.pootle_path, last_revision))
        else:
            logging.info(u"[sync] nothing changed in %s [revision: %d]" %
                          (self.pootle_path, last_revision))

        self.last_sync_revision = last_revision
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

######################## TranslationStore #########################

    suggestions_in_format = True

    def max_index(self):
        """Largest unit index"""
        return max_column(self.unit_set.all(), 'index', -1)

    def addunit(self, unit, index=None, user=None, revision=None):
        if index is None:
            index = self.max_index() + 1

        newunit = self.UnitClass(store=self, index=index)
        newunit.update(unit, user=user)
        if newunit._target_updated or newunit.istranslated():
            newunit.submitted_by = user
            newunit.submitted_on = timezone.now()

        if self.id:
            newunit.save(revision=revision)
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
            return self.unit_set.get(unitid_hash=unitid_hash)
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

    def get_max_unit_revision(self):
        return max_column(self.unit_set.all(), 'revision', 0)

    ### TreeItem
    def can_be_updated(self):
        return not self.obsolete

    def get_parents(self):
        if self.parent.is_translationproject():
            parents = [self.translation_project]
        else:
            parents = [self.parent]

        parents.extend(self.parent_vfolder_treeitems)

        return parents

    def get_cachekey(self):
        return self.pootle_path

    def _get_wordcount_stats(self):
        """calculate full wordcount statistics"""
        ret = {
            'total': 0,
            'translated': 0,
            'fuzzy': 0
        }
        # XXX: `order_by()` here is important as it removes the default
        # ordering for units. See #3897 for reference.
        res = self.units.order_by().values('state') \
                        .annotate(wordcount=models.Sum('source_wordcount'))
        for item in res:
            ret['total'] += item['wordcount']
            if item['state'] == TRANSLATED:
                ret['translated'] = item['wordcount']
            elif item['state'] == FUZZY:
                ret['fuzzy'] = item['wordcount']

        return ret

    def _get_checks(self):
        try:
            queryset = QualityCheck.objects.filter(unit__store=self,
                                                   unit__state__gt=UNTRANSLATED,
                                                   false_positive=False)

            queryset = queryset.values('unit', 'name', 'category') \
                               .order_by('unit', '-category')

            saved_unit = None
            result = {
                'unit_critical_error_count': 0,
                'checks': {},
            }
            for item in queryset:
                if item['unit'] != saved_unit or saved_unit is None:
                    saved_unit = item['unit']
                    if item['category'] == Category.CRITICAL:
                        result['unit_critical_error_count'] += 1
                if item['name'] in result['checks']:
                    result['checks'][item['name']] += 1
                else:
                    result['checks'][item['name']] = 1

            return result
        except Exception as e:
            logging.info(u"Error getting quality checks for %s\n%s",
                         self.name, e)
            return {}

    def _get_mtime(self):
        return max_column(self.unit_set.all(), 'mtime', datetime_min)

    def _get_last_updated(self):
        try:
            max_unit = self.unit_set.all().order_by('-creation_time')[0]
        except IndexError:
            max_unit = None

        # creation_time field has been added recently, so it can have NULL value
        if max_unit is not None:
            max_time = max_unit.creation_time
            if max_time:
                return max_unit.get_last_updated_info()

        return CachedTreeItem._get_last_updated()

    def _get_last_action(self, submission=None):
        if submission is None:
            try:
                sub = Submission.simple_objects.filter(store=self) \
                                .exclude(type=SubmissionTypes.UNIT_CREATE) \
                                .latest()
            except Submission.DoesNotExist:
                return CachedTreeItem._get_last_action()
        else:
            sub = submission

        return sub.get_submission_info()

    def _get_suggestion_count(self):
        """Check if any unit in the store has suggestions"""
        return Suggestion.objects.filter(unit__store=self,
                                         unit__state__gt=OBSOLETE,
                                         state=SuggestionStates.PENDING).count()

    def refresh_stats(self, include_children=True, cached_methods=None):
        """This TreeItem method is used on directories, translation projects,
        languages and projects. For stores do nothing"""
        return

    def all_pootle_paths(self):
        """Get cache_key for all parents (to the Language and Project)
        of current TreeItem
        """
        pootle_paths = super(Store, self).all_pootle_paths()

        for vfolder_treeitem in self.parent_vfolder_treeitems:
            pootle_paths.extend(vfolder_treeitem.all_pootle_paths())

        return pootle_paths

    ### /TreeItem


################################ Translation #############################

    def getitem(self, item):
        """Returns a single unit based on the item number."""
        return self.units[item]


    def update_store_header(self, user=None):
        language = self.translation_project.language
        source_language = self.translation_project.project.source_language
        disk_store = self.file.store
        disk_store.settargetlanguage(language.code)
        disk_store.setsourcelanguage(source_language.code)

        from translate.storage import poheader
        if isinstance(disk_store, poheader.poheader):
            mtime = self.get_cached_value(CachedMethods.MTIME)
            if mtime is None or mtime == datetime_min:
                mtime = timezone.now()
            if user is None:
                try:
                    submit = self.translation_project.submission_set \
                                 .filter(creation_time=mtime).latest()
                    if submit.submitter.username != 'nobody':
                        user = submit.submitter
                except ObjectDoesNotExist:
                    try:
                        lastsubmit = self.translation_project.submission_set \
                                                             .latest()
                        if lastsubmit.submitter.username != 'nobody':
                            user = lastsubmit.submitter
                        mtime = min(lastsubmit.creation_time, mtime)
                    except ObjectDoesNotExist:
                        pass

            po_revision_date = mtime.strftime('%Y-%m-%d %H:%M') + \
                               poheader.tzstring()
            from pootle.core.utils.version import get_major_minor_version
            x_generator = "Pootle %s" % get_major_minor_version()
            headerupdates = {
                    'PO_Revision_Date': po_revision_date,
                    'X_Generator': x_generator,
                    'X_POOTLE_MTIME': ('%s.%06d' %
                                       (int(dateformat.format(mtime, 'U')),
                                        mtime.microsecond)),
                    }
            if user and user.is_authenticated():
                headerupdates['Last_Translator'] = '%s <%s>' % \
                        (user.display_name, user.email)
            else:
                #FIXME: maybe insert settings.POOTLE_TITLE or domain here?
                headerupdates['Last_Translator'] = 'Anonymous Pootle User'
            disk_store.updateheader(add=True, **headerupdates)

            if language.nplurals and language.pluralequation:
                disk_store.updateheaderplural(language.nplurals,
                                              language.pluralequation)
