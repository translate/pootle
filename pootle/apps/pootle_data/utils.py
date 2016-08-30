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
from django.db.models import Max
from django.utils.functional import cached_property

from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import FUZZY, TRANSLATED, UNTRANSLATED
from pootle_store.util import SuggestionStates


class StoreDataTool(object):
    """Sets the stats for a store"""

    def __init__(self, store):
        self.store = store

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
