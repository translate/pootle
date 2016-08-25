# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.filters.decorators import Category

from django.db import models
from django.db.models import Case, Count, Max, When, Q, Sum
from django.utils.functional import cached_property

from pootle.core.delegate import data_updater
from pootle.core.url_helpers import split_pootle_path
from pootle_data.models import StoreChecksData, StoreData
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED
from pootle_store.models import QualityCheck
from pootle_store.unit.timeline import SubmissionProxy
from pootle_store.util import SuggestionStates


SUM_FIELDS = (
    "critical_checks",
    "total_words",
    "fuzzy_words",
    "translated_words")


class DataUpdater(object):
    """Set data for an object"""

    sum_fields = SUM_FIELDS

    def __init__(self, tool):
        self.tool = tool

    @property
    def model(self):
        return self.tool.context

    @cached_property
    def data(self):
        try:
            return self.model.data
        except self.data_field.related_model.DoesNotExist:
            return self.data_field.related_model.objects.create(
                **{self.related_name: self.model})

    def get_max_unit_mtime(self, unit=None, store_data=None):
        """Returns the max mtime of the store"""
        if unit:
            return unit.mtime
        return (store_data or self.store_data)["mtime"]

    def get_max_unit_revision(self, unit=None, store_data=None):
        """Returns the max mtime of the store"""
        if unit:
            return unit.revision
        return (store_data or self.store_data)["revision"]

    def get_last_submission(self, submission=None, store_data=None):
        """Returns the max mtime of the store"""
        if submission:
            return submission.id
        return (store_data or self.store_data)["last_submission"]

    def set_check_data(self, store_data=None):
        checks = {}
        existing_checks = self.model.check_data.values_list(
            "category", "name", "count")
        for category, name, count in existing_checks:
            checks[category] = checks.get("category", {})
            checks[category][name] = count
        to_update = []
        to_add = []
        to_delete = []
        for check in store_data["checks"]:
            category = check["category"]
            name = check["name"]
            count = check["count"]
            check_exists = (
                checks.get(category)
                and checks[category].get(name))
            if not check_exists:
                to_add.append(check)
                continue
            elif checks[category][name] != count:
                to_update.append(check)
            del checks[category][name]
            if not len(checks[category]):
                del checks[category]
        for category, info in checks.items():
            for name in info.keys():
                to_delete.append((category, name))
        new_checks = []
        for check in to_add:
            new_checks.append(
                self.check_data_field.related_model(
                    **{self.related_name: self.model,
                       "category": check["category"],
                       "name": check["name"],
                       "count": check["count"]}))
        if new_checks:
            self.model.check_data.bulk_create(new_checks)

    def set_last_created_unit(self, unit, store_data):
        """Sets the last_created_unit. If the unit is provided that one is used
        else its calculated. Returns True if the data was changed
        """
        newunit = unit and unit.pk or store_data["last_created_unit"]
        if self.data.last_created_unit_id != newunit:
            self.data.last_created_unit_id = newunit
            return True
        return False

    def set_last_updated_unit(self, unit, store_data):
        """Sets the last_updated_unit. If the unit is provided that one is used
        else its calculated. Returns True if the data was changed
        """
        newunit = unit and unit.pk or store_data["last_updated_unit"]
        if self.data.last_updated_unit_id != newunit:
            self.data.last_updated_unit_id = newunit
            return True
        return False

    def set_max_unit_mtime(self, unit=None, store_data=None):
        """Returns the max mtime of the store"""
        mtime = self.get_max_unit_mtime(unit, store_data)
        if self.data.max_unit_mtime != mtime:
            self.data.max_unit_mtime = mtime
            return True
        return False

    def set_max_unit_revision(self, unit=None, store_data=None):
        """Returns the max revision of the store"""
        revision = self.get_max_unit_revision(unit, store_data) or 0
        if self.data.max_unit_revision != revision:
            self.data.max_unit_revision = revision
            return True
        return False

    def set_last_submission(self, submission, store_data=None):
        """Sets the last_submission. If the submission is provided that one is used
        else its calculated. Returns True if the data was changed
        """
        new_submission = self.get_last_submission(submission, store_data)
        if self.data.last_submission_id != new_submission:
            self.data.last_submission_id = new_submission
            return True
        return False

    def set_critical_check_count(self, store_data):
        critical_checks = store_data.get("critical_checks")
        if critical_checks is None and store_data.get("checks"):
            critical_checks = sum(
                check["count"]
                for check
                in store_data["checks"]
                if check["category"] == Category.CRITICAL)
        else:
            critical_checks = 0
        if self.data.critical_checks != critical_checks:
            self.data.critical_checks = critical_checks
            return True
        return False

    def set_fuzzy_wordcount(self, store_data):
        fuzzy_words = store_data["fuzzy_words"] or 0
        if self.data.fuzzy_words != fuzzy_words:
            self.data.fuzzy_words = fuzzy_words
            return True
        return False

    def set_suggestion_count(self, store_data):
        pending_suggestions = store_data["pending_suggestions"] or 0
        if self.data.pending_suggestions != pending_suggestions:
            self.data.pending_suggestions = pending_suggestions
            return True
        return False

    def set_total_wordcount(self, store_data):
        total_words = store_data["total_words"] or 0
        if self.data.total_words != total_words:
            self.data.total_words = total_words
            return True
        return False

    def set_translated_wordcount(self, store_data):
        translated_words = store_data["translated_words"] or 0
        if self.data.translated_words != translated_words:
            self.data.translated_words = translated_words
            return True
        return False

    @property
    def data_field(self):
        # one2one field
        return self.model._meta.get_field("data")

    @property
    def check_data_field(self):
        return self.model._meta.get_field("check_data")

    def update(self, created_unit=None, updated_unit=None, submission=None):
        store_data = self.store_data
        data_changed = False
        # set unit creation info
        if self.set_last_created_unit(created_unit, store_data):
            data_changed = True
        # set the last update info
        if self.set_last_updated_unit(updated_unit, store_data):
            data_changed = True
        if self.set_max_unit_mtime(updated_unit, store_data):
            data_changed = True
        if self.set_max_unit_revision(updated_unit, store_data):
            data_changed = True
        # set the last submission
        if self.set_last_submission(submission, store_data):
            data_changed = True
        # set the checks
        self.set_check_data(store_data)
        if self.set_critical_check_count(store_data):
            data_changed = True
        # set wordcounts
        if self.set_total_wordcount(store_data):
            data_changed = True
        if self.set_translated_wordcount(store_data):
            data_changed = True
        if self.set_fuzzy_wordcount(store_data):
            data_changed = True
        if self.set_suggestion_count(store_data):
            data_changed = True
        if data_changed:
            self.data.save()


