# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models import Max
from django.utils.functional import cached_property

from pootle_store.constants import SIMPLY_SORTED
from pootle_store.models import Unit
from pootle_store.unit.filters import UnitSearchFilter, UnitTextSearch


class DBSearchBackend(object):

    default_chunk_size = None
    default_order = "store__pootle_path", "index"
    select_related = (
        'store__translation_project__project',
        'store__translation_project__language')

    def __init__(self, request_user, **kwargs):
        self.kwargs = kwargs
        self.request_user = request_user

    @property
    def chunk_size(self):
        return self.kwargs.get(
            'count',
            self.default_chunk_size)

    @property
    def project_code(self):
        return self.kwargs.get("project_code")

    @property
    def language_code(self):
        return self.kwargs.get("language_code")

    @property
    def dir_path(self):
        return self.kwargs.get("dir_path")

    @property
    def filename(self):
        return self.kwargs.get("filename")

    @property
    def unit_filter(self):
        return self.kwargs.get("filter")

    @property
    def offset(self):
        return self.kwargs.get("offset", None)

    @property
    def previous_uids(self):
        return self.kwargs.get("previous_uids", []) or []

    @property
    def sort_by(self):
        return self.kwargs.get("sort_by")

    @property
    def sort_on(self):
        return self.kwargs.get("sort_on")

    @property
    def qs_kwargs(self):
        kwargs = {
            k: getattr(self, k)
            for k in [
                "project_code",
                "language_code",
                "dir_path",
                "filename"]}
        kwargs["user"] = self.request_user
        return kwargs

    @property
    def uids(self):
        return self.kwargs.get("uids", [])

    @property
    def units_qs(self):
        return (
            Unit.objects.get_translatable(**self.qs_kwargs)
                        .order_by(*self.default_order)
                        .select_related(*self.select_related))

    def sort_qs(self, qs):
        if self.unit_filter and self.sort_by is not None:
            sort_by = self.sort_by
            if self.sort_on not in SIMPLY_SORTED:
                # Omit leading `-` sign
                if self.sort_by[0] == '-':
                    max_field = self.sort_by[1:]
                    sort_by = '-sort_by_field'
                else:
                    max_field = self.sort_by
                    sort_by = 'sort_by_field'
                # It's necessary to use `Max()` here because we can't
                # use `distinct()` and `order_by()` at the same time
                qs = qs.annotate(sort_by_field=Max(max_field))
            return qs.order_by(
                sort_by, "store__pootle_path", "index")
        return qs

    def filter_qs(self, qs):
        kwargs = self.kwargs
        category = kwargs['category']
        checks = kwargs['checks']
        exact = 'exact' in kwargs['soptions']
        case = 'case' in kwargs['soptions']
        modified_since = kwargs['modified-since']
        month = kwargs['month']
        search = kwargs['search']
        sfields = kwargs['sfields']
        user = kwargs['user']

        if self.unit_filter:
            qs = UnitSearchFilter().filter(
                qs, self.unit_filter,
                user=user, checks=checks, category=category)

            if modified_since is not None:
                qs = qs.filter(
                    change__submitted_on__gt=modified_since).distinct()

            if month is not None:
                qs = qs.filter(
                    change__submitted_on__gte=month[0],
                    change__submitted_on__lte=month[1]).distinct()

        if sfields and search:
            qs = UnitTextSearch(qs).search(
                search, sfields, exact=exact, case=case)
        return qs

    @cached_property
    def results(self):
        return self.sort_qs(self.filter_qs(self.units_qs))

    def search(self):
        total = self.results.count()
        start = self.offset

        if start > (total + len(self.previous_uids)):
            return total, total, total, self.results.none()

        find_unit = (
            self.language_code
            and self.project_code
            and self.filename
            and self.uids)
        find_next_slice = (
            self.previous_uids
            and self.offset)

        if not find_unit and find_next_slice:
            # if both previous_uids and offset are set then try to ensure
            # that the results we are returning start from the end of previous
            # result set
            _start = start = max(self.offset - len(self.previous_uids), 0)
            end = min(self.offset + (2 * self.chunk_size), total)
            uid_list = self.results[start:end].values_list("pk", flat=True)
            offset = 0
            for i, uid in enumerate(uid_list):
                if uid in self.previous_uids:
                    start = _start + i + 1
                    offset = i + 1
            start = start or 0
            end = min(start + (2 * self.chunk_size), total)
            return (
                total,
                start,
                end,
                uid_list[offset:offset + (2 * self.chunk_size)])
        if find_unit:
            # find the uid in the Store
            uid_list = list(self.results.values_list("pk", flat=True))
            if self.chunk_size and self.uids[0] in uid_list:
                unit_index = uid_list.index(self.uids[0])
                start = (
                    int(unit_index / (2 * self.chunk_size))
                    * (2 * self.chunk_size))
        if self.chunk_size is None:
            return total, 0, total, self.results
        start = start or 0
        end = min(start + (2 * self.chunk_size), total)
        return (
            total,
            start,
            end,
            list(self.results[start:end].values_list("pk", flat=True)))
