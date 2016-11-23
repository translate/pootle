# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime
import operator
from hashlib import md5

from collections import OrderedDict

from translate.filters.decorators import Category
from translate.storage import base

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.http import urlquote

from pootle.core.contextmanagers import update_data_after
from pootle.core.delegate import data_tool, format_syncers, format_updaters
from pootle.core.log import (
    TRANSLATION_ADDED, TRANSLATION_CHANGED, TRANSLATION_DELETED,
    UNIT_ADDED, UNIT_DELETED, UNIT_OBSOLETE, UNIT_RESURRECTED,
    STORE_ADDED, STORE_DELETED, STORE_OBSOLETE,
    MUTE_QUALITYCHECK, UNMUTE_QUALITYCHECK,
    action_log, store_log)
from pootle.core.mixins import CachedTreeItem
from pootle.core.models import Revision
from pootle.core.search import SearchBroker
from pootle.core.signals import update_data
from pootle.core.storage import PootleFileSystemStorage
from pootle.core.url_helpers import (
    get_editor_filter, split_pootle_path, to_tp_relative_path)
from pootle.core.utils import dateformat
from pootle.core.utils.aggregate import max_column
from pootle.core.utils.multistring import PLURAL_PLACEHOLDER, SEPARATOR
from pootle.core.utils.timezone import datetime_min, make_aware
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_format.models import Format
from pootle_misc.checks import check_names
from pootle_misc.util import import_func
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)

from .constants import (
    DEFAULT_PRIORITY, FUZZY, NEW, OBSOLETE, POOTLE_WINS,
    TRANSLATED, UNTRANSLATED)
from .fields import MultiStringField, TranslationStoreField
from .managers import StoreManager, SuggestionManager, UnitManager
from .store.deserialize import StoreDeserialization
from .store.serialize import StoreSerialization
from .util import SuggestionStates, vfolders_installed


TM_BROKER = None


def get_tm_broker():
    global TM_BROKER
    if TM_BROKER is None:
        TM_BROKER = SearchBroker()
    return TM_BROKER


# # # # # # # # Quality Check # # # # # # #


class QualityCheck(models.Model):
    """Database cache of results of qualitychecks on unit."""

    name = models.CharField(max_length=64, db_index=True)
    unit = models.ForeignKey("pootle_store.Unit", db_index=True,
                             on_delete=models.CASCADE)
    category = models.IntegerField(null=False, default=Category.NO_CATEGORY)
    message = models.TextField()
    false_positive = models.BooleanField(default=False, db_index=True)

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

# # # # # # # # # Suggestion # # # # # # # #


class Suggestion(models.Model, base.TranslationUnit):
    """Suggested translation for a :cls:`~pootle_store.models.Unit`, provided
    by users or automatically generated after a merge.
    """

    target_f = MultiStringField()
    target_hash = models.CharField(max_length=32, db_index=True)
    unit = models.ForeignKey('pootle_store.Unit', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False,
                             related_name='suggestions', db_index=True,
                             on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                 related_name='reviews', db_index=True,
                                 on_delete=models.CASCADE)

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

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

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

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return unicode(self.target)

    def _set_hash(self):
        string = self.translator_comment_f
        if string:
            string = self.target_f + SEPARATOR + string
        else:
            string = self.target_f
        self.target_hash = md5(string.encode("utf-8")).hexdigest()


# # # # # # # # Unit # # # # # # # # # #

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


