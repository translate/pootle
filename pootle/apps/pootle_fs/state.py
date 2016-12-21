# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
from copy import copy

from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.state import ItemState, State
from pootle_store.constants import POOTLE_WINS, SOURCE_WINS

from .models import StoreFS
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
        elif "store" in self.kwargs:
            return self.kwargs["store"].pootle_path

    @property
    def fs_path(self):
        return self.kwargs.get("fs_path")

    @property
    def project(self):
        return self.plugin.project

    @property
    def plugin(self):
        return self.state.context

    @cached_property
    def store_fs(self):
        store_fs = self.kwargs.get("store_fs")
        if isinstance(store_fs, (int, long)):
            return StoreFS.objects.filter(pk=store_fs).first()
        return store_fs

    @property
    def store(self):
        return self.kwargs.get("store")

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.pootle_path > other.pootle_path
        return object.__gt__(other)


class ProjectFSState(State):

    item_state_class = FSItemState

    def __init__(self, context, fs_path=None, pootle_path=None, load=True):
        self.fs_path = fs_path
        self.pootle_path = pootle_path
        super(ProjectFSState, self).__init__(
            context, fs_path=fs_path, pootle_path=pootle_path,
            load=load)

    @cached_property
    def cache_key(self):
        return self.context.cache_key

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
            pootle_changed_, fs_changed = self._get_changes(store_fs.file)
            if fs_changed:
                yield dict(
                    store_fs=store_fs.pk,
                    pootle_path=store_fs.pootle_path,
                    fs_path=store_fs.path)

    @property
    def state_fs_untracked(self):
        tracked_paths = self.resources.tracked_paths
        tracked_pootle_paths = tracked_paths.values()
        trackable_store_paths = self.trackable_store_paths
        trackable_fs_paths = trackable_store_paths.values()
        result = []
        for pootle_path, fs_path in self.resources.found_file_matches:
            fs_untracked = (
                fs_path not in tracked_paths
                and pootle_path not in tracked_pootle_paths
                and fs_path not in trackable_fs_paths
                and pootle_path not in trackable_store_paths)
            if fs_untracked:
                result.append(
                    dict(pootle_path=pootle_path,
                         fs_path=fs_path))
        return result

    @property
    def state_pootle_untracked(self):
        result = []
        trackable_stores = self.trackable_store_paths
        found_paths = self.found_file_paths
        for pootle_path in sorted(trackable_stores.keys()):
            path = trackable_stores[pootle_path]
            if path not in found_paths:
                result.append(
                    dict(pootle_path=pootle_path,
                         fs_path=path))
        return result

    @cached_property
    def trackable_store_paths(self):
        return self.resources.trackable_store_paths

    @cached_property
    def found_file_paths(self):
        return self.resources.found_file_paths

    @cached_property
    def synced_not_missing_fs(self):
        return self.resources.synced_not_missing_fs

    @cached_property
    def synced_missing_fs(self):
        return self.resources.synced_missing_fs

    @cached_property
    def unsynced_fs_wins(self):
        return self.resources.unsynced_fs_wins

    @property
    def state_conflict_untracked(self):
        result = []
        trackable_stores = self.trackable_store_paths
        found_paths = self.found_file_paths
        for pootle_path in sorted(trackable_stores.keys()):
            path = trackable_stores[pootle_path]
            if path in found_paths:
                result.append(
                    dict(pootle_path=pootle_path,
                         fs_path=path))
        return result

    @property
    def state_remove(self):
        to_remove = (
            self.resources.tracked.filter(staged_for_removal=True)
                                  .values_list("pk", "pootle_path", "path"))
        for pk, pootle_path, path in to_remove.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

    @property
    def state_unchanged(self):
        has_changes = []
        for v in self.__state__.values():
            if v:
                has_changes.extend([p.pootle_path for p in v])
        unchanged = (
            self.resources.synced.exclude(pootle_path__in=has_changes)
                                 .order_by("pootle_path")
                                 .values_list("pk", "pootle_path", "path"))
        for pk, pootle_path, path in unchanged.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

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
        staged = staged.values_list("pk", "pootle_path", "path")
        for pk, pootle_path, path in staged.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

    @property
    def state_fs_ahead(self):
        fs_changed = self.synced_not_missing_fs
        for store_fs in fs_changed:
            pootle_changed, fs_changed = self._get_changes(store_fs.file)
            fs_ahead = (
                fs_changed
                and (
                    not pootle_changed
                    or store_fs.resolve_conflict == SOURCE_WINS))
            if fs_ahead:
                yield dict(
                    store_fs=store_fs.pk,
                    pootle_path=store_fs.pootle_path,
                    fs_path=store_fs.path)

    @property
    def state_fs_removed(self):
        removed = (
            self.resources.synced
                          .filter(path__in=self.resources.missing_file_paths)
                          .exclude(resolve_conflict=POOTLE_WINS)
                          .exclude(store_id__isnull=True)
                          .exclude(store__obsolete=True))
        removed = removed.values_list("pk", "pootle_path", "path")
        for pk, pootle_path, path in removed.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

    @property
    def state_merge_pootle_wins(self):
        to_merge = self.resources.tracked.filter(
            staged_for_merge=True,
            resolve_conflict=POOTLE_WINS)
        to_merge = to_merge.values_list("pk", "pootle_path", "path")
        for pk, pootle_path, path in to_merge.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

    @property
    def state_merge_fs_wins(self):
        to_merge = self.resources.tracked.filter(
            staged_for_merge=True,
            resolve_conflict=SOURCE_WINS)
        to_merge = to_merge.values_list("pk", "pootle_path", "path")
        for pk, pootle_path, path in to_merge.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

    @property
    def state_pootle_ahead(self):
        for store_fs in self.resources.pootle_changed.iterator():
            pootle_changed_, fs_changed = self._get_changes(store_fs.file)
            pootle_ahead = (
                not fs_changed
                or store_fs.resolve_conflict == POOTLE_WINS)
            if pootle_ahead:
                yield dict(
                    store_fs=store_fs.pk,
                    pootle_path=store_fs.pootle_path,
                    fs_path=store_fs.path)

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
            fs_staged = (
                not store_fs.resolve_conflict == POOTLE_WINS
                and (store_fs.file
                     and store_fs.file.file_exists))
            if fs_staged:
                continue
            yield dict(
                store_fs=store_fs.pk,
                pootle_path=store_fs.pootle_path,
                fs_path=store_fs.path)

    @property
    def state_both_removed(self):
        removed = (
            self.resources.synced
                          .filter(Q(store__obsolete=True) | Q(store__isnull=True))
                          .filter(path__in=self.resources.missing_file_paths))
        removed = removed.values_list("pk", "pootle_path", "path")
        for pk, pootle_path, path in removed.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

    @property
    def state_pootle_removed(self):
        synced = (
            self.resources.synced
                          .exclude(resolve_conflict=SOURCE_WINS)
                          .exclude(path__in=self.resources.missing_file_paths)
                          .filter(Q(store__isnull=True) | Q(store__obsolete=True)))
        synced = synced.values_list("pk", "pootle_path", "path")
        for pk, pootle_path, path in synced.iterator():
            yield dict(
                store_fs=pk,
                pootle_path=pootle_path,
                fs_path=path)

    @lru_cache()
    def _get_changes(self, fs_file):
        return fs_file.pootle_changed, fs_file.fs_changed

    def clear_cache(self):
        if "resources" in self.__dict__:
            del self.__dict__["resources"]
        return super(ProjectFSState, self).clear_cache()

    def filter(self, fs_paths=None, pootle_paths=None, states=None):
        filtered = self.__class__(
            self.context,
            pootle_path=self.pootle_path,
            fs_path=self.fs_path,
            load=False)
        for k in self.states:
            if states and k not in states:
                filtered[k] = []
                continue
            filtered[k] = [
                copy(item)
                for item in self.__state__[k]
                if (not pootle_paths
                    or item.pootle_path in pootle_paths)
                and (not fs_paths
                     or item.fs_path in fs_paths)]
        return filtered
