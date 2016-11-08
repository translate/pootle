# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models import Max, Sum
from django.db.models.functions import Coalesce

from pootle.core.delegate import revision
from pootle_data.models import StoreChecksData, StoreData

from .utils import DataUpdater, RelatedStoresDataTool


class TPDataUpdater(DataUpdater):
    related_name = "tp"
    aggregate_fields = (
        "words",
        "critical_checks",
        "last_created_unit",
        "last_submission",
        "max_unit_revision",
        "max_unit_mtime",
        "pending_suggestions")

    @property
    def aggregate_critical_checks(self):
        return dict(
            critical_checks=Coalesce(
                Sum("critical_checks"), 0))

    @property
    def aggregate_last_created_unit(self):
        return dict(last_created_unit=Max("last_created_unit"))

    @property
    def aggregate_last_submission(self):
        return dict(last_submission=Max("last_submission"))

    @property
    def aggregate_max_unit_mtime(self):
        return dict(max_unit_mtime=Max("max_unit_mtime"))

    @property
    def aggregate_max_unit_revision(self):
        return dict(
            max_unit_revision=Coalesce(
                Max("max_unit_revision"), 0))

    @property
    def aggregate_pending_suggestions(self):
        return dict(
            pending_suggestions=Coalesce(
                Sum("pending_suggestions"), 0))

    @property
    def aggregate_words(self):
        return dict(
            total_words=Coalesce(Sum("total_words"), 0),
            fuzzy_words=Coalesce(Sum("fuzzy_words"), 0),
            translated_words=Coalesce(Sum("translated_words"), 0))

    @property
    def store_data_qs(self):
        return StoreData.objects.filter(
            store__translation_project_id=self.tool.context.id)

    @property
    def store_check_data_qs(self):
        return StoreChecksData.objects.filter(
            store__translation_project_id=self.tool.context.id)

    def get_last_created_unit(self, **kwargs):
        return self.get_aggregate_data(
            fields=["last_created_unit"])["last_created_unit"]

    def get_last_submission(self, **kwargs):
        return self.get_aggregate_data(
            fields=["last_submission"])["last_submission"]

    def get_pending_suggestions(self, **kwargs):
        return self.get_aggregate_data(
            fields=["pending_suggestions"])["pending_suggestions"]

    def get_checks(self, **kwargs):
        return self.store_check_data_qs.values(
            "category", "name").annotate(count=Sum("count"))


class TPDataTool(RelatedStoresDataTool):
    """Retrieves aggregate stats for a TP"""

    group_by = ("store__tp_path", )
    cache_key_name = "directory"

    def get_root_child_path(self, child):
        remainder = child["store__tp_path"].replace(
            "/%s" % (self.dir_path), "", 1)
        return remainder.split("/")[0]

    @property
    def rev_cache_key(self):
        return revision.get(self.context.directory.__class__)(
            self.context.directory).get(key="stats")

    @property
    def context_name(self):
        return self.context.pootle_path.strip("/").replace("/", ".")

    @property
    def object_stats(self):
        stats = {
            v: getattr(self.context.data, k)
            for k, v in self.stats_mapping.items()}
        return stats

    @property
    def stat_data(self):
        return self.data_model.filter(
            store__translation_project=self.context)

    def get_lastaction(self, **kwargs):
        return (
            self.context.data.last_submission
            and self.context.data.last_submission.get_submission_info()
            or None)

    def get_lastupdated(self, **kwargs):
        return (
            self.context.data.last_created_unit
            and self.context.data.last_created_unit.get_last_updated_info()
            or None)

    def aggregate_children(self, stats):
        agg = dict(total=0, fuzzy=0, translated=0, critical=0, suggestions=0)
        for child in stats["children"].values():
            for k in agg.keys():
                agg[k] += child[k]
        stats.update(agg)
        return stats

    def get_checks(self, **kwargs):
        return dict(self.context.check_data.values_list("name", "count"))

    @property
    def max_unit_revision(self):
        return self.context.data.max_unit_revision
