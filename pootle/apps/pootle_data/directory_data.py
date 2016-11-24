# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models import Max

from pootle_translationproject.models import TranslationProject

from .utils import RelatedStoresDataTool


class DirectoryDataTool(RelatedStoresDataTool):
    """Retrieves aggregate stats for a Directory"""

    group_by = ("store__parent__tp_path", )
    cache_key_name = "directory"

    @property
    def context_name(self):
        return self.context.pootle_path

    @property
    def max_unit_revision(self):
        try:
            return self.context.translationproject.data_tool.max_unit_revision
        except TranslationProject.DoesNotExist:
            return self.all_stat_data.aggregate(rev=Max("max_unit_revision"))["rev"]

    def filter_data(self, qs):
        return (
            qs.filter(
                store__translation_project=self.context.translation_project,
                store__parent__tp_path__startswith=self.context.tp_path)
              .exclude(store__parent=self.context))

    def get_children_stats(self, qs):
        children = {}
        for child in qs.iterator():
            self.add_child_stats(children, child)
        child_stores = self.data_model.filter(store__parent=self.context).values(
            *("store__name", ) + self.max_fields + self.sum_fields)
        for child in child_stores:
            self.add_child_stats(
                children,
                child,
                root=child["store__name"],
                use_aggregates=False)
        self.add_submission_info(self.stat_data, children)
        self.add_last_created_info(child_stores, children)
        return children

    def get_root_child_path(self, child):
        return child["store__parent__tp_path"][
            len(self.context.tp_path):].split("/")[0]
