# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import Counter

from translate.filters.decorators import Category

from django.db import models
from django.db.models import Case, Count, Max, Q, When
from django.utils.functional import cached_property

from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from pootle_store.models import QualityCheck
from pootle_store.util import SuggestionStates

from .utils import DataTool, DataUpdater


class StoreDataTool(DataTool):
    """Sets the stats for a store"""

    @property
    def store(self):
        return self.context

    @property
    def units(self):
        """Non-obsolete units in this Store"""
        return self.store.unit_set.live()

    @cached_property
    def last_created_unit(self):
        """Last unit created in this Store"""
        return (
            self.units.exclude(creation_time__isnull=True)
                      .order_by('-creation_time', '-revision').first())

    @cached_property
    def last_updated_unit(self):
        """Last unit updated in this Store"""
        return self.units.order_by('-revision', '-mtime').first()

    @cached_property
    def last_submission(self):
        """Last non-UNIT_CREATE submission for this store"""
        return (
            self.store.submission_set.exclude(type=SubmissionTypes.UNIT_CREATE)
                                     .latest())

    @cached_property
    def wordcount(self):
        """Returns a dictionary of translated,fuzzy,total words for store"""
        # XXX: `order_by()` here is important as it removes the default
        # ordering for units. See #3897 for reference.
        wordcount = (
            self.units.order_by().values_list('state')
                      .annotate(wordcount=models.Sum('source_wordcount')))
        result = dict(total=0, translated=0, fuzzy=0)
        for state, wordcount in wordcount.iterator():
            result['total'] += wordcount
            if state == TRANSLATED:
                result['translated'] = wordcount
            elif state == FUZZY:
                result['fuzzy'] = wordcount
        return result

    @property
    def suggestion_count(self):
        """Return the count of pending suggetions for the store"""
        return (
            self.units.filter(suggestion__state=SuggestionStates.PENDING)
                      .values_list("suggestion").count())

    def get_max_unit_revision(self, unit=None):
        """Returns the max revision of the store"""
        return (
            unit.revision
            if unit is not None
            else self.store.unit_set.aggregate(
                result=Max("revision"))['result'])

    @cached_property
    def checks(self):
        """Dictionary of checks and critical check count for the store"""
        qc_fields = (
            "qualitycheck__category",
            "qualitycheck__name",
            "qualitycheck__false_positive")
        qc_qs = (
            self.store.unit_set.filter(state__gt=UNTRANSLATED)
                               .filter(qualitycheck__isnull=False)
                               .values_list(*qc_fields)
                               .iterator())
        result = dict(critical_count=0, checks={})
        for (category, name, muted), count in Counter(qc_qs).items():
            if muted:
                continue
            if category == Category.CRITICAL:
                result["critical_count"] += count
            result["checks"][name] = count
        return result


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
                         & Q(source_wordcount__gt=0),
                         then="source_wordcount"),
                    default=0)),
            translated_words=models.Sum(
                Case(
                    When(Q(state=TRANSLATED)
                         & Q(source_wordcount__gt=0),
                         then="source_wordcount"),
                    default=0)),
            fuzzy_words=models.Sum(
                Case(
                    When(Q(state=FUZZY)
                         & Q(source_wordcount__gt=0),
                         then="source_wordcount"),
                    default=0)))

    @property
    def aggregate_max_unit_revision(self):
        return dict(max_unit_revision=Max("revision"))

    @property
    def aggregate_max_unit_mtime(self):
        return dict(max_unit_mtime=Max("mtime"))

    def get_last_created_unit(self, **kwargs):
        order_by = ("-creation_time", "-revision", "-id")
        units = self.store.units.filter(creation_time__isnull=False)
        return units.order_by(*order_by).values_list("id", flat=True).first()

    def get_critical_checks(self, **kwargs):
        return sum(
            check["count"]
            for check
            in kwargs["data"]["checks"]
            if check["category"] == Category.CRITICAL)

    def get_checks(self, **kwargs):
        return (
            QualityCheck.objects.exclude(false_positive=True)
                        .filter(unit__store_id=self.store.id)
                        .filter(unit__state__gt=OBSOLETE)
                        .values("category", "name")
                        .annotate(count=Count("id")))

    def get_last_submission(self, **kwargs):
        """Last non-UNIT_CREATE submission for this store"""
        submissions = self.store.submission_set
        try:
            return (
                submissions.exclude(type=SubmissionTypes.UNIT_CREATE)
                           .values_list("pk", flat=True)
                           .latest())
        except submissions.model.DoesNotExist:
            return None

    def get_pending_suggestions(self, **kwargs):
        """Return the count of pending suggetions for the store"""
        return (
            self.units.filter(suggestion__state=SuggestionStates.PENDING)
                      .values_list("suggestion").count())
