# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import fnmatch

from django.db.models import Max, Sum

from pootle.core.decorators import persistent_property
from pootle_data.utils import RelatedStoresDataTool
from pootle_fs.utils import PathFilter
from pootle_store.models import Store

from .models import VirtualFolder


class VirtualFolderFinder(object):
    """Find vfs for a new store"""

    def __init__(self, store):
        self.store = store

    @property
    def language(self):
        return self.store.translation_project.language

    @property
    def project(self):
        return self.store.translation_project.project

    @property
    def possible_vfolders(self):
        return (
            self.project.vfolders.filter(all_languages=True)
            | self.language.vfolders.filter(all_projects=True)
            | self.project.vfolders.filter(languages=self.language)
            | VirtualFolder.objects.filter(
                all_languages=True, all_projects=True))

    def add_to_vfolders(self):
        to_add = []
        for vf in self.possible_vfolders:
            if vf.path_matcher.should_add_store(self.store):
                to_add.append(vf)
        if to_add:
            self.store.vfolders.add(*to_add)
            self.store.set_priority()


class VirtualFolderPathMatcher(object):

    tp_path = "/[^/]*/[^/]*/"

    def __init__(self, vf):
        self.vf = vf

    @property
    def existing_stores(self):
        """Currently associated Stores"""
        return self.vf.stores.all()

    @property
    def languages(self):
        """The languages associated with this vfolder
        If `all_languages` is set then `None` is returned
        """
        if self.vf.all_languages:
            return None
        return self.vf.languages.values_list("pk", flat=True)

    @property
    def projects(self):
        """The projects associated with this vfolder
        If `all_projects` is set then `None` is returned
        """
        if self.vf.all_projects:
            return None
        return self.vf.projects.values_list("pk", flat=True)

    @property
    def matching_stores(self):
        """Store qs containing all stores that match
        project, language, and rules for this vfolder
        """
        return self.filter_from_rules(self.store_qs)

    @property
    def rules(self):
        """Glob matching rules"""
        return (
            "%s" % r.strip()
            for r
            in self.vf.filter_rules.split(","))

    @property
    def store_manager(self):
        """The root object manager for finding/adding stores"""
        return Store.objects

    @property
    def store_qs(self):
        """The stores qs without any rule filtering"""
        return self.filter_projects(
            self.filter_languages(
                self.store_manager))

    def add_and_remove_stores(self):
        """Add Stores that should be associated but arent, delete Store
        associations for Stores that are associated but shouldnt be
        """
        existing_stores = set(self.existing_stores)
        matching_stores = set(self.matching_stores)
        to_add = matching_stores - existing_stores
        to_remove = existing_stores - matching_stores
        if to_add:
            self.add_stores(to_add)
        if to_remove:
            self.remove_stores(to_remove)
        return to_add, to_remove

    def add_stores(self, stores):
        """Associate a Store"""
        self.vf.stores.add(*stores)

    def filter_from_rules(self, qs):
        filtered_qs = qs.none()
        for rule in self.rules:
            filtered_qs = (
                filtered_qs
                | qs.filter(pootle_path__regex=self.get_rule_regex(rule)))
        return filtered_qs

    def filter_languages(self, qs):
        if self.languages is None:
            return qs
        return qs.filter(
            translation_project__language_id__in=self.languages)

    def filter_projects(self, qs):
        if self.projects is None:
            return qs
        return qs.filter(
            translation_project__project_id__in=self.projects)

    def get_rule_regex(self, rule):
        """For a given *glob* rule, return a pootle_path *regex*"""
        return (
            "^%s%s"
            % (self.tp_path,
               PathFilter().path_regex(rule)))

    def path_matches(self, path):
        """Returns bool of whether path is valid for this VF.
        """
        for rule in self.rules:
            if fnmatch(rule, path):
                return True
        return False

    def remove_stores(self, stores):
        self.vf.stores.remove(*stores)

    def should_add_store(self, store):
        return (
            self.store_matches(store)
            and not self.store_associated(store))

    def store_associated(self, store):
        return self.vf.stores.through.objects.filter(
            store_id=store.id,
            virtualfolder_id=self.vf.id).exists()

    def store_matches(self, store):
        return self.path_matches(store.path)

    def update_stores(self):
        """Add and delete Store associations as necessary, and set the
        priority for any affected Stores
        """
        added, removed = self.add_and_remove_stores()
        for store in added:
            if store.priority < self.vf.priority:
                store.set_priority(priority=self.vf.priority)
        for store in removed:
            if store.priority == self.vf.priority:
                store.set_priority()


class DirectoryVFDataTool(RelatedStoresDataTool):
    group_by = ("store__vfolders__name", )
    ns = "virtualfolder"
    cache_key_name = "vfolder"

    @property
    def context_name(self):
        return self.context.pootle_path

    @property
    def max_unit_revision(self):
        return VirtualFolder.stores.through.objects.filter(
            store__translation_project=self.context.translation_project,
            store__pootle_path__startswith=self.context.pootle_path).aggregate(
                rev=Max("store__data__max_unit_revision"))

    def filter_data(self, qs):
        return (
            qs.filter(store__translation_project=self.context.translation_project)
              .filter(store__pootle_path__startswith=self.context.pootle_path)
              .filter(store__vfolders__gt=0))

    def vfolder_is_visible(self, vfolder, vfolder_stats):
        return (
            vfolder_stats["critical"]
            or vfolder_stats["suggestions"]
            or (vfolder.priority >= 1
                and vfolder_stats["total"] != vfolder_stats["translated"]))

    @persistent_property
    def all_vf_stats(self):
        return self.get_vf_stats(self.all_children_stats, show_all=True)

    @persistent_property
    def vf_stats(self):
        return self.get_vf_stats(self.children_stats)

    def get_vf_stats(self, stats, show_all=False):
        vfolders = {
            vf.name: vf
            for vf
            in VirtualFolder.objects.filter(name__in=stats.keys())}
        for k, v in stats.items():
            vfolder = vfolders.get(k)
            stats[k]["priority"] = vfolder.priority
            stats[k]["isVisible"] = (
                vfolder.is_public
                and self.vfolder_is_visible(vfolder, v))
            if not stats[k]["isVisible"] and not show_all:
                del stats[k]
                continue
            stats[k]["name"] = k
            stats[k]["code"] = k
            stats[k]["title"] = k
        return stats

    def get_stats(self, user=None):
        if self.show_all_to(user):
            return self.all_vf_stats
        return self.vf_stats

    def _group_vf_check_data(self, data):
        checks = {}
        for vf, name, count in data:
            checks[vf] = checks.get(vf, {})
            checks[vf][name] = count
        return checks

    @persistent_property
    def all_checks_data(self):
        return self._group_vf_check_data(
            self.filter_data(self.checks_data_model)
                .values_list("store__vfolders", "name")
                .annotate(Sum("count")))

    @persistent_property
    def checks_data(self):
        data = self.filter_accessible(
            self.filter_data(self.checks_data_model))
        return self._group_vf_check_data(
            data.values_list("store__vfolders", "name")
                .annotate(Sum("count")))
