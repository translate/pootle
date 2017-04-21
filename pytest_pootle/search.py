# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby

from django.db.models import Max
from django.urls import resolve

from pootle.core.dateparse import parse_datetime
from pootle.core.url_helpers import split_pootle_path
from pootle_checks.utils import get_category_id
from pootle_misc.util import get_date_interval
from pootle_store.constants import ALLOWED_SORTS, SIMPLY_SORTED
from pootle_store.models import Unit
from pootle_store.unit.filters import UnitSearchFilter, UnitTextSearch
from pootle_store.unit.results import GroupedResults, StoreResults


def get_max_and_order_fields(sort_by):
    if sort_by[0] == '-':
        max_field = sort_by[1:]
        sort_order = '-sort_by_field'
    else:
        max_field = sort_by
        sort_order = 'sort_by_field'

    return max_field, sort_order


def calculate_search_results(kwargs, user):
    pootle_path = kwargs["pootle_path"]
    category = kwargs.get("category")
    checks = kwargs.get("checks")
    offset = kwargs.get("offset", 0)
    limit = kwargs.get("count", 9)
    modified_since = kwargs.get("modified-since")
    month = kwargs.get("month")
    search = kwargs.get("search")
    sfields = kwargs.get("sfields")
    soptions = kwargs.get("soptions", [])
    sort = kwargs.get("sort", None)
    vfolder = kwargs.get("vfolder", None)
    language_code, project_code, dir_path_, filename = (
        split_pootle_path(kwargs["pootle_path"]))
    uids = [
        int(x)
        for x
        in kwargs.get("uids", "").split(",")
        if x]
    unit_filter = kwargs.get("filter")

    if modified_since:
        modified_since = parse_datetime(modified_since)
    if month:
        month = get_date_interval(month)

    path_kwargs = {
        k: v
        for k, v
        in resolve(pootle_path).kwargs.items()
        if k in [
            "language_code",
            "project_code",
            "dir_path",
            "filename"]}
    qs = (
        Unit.objects.get_translatable(user=user, **path_kwargs)
                    .order_by("store", "index"))
    if vfolder is not None:
        qs = qs.filter(store__vfolders=vfolder)
    # if "filter" is present in request vars...
    if unit_filter:
        # filter the results accordingly
        qs = UnitSearchFilter().filter(
            qs,
            unit_filter,
            user=user,
            checks=checks,
            category=get_category_id(category))
        # filter by modified
        if modified_since:
            qs = qs.filter(change__submitted_on__gt=modified_since).distinct()
        if month is not None:
            qs = qs.filter(
                change__submitted_on__gte=month[0],
                change__submitted_on__lte=month[1]).distinct()
        # sort results
        if unit_filter in ["my-suggestions", "user-suggestions"]:
            sort_on = "suggestions"
        elif unit_filter in ["my-submissions", "user-submissions"]:
            sort_on = "submissions"
        else:
            sort_on = "units"
        sort_by = ALLOWED_SORTS[sort_on].get(sort, None)
        if sort_by is not None:
            # filtered sort
            if sort_on in SIMPLY_SORTED:
                qs = qs.order_by(sort_by, "store__pootle_path", "index")
            else:
                max_field, sort_order = get_max_and_order_fields(sort_by)
                qs = (
                    qs.annotate(sort_by_field=Max(max_field))
                      .order_by(sort_order, "store__pootle_path", "index"))
    # text search
    if search and sfields:
        qs = UnitTextSearch(qs).search(
            search,
            [sfields],
            "exact" in soptions)

    find_unit = (
        not offset
        and language_code
        and project_code
        and filename
        and uids)
    start = offset
    total = qs.count()
    if find_unit:
            # find the uid in the Store
        uid_list = list(qs.values_list("pk", flat=True))
        unit_index = uid_list.index(uids[0])
        start = int(unit_index / (2 * limit)) * (2 * limit)
    end = min(start + (2 * limit), total)

    unit_groups = []
    units_by_path = groupby(
        qs.values(*GroupedResults.select_fields)[start:end],
        lambda x: x["store__pootle_path"])
    for pootle_path, units in units_by_path:
        unit_groups.append(
            {pootle_path: StoreResults(units).data})

    total = qs.count()
    return total, start, min(end, total), unit_groups
