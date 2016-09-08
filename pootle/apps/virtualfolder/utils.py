# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import fnmatch
import os


from pootle.core.url_helpers import split_pootle_path
from pootle_store.models import Store
from pootle_data.utils import RelatedStoresDataTool, RelatedStoresDataUpdater
from pootle_store.constants import OBSOLETE


class VirtualFolderPathMatcher(object):

    def __init__(self, vf):
        self.vf = vf

    def update_matching_stores(self):
        existing_stores = self.vf.stores.all()
        matching_stores = self.find_matching_stores()
        to_add = []
        to_delete = []
        for store in matching_stores:
            if store not in existing_stores:
                to_add.append(store)
        for store in existing_stores:
            if store not in matching_stores:
                to_delete.append(store.id)
        if to_add:
            self.vf.stores.add(*to_add)
        if to_delete:
            self.vf.stores.filter(id__in=to_delete).delete()

    def add_store_if_matching(self, store):
        pootle_dir_path = "".join(
            ("/", ) + split_pootle_path(store.pootle_path)[2:])
        no_add = (
            not self.path_matches(pootle_dir_path)
            or self.vf.stores.through.objects.filter(store_id=store.id).exists())
        if no_add:
            return
        self.vf.stores.add(store)

    @property
    def filter_rules(self):
        return (
            "%s" % r.strip()
            for r
            in self.vf.filter_rules.split(","))

    @property
    def lang_code(self):
        return (
            self.vf.language
            and self.vf.language.code)

    @property
    def proj_code(self):
        return (
            self.vf.project
            and self.vf.project.code)

    @property
    def store_qs(self):
        qs = Store.objects
        if self.lang_code:
            qs = qs.filter(translation_project__language__code=self.lang_code)
        if self.proj_code:
            qs = qs.filter(translation_project__project__code=self.proj_code)
        if self.use_regex:
            if self.lang_code or self.proj_code:
                qs = qs.filter(pootle_path__regex="^%s" % self.path)
        else:
            qs = qs.filter(pootle_path__startswith=self.path)
        return qs

    @property
    def use_regex(self):
        return (
            not self.lang_code
            or not self.proj_code)

    @property
    def regexes(self):
        return (
            "%s%s" % (self.path, rule)
            for rule
            in self.filter_rules)

    @property
    def path(self):
        regex = "[^/]*"
        return (
            "/%s/%s"
            % (self.lang_code or regex,
               self.proj_code or regex))

    def get_rule_path(self, rule):
        return "%s%s" % (self.path, rule)

    def filter_by_rule(self, qs, rule):
        rule_path = self.get_rule_path(rule)
        is_file = "." in os.path.basename(rule)
        if self.use_regex:
            return (
                qs.filter(pootle_path__regex="^%s$" % rule_path)
                if is_file
                else qs.filter(pootle_path__regex="^%s" % rule_path))
        return (
            qs.filter(pootle_path=rule_path)
            if is_file
            else qs.filter(pootle_path__startswith=rule_path))

    def filter_from_rules(self, qs):
        if not self.filter_rules:
            return qs
        filtered_qs = qs.none()
        for rule in self.filter_rules:
            filtered_qs = filtered_qs | self.filter_by_rule(qs, rule)
        return filtered_qs

    def find_matching_stores(self):
        return self.filter_from_rules(self.store_qs)

    def path_matches(self, path):
        """Returns bool of whether path is valid for this VF.
        """
        for rule in self.filter_rules:
            if fnmatch(rule, path):
                return True
        return False

    def dir_path_matches(self, path):
        """Returns bool of whether path is valid for this VF.
        or as a parent of any valid paths
        """
        dir_path = "%s%s" % (self.path, path)
        if self.use_regex:
            return self.vf.stores.filter(
                pootle_path__regex=dir_path).exists()
        return self.vf.stores.filter(
            pootle_path__startswith=dir_path).exists()


class VirtualFolderDataUpdater(RelatedStoresDataUpdater):
    related_name = "vf"

    @property
    def store_data_qs(self):
        return self.tool.data_model.filter(
            store__in=self.model.stores.filter(state__gt=OBSOLETE))


class VirtualFolderDataTool(RelatedStoresDataTool):

    @property
    def vf(self):
        return self.context


class TPVirtualFoldersDataTool(RelatedStoresDataTool):

    @property
    def vf(self):
        return self.context


class DirectoryVirtualFoldersDataTool(RelatedStoresDataTool):

    @property
    def stat_data(self):
        return self.data_model.filter(
            store__pootle_path__startswith=self.context.pootle_path)


class LanguageVirtualFoldersDataTool(RelatedStoresDataTool):

    @property
    def stat_data(self):
        return self.data_model.filter(
            store__translation_project__language=self.context)
