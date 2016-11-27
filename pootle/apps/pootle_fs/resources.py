# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import fnmatch

from django.db.models import F, Max
from django.utils.functional import cached_property

from pootle.core.decorators import persistent_property
from pootle_store.constants import POOTLE_WINS
from pootle_store.models import Store

from .models import StoreFS
from .utils import StoreFSPathFilter, StorePathFilter


class FSProjectResources(object):

    def __init__(self, project):
        self.project = project

    def __str__(self):
        return (
            "<%s(%s)>"
            % (self.__class__.__name__,
               self.project))

    @property
    def excluded_languages(self):
        return self.project.config.get("pootle.fs.excluded_languages")

    @property
    def stores(self):
        excluded = self.excluded_languages
        stores = Store.objects.filter(
            translation_project__project=self.project)
        if excluded:
            stores = stores.exclude(
                translation_project__language__code__in=excluded)
        return stores

    @property
    def tracked(self):
        return StoreFS.objects.filter(
            project=self.project)

    @property
    def synced(self):
        return (
            self.tracked.exclude(last_sync_revision__isnull=True)
                        .exclude(last_sync_hash__isnull=True))

    @property
    def unsynced(self):
        return (
            self.tracked.filter(last_sync_revision__isnull=True)
                        .filter(last_sync_hash__isnull=True))

    @property
    def trackable_stores(self):
        return self.stores.exclude(obsolete=True).filter(fs__isnull=True).order_by()


class FSProjectStateResources(object):
    """Wrap FSPlugin and cache available resources
    Accepts `pootle_path` and `fs_path` glob arguments.
    If present all resources are filtered accordingly.
    """

    def __init__(self, context, pootle_path=None, fs_path=None):
        self.context = context
        self.pootle_path = pootle_path
        self.fs_path = fs_path

    def match_fs_path(self, path):
        """Match fs_paths using file glob if set"""
        if not self.fs_path or fnmatch(path, self.fs_path):
            return path

    def _exclude_staged(self, qs):
        return (
            qs.exclude(staged_for_removal=True)
              .exclude(staged_for_merge=True))

    @cached_property
    def fs_revision(self):
        return self.context.project.directory.revisions.get(
            key="fs").value

    @cached_property
    def project_revision(self):
        return self.context.project.directory.revisions.get(
            key="stats").value

    @cached_property
    def cache_key(self):
        if self.context.latest_hash is None:
            return
        return (
            "pootle_fs.resources.%s.%s.%s"
            % (self.project_revision,
               self.fs_revision,
               self.context.latest_hash))

    @cached_property
    def match_cache_key(self):
        if self.context.latest_hash is None:
            return
        return (
            "pootle_fs.resources.match.%s.%s"
            % (self.project_revision,
               self.context.latest_hash))

    @cached_property
    def pootle_cache_key(self):
        if self.context.latest_hash is None:
            return
        return (
            "pootle_fs.resources.pootle.%s"
            % self.project_revision)

    def _obsolete_stores(self):
        return list(
            self.resources.stores.filter(
                obsolete=True).values_list("id", flat=True))
    obsolete_stores = persistent_property(
        _obsolete_stores, key_attr="pootle_cache_key")

    def _found_file_matches(self):
        return sorted(self.context.find_translations(
            fs_path=self.fs_path, pootle_path=self.pootle_path))
    found_file_matches = persistent_property(
        _found_file_matches, key_attr="match_cache_key")

    def _found_file_paths(self):
        return [x[1] for x in self.found_file_matches]
    found_file_paths = persistent_property(
        _found_file_paths, key_attr="match_cache_key")

    def _staged_store_exists(self):
        return list(
            self.unsynced
                .exclude(store__isnull=True)
                .exclude(store__obsolete=True))
    staged_store_exists = persistent_property(
        _staged_store_exists, key_attr="fs_cache_key")

    @persistent_property
    def unsynced_fs_wins(self):
        unsynced = self.unsynced
        res = []
        missing_file_paths = self.missing_file_paths
        for _s in unsynced.exclude(resolve_conflict=POOTLE_WINS).iterator():
            if _s.path not in missing_file_paths:
                res.append(_s)
        return res

    def _synced_not_missing_fs(self):
        synced = self.synced
        res = []
        for _s in synced.iterator():
            if _s.path not in self.missing_file_paths:
                res.append(_s)
        return res
    synced_not_missing_fs = persistent_property(
        _synced_not_missing_fs, key_attr="match_cache_key")

    def _synced_missing_fs(self):
        synced = self.synced
        res = []
        missing_file_paths = self.missing_file_paths
        for _s in synced.iterator():
            if _s.path in missing_file_paths:
                res.append(_s)
        return res
    synced_missing_fs = persistent_property(
        _synced_missing_fs, key_attr="match_cache_key")

    @cached_property
    def resources(self):
        """Uncached Project resources provided by FSPlugin"""
        return self.context.resources

    @cached_property
    def store_filter(self):
        """Filter Store querysets using file globs"""
        return StorePathFilter(
            pootle_path=self.pootle_path)

    @cached_property
    def storefs_filter(self):
        """Filter StoreFS querysets using file globs"""
        return StoreFSPathFilter(
            pootle_path=self.pootle_path,
            fs_path=self.fs_path)

    @cached_property
    def synced(self):
        """Returns tracked StoreFSs that have sync information, and are not
        currently staged for any kind of operation
        """
        return self.storefs_filter.filtered(
            self._exclude_staged(self.resources.synced))

    @persistent_property
    def filtered_stores(self):
        return list(
            self.store_filter.filtered(self.resources.trackable_stores))

    @cached_property
    def trackable_stores(self):
        """Stores that are not currently tracked but could be"""
        _trackable = []
        for store in self.filtered_stores:
            fs_path = self.match_fs_path(
                self.context.get_fs_path(store.pootle_path))
            if fs_path:
                _trackable.append((store, fs_path))
        return _trackable

    @persistent_property
    def trackable_store_paths(self):
        """Dictionary of pootle_path, fs_path for trackable Stores"""
        return {
            store.pootle_path: fs_path
            for store, fs_path
            in self.trackable_stores}

    @persistent_property
    def missing_file_paths(self):
        return (
            set(self.tracked_paths.keys())
            - set(self.found_file_paths))

    @cached_property
    def tracked(self):
        """StoreFS queryset of tracked resources"""
        return self.storefs_filter.filtered(self.resources.tracked)

    @persistent_property
    def tracked_paths(self):
        """Dictionary of fs_path, path for tracked StoreFS"""
        return dict(self.tracked.values_list("path", "pootle_path"))

    @cached_property
    def unsynced(self):
        """Returns tracked StoreFSs that have NO sync information, and are not
        currently staged for any kind of operation
        """
        return self.storefs_filter.filtered(
            self._exclude_staged(
                self.resources.unsynced))

    @property
    def pootle_changed(self):
        """StoreFS queryset of tracked resources where the Store has changed
        since it was last synced.
        """
        return (
            self.synced.exclude(store__isnull=True)
                       .exclude(store__obsolete=True)
                       .annotate(max_revision=Max("store__unit__revision"))
                       .exclude(last_sync_revision=F("max_revision")))

    def reload(self):
        """Uncache cached_properties"""
        for k, v_ in self.__dict__.items():
            if k in ["context", "pootle_path", "fs_path"]:
                continue
            del self.__dict__[k]