class Unit(models.Model, base.TranslationUnit):
    store = models.ForeignKey("pootle_store.Store", db_index=True,
                              on_delete=models.CASCADE)
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

    state = models.IntegerField(null=False, default=UNTRANSLATED,
                                db_index=True)
    revision = models.IntegerField(null=False, default=0, db_index=True,
                                   blank=True)

    # Metadata
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    mtime = models.DateTimeField(auto_now=True, db_index=True, editable=False)

    # unit translator
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                     db_index=True, related_name='submitted',
                                     on_delete=models.CASCADE)
    submitted_on = models.DateTimeField(db_index=True, null=True)

    commented_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                     db_index=True, related_name='commented',
                                     on_delete=models.CASCADE)
    commented_on = models.DateTimeField(db_index=True, null=True)

    # reviewer: who has accepted suggestion or removed FUZZY
    # None if translation has been submitted by approved translator
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    db_index=True, related_name='reviewed',
                                    on_delete=models.CASCADE)
    reviewed_on = models.DateTimeField(db_index=True, null=True)

    objects = UnitManager()

    class Meta(object):
        unique_together = (
            ('store', 'unitid_hash'),
            ("store", "state", "index", "unitid_hash"))
        get_latest_by = 'mtime'
        index_together = [
            ["store", "index"],
            ["store", "revision"],
            ["store", "mtime"],
            ["store", "state"]]

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

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

    # # # # # # # # # # # # # Class & static methods # # # # # # # # # # # # #

    @classmethod
    def max_revision(cls):
        """Returns the max revision number across all units."""
        return max_column(cls.objects.all(), 'revision', 0)

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        # FIXME: consider using unit id instead?
        return unicode(self.source)

    def __str__(self):
        return str(self.convert())

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

    def delete(self, *args, **kwargs):
        action_log(user='system', action=UNIT_DELETED,
                   lang=self.store.translation_project.language.code,
                   unit=self.id, translation='', path=self.store.pootle_path)
        super(Unit, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        created = self.id is None
        source_updated = kwargs.pop("source_updated", None) or self._source_updated
        target_updated = kwargs.pop("target_updated", None) or self._target_updated
        state_updated = kwargs.pop("state_updated", None) or self._state_updated
        auto_translated = (
            kwargs.pop("auto_translated", None)
            or self._auto_translated)
        comment_updated = (
            kwargs.pop("comment_updated", None)
            or self._comment_updated)
        action = kwargs.pop("action", None) or getattr(self, "_save_action", None)

        if not hasattr(self, '_log_user'):
            User = get_user_model()
            self._log_user = User.objects.get_system_user()
        user = kwargs.pop("user", self._log_user)

        if created:
            action = UNIT_ADDED

        if source_updated:
            # update source related fields
            self.source_hash = md5(self.source_f.encode("utf-8")).hexdigest()
            self.source_length = len(self.source_f)
            self.update_wordcount(auto_translate=True)

        if target_updated:
            # update target related fields
            self.target_wordcount = count_words(self.target_f.strings)
            self.target_length = len(self.target_f)
            if filter(None, self.target_f.strings):
                if self.state == UNTRANSLATED:
                    self.state = TRANSLATED
                    action = action or TRANSLATION_ADDED
                else:
                    action = action or TRANSLATION_CHANGED
            else:
                action = TRANSLATION_DELETED
                # if it was TRANSLATED then set to UNTRANSLATED
                if self.state > FUZZY:
                    self.state = UNTRANSLATED

        # Updating unit from the .po file set its revision property to
        # a new value (the same for all units during its store updated)
        # since that change doesn't require further sync but note that
        # auto_translated units require further sync
        revision = kwargs.pop('revision', None)
        if revision is not None and not auto_translated:
            self.revision = revision
        elif target_updated or state_updated or comment_updated:
            self.revision = Revision.incr()

        if not created and action:
            action_log(
                user=self._log_user,
                action=action,
                lang=self.store.translation_project.language.code,
                unit=self.id,
                translation=self.target_f,
                path=self.store.pootle_path)
        was_fuzzy = (
            state_updated and self.state == TRANSLATED
            and action == TRANSLATION_CHANGED
            and not target_updated)
        if was_fuzzy:
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

        if action and action == UNIT_ADDED:
            action_log(
                user=self._log_user,
                action=action,
                lang=self.store.translation_project.language.code,
                unit=self.id,
                translation=self.target_f,
                path=self.store.pootle_path)
            self.add_initial_submission(user=user)

        if source_updated or target_updated:
            if not (created and self.state == UNTRANSLATED):
                self.update_qualitychecks()
            if self.istranslated():
                self.update_tmserver()

        # done processing source/target update remove flag
        self._source_updated = False
        self._target_updated = False
        self._state_updated = False
        self._comment_updated = False
        self._auto_translated = False

        update_data.send(
            self.store.__class__, instance=self.store)

    def get_absolute_url(self):
        return self.store.get_absolute_url()

    def get_translate_url(self):
        return (
            "%s%s"
            % (self.store.get_translate_url(),
               '#unit=%s' % unicode(self.id)))

    def get_search_locations_url(self):
        (proj_code, dir_path,
         filename) = split_pootle_path(self.store.pootle_path)[1:]

        return u''.join([
            reverse('pootle-project-translate',
                    args=[proj_code, dir_path, filename]),
            get_editor_filter(search=self.locations, sfields='locations'),
        ])

    def get_screenshot_url(self):
        prefix = self.store.translation_project.\
            project.screenshot_search_prefix
        if prefix:
            return prefix + urlquote(self.source_f)

    def is_accessible_by(self, user):
        """Returns `True` if the current unit is accessible by `user`."""
        if user.is_superuser:
            return True

        from pootle_project.models import Project
        user_projects = Project.accessible_by_user(user)
        return self.store.translation_project.project.code in user_projects

    def add_initial_submission(self, user=None):
        if self.istranslated() or self.isfuzzy():
            Submission.objects.create(
                creation_time=self.creation_time,
                translation_project=self.store.translation_project,
                submitter=user or self._log_user,
                unit=self,
                store=self.store,
                type=SubmissionTypes.UNIT_CREATE,
                field=SubmissionFields.TARGET,
                new_value=self.target,
            )

    @cached_property
    def unit_syncer(self):
        return self.store.syncer.unit_sync_class(self)

    def convert(self, unitclass=None):
        """Convert to a unit of type :param:`unitclass` retaining as much
        information from the database as the target format can support.
        """
        return self.unit_syncer.convert(unitclass)

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
                unit.addnote(self_notes, origin="translator",
                             position="replace")
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

        :param user: User to attribute updates to.
        :rtype: bool
        :return: True if the new :param:`unit` differs from the current unit.
            Two units differ when any of the fields differ (source, target,
            translator/developer comments, locations, context, status...).
        """
        changed = False

        if user is None:
            User = get_user_model()
            user = User.objects.get_system_user()

        update_source = (
            self.source != unit.source
            or (len(self.source.strings)
                != stringcount(unit.source))
            or (self.hasplural()
                != unit.hasplural()))
        if update_source:
            if unit.hasplural() and len(unit.source.strings) == 1:
                self.source = [unit.source, PLURAL_PLACEHOLDER]
            else:
                self.source = unit.source
            changed = True

        update_target = (
            self.target != unit.target
            or (len(self.target.strings)
                != stringcount(unit.target)))
        if update_target:
            notempty = filter(None, self.target_f.strings)
            self.target = unit.target
            self.submitted_by = user
            self.submitted_on = timezone.now()

            if filter(None, self.target_f.strings) or notempty:
                # FIXME: we need to do this cause we discard nplurals for empty
                # plurals
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

    def update_qualitychecks(self, keep_false_positives=False):
        """Run quality checks and store result in the database.

        :param keep_false_positives: when set to `False`, it will activate
            (unmute) any existing false positive checks.
        :return: `True` if quality checks were updated or `False` if they
            left unchanged.
        """
        unmute_list = []
        result = False

        checks = self.qualitycheck_set.all()

        existing = {}
        for check in checks.values('name', 'false_positive', 'id'):
            existing[check['name']] = {
                'false_positive': check['false_positive'],
                'id': check['id'],
            }

        # no checks if unit is untranslated
        if not self.target:
            if existing:
                self.qualitycheck_set.all().delete()
                return True

            return False

        checker = self.store.translation_project.checker
        qc_failures = checker.run_filters(self, categorised=True)
        checks_to_add = []
        for name in qc_failures.iterkeys():
            if name in existing:
                # keep false-positive checks if check is active
                if (existing[name]['false_positive'] and
                        not keep_false_positives):
                    unmute_list.append(name)
                del existing[name]
                continue

            message = qc_failures[name]['message']
            category = qc_failures[name]['category']
            checks_to_add.append(
                QualityCheck(
                    unit=self,
                    name=name,
                    message=message,
                    category=category))
            result = True

        if checks_to_add:
            self.qualitycheck_set.bulk_create(checks_to_add)

        if not keep_false_positives and unmute_list:
            self.qualitycheck_set.filter(name__in=unmute_list) \
                                 .update(false_positive=False)

        # delete inactive checks
        if existing:
            self.qualitycheck_set.filter(name__in=existing).delete()

        changed = result or bool(unmute_list) or bool(existing)
        return changed

    def get_qualitychecks(self):
        return self.qualitycheck_set.all()

    def get_critical_qualitychecks(self):
        return self.get_qualitychecks().filter(category=Category.CRITICAL)

    def get_active_critical_qualitychecks(self):
        return self.get_active_qualitychecks().filter(
            category=Category.CRITICAL)

    def get_warning_qualitychecks(self):
        return self.get_qualitychecks().exclude(category=Category.CRITICAL)

    def get_active_qualitychecks(self):
        return self.qualitycheck_set.filter(false_positive=False)

# # # # # # # # # # # Related Submissions # # # # # # # # # # # #

    def get_edits(self):
        return self.submission_set.get_unit_edits()

    def get_comments(self):
        return self.submission_set.get_unit_comments()

    def get_state_changes(self):
        return self.submission_set.get_unit_state_changes()

    def get_suggestion_reviews(self):
        return self.submission_set.get_unit_suggestion_reviews()

# # # # # # # # # # # TranslationUnit # # # # # # # # # # # # # #

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

        if self.submitted_on:
            obj.update({
                'iso_submitted_on': self.submitted_on.isoformat(),
                'display_submitted_on': dateformat.format(self.submitted_on),
            })

        if self.submitted_by:
            obj.update({
                'username': self.submitted_by.username,
                'fullname': self.submitted_by.full_name,
                'email_md5': md5(self.submitted_by.email).hexdigest(),
            })

        get_tm_broker().update(self.store.translation_project.language.code,
                               obj)

    def get_tm_suggestions(self):
        return get_tm_broker().search(self)

# # # # # # # # # # # TranslationUnit # # # # # # # # # # # # # #

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
                (len(self.source.strings) > 1 or
                 hasattr(self.source, "plural") and
                 self.source.plural))

    def isobsolete(self):
        return self.state == OBSOLETE

    def makeobsolete(self):
        if self.state > OBSOLETE:
            # when Unit becomes obsolete the cache flags should be updated
            self._state_updated = True
            self._save_action = UNIT_OBSOLETE

            self.state = OBSOLETE
            self.index = 0

    def resurrect(self, is_fuzzy=False):
        if self.state > OBSOLETE:
            return

        if filter(None, self.target_f.strings):
            # when Unit toggles its OBSOLETE state the number of translated
            # words or fuzzy words also changes
            if is_fuzzy:
                self.state = FUZZY
            else:
                self.state = TRANSLATED
        else:
            self.state = UNTRANSLATED

        self.update_qualitychecks(keep_false_positives=True)
        self._state_updated = True
        self._save_action = UNIT_RESURRECTED

    def istranslated(self):
        return self.state >= TRANSLATED

# # # # # # # # # # # Suggestions # # # # # # # # # # # # # # # # #
    def get_suggestions(self):
        return self.suggestion_set.pending().select_related('user').all()

    def has_critical_checks(self):
        return self.qualitycheck_set.filter(
            category=Category.CRITICAL,
        ).exists()

    def toggle_qualitycheck(self, check_id, false_positive, user):
        check = self.qualitycheck_set.get(id=check_id)

        if check.false_positive == false_positive:
            return

        check.false_positive = false_positive
        check.save()

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

        sub = Submission(creation_time=make_aware(timezone.now()),
                         translation_project=self.store.translation_project,
                         submitter=user, field=SubmissionFields.NONE,
                         unit=self, store=self.store, type=sub_type,
                         quality_check=check)
        sub.save()

        # update timestamp
        # log user action
        self.save()

    def get_terminology(self):
        """get terminology suggestions"""
        matcher = self.store.translation_project.gettermmatcher()
        if matcher is None:
            return []

        return matcher.matches(self.source)

    def get_last_created_unit_info(self):
        return {
            "display_datetime": dateformat.format(self.creation_time),
            "creation_time": int(dateformat.format(self.creation_time, 'U')),
            "unit_source": truncatechars(self, 50),
            "unit_url": self.get_translate_url(),
        }


# # # # # # # # # # #  Store # # # # # # # # # # # # # #


def validate_no_slashes(value):
    if '/' in value:
        raise ValidationError('Store name cannot contain "/" characters')

    if '\\' in value:
        raise ValidationError('Store name cannot contain "\\" characters')


# Needed to alter storage location in tests
fs = PootleFileSystemStorage()


class Store(models.Model, CachedTreeItem, base.TranslationStore):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""

    UnitClass = Unit
    Name = "Model Store"
    is_dir = False

    file = TranslationStoreField(max_length=255, storage=fs, db_index=True,
                                 null=False, editable=False)

    parent = models.ForeignKey(
        'pootle_app.Directory', related_name='child_stores', db_index=True,
        editable=False, on_delete=models.CASCADE)

    translation_project_fk = 'pootle_translationproject.TranslationProject'
    translation_project = models.ForeignKey(
        translation_project_fk, related_name='stores', db_index=True,
        editable=False, on_delete=models.CASCADE)

    filetype = models.ForeignKey(
        Format, related_name='stores', null=True, blank=True, db_index=True,
        on_delete=models.CASCADE)
    is_template = models.BooleanField(default=False)

    # any changes to the `pootle_path` field may require updating the schema
    # see migration 0007_case_sensitive_schema.py
    pootle_path = models.CharField(max_length=255, null=False, unique=True,
                                   db_index=True, verbose_name=_("Path"))

    tp_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Path"))
    # any changes to the `name` field may require updating the schema
    # see migration 0007_case_sensitive_schema.py
    name = models.CharField(max_length=128, null=False, editable=False,
                            validators=[validate_no_slashes])

    file_mtime = models.DateTimeField(default=datetime_min)
    state = models.IntegerField(null=False, default=NEW, editable=False,
                                db_index=True)
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    last_sync_revision = models.IntegerField(db_index=True, null=True,
                                             blank=True)
    obsolete = models.BooleanField(default=False)

    # this is calculated from virtualfolders if installed and linked
    priority = models.FloatField(
        db_index=True, default=1,
        validators=[MinValueValidator(0)])

    objects = StoreManager()

    class Meta(object):
        ordering = ['pootle_path']
        index_together = [
            ["translation_project", "is_template"],
            ["translation_project", "pootle_path", "is_template", "filetype"]]
        unique_together = (
            ('parent', 'name'),
            ("obsolete", "translation_project", "tp_path"))

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @property
    def code(self):
        return self.name.replace('.', '-')

    @property
    def tp(self):
        return self.translation_project

    @property
    def real_path(self):
        return self.file.name

    @property
    def has_terminology(self):
        """is this a project specific terminology store?"""
        # TODO: Consider if this should check if the store belongs to a
        # terminology project. Probably not, in case this might be called over
        # several files in a project.
        return self.name.startswith('pootle-terminology')

    @property
    def units(self):
        return self.unit_set.filter(state__gt=OBSOLETE).order_by('index')

    @units.setter
    def units(self, value):
        """Null setter to avoid tracebacks if :meth:`TranslationStore.__init__`
        is called.
        """
        pass

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    @cached_property
    def path(self):
        """Returns just the path part omitting language and project codes.

        If the `pootle_path` of a :cls:`Store` object `store` is
        `/af/project/dir1/dir2/file.po`, `store.path` will return
        `dir1/dir2/file.po`.
        """
        return to_tp_relative_path(self.pootle_path)

    def __init__(self, *args, **kwargs):
        super(Store, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.pootle_path)

    def __str__(self):
        return str(self.syncer.convert())

    def save(self, *args, **kwargs):
        created = not self.id
        self.pootle_path = self.parent.pootle_path + self.name
        self.tp_path = self.parent.tp_path + self.name

        # Force validation of fields.
        self.full_clean()

        super(Store, self).save(*args, **kwargs)
        if created:
            store_log(user='system', action=STORE_ADDED,
                      path=self.pootle_path, store=self.id)

    def delete(self, *args, **kwargs):
        store_log(user='system', action=STORE_DELETED,
                  path=self.pootle_path, store=self.id)

        lang = self.translation_project.language.code
        for unit in self.unit_set.iterator():
            action_log(user='system', action=UNIT_DELETED, lang=lang,
                       unit=unit.id, translation='', path=self.pootle_path)

        super(Store, self).delete(*args, **kwargs)

    def calculate_priority(self):
        if not vfolders_installed():
            return DEFAULT_PRIORITY

        from virtualfolder.models import VirtualFolder

        vfolders = VirtualFolder.objects
        priority = (
            vfolders.filter(stores=self)
                    .aggregate(priority=models.Max("priority"))["priority"])
        if priority is None:
            return DEFAULT_PRIORITY
        return priority

    def set_priority(self, priority=None):
        priority = (
            self.calculate_priority()
            if priority is None
            else priority)

        if priority != self.priority:
            Store.objects.filter(pk=self.pk).update(priority=priority)

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

    def get_absolute_url(self):
        return reverse(
            'pootle-tp-store-browse',
            args=split_pootle_path(self.pootle_path))

    def get_translate_url(self, **kwargs):
        return u''.join(
            [reverse("pootle-tp-store-translate",
                     args=split_pootle_path(self.pootle_path)),
             get_editor_filter(**kwargs)])

    def findid_bulk(self, ids, unit_set=None):
        chunks = 200
        for i in xrange(0, len(ids), chunks):
            units = (unit_set or self.unit_set).filter(id__in=ids[i:i+chunks])
            for unit in units.iterator():
                yield unit

    def get_file_mtime(self):
        disk_mtime = datetime.datetime.fromtimestamp(self.file.getpomtime()[0])
        # set microsecond to 0 for comparing with a time value without
        # microseconds
        disk_mtime = make_aware(disk_mtime.replace(microsecond=0))

        return disk_mtime

    def update_index(self, start, delta):
        with update_data_after(self):
            Unit.objects.filter(store_id=self.id, index__gte=start).update(
                index=operator.add(F('index'), delta))

    def mark_units_obsolete(self, uids_to_obsolete, update_revision=None):
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
                unit.save(revision=update_revision)
                obsoleted += 1

        return obsoleted

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    @cached_property
    def updater(self):
        updaters = format_updaters.gather()
        updater_class = (
            updaters.get(self.filetype.name)
            or updaters.get("default"))
        return updater_class(self)

    @cached_property
    def syncer(self):
        syncers = format_syncers.gather()
        syncer_class = (
            syncers.get(self.filetype.name)
            or syncers.get("default"))
        return syncer_class(self)

    def record_submissions(self, unit, old_target, old_state, current_time, user,
                           submission_type=None, **kwargs):
        """Records all applicable submissions for `unit`.

        EXTREME HAZARD: this relies on implicit `._<field>_updated` members
        being available in `unit`. Let's look into replacing such members with
        something saner (#3895).
        """
        state_updated = kwargs.get("state_updated") or unit._state_updated
        target_updated = kwargs.get("target_updated") or unit._target_updated
        comment_updated = kwargs.get("comment_updated") or unit._comment_updated

        create_subs = OrderedDict()

        if state_updated:
            create_subs[SubmissionFields.STATE] = [
                old_state,
                unit.state]

        if target_updated:
            create_subs[SubmissionFields.TARGET] = [
                old_target,
                unit.target_f]

        if comment_updated:
            create_subs[SubmissionFields.COMMENT] = [
                '',
                unit.translator_comment or '']

        if submission_type is None:
            submission_type = SubmissionTypes.SYSTEM

        subs_created = []
        for field in create_subs:
            subs_created.append(
                Submission(
                    creation_time=current_time,
                    translation_project_id=self.translation_project_id,
                    submitter=user,
                    unit=unit,
                    store_id=self.id,
                    field=field,
                    type=submission_type,
                    old_value=create_subs[field][0],
                    new_value=create_subs[field][1]))
        if subs_created:
            unit.submission_set.add(*subs_created, bulk=False)

    def update(self, store, user=None, store_revision=None,
               submission_type=None, resolve_conflict=POOTLE_WINS,
               allow_add_and_obsolete=True):
        """Update DB with units from a ttk Store.

        :param store: a source `Store` instance from TTK.
        :param store_revision: revision at which the source `Store` was last
            synced.
        :param user: User to attribute updates to.
        :param submission_type: Submission type of saved updates.
        :param allow_add_and_obsolete: allow to add new units
            and make obsolete existing units
        """
        self.updater.update(
            store, user=user, store_revision=store_revision,
            submission_type=submission_type, resolve_conflict=resolve_conflict,
            allow_add_and_obsolete=allow_add_and_obsolete)

    def deserialize(self, data):
        return StoreDeserialization(self).deserialize(data)

    def serialize(self):
        return StoreSerialization(self).serialize()

    def sync(self, update_structure=False, conservative=True,
             user=None, skip_missing=False, only_newer=True):
        """Sync file with translations from DB."""
        if skip_missing and not self.file.exists():
            return

        self.syncer.sync(
            update_structure=update_structure,
            conservative=conservative,
            user=user,
            only_newer=only_newer)


# # # # # # # # # # # #  TranslationStore # # # # # # # # # # # # #

    suggestions_in_format = True

    def max_index(self):
        """Largest unit index"""
        return max_column(self.unit_set.all(), 'index', -1)

    def addunit(self, unit, index=None, user=None, update_revision=None):
        if index is None:
            index = self.max_index() + 1

        newunit = self.UnitClass(store=self, index=index)
        newunit.update(unit, user=user)

        if self.id:
            newunit.save(revision=update_revision, user=user)
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

    def header(self):
        # FIXME: we should store some metadata in db
        if self.file and hasattr(self.file.store, 'header'):
            return self.file.store.header()

    def get_max_unit_revision(self):
        return max_column(self.unit_set.all(), 'revision', 0)

    # # # TreeItem
    def get_parents(self):
        if self.parent.is_translationproject():
            return [self.translation_project]
        return [self.parent]

    # # # /TreeItem


# # # # # # # # # # # # # # # #  Translation # # # # # # # # # # # # # # #
