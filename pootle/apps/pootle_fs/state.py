# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.decorators import persistent_property
from pootle.core.models import Revision
from pootle.core.state import ItemState, State
from pootle_store.constants import POOTLE_WINS, SOURCE_WINS

from .resources import FSProjectStateResources


FS_STATE = OrderedDict()
FS_STATE["conflict"] = {
    "title": "Conflicts",
    "description": "Both Pootle Store and file in filesystem have changed"}
FS_STATE["conflict_untracked"] = {
    "title": "Untracked conflicts",
    "description": (
        "Newly created files in the filesystem matching newly created Stores "
        "in Pootle")}
FS_STATE["pootle_ahead"] = {
    "title": "Changed in Pootle",
    "description": "Stores that have changed in Pootle"}
FS_STATE["pootle_untracked"] = {
    "title": "Untracked Stores",
    "description": "Newly created Stores in Pootle"}
FS_STATE["pootle_staged"] = {
    "title": "Added in Pootle",
    "description": (
        "Stores that have been added in Pootle and are now being tracked")}
FS_STATE["pootle_removed"] = {
    "title": "Removed from Pootle",
    "description": "Stores that have been removed from Pootle"}
FS_STATE["fs_ahead"] = {
    "title": "Changed in filesystem",
    "description": "A file has been changed in the filesystem"}
FS_STATE["fs_untracked"] = {
    "title": "Untracked files",
    "description": "Newly created files in the filesystem"}
FS_STATE["fs_staged"] = {
    "title": "Fetched from filesystem",
    "description": (
        "Files that have been fetched from the filesystem and are now being "
        "tracked")}
FS_STATE["fs_removed"] = {
    "title": "Removed from filesystem",
    "description": "Files that have been removed from the filesystem"}
FS_STATE["merge_pootle_wins"] = {
    "title": "Staged for merge (Pootle wins)",
    "description": (
        "Files or Stores that have been staged for merging on sync - pootle "
        "wins where units are both updated")}
FS_STATE["merge_fs_wins"] = {
    "title": "Staged for merge (FS wins)",
    "description": (
        "Files or Stores that have been staged for merging on sync - FS "
        "wins where units are both updated")}
FS_STATE["remove"] = {
    "title": "Staged for removal",
    "description": "Files or Stores that have been staged or removal on sync"}
FS_STATE["both_removed"] = {
    "title": "Removed from Pootle and filesystem",
    "description": (
        "Files or Stores that were previously tracked but have now "
        "disappeared")}


class FSItemState(ItemState):

    @property
    def pootle_path(self):
        if "pootle_path" in self.kwargs:
            return self.kwargs["pootle_path"]
        elif "store_fs" in self.kwargs:
            return self.kwargs["store_fs"].pootle_path
        elif "store" in self.kwargs:
            return self.kwargs["store"].pootle_path

    @property
    def fs_path(self):
        if "fs_path" in self.kwargs:
            return self.kwargs["fs_path"]
        elif "store_fs" in self.kwargs:
            return self.kwargs["store_fs"].path

    @property
    def project(self):
        return self.plugin.project

    @property
    def plugin(self):
        return self.state.context

    @property
    def store_fs(self):
        return self.kwargs.get("store_fs")

    @property
    def store(self):
        return self.kwargs.get("store")

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.pootle_path > other.pootle_path
        return object.__gt__(other)


