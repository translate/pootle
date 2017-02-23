# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime
import logging
import operator
import os
from hashlib import md5

from collections import OrderedDict

from translate.filters.decorators import Category

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.http import urlquote

from pootle.core.contextmanagers import update_data_after
from pootle.core.delegate import (
    data_tool, format_syncers, format_updaters, frozen, terminology_matcher)
from pootle.core.log import (
    TRANSLATION_ADDED, TRANSLATION_CHANGED, TRANSLATION_DELETED,
    UNIT_ADDED, UNIT_DELETED, UNIT_OBSOLETE, UNIT_RESURRECTED,
    STORE_ADDED, STORE_DELETED, STORE_OBSOLETE,
    MUTE_QUALITYCHECK, UNMUTE_QUALITYCHECK,
    action_log, log, store_log)
from pootle.core.models import Revision
from pootle.core.search import SearchBroker
from pootle.core.signals import update_data
from pootle.core.url_helpers import (
    get_editor_filter, split_pootle_path, to_tp_relative_path)
from pootle.core.utils import dateformat
from pootle.core.utils.aggregate import max_column
from pootle.core.utils.multistring import PLURAL_PLACEHOLDER, SEPARATOR
from pootle.core.utils.timezone import datetime_min, make_aware
from pootle_misc.checks import check_names
from pootle_misc.util import import_func
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)

from .abstracts import (
    AbstractUnit, AbstractQualityCheck, AbstractStore, AbstractSuggestion,
    AbstractUnitChange, AbstractUnitSource)
from .constants import (
    DEFAULT_PRIORITY, FUZZY, OBSOLETE, POOTLE_WINS,
    TRANSLATED, UNTRANSLATED)
from .managers import SuggestionManager, UnitManager
from .store.deserialize import StoreDeserialization
from .store.serialize import StoreSerialization
from .util import get_change_str, vfolders_installed


TM_BROKER = None


def get_tm_broker():
    global TM_BROKER
    if TM_BROKER is None:
        TM_BROKER = SearchBroker()
    return TM_BROKER


# # # # # # # # Quality Check # # # # # # #


class QualityCheck(AbstractQualityCheck):
    """Database cache of results of qualitychecks on unit."""

    class Meta(AbstractQualityCheck.Meta):
        abstract = False
        db_table = "pootle_store_qualitycheck"

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

class Suggestion(AbstractSuggestion):
    """Suggested translation for a :cls:`~pootle_store.models.Unit`, provided
    by users or automatically generated after a merge.
    """

    class Meta(AbstractSuggestion.Meta):
        abstract = False
        db_table = "pootle_store_suggestion"

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


class UnitChange(AbstractUnitChange):

    class Meta(AbstractUnit.Meta):
        abstract = False
        db_table = "pootle_store_unit_change"


class UnitSource(AbstractUnitSource):

    class Meta(AbstractUnit.Meta):
        abstract = False
        db_table = "pootle_store_unit_source"