class RelatedStoresDataUpdater(DataUpdater):

    @property
    def store_data(self):
        store_data = self.store_data_qs.aggregate(
            revision=models.Max("max_unit_revision"),
            mtime=models.Max("max_unit_mtime"),
            last_update_revision=Max("last_updated_unit__revision"),
            pending_suggestions=models.Sum("pending_suggestions"),
            total_words=models.Sum("total_words"),
            fuzzy_words=models.Sum("fuzzy_words"),
            translated_words=models.Sum("translated_words"),
            last_created_unit=models.Max("last_created_unit"),
            last_submission=models.Max("last_submission"),
            critical_checks=models.Sum("critical_checks"))
        store_data["checks"] = self.store_check_data_qs.values(
            "category", "name").annotate(count=Sum("count"))
        if not store_data["last_update_revision"]:
            store_data["last_updated_unit"] = None
            return store_data
        units_at_revision = self.store_data_qs.filter(
            last_updated_unit__revision=store_data["last_update_revision"])
        store_data["last_updated_unit"] = (
            units_at_revision.order_by("-last_updated_unit__mtime",
                                       "-last_updated_unit_id")
                             .values_list("last_updated_unit_id",
                                          flat=True).first())
        return store_data


class StoreDataUpdater(DataUpdater):

    related_name = "store"

    @property
    def store(self):
        return self.model

    @property
    def units(self):
        """Non-obsolete units in this Store"""
        return self.store.unit_set.filter(state__gt=OBSOLETE)

    @property
    def store_data(self):
        store_data = self.store.unit_set.aggregate(
            max_revision=Max("revision"),
            max_mtime=models.Max("mtime"),
            last_creation_time=Max(
                Case(
                    When(Q(state__gt=OBSOLETE)
                         & Q(revision__isnull=False),
                         then="creation_time"))),
            last_update_revision=Max(
                Case(
                    When(Q(state__gt=OBSOLETE)
                         & Q(revision__isnull=False),
                         then="revision"))),
            total_words=models.Sum(
                Case(
                    When(Q(state__gt=OBSOLETE)
                         & Q(source_wordcount__gt=0),
                         then="source_wordcount"))),
            translated_words=models.Sum(
                Case(
                    When(Q(state=TRANSLATED)
                         & Q(source_wordcount__gt=0),
                         then="source_wordcount"))),
            fuzzy_words=models.Sum(
                Case(
                    When(Q(state=FUZZY)
                         & Q(source_wordcount__gt=0),
                         then="source_wordcount"))))
        units = self.store.unit_set.filter(state__gt=OBSOLETE)
        store_data["last_created_unit"] = (
            units.filter(creation_time=store_data["last_creation_time"])
                 .order_by("-revision", "-id")
                 .values_list("id", flat=True).first())
        last_update_revision = store_data["last_update_revision"] or 0
        store_data["last_updated_unit"] = (
            units.filter(revision=last_update_revision)
                 .order_by("-mtime", "-id")
                 .values_list("id", flat=True).first())
        store_data.update(
            dict(pending_suggestions=self.suggestion_count,
                 last_submission=self.last_submission))
        store_data["revision"] = store_data["max_revision"]
        store_data["mtime"] = store_data["max_mtime"]
        store_data["checks"] = self.check_count
        return store_data

    @property
    def check_count(self):
        return (
            QualityCheck.objects.exclude(false_positive=True)
                        .filter(unit__store_id=self.store.id)
                        .filter(unit__state__gt=OBSOLETE)
                        .values("category", "name")
                        .annotate(count=Count("id")))

    @property
    def last_submission(self):
        """Last non-UNIT_CREATE submission for this store"""
        submissions = self.store.submission_set
        try:
            return (
                submissions.exclude(type=SubmissionTypes.UNIT_CREATE)
                           .latest())
        except submissions.model.DoesNotExist:
            return None

    @property
    def suggestion_count(self):
        """Return the count of pending suggetions for the store"""
        return (
            self.units.filter(suggestion__state=SuggestionStates.PENDING)
                      .values_list("suggestion").count())


