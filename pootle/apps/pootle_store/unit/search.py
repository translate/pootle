# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import time

from django.utils.functional import cached_property

from .filters import SearchFilter
from .sort import SearchSort
from .group import UnitGroups


logger = logging.getLogger(__name__)


class UnitSearch(object):

    filter_class = SearchFilter
    sort_class = SearchSort
    group_class = UnitGroups

    def __init__(self, request_user, limit=None, **kwa):
        self.request_user = request_user
        self._limit = limit
        self.kwa = kwa

    @cached_property
    def qs(self):
        from pootle_store.models import Unit

        if self.kwa.get("pootle_path", None):
            return Unit.objects.get_for_path(
                self.kwa["pootle_path"],
                self.request_user)
        else:
            return Unit.objects.get_for_user(self.request_user)

    @cached_property
    def limit(self):
        if self._limit:
            return self.kwa.get("count", None)

    @cached_property
    def filtered_qs(self):
        return self.filter_class(self.qs).filter_qs(**self.kwa)

    @cached_property
    def sorted_qs(self):
        return self.sort_class(self.filtered_qs).sort_qs(
            self.kwa.get("sort_on"), self.kwa.get("sort_by"))

    @cached_property
    def sliced_qs(self):
        qs = self.sorted_qs
        if self.unit_index:
            qs = qs[self.unit_index:]
        if self.limit:
            qs = qs[:self.limit]
        return qs

    @cached_property
    def uid_list(self):
        return self.sorted_qs.values("pk", "store__pootle_path").values_list("pk")

    @cached_property
    def unit_index(self):
        pk = self.first_unit['pk']
        for i, unit in enumerate(self.uid_list.iterator()):
            if unit == pk:
                return i

    @cached_property
    def total(self):
        start = time.time()
        total = (
            self.filtered_qs.values_list("id", "store__pootle_path")
                            .values("id").count())
        logger.debug(
            "fetched total (%s) in %s seconds"
            % (total, time.time() - start))
        return total

    @cached_property
    def unit_groups(self):
        start = time.time()
        unit_groups = self.group_class(self.sliced_qs).group_units()
        logger.debug(
            "ran search query in %s seconds"
            % (time.time() - start))
        return unit_groups

    def grouped_search(self):
        total = self.total
        unit_index = self.unit_index
        return {
            "total": total,
            'unitGroups': self.unit_groups,
            "unit_index": unit_index}