class ProjectFSState(State):

    item_state_class = FSItemState

    def __init__(self, context, fs_path=None, pootle_path=None):
        self.fs_path = fs_path
        self.pootle_path = pootle_path
        super(ProjectFSState, self).__init__(
            context, fs_path=fs_path, pootle_path=pootle_path)

    @cached_property
    def cache_key(self):
        latest_hash = self.context.get_latest_hash()
        if latest_hash is None:
            return
        return (
            "%s/%s"
            % (Revision.get(),
               latest_hash))

    @property
    def project(self):
        return self.context.project

    @property
    def states(self):
        return FS_STATE.keys()

    @cached_property
    def resources(self):
        return FSProjectStateResources(
            self.context,
            pootle_path=self.pootle_path,
            fs_path=self.fs_path)

    @property
    def state_conflict(self):
        conflict = self.resources.pootle_changed.exclude(
            resolve_conflict__gt=0)
        for store_fs in conflict.iterator():
            store_fs.project = self.project
            pootle_changed_, fs_changed = self._get_changes(store_fs.file)
            if fs_changed:
                yield dict(store_fs=store_fs)

    @persistent_property
    def state_fs_untracked(self):
        tracked_fs_paths = self.resources.tracked_paths.keys()
        tracked_pootle_paths = self.resources.tracked_paths.values()
        trackable_fs_paths = self.resources.trackable_store_paths.values()
        trackable_pootle_paths = self.resources.trackable_store_paths.keys()
        result = []
        for pootle_path, fs_path in self.resources.found_file_matches:
            fs_untracked = (
                fs_path not in tracked_fs_paths
                and pootle_path not in tracked_pootle_paths
                and fs_path not in trackable_fs_paths
                and pootle_path not in trackable_pootle_paths)
            if fs_untracked:
                result.append(
                    dict(pootle_path=pootle_path,
                         fs_path=fs_path))
        return result

    @persistent_property
    def state_pootle_untracked(self):
        result = []
        for store, path in self.resources.trackable_stores:
            if path not in self.resources.found_file_paths:
                result.append(
                    dict(store=store,
                         fs_path=path))
        return result

    @persistent_property
    def state_conflict_untracked(self):
        result = []
        for store, path in self.resources.trackable_stores:
            if path in self.resources.found_file_paths:
                result.append(
                    dict(store=store,
                         fs_path=path))
        return result

    @property
    def state_remove(self):
        to_remove = self.resources.tracked.filter(staged_for_removal=True)
        for store_fs in to_remove.iterator():
            yield dict(store_fs=store_fs)

    @property
    def state_unchanged(self):
        has_changes = []
        for v in self.__state__.values():
            if v:
                has_changes.extend([p.pootle_path for p in v])
        return self.resources.synced.exclude(pootle_path__in=has_changes)

    @property
    def state_fs_staged(self):
        staged = (
            self.resources.unsynced
                          .exclude(path__in=self.resources.missing_file_paths)
                          .exclude(resolve_conflict=POOTLE_WINS)
            | self.resources.synced
                            .filter(Q(store__isnull=True) | Q(store__obsolete=True))
                            .exclude(path__in=self.resources.missing_file_paths)
                            .filter(resolve_conflict=SOURCE_WINS))
        for store_fs in staged.iterator():
            store_fs.project = self.project
            yield dict(store_fs=store_fs)

    @persistent_property
    def state_fs_ahead(self):
        result = []
        fs_changed = (
            self.resources.synced
                          .exclude(path__in=self.resources.missing_file_paths))
        for store_fs in fs_changed.iterator():
            store_fs.project = self.project
            pootle_changed, fs_changed = self._get_changes(store_fs.file)
            fs_ahead = (
                fs_changed
                and (
                    not pootle_changed
                    or store_fs.resolve_conflict == SOURCE_WINS))
            if fs_ahead:
                result.append(dict(store_fs=store_fs))
        return result

    @property
    def state_fs_removed(self):
        removed = (
            self.resources.synced
                          .filter(path__in=self.resources.missing_file_paths)
                          .exclude(resolve_conflict=POOTLE_WINS)
                          .exclude(store_id__isnull=True)
                          .exclude(store__obsolete=True))
        for store_fs in removed.iterator():
            store_fs.project = self.project
            yield dict(store_fs=store_fs)

    @property
    def state_merge_pootle_wins(self):
        to_merge = self.resources.tracked.filter(
            staged_for_merge=True,
            resolve_conflict=POOTLE_WINS)
        for store_fs in to_merge.iterator():
            store_fs.project = self.project
            yield dict(store_fs=store_fs)

    @property
    def state_merge_fs_wins(self):
        to_merge = self.resources.tracked.filter(
            staged_for_merge=True,
            resolve_conflict=SOURCE_WINS)
        for store_fs in to_merge.iterator():
            store_fs.project = self.project
            yield dict(store_fs=store_fs)

    @property
    def state_pootle_ahead(self):
        for store_fs in self.resources.pootle_changed.iterator():
            store_fs.project = self.project
            pootle_changed_, fs_changed = self._get_changes(store_fs.file)
            pootle_ahead = (
                not fs_changed
                or store_fs.resolve_conflict == POOTLE_WINS)
            if pootle_ahead:
                yield dict(store_fs=store_fs)

    @property
    def state_pootle_staged(self):
        staged = (
            self.resources.unsynced
                          .exclude(resolve_conflict=SOURCE_WINS)
                          .exclude(store__isnull=True)
                          .exclude(store__obsolete=True)
            | self.resources.synced
                            .exclude(store__obsolete=True)
                            .exclude(store__isnull=True)
                            .filter(path__in=self.resources.missing_file_paths)
                            .filter(resolve_conflict=POOTLE_WINS))
        for store_fs in staged.iterator():
            store_fs.project = self.project
            yield dict(store_fs=store_fs)

    @property
    def state_both_removed(self):
        removed = (
            self.resources.synced
                          .filter(Q(store__obsolete=True) | Q(store__isnull=True))
                          .filter(path__in=self.resources.missing_file_paths))
        for store_fs in removed.iterator():
            store_fs.project = self.project
            yield dict(store_fs=store_fs)

    @property
    def state_pootle_removed(self):
        synced = (
            self.resources.synced
                          .exclude(resolve_conflict=SOURCE_WINS)
                          .exclude(path__in=self.resources.missing_file_paths)
                          .filter(Q(store__isnull=True) | Q(store__obsolete=True)))
        for store_fs in synced.iterator():
            store_fs.project = self.project
            yield dict(store_fs=store_fs)

    @lru_cache()
    def _get_changes(self, fs_file):
        return fs_file.pootle_changed, fs_file.fs_changed

    def clear_cache(self):
        for x in dir(self):
            x = getattr(self, x)
            if callable(x) and hasattr(x, "cache_clear"):
                x.cache_clear()
        if "resources" in self.__dict__:
            del self.__dict__["resources"]
        return super(ProjectFSState, self).clear_cache()