class Unit(AbstractUnit):

    objects = UnitManager()

    class Meta(AbstractUnit.Meta):
        abstract = False
        db_table = "pootle_store_unit"
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

    @property
    def _target(self):
        return self.target_f

    @_target.setter
    def _target(self, value):
        self.target_f = value

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
        self._rich_target = None
        self._comment_updated = False
        self._auto_translated = False
        self._encoding = 'UTF-8'
        self._frozen = frozen.get(Unit)(self)

    def delete(self, *args, **kwargs):
        action_log(user='system', action=UNIT_DELETED,
                   lang=self.store.translation_project.language.code,
                   unit=self.id, translation='', path=self.store.pootle_path)
        super(Unit, self).delete(*args, **kwargs)

    @property
    def source_updated(self):
        return self.source != self._frozen.source

    @property
    def state_updated(self):
        return self.state != self._frozen.state

    @property
    def target_updated(self):
        return self.target != self._frozen.target

    @property
    def context_updated(self):
        return self.context != self._frozen.context

    @property
    def changed(self):
        try:
            self.change
            return True
        except UnitChange.DoesNotExist:
            return False

    def save(self, *args, **kwargs):
        created = self.id is None
        changed_with = kwargs.pop("changed_with", None) or SubmissionTypes.SYSTEM
        reviewed_by = kwargs.pop("reviewed_by", None)
        reviewed_on = kwargs.pop("reviewed_on", None)
        submitted_by = kwargs.pop("submitted_by", None)
        submitted_on = kwargs.pop("submitted_on", None)

        auto_translated = (
            kwargs.pop("auto_translated", None)
            or self._auto_translated)
        comment_updated = (
            kwargs.pop("comment_updated", None)
            or self._comment_updated)

        was_fuzzy = self._frozen.state == FUZZY
        action = None
        if "action" in kwargs:
            action = kwargs.pop("action", None)
        elif created:
            action = UNIT_ADDED
        elif self.state == OBSOLETE and self._frozen.state > OBSOLETE:
            action = UNIT_OBSOLETE
        elif self.state > OBSOLETE and self._frozen.state == OBSOLETE:
            action = UNIT_RESURRECTED
        elif self.isfuzzy() != was_fuzzy:
            action = TRANSLATION_CHANGED

        user = kwargs.pop("user", get_user_model().objects.get_system_user())

        if created or self.source_updated:
            # update source related fields
            self.source_hash = md5(self.source_f.encode("utf-8")).hexdigest()
            self.source_length = len(self.source_f)
            self.update_wordcount(auto_translate=True)

        if self.target_updated:
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
        elif self.target_updated or self.state_updated or comment_updated:
            self.revision = Revision.incr()

        if not created and action:
            action_log(
                user=user,
                action=action,
                lang=self.store.translation_project.language.code,
                unit=self.id,
                translation=self.target_f,
                path=self.store.pootle_path)
        if was_fuzzy:
            # set reviewer data if FUZZY has been removed only and
            # translation hasn't been updated
            self.reviewed_on = timezone.now()
            self.reviewed_by = user
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
        submitted_by = submitted_by or self.submitted_by
        submitted_on = submitted_on or self.submitted_on
        if created:
            unit_source = self.unit_source.model(unit=self)
            unit_source.created_by = submitted_by or user
            unit_source.created_with = changed_with
            submitted_on = self.creation_time
        elif self.source_updated:
            unit_source = self.unit_source.get()
        if created or self.source_updated:
            unit_source.source_hash = self.source_hash
            unit_source.source_length = self.source_length
            unit_source.source_wordcount = self.source_wordcount
            unit_source.save()
        changed = (
            (self.source_updated and not created)
            or self.target_updated
            or comment_updated)
        if changed and not self.changed:
            self.change = UnitChange(
                unit=self,
                changed_with=changed_with)
        if changed:
            if changed_with is not None:
                self.change.changed_with = changed_with
            if submitted_by is not None:
                self.change.submitted_by = submitted_by
            if reviewed_by is not None:
                self.change.reviewed_by = reviewed_by
            if submitted_on is not None:
                self.change.submitted_on = submitted_on
            if reviewed_on is not None:
                self.change.reviewed_on = reviewed_on
            self.change.save()

        # done processing source/target update remove flag
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

    @cached_property
    def unit_syncer(self):
        return self.store.syncer.unit_sync_class(self)

    def convert(self, unitclass=None):
        """Convert to a unit of type :param:`unitclass` retaining as much
        information from the database as the target format can support.
        """
        return self.unit_syncer.convert(unitclass)

    def sync(self, unit, unitclass=None):
        """Sync in file unit with translations from the DB."""
        changed = False

        if not self.isobsolete() and unit.isobsolete():
            unit.resurrect()
            changed = True

        target = (
            unitclass(self).target
            if unitclass
            else unit.target)

        if unit.target != target:
            if unit.hasplural():
                nplurals = self.store.translation_project.language.nplurals
                target_plurals = len(target.strings)
                strings = target.strings
                if target_plurals < nplurals:
                    strings.extend([u'']*(nplurals - target_plurals))
                if unit.target.strings != strings:
                    unit.target = strings
                    changed = True
            else:
                unit.target = target
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

        # this is problematic - it compares getid, but then sets getid *or* source
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
        if value:
            self.state = FUZZY
        elif self.state <= FUZZY:
            if filter(None, self.target_f.strings):
                self.state = TRANSLATED
            else:
                self.state = UNTRANSLATED

    def hasplural(self):
        return (self.source is not None and
                (len(self.source.strings) > 1 or
                 hasattr(self.source, "plural") and
                 self.source.plural))

    def isobsolete(self):
        return self.state == OBSOLETE

    def makeobsolete(self):
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
        self.index = self.store.max_index() + 1

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
        self.save(
            revision=Revision.incr(),
            action=(
                MUTE_QUALITYCHECK
                if false_positive
                else UNMUTE_QUALITYCHECK))

    def get_terminology(self):
        """get terminology suggestions"""
        results = terminology_matcher.get(self.__class__)(self).matches
        return [m[1] for m in results]

    def get_last_created_unit_info(self):
        return {
            "display_datetime": dateformat.format(self.creation_time),
            "creation_time": int(dateformat.format(self.creation_time, 'U')),
            "unit_source": truncatechars(self, 50),
            "unit_url": self.get_translate_url(),
        }


