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

from translate.filters.decorators import Category

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import six, timezone
from django.utils.functional import cached_property
from django.utils.http import urlquote

from pootle.core.delegate import (
    data_tool, format_syncers, format_updaters, frozen, terminology_matcher,
    wordcount)
from pootle.core.log import (
    STORE_DELETED, STORE_OBSOLETE, log, store_log)
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
from pootle_statistics.models import (
    MUTED, UNMUTED, Submission, SubmissionFields,
    SubmissionTypes)

from .abstracts import (
    AbstractUnit, AbstractQualityCheck, AbstractStore, AbstractSuggestion,
    AbstractSuggestionState, AbstractUnitChange, AbstractUnitSource)
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


@six.python_2_unicode_compatible
class QualityCheck(AbstractQualityCheck):
    """Database cache of results of qualitychecks on unit."""

    class Meta(AbstractQualityCheck.Meta):
        abstract = False
        db_table = "pootle_store_qualitycheck"

    def __str__(self):
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


class SuggestionState(AbstractSuggestionState):

    class Meta(AbstractSuggestionState.Meta):
        abstract = False
        db_table = "pootle_store_suggestion_state"


@six.python_2_unicode_compatible
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

    def __str__(self):
        return unicode(self.target)

    def _set_hash(self):
        string = self.translator_comment_f
        if string:
            string = self.target_f + SEPARATOR + string
        else:
            string = self.target_f
        self.target_hash = md5(string.encode("utf-8")).hexdigest()


# # # # # # # # Unit # # # # # # # # # #


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


@six.python_2_unicode_compatible
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

    def __str__(self):
        # FIXME: consider using unit id instead?
        return unicode(self.source)

    def __str__(self):
        return str(self.convert())

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)
        self._rich_source = None
        self._rich_target = None
        self._encoding = 'UTF-8'
        self._frozen = frozen.get(Unit)(self)

    @cached_property
    def counter(self):
        return wordcount.get(Unit)

    @property
    def comment_updated(self):
        return (
            self.translator_comment
            != self._frozen.translator_comment)

    @property
    def revision_updated(self):
        return self.revision != self._frozen.revision

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
    def updated(self):
        created = self._frozen.pk is None
        return (
            (self.source_updated and not created)
            or self.target_updated
            or (self.state_updated and not created)
            or (self.comment_updated and not created))

    @property
    def changed(self):
        try:
            self.change
            return True
        except UnitChange.DoesNotExist:
            return False

    def save(self, *args, **kwargs):
        created = self.id is None
        user = (
            kwargs.pop("user", None)
            or get_user_model().objects.get_system_user())
        reviewed_by = kwargs.pop("reviewed_by", None) or user
        changed_with = kwargs.pop("changed_with", None) or SubmissionTypes.SYSTEM
        super(Unit, self).save(*args, **kwargs)
        timestamp = self.mtime
        if created:
            unit_source = UnitSource(unit=self)
            unit_source.created_by = user
            unit_source.created_with = changed_with
            timestamp = self.creation_time
        elif self.source_updated:
            unit_source = self.unit_source
        if created or self.source_updated:
            unit_source.save()
        if self.updated and (created or not self.changed):
            self.change = UnitChange(
                unit=self,
                changed_with=changed_with)
        if self.updated:
            if changed_with is not None:
                self.change.changed_with = changed_with
            if self.comment_updated:
                self.change.commented_by = user
                self.change.commented_on = timestamp
            update_submit = (
                (self.target_updated or self.source_updated)
                or not self.change.submitted_on)
            if update_submit:
                self.change.submitted_by = user
                self.change.submitted_on = timestamp
            is_review = (
                reviewed_by != user
                or (self.state_updated and not self.target_updated)
                or (self.state_updated
                    and self.state == UNTRANSLATED))
            if is_review:
                self.change.reviewed_by = reviewed_by
                self.change.reviewed_on = timestamp
            self.change.save()
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
        if self.changed and self.change.submitted_on:
            obj.update({
                'iso_submitted_on': self.change.submitted_on.isoformat(),
                'display_submitted_on': dateformat.format(self.change.submitted_on),
            })

        if self.changed and self.change.submitted_by:
            obj.update({
                'username': self.change.submitted_by.username,
                'fullname': self.change.submitted_by.full_name,
                'email_md5': md5(self.change.submitted_by.email).hexdigest(),
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

        self.revision = Revision.incr()
        self.save(
            reviewed_by=user)
        check.false_positive = false_positive
        check.save()

        # create submission
        old_value = MUTED
        new_value = UNMUTED
        if false_positive:
            old_value = UNMUTED
            new_value = MUTED

        update_time = make_aware(timezone.now())
        sub = Submission(
            creation_time=update_time,
            translation_project=self.store.translation_project,
            submitter=user,
            field=SubmissionFields.NONE,
            unit=self,
            type=SubmissionTypes.WEB,
            old_value=old_value,
            new_value=new_value,
            quality_check=check)
        sub.save()

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


@six.python_2_unicode_compatible
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

    def __str__(self):
        return unicode(self.pootle_path)

    def __str__(self):
        return str(self.syncer.convert())

    def save(self, *args, **kwargs):
        self.pootle_path = self.parent.pootle_path + self.name
        self.tp_path = self.parent.tp_path + self.name

        # Force validation of required fields.
        self.full_clean(
            validate_unique=False,
            exclude=[
                "translation_project",
                "parent",
                "filetype"])

        super(Store, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        store_log(user='system', action=STORE_DELETED,
                  path=self.pootle_path, store=self.id)
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
        store_log(
            user='system',
            action=STORE_OBSOLETE,
            path=self.pootle_path,
            store=self.id)
        unit_query = self.unit_set.filter(state__gt=OBSOLETE)
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
        Unit.objects.filter(store_id=self.id, index__gte=start).update(
            index=operator.add(F('index'), delta))

    def mark_units_obsolete(self, uids_to_obsolete,
                            update_revision=None, user=None):
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
                unit.revision = update_revision
                unit.save(user=user)
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
            newunit.revision = update_revision
            newunit.save(
                user=user,
                changed_with=changed_with)
        return newunit

    def findunits(self, source, obsolete=False):
        if not obsolete and hasattr(self, "sourceindex"):
            return super(Store, self).findunits(source)

        # find using hash instead of index
        source_hash = md5(source.encode("utf-8")).hexdigest()
        units = self.unit_set.filter(
            unit_source__source_hash=source_hash)
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