class TPDataUpdater(RelatedStoresDataUpdater):
    related_name = "tp"

    @property
    def store_data_qs(self):
        return StoreData.objects.filter(
            store__translation_project=self.tool.context)

    @property
    def store_check_data_qs(self):
        return StoreChecksData.objects.filter(
            store__translation_project=self.tool.context)


class DataTool(object):

    def __init__(self, context):
        self.context = context

    @property
    def project_code(self):
        return split_pootle_path(self.context.pootle_path)[1]

    @property
    def dir_path(self):
        return split_pootle_path(self.context.pootle_path)[2]

    @property
    def filename(self):
        path_parts = split_pootle_path(self.context.pootle_path)
        return path_parts[3]

    @property
    def data_model(self):
        return StoreData.objects

    @property
    def updater(self):
        return data_updater.get(self.__class__)(self)

    def get_checks(self, children=False, user=None):
        return {}

    def update(self):
        if self.updater:
            return self.updater.update()

    def get_info_for_sub(self, child, sub):
        return SubmissionProxy(
            sub, prefix="last_submission__").get_submission_info()


class StoreDataTool(DataTool):
    """Sets the stats for a store"""

    @property
    def store(self):
        return self.context

    def get_stats(self, children=False, user=None):
        return self.object_stats

    @property
    def stat_data(self):
        return self.data_model.filter(
            store=self.context).values().first()

    @property
    def object_stats(self):
        mapping = dict(
            total_words="total",
            fuzzy_words="fuzzy",
            translated_words="translated",
            critical_checks="critical",
            pending_suggestions="suggestions")
        stats = {
            mapping.get(k, k): v
            for k, v
            in self.stat_data.items()}
        stats["lastaction"] = None
        stats["lastupdated"] = None
        return stats


