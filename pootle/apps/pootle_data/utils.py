# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle.core.delegate import data_updater


SUM_FIELDS = (
    "critical_checks",
    "total_words",
    "fuzzy_words",
    "translated_words")


class DataTool(object):

    def __init__(self, context):
        self.context = context

    @property
    def children_stats(self):
        return {}

    @property
    def object_stats(self):
        return {}

    @property
    def updater(self):
        updater = data_updater.get(self.__class__)
        if updater:
            return updater(self)

    def get_checks(self):
        return {}

    def get_stats(self, include_children=True, user=None):
        stats = self.object_stats
        if include_children:
            stats["children"] = {}
        return stats

    def update(self, **kwargs):
        if self.updater:
            return self.updater.update(**kwargs)


class DataUpdater(object):
    """Set data for an object"""

    sum_fields = SUM_FIELDS
    aggregate_fields = ()
    update_fields = (
        "checks",
        "critical_checks",
        "last_created_unit",
        "max_unit_mtime",
        "max_unit_revision",
        "last_submission",
        "translated_words",
        "total_words",
        "fuzzy_words",
        "pending_suggestions")
    fk_fields = (
        "last_created_unit",
        "last_submission")
    aggregate_defaults = dict(
        total_words=0,
        fuzzy_words=0,
        translated_words=0,
        critical_checks=0,
        pending_suggestions=0)

    def __init__(self, tool):
        self.tool = tool

    @property
    def check_data_field(self):
        return self.model._meta.get_field("check_data")

    @cached_property
    def data(self):
        try:
            return self.model.data
        except self.data_field.related_model.DoesNotExist:
            return self.data_field.related_model.objects.create(
                **{self.related_name: self.model})

    @property
    def data_field(self):
        # one2one field
        return self.model._meta.get_field("data")

    @property
    def model(self):
        return self.tool.context

    def filter_aggregate_fields(self, fields_to_get):
        aggregate_fields = list(self.aggregate_fields)
        for f in ["max_unit_revision", "max_unit_mtime"]:
            if f not in fields_to_get:
                aggregate_fields.remove(f)
        return aggregate_fields

    def filter_fields(self, **kwargs):
        if "fields" in kwargs:
            return list(
                set(kwargs["fields"])
                & set(self.update_fields))
        return self.update_fields

    def get_aggregate_data(self, fields):
        fields = self.filter_aggregate_fields(fields)
        if not fields:
            return {}
        data = self.store_data_qs.aggregate(
            **self.get_aggregation(fields))
        for k, v in data.items():
            if v is None and k in self.aggregate_defaults:
                data[k] = self.aggregate_defaults[k]
        return data

    def get_aggregation(self, fields):
        agg_fields = self.aggregate_fields
        agg = {}
        if fields:
            agg_fields = [
                f for f
                in fields
                if f in fields]
        for field in agg_fields:
            agg.update(getattr(self, "aggregate_%s" % field))
        return agg

    def get_fields(self, fields_to_get):
        field_data = {}
        kwargs = self.get_aggregate_data(fields_to_get)
        kwargs["data"] = {}
        for k in fields_to_get:
            field_data[k] = (
                kwargs[k]
                if k in kwargs
                else getattr(self, "get_%s" % k)(**kwargs))
            kwargs["data"].update(field_data)
        return field_data

    def get_max_unit_mtime(self, **kwargs):
        return self.get_aggregate_data(
            fields=["max_unit_mtime"])["max_unit_mtime"]

    def get_max_unit_revision(self, **kwargs):
        return self.get_aggregate_data(
            fields=["max_unit_revision"])["max_unit_revision"]

    def get_store_data(self, **kwargs):
        data = self.get_fields(self.filter_fields(**kwargs))
        data.update(kwargs)
        return data

    def set_check_data(self, store_data=None):
        checks = {}
        existing_checks = self.model.check_data.values_list(
            "pk", "category", "name", "count")
        for pk, category, name, count in existing_checks:
            checks[(category, name)] = (pk, count)
        to_update = []
        to_add = []
        for check in store_data["checks"]:
            category = check["category"]
            name = check["name"]
            count = check["count"]
            check_exists = (
                checks.get((category, name)))
            if not check_exists:
                to_add.append(check)
                continue
            elif checks[(category, name)][1] != count:
                to_update.append((checks[(category, name)][0], count))
            del checks[(category, name)]
        for category, name in checks.keys():
            # bulk delete?
            self.model.check_data.filter(category=category, name=name).delete()
        for pk, count in to_update:
            # bulk update?
            check = self.model.check_data.get(pk=pk)
            check.count = count
            check.save()
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

    def set_data(self, k, v):
        k = (k in self.fk_fields
             and "%s_id" % k
             or k)
        if not hasattr(self.data, k):
            return
        existing_value = getattr(self.data, k)
        if existing_value is None or existing_value != v:
            setattr(self.data, k, v)
            return True
        return False

    def update(self, **kwargs):
        store_data = self.get_store_data(**kwargs)
        data_changed = any(
            [self.set_data(k, store_data[k])
             for k in self.filter_fields(**kwargs)])
        # set the checks
        if "checks" in store_data:
            self.set_check_data(store_data)
        if data_changed:
            self.save_data()

    def save_data(self):
        self.data.save()
        # this ensures that any calling code gets the
        # correct revision. It doesnt refresh the last
        # created/updated fks tho
        self.model.data = self.data
