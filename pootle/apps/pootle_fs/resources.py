# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from fnmatch import fnmatch

from django.db.models import F, Max
from django.utils.functional import cached_property

from pootle.core.decorators import persistent_property
from pootle_store.models import Store

from .apps import PootleFSConfig
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
            project=self.project).select_related("store")

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
        return self.stores.exclude(obsolete=True).filter(fs__isnull=True)


class FSProjectStateResources(object):
    """Wrap FSPlugin and cache available resources
    Accepts `pootle_path` and `fs_path` glob arguments.
    If present all resources are filtered accordingly.
    """

    ns = "pootle.fs.resources"
    sw_version = PootleFSConfig.version

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

    @persistent_property
    def found_file_matches(self):
        return sorted(self.context.find_translations(
            fs_path=self.fs_path, pootle_path=self.pootle_path))

    def _found_file_paths(self):
        return [x[1] for x in self.found_file_matches]
    found_file_paths = persistent_property(
        _found_file_paths,
        key_attr="fs_revision")

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

    @cached_property
    def trackable_stores(self):
        """Stores that are not currently tracked but could be"""
        _trackable = []
        stores = self.store_filter.filtered(self.resources.trackable_stores)
        for store in stores:
            fs_path = self.match_fs_path(
                self.context.get_fs_path(store.pootle_path))
            if fs_path:
                _trackable.append((store, fs_path))
        return _trackable

    @cached_property
    def trackable_store_paths(self):
        """Dictionary of pootle_path, fs_path for trackable Stores"""
        return {
            store.pootle_path: fs_path
            for store, fs_path
            in self.trackable_stores}

    @persistent_property
    def missing_file_paths(self):
        return [
            path for path in self.tracked_paths.keys()
            if path not in self.found_file_paths]

    @cached_property
    def tracked(self):
        """StoreFS queryset of tracked resources"""
        return self.storefs_filter.filtered(self.resources.tracked)

    def _tracked_paths(self):
        """Dictionary of fs_path, path for tracked StoreFS"""
        return dict(self.tracked.values_list("path", "pootle_path"))
    tracked_paths = persistent_property(
        _tracked_paths,
        key_attr="sync_revision")

    @cached_property
    def unsynced(self):
        """Returns tracked StoreFSs that have NO sync information, and are not
        currently staged for any kind of operation
        """
        return self.storefs_filter.filtered(
            self._exclude_staged(
                self.resources.unsynced))

    @cached_property
    def pootle_changed(self):
        """StoreFS queryset of tracked resources where the Store has changed
        since it was last synced.
        """
        return (
            self.synced.exclude(store_id__isnull=True)
                       .exclude(store__obsolete=True)
                       .annotate(max_revision=Max("store__unit__revision"))
                       .exclude(last_sync_revision=F("max_revision")))

    @cached_property
    def pootle_revisions(self):
        return dict(
            self.synced.exclude(store_id__isnull=True)
                       .exclude(store__obsolete=True)
                       .values_list("store_id", "store__data__max_unit_revision"))

    @cached_property
    def file_hashes(self):
        hashes = {}

        def _get_file_hash(path):
            file_path = os.path.join(
                self.context.project.local_fs_path,
                path.strip("/"))
            if os.path.exists(file_path):
                return str(os.stat(file_path).st_mtime)
        for pootle_path, path in self.found_file_matches:
            hashes[pootle_path] = _get_file_hash(path)
        return hashes

    @cached_property
    def fs_changed(self):
        """StoreFS queryset of tracked resources where the Store has changed
        since it was last synced.
        """
        hashes = self.file_hashes
        tracked_files = []
        for store_fs in self.synced.iterator():
            if store_fs.last_sync_hash == hashes.get(store_fs.pootle_path):
                continue
            tracked_files.append(store_fs.pk)
        return tracked_files

    def reload(self):
        """Uncache cached_properties"""
        cache_reload = [
            "context", "pootle_path", "fs_path",
            "cache_key", "sync_revision", "fs_revision"]
        for k, v_ in self.__dict__.items():
            if k in cache_reload:
                continue
            del self.__dict__[k]

    @cached_property
    def fs_revision(self):
        return self.context.fs_revision

    @cached_property
    def sync_revision(self):
        return self.context.sync_revision

    @cached_property
    def cache_key(self):
        return self.context.cache_key