class RelatedStoresDataTool(DataTool):
    group_by = (
        "store__pootle_path",
        "last_updated_unit")
    max_fields = (
        "last_submission__pk", )
    sum_fields = SUM_FIELDS
    submission_fields = (
        ("pk", )
        + SubmissionProxy.info_fields)

    @property
    def object_stats(self):
        stats = {
            k[:-5]: v
            for k, v
            in self.stat_data.aggregate(*self.aggregate_sum_fields).items()}
        mapping = dict(
            total_words="total",
            fuzzy_words="fuzzy",
            translated_words="translated",
            critical_checks="critical",
            pending_suggestions="suggestions")
        stats = {
            mapping.get(k, k): v
            for k, v
            in stats.items()}
        stats["lastaction"] = None
        stats["lastupdated"] = None
        stats["suggestions"] = None
        return stats

    @property
    def aggregate_sum_fields(self):
        return list(
            models.Sum(f)
            for f
            in self.sum_fields)

    @property
    def aggregate_max_fields(self):
        return list(
            models.Max(f)
            for f
            in self.max_fields)

    @property
    def child_stats_qs(self):
        return (
            self.stat_data.values(*self.group_by)
                          .annotate(*(self.aggregate_sum_fields
                                      + self.aggregate_max_fields)))

    @property
    def children_stats(self):
        children = {}
        for child in self.child_stats_qs.iterator():
            self.get_child_stats(children, child)
        self.add_submission_info(children)
        return children

    def get_stats(self, children=False, user=None):
        if not children:
            return self.object_stats
        object_stats = {}
        object_stats["children"] = self.children_stats
        kids = object_stats["children"].values()
        mapping = dict(
            total_words="total",
            fuzzy_words="fuzzy",
            translated_words="translated",
            critical_checks="critical",
            pending_suggestions="suggestions")
        for k in self.sum_fields:
            object_stats[k] = sum(child[mapping.get(k, k)] for child in kids)
        for k in self.max_fields:
            object_stats[k] = max(child[mapping.get(k, k)] for child in kids)
        object_stats = {
            mapping.get(k, k): v
            for k, v
            in object_stats.items()}
        return object_stats

    def add_submission_info(self, children):
        subs = self.get_submissions_for_children(children)
        for child in children.values():
            if child["last_submission__pk"]:
                sub = subs[child["last_submission__pk"]]
                self.get_info_for_sub(child, sub)

    def get_submissions_for_children(self, children):
        last_submissions = [
            v["last_submission__pk"]
            for v in children.values()]
        stores_with_subs = (
            self.stat_data.filter(last_submission_id__in=last_submissions))
        subs = stores_with_subs.values(
            *["last_submission__%s" % field
              for field
              in self.submission_fields])
        return {sub["last_submission__pk"]: sub for sub in subs}

    def get_root(self, child):
        return child[self.group_by[0]]

    def get_child_stats(self, children, child):
        root = self.get_root(child)
        mapping = dict(
            total_words="total",
            fuzzy_words="fuzzy",
            translated_words="translated",
            critical_checks="critical",
            pending_suggestions="suggestions")
        if root not in children:
            children[root] = dict(
                critical=0,
                total=0,
                fuzzy=0,
                translated=0)
        for k in self.sum_fields:
            children[root][mapping.get(k, k)] += child["%s__sum" % k]
        for k in self.max_fields:
            update_max = (
                mapping.get(k, k) not in children[root]
                or (child["%s__max" % k]
                    and (child["%s__max" % k]
                         > children[root][mapping.get(k, k)])))
            if update_max:
                children[root][mapping.get(k, k)] = child["%s__max" % k]
        return root


