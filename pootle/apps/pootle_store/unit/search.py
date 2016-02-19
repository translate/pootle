#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property
from django.db.models import Max

from pootle_store.models import Unit
from pootle_store.unit.filters import UnitSearchFilter, UnitTextSearch
from pootle_store.views import SIMPLY_SORTED


class DBSearchBackend(object):

    default_chunk_size = 9
    default_order = "store", "index"
    select_related = (
        'store__translation_project__project',
        'store__translation_project__language')

    def __init__(self, request_user, **kwargs):
        self.kwargs = kwargs
        self.request_user = request_user

    @property
    def chunk_size(self):
        return self.kwargs.get(
            'chunk_size',
            self.default_chunk_size)

    @property
    def initial(self):
        return self.kwargs.get('initial', True)

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
        modified_since = kwargs['modified-since']
        month = kwargs['month']
        search = kwargs['search']
        sfields = kwargs['sfields']
        user = kwargs['user']
        vfolder = kwargs["vfolder"]

        if vfolder is not None:
            qs = qs.filter(vfolders=vfolder)

        if self.unit_filter:
            qs = UnitSearchFilter().filter(
                qs, self.unit_filter,
                user=user, checks=checks, category=category)

            if modified_since is not None:
                qs = qs.filter(
                    submitted_on__gt=modified_since).distinct()

            if month is not None:
                qs = qs.filter(
                    submitted_on__gte=month[0],
                    submitted_on__lte=month[1]).distinct()

        if sfields and search:
            qs = UnitTextSearch(qs).search(
                search, sfields, exact=exact)
        return qs

    @cached_property
    def results(self):
        return self.sort_qs(self.filter_qs(self.units_qs))

    def search(self):
        uid_list = None
        begin = 0
        end = 2 * self.chunk_size
        if self.initial:
            results = self.results
            uid_list = list(results.values_list('id', flat=True))
            if len(self.uids) == 1:
                if self.uids[0] not in uid_list:
                    return [], results.none()
                index = uid_list.index(self.uids[0])
                begin = max(index - self.chunk_size, 0)
                end = min(index + self.chunk_size + 1, len(uid_list))
        elif self.uids:
            results = self.results.filter(id__in=self.uids)
        return uid_list, results[begin:end]
