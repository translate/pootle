# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.filters.decorators import Category

from django.db import models
from django.db.models import Case, Count, Max, Q, When

from pootle.core.bulk import BulkCRUD
from pootle.core.signals import update_data, update_revisions
from pootle_statistics.models import Submission
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED
from pootle_store.models import QualityCheck

from .models import StoreChecksData, StoreData
from .utils import DataTool, DataUpdater


class StoreDataCRUD(BulkCRUD):
    model = StoreData

    def update_tps_and_revisions(self, stores):
        tps = {}
        for store in stores:
            if store.translation_project_id not in tps:
                tps[store.translation_project_id] = store.translation_project
            update_revisions.send(
                store.__class__,
                instance=store,
                keys=["stats", "checks"])
        for tp in tps.values():
            update_data.send(
                tp.__class__,
                instance=tp)

    def post_create(self, instance=None, objects=None, pre=None, result=None):
        if objects:
            self.update_tps_and_revisions(set(result.store for data in objects))

    def post_update(self, instance=None, objects=None, pre=None, result=None):
        if objects:
            self.update_tps_and_revisions(set(data.store for data in objects))


class StoreChecksDataCRUD(BulkCRUD):
    model = StoreChecksData


class StoreDataTool(DataTool):
    """Sets the stats for a store"""

    @property
    def object_stats(self):
        stats = {
            v: getattr(self.context.data, k)
            for k, v in self.stats_mapping.items()}
        stats["children"] = {}
        stats["last_submission"] = (
            self.context.data.last_submission
            and self.context.data.last_submission.get_submission_info()
            or None)
        stats["last_created_unit"] = (
            self.context.data.last_created_unit
            and self.context.data.last_created_unit.get_last_created_unit_info()
            or None)
        return stats

    def get_checks(self, **kwargs):
        return dict(self.context.check_data.values_list("name", "count"))


class StoreDataUpdater(DataUpdater):

    related_name = "store"
    aggregate_fields = (
        "words",
        "max_unit_revision",
        "max_unit_mtime")

    @property
    def store(self):
        return self.model

    @property
    def store_data_qs(self):
        return self.store.unit_set

    @property
    def units(self):
        """Non-obsolete units in this Store"""
        return self.store_data_qs.filter(state__gt=OBSOLETE)

    @property
    def aggregate_words(self):
        return dict(
            total_words=models.Sum(
                Case(
                    When(Q(state__gt=OBSOLETE)
                         & Q(unit_source__source_wordcount__gt=0),
                         then="unit_source__source_wordcount"),
                    default=0)),
            translated_words=models.Sum(
                Case(
                    When(Q(state=TRANSLATED)
                         & Q(unit_source__source_wordcount__gt=0),
                         then="unit_source__source_wordcount"),
                    default=0)),
            fuzzy_words=models.Sum(
                Case(
                    When(Q(state=FUZZY)
                         & Q(unit_source__source_wordcount__gt=0),
                         then="unit_source__source_wordcount"),
                    default=0)))

    @property
    def aggregate_max_unit_revision(self):
        return dict(max_unit_revision=Max("revision"))

    @property
    def aggregate_max_unit_mtime(self):
        return dict(max_unit_mtime=Max("mtime"))

    def get_last_created_unit(self, **kwargs):
        order_by = ("-creation_time", "-revision", "-id")
        units = self.store.unit_set.filter(
            state__gt=OBSOLETE, creation_time__isnull=False)
        return units.order_by(*order_by).values_list("id", flat=True).first()

    def get_critical_checks(self, **kwargs):
        return sum(
            check["count"]
            for check
            in kwargs["data"]["checks"]
            if check["category"] == Category.CRITICAL)

    def get_checks(self, **kwargs):
        if self.store.obsolete:
            return []
        return (
            QualityCheck.objects.exclude(false_positive=True)
                        .filter(unit__store_id=self.store.id)
                        .filter(unit__state__gt=OBSOLETE)
                        .values("category", "name")
                        .annotate(count=Count("id")))

    def get_last_submission(self, **kwargs):
        """Last submission for this store"""
        submissions = Submission.objects.filter(unit__store_id=self.store.id)
        try:
            return (
                submissions.values_list("pk", flat=True)
                           .latest())
        except submissions.model.DoesNotExist:
            return None

    def get_pending_suggestions(self, **kwargs):
        """Return the count of pending suggetions for the store"""
        return (
            self.units.filter(suggestion__state__name="pending")
                      .values_list("suggestion").count())

    def get_store_data(self, **kwargs):
        if self.store.obsolete:
            kwargs["fields"] = (
                "checks",
                "last_created_unit",
                "max_unit_mtime",
                "max_unit_revision",
                "last_submission")

        data = super(StoreDataUpdater, self).get_store_data(**kwargs)

        if self.store.obsolete:
            data.update(self.aggregate_defaults)

        return data