class TPDataTool(RelatedStoresDataTool):
    """Retrieves aggregate stats for a TP"""

    # TODO: use tp stats table

    @property
    def data_model(self):
        return StoreData.objects

    def get_root(self, child):
        remainder = child["store__pootle_path"].replace(
            "%s%s" % (self.context.pootle_path, self.dir_path), "")
        return remainder.split("/")[0]

    @property
    def stat_data(self):
        return self.data_model.filter(
            store__translation_project=self.context)


class DirectoryDataTool(RelatedStoresDataTool):
    """Retrieves aggregate stats for a Directory"""

    group_by = ("store__parent__pootle_path", )

    @property
    def stat_data(self):
        return (
            self.data_model.filter(
                store__translation_project=self.context.translation_project,
                store__pootle_path__startswith=self.context.pootle_path))

    def get_root(self, child):
        return (
            child["store__parent__pootle_path"].replace(
                self.context.pootle_path, "").split("/")[0])

    @property
    def children_stats(self):
        children = {}
        for child in self.child_stats_qs.iterator():
            self.get_child_stats(children, child)
        child_stores = self.data_model.filter(store__parent=self.context).values(
            *("store__name", "last_submission__pk") + self.sum_fields)
        for child in child_stores:
            store_name = child.pop("store__name")
            mapping = dict(
                total_words="total",
                fuzzy_words="fuzzy",
                translated_words="translated",
                critical_checks="critical",
                pending_suggestions="suggestions")
            child = {
                mapping.get(k, k): v
                for k, v
                in child.items()}
            children[store_name] = child
        self.add_submission_info(children)
        return children

    @property
    def child_stats_qs(self):
        return super(
            DirectoryDataTool,
            self).child_stats_qs.exclude(store__parent=self.context)


class ProjectDataTool(RelatedStoresDataTool):
    """Retrieves aggregate stats for a Project"""

    group_by = (
        "store__translation_project__language__code",
        "store__translation_project__project__code")

    @property
    def stat_data(self):
        return self.data_model.filter(
            store__translation_project__project=self.context)

    def get_root(self, child):
        return "-".join(child[field] for field in self.group_by)


class ProjectResourceDataTool(RelatedStoresDataTool):
    group_by = ("store__translation_project__language__code", )

    @property
    def stat_data(self):
        project_path = (
            "/%s/%s%s"
            % (self.project_code,
               self.dir_path,
               self.filename))
        regex = r"^/[^/]*%s" % project_path
        data_model = self.data_model.filter(
            store__translation_project__project__code=self.project_code)
        return (
            data_model.filter(store__pootle_path__contains=project_path)
                      .filter(store__pootle_path__regex=regex))


class ProjectSetDataTool(RelatedStoresDataTool):
    group_by = ("store__translation_project__project", )

    @property
    def stat_data(self):
        return self.data_model.all()


class LanguageDataTool(RelatedStoresDataTool):
    """Retrieves aggregate stats for a Language"""

    group_by = (
        "store__translation_project__language__code",
        "store__translation_project__project__code")

    @property
    def stat_data(self):
        return self.data_model.filter(
            store__translation_project__language=self.context)

    def get_root(self, child):
        return "-".join(child[field] for field in self.group_by)