# # # # # # # # # # #  Store # # # # # # # # # # # # # #


class Store(AbstractStore):
    """A model representing a translation store (i.e. a PO or XLIFF file)."""

    UnitClass = Unit
    Name = "Model Store"
    is_dir = False

    class Meta(AbstractStore.Meta):
        abstract = False
        db_table = "pootle_store_store"

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
        update_data.send(self.__class__, instance=self)

    def resurrect(self, save=True, resurrect_units=True):
        self.obsolete = False
        self.file_mtime = datetime_min
        if self.last_sync_revision is None:
            self.last_sync_revision = self.data.max_unit_revision
        if resurrect_units:
            for unit in self.unit_set.all():
                unit.resurrect()
                unit.save()
        if save:
            self.save()
        update_data.send(self.__class__, instance=self)

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
        """
        state_updated = kwargs.get("state_updated")
        target_updated = kwargs.get("target_updated")
        comment_updated = kwargs.get("comment_updated")
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
                    revision=unit.revision,
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

    def create_file_store(self, last_revision, user):
        path_parts = split_pootle_path(self.pootle_path)
        file_path = os.path.join(
            self.translation_project.abs_real_path,
            *path_parts[2:])
        path_prefix = [path_parts[1]]
        if self.translation_project.project.get_treestyle() != "gnu":
            path_prefix.append(path_parts[0])
        relative_file_path = os.path.join(*(path_prefix + list(path_parts[2:])))
        logging.debug(u"Creating file %s", self.pootle_path)
        store = self.syncer.convert()
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        self.file = relative_file_path
        store.savefile(file_path)
        log(u"Created file for %s [revision: %d]" %
            (self.pootle_path, last_revision))
        self.syncer.update_store_header(store, user=user)
        self.file.savestore()
        self.file_mtime = self.get_file_mtime()
        self.last_sync_revision = last_revision
        self.save()

    def update_file_store(self, changes, last_revision, user):
        self.syncer.update_store_header(self.file.store, user=user)
        self.file.savestore()
        self.file_mtime = self.get_file_mtime()
        log(u"[sync] File saved; %s units in %s [revision: %d]" %
            (get_change_str(changes),
             self.pootle_path,
             last_revision))

    def sync(self, update_structure=False, conservative=True,
             user=None, skip_missing=False, only_newer=True):
        """Sync file with translations from DB."""
        if skip_missing and not self.file.exists():
            return

        last_revision = self.data.max_unit_revision or 0

        # TODO only_newer -> not force
        if only_newer and not self.syncer.update_newer(last_revision):
            logging.info(
                u"[sync] No updates for %s after [revision: %d]",
                self.pootle_path, last_revision)
            return

        if not self.file.exists():
            return self.create_file_store(last_revision, user)

        if conservative and self.is_template:
            return

        file_changed, changes = self.syncer.sync(
            self.file.store,
            last_revision,
            update_structure=update_structure,
            conservative=conservative)

        # TODO conservative -> not overwrite
        if file_changed or not conservative:
            self.update_file_store(changes, last_revision, user)
        else:
            logging.info(
                u"[sync] nothing changed in %s [revision: %d]",
                self.pootle_path,
                last_revision)
        self.last_sync_revision = last_revision
        self.save()

# # # # # # # # # # # #  TranslationStore # # # # # # # # # # # # #

    suggestions_in_format = True

    def max_index(self):
        """Largest unit index"""
        return max_column(self.unit_set.all(), 'index', -1)

    def addunit(self, unit, index=None, user=None, update_revision=None,
                changed_with=None):
        if index is None:
            index = self.max_index() + 1

        newunit = self.UnitClass(
            store=self,
            index=index)
        newunit.update(unit, user=user)

        if self.id:
            newunit.save(
                revision=update_revision,
                user=user,
                changed_with=changed_with)
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
