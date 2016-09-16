# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models
from django.utils.functional import cached_property

from pootle.core.delegate import data_updater
from pootle.core.url_helpers import split_pootle_path
from pootle_statistics.proxy import SubmissionProxy
from pootle_store.models import Unit

from .models import StoreData


SUM_FIELDS = (
    "critical_checks",
    "total_words",
    "fuzzy_words",
    "translated_words",
    "pending_suggestions")


class DataTool(object):

    stats_mapping = dict(
        total_words="total",
        fuzzy_words="fuzzy",
        translated_words="translated",
        critical_checks="critical",
        pending_suggestions="suggestions")

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


class RelatedStoresDataTool(DataTool):
    group_by = (
        "store__pootle_path", )
    max_fields = (
        "last_submission__pk",
        "last_created_unit__pk")
    sum_fields = SUM_FIELDS
    submission_fields = (
        ("pk", )
        + SubmissionProxy.info_fields)

    @property
    def data_model(self):
        return StoreData.objects

    @property
    def dir_path(self):
        return split_pootle_path(self.context.pootle_path)[2]

    @property
    def object_stats(self):
        stats = {
            k[:-5]: v
            for k, v
            in self.stat_data.aggregate(*self.aggregate_sum_fields).items()}
        stats = {
            self.stats_mapping.get(k, k): v
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
        """Aggregates grouped sum/max fields"""
        return (
            self.stat_data.values(*self.group_by)
                          .annotate(*(self.aggregate_sum_fields
                                      + self.aggregate_max_fields)))

    def aggregate_children(self, stats):
        """For a stats dictionary containing children qs.values, aggregate the
        children to calculate the sum/max for the context
        """
        agg = dict(total=0, fuzzy=0, translated=0, critical=0, suggestions=0)
        lastactionpk = None
        for child in stats["children"].values():
            for k in agg.keys():
                agg[k] += child[k]
            if child["last_submission__pk"] > lastactionpk:
                stats['lastaction'] = child["last_submission"]
                lastactionpk = child["last_submission__pk"]
        stats.update(agg)
        return stats

    @property
    def children_stats(self):
        """For a given object returns stats for each of the objects
        immediate descendants
        """
        children = {}
        for child in self.child_stats_qs.iterator():
            self.add_child_stats(children, child)
        self.add_submission_info(children)
        return children

    def add_submission_info(self, children):
        """For a given qs.values of child stats data, updates the values
        with submission info
        """
        subs = self.get_submissions_for_children(children)
        for child in children.values():
            if child["last_submission__pk"]:
                sub = subs[child["last_submission__pk"]]
                child["last_submission"] = self.get_info_for_sub(sub)

    def get_info_for_sub(self, sub):
        """Uses a SubmissionProxy to turn the member of a qs.values
        into submission_info
        """
        return SubmissionProxy(
            sub, prefix="last_submission__").get_submission_info()

    def get_submissions_for_children(self, children):
        """For a given qs.values of children returns a qs.values
        of related last_submission data
        """
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

    def get_root_child_path(self, child):
        """For a given child returns the label for its root node (ie the parent
        node which is the immediate descendant of the context).
        """
        return child[self.group_by[0]]

    def get_stats(self, include_children=True, user=None):
        """Get stats for an object. If include_children is set it will
        also return stats for each of the immediate descendants.
        """

        if include_children:
            stats = {}
            stats["children"] = self.children_stats
            self.aggregate_children(stats)
        else:
            stats = self.object_stats
        stats["is_dirty"] = False
        stats["lastaction"] = self.get_lastaction(**stats)
        stats["lastupdated"] = self.get_lastupdated(**stats)
        return stats

    def add_child_stats(self, children, child, root=None, use_aggregates=True):
        """For a child member of children qs.values, add the childs stats to aggregate
        stats for the child' root node (ie the parent node which is the immediate
        descendant of the context).
        """
        root = root or self.get_root_child_path(child)
        children[root] = children.get(
            root,
            dict(critical=0,
                 total=0,
                 fuzzy=0,
                 translated=0,
                 suggestions=0))
        for k in self.sum_fields:
            child_k = (
                k if not use_aggregates
                else "%s__sum" % k)
            mapped_k = self.stats_mapping.get(k, k)
            children[root][mapped_k] += child[child_k]
        for k in self.max_fields:
            child_k = (
                k if not use_aggregates
                else "%s__max" % k)
            mapped_k = self.stats_mapping.get(k, k)
            update_max = (
                mapped_k not in children[root]
                or (child[child_k]
                    and (child[child_k] > children[root][mapped_k])))
            if update_max:
                children[root][mapped_k] = child[child_k]
        return root

    def get_lastaction(self, **kwargs):
        return kwargs.get("lastaction")

    def get_lastupdated(self, **kwargs):
        return (
            kwargs.get("lastcreated")
            and Unit.objects.select_related(
                "store").get(pk=kwargs["lastcreated"]).get_last_updated_info()
            or None)
