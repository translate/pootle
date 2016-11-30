#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import fnmatch
import sys

import pytest

from django.utils.functional import cached_property

from pootle_fs.apps import PootleFSConfig
from pootle_fs.models import StoreFS
from pootle_fs.resources import (
    FSProjectResources, FSProjectStateResources)
from pootle_project.models import Project
from pootle_store.models import Store


@pytest.mark.django_db
def test_project_resources_instance():
    project = Project.objects.get(code="project0")
    resources = FSProjectResources(project)
    assert resources.project == project
    assert str(resources) == "<FSProjectResources(Project 0)>"


@pytest.mark.django_db
def test_project_resources_stores(project0, language0):
    stores = Store.objects.filter(
        translation_project__project=project0)
    assert list(FSProjectResources(project0).stores) == list(stores)
    # mark some Stores obsolete - should still show
    store_count = stores.count()
    assert store_count
    for store in stores:
        store.makeobsolete()
    assert list(FSProjectResources(project0).stores) == list(stores)
    assert stores.count() == store_count
    project0.config["pootle.fs.excluded_languages"] = [language0.code]
    filtered_stores = stores.exclude(
        translation_project__language=language0)
    assert (
        list(FSProjectResources(project0).stores)
        != list(stores))
    assert (
        list(FSProjectResources(project0).stores)
        == list(filtered_stores))


@pytest.mark.django_db
def test_project_resources_trackable_stores(project0_fs_resources):
    project = project0_fs_resources
    stores = Store.objects.filter(
        translation_project__project=project)
    # only stores that are not obsolete and do not have an
    # exiting StoreFS should be trackable
    trackable = stores.filter(obsolete=False).order_by("pk")
    trackable = trackable.filter(fs__isnull=True)
    assert (
        list(FSProjectResources(project).trackable_stores.order_by("pk"))
        == list(trackable))
    for store in FSProjectResources(project).trackable_stores:
        try:
            fs = store.fs.get()
        except StoreFS.DoesNotExist:
            fs = None
        assert fs is None
        assert store.obsolete is False


@pytest.mark.django_db
def test_project_resources_tracked(project0_fs_resources):
    project = project0_fs_resources
    assert (
        list(FSProjectResources(project).tracked.order_by("pk"))
        == list(StoreFS.objects.filter(project=project).order_by("pk")))
    # this includes obsolete stores
    assert FSProjectResources(project).tracked.filter(
        store__obsolete=True).exists()


@pytest.mark.django_db
def test_project_resources_synced(project0_fs_resources):
    project = project0_fs_resources
    synced = StoreFS.objects.filter(project=project).order_by("pk")
    obsoleted = synced.filter(store__obsolete=True).first()
    obsoleted.last_sync_hash = "FOO"
    obsoleted.last_sync_revision = 23
    obsoleted.save()
    active = synced.exclude(store__obsolete=True).first()
    active.last_sync_hash = "FOO"
    active.last_sync_revision = 23
    active.save()
    synced = synced.exclude(last_sync_revision__isnull=True)
    synced = synced.exclude(last_sync_hash__isnull=True)
    assert (
        list(FSProjectResources(project).synced.order_by("pk"))
        == list(synced))
    assert FSProjectResources(project).synced.count() == 2


@pytest.mark.django_db
def test_project_resources_unsynced(project0_fs_resources):
    project = project0_fs_resources
    for store_fs in FSProjectResources(project).tracked:
        store_fs.last_sync_hash = "FOO"
        store_fs.last_sync_revision = 23
        store_fs.save()
    unsynced = StoreFS.objects.filter(project=project).order_by("pk")
    obsoleted = unsynced.filter(store__obsolete=True).first()
    obsoleted.last_sync_hash = None
    obsoleted.last_sync_revision = None
    obsoleted.save()
    active = unsynced.exclude(store__obsolete=True).first()
    active.last_sync_hash = None
    active.last_sync_revision = None
    active.save()
    unsynced = unsynced.filter(last_sync_revision__isnull=True)
    unsynced = unsynced.filter(last_sync_hash__isnull=True)
    assert (
        list(FSProjectResources(project).unsynced.order_by("pk"))
        == list(unsynced))
    assert FSProjectResources(project).unsynced.count() == 2


class DummyPlugin(object):

    def __init__(self, project):
        self.project = project

    @cached_property
    def resources(self):
        return FSProjectResources(self.project)

    def reload(self):
        if "resources" in self.__dict__:
            del self.__dict__["resources"]


@pytest.mark.django_db
def test_fs_state_resources(project0_fs_resources):
    project = project0_fs_resources
    plugin = DummyPlugin(project)
    state_resources = FSProjectStateResources(plugin)
    assert state_resources.resources is plugin.resources
    # resources are cached on state and plugin
    plugin.reload()
    assert state_resources.resources is not plugin.resources
    state_resources.reload()
    assert state_resources.resources is plugin.resources


@pytest.mark.django_db
def test_fs_state_trackable(fs_path_qs, dummyfs_untracked):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_untracked
    qs = Store.objects.filter(
        translation_project__project=plugin.project)
    if qfilter is False:
        qs = qs.none()
    elif qfilter:
        qs = qs.filter(qfilter)
    trackable = FSProjectStateResources(
        plugin,
        pootle_path=pootle_path,
        fs_path=fs_path).trackable_stores
    assert (
        sorted(trackable, key=lambda item: item[0].pk)
        == [(store, plugin.get_fs_path(store.pootle_path))
            for store in list(qs.order_by("pk"))])


@pytest.mark.django_db
def test_fs_state_trackable_store_paths(fs_path_qs, dummyfs_untracked):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_untracked
    qs = Store.objects.filter(
        translation_project__project=plugin.project)
    if qfilter is False:
        qs = qs.none()
    elif qfilter:
        qs = qs.filter(qfilter)
    resources = FSProjectStateResources(plugin)
    assert (
        sorted(
            (store.pootle_path, fs_path)
            for store, fs_path
            in resources.trackable_stores)
        == sorted(resources.trackable_store_paths.items()))


@pytest.mark.django_db
def test_fs_state_trackable_tracked(dummyfs, no_complex_po_):
    plugin = dummyfs
    resources = FSProjectStateResources(plugin)
    store_fs = resources.tracked[0]
    store = store_fs.store
    store_fs.delete()
    trackable = resources.trackable_stores
    store = plugin.resources.stores.get(
        pootle_path=store.pootle_path)
    assert len(trackable) == 1
    assert trackable[0][0] == store
    assert (
        trackable[0][1]
        == plugin.get_fs_path(store.pootle_path))


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_synced(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    qs = StoreFS.objects.filter(project=plugin.project)
    if qfilter is False:
        qs = qs.none()
    elif qfilter:
        qs = qs.filter(qfilter)
    synced = FSProjectStateResources(
        plugin,
        pootle_path=pootle_path,
        fs_path=fs_path).synced
    assert (
        list(synced.order_by("pk"))
        == list(qs.order_by("pk")))


@pytest.mark.django_db
def test_fs_state_synced_staged(dummyfs):
    plugin = dummyfs
    resources = FSProjectStateResources(plugin)
    store_fs = resources.tracked[0]
    resources.tracked.exclude(pk=store_fs.pk).update(
        last_sync_hash=None,
        last_sync_revision=None)
    assert resources.synced.count() == 1
    # synced does not include any that are staged rm/merge
    store_fs.staged_for_merge = True
    store_fs.save()
    assert resources.synced.count() == 0
    store_fs.staged_for_merge = False
    store_fs.staged_for_removal = True
    store_fs.save()
    assert resources.synced.count() == 0
    store_fs.staged_for_removal = False
    store_fs.save()
    assert resources.synced.count() == 1


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_unsynced(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    resources = FSProjectStateResources(plugin)
    resources.tracked.update(
        last_sync_hash=None,
        last_sync_revision=None)
    qs = StoreFS.objects.filter(project=plugin.project)
    if qfilter is False:
        qs = qs.none()
    elif qfilter:
        qs = qs.filter(qfilter)
    unsynced = FSProjectStateResources(
        plugin,
        pootle_path=pootle_path,
        fs_path=fs_path).unsynced
    assert (
        list(unsynced.order_by("pk"))
        == list(qs.order_by("pk")))


@pytest.mark.django_db
def test_fs_state_unsynced_staged(dummyfs):
    plugin = dummyfs
    resources = FSProjectStateResources(plugin)
    store_fs = resources.tracked[0]
    store_fs.last_sync_hash = None
    store_fs.last_sync_revision = None
    store_fs.save()
    assert resources.unsynced.count() == 1
    # unsynced does not include any that are staged rm/merge
    store_fs.staged_for_merge = True
    store_fs.save()
    assert resources.unsynced.count() == 0
    store_fs.staged_for_merge = False
    store_fs.staged_for_removal = True
    store_fs.save()
    assert resources.unsynced.count() == 0
    store_fs.staged_for_removal = False
    store_fs.save()
    assert resources.unsynced.count() == 1


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_tracked(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    qs = StoreFS.objects.filter(project=plugin.project)
    if qfilter is False:
        qs = qs.none()
    elif qfilter:
        qs = qs.filter(qfilter)
    tracked = FSProjectStateResources(
        plugin,
        pootle_path=pootle_path,
        fs_path=fs_path).tracked
    assert (
        list(tracked.order_by("pk"))
        == list(qs.order_by("pk")))


@pytest.mark.django_db
def test_fs_state_tracked_paths(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    resources = FSProjectStateResources(plugin)
    resources.tracked.update(
        last_sync_hash=None,
        last_sync_revision=None)
    qs = StoreFS.objects.filter(project=plugin.project)
    if qfilter is False:
        qs = qs.none()
    elif qfilter:
        qs = qs.filter(qfilter)
    resources = FSProjectStateResources(plugin)
    assert (
        sorted(resources.tracked.values_list("path", "pootle_path"))
        == sorted(resources.tracked_paths.items()))


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_pootle_changed(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    resources = FSProjectStateResources(plugin)
    assert list(
        FSProjectStateResources(
            plugin,
            pootle_path=pootle_path,
            fs_path=fs_path).pootle_changed) == []
    for store_fs in plugin.resources.tracked:
        store_fs.last_sync_revision = store_fs.last_sync_revision - 1
        store_fs.save()
    qs = StoreFS.objects.filter(project=plugin.project)
    if qfilter is False:
        qs = qs.none()
    elif qfilter:
        qs = qs.filter(qfilter)
    resources = FSProjectStateResources(
        plugin,
        pootle_path=pootle_path,
        fs_path=fs_path)
    assert (
        sorted(resources.pootle_changed.values_list("pk", flat=True))
        == sorted(qs.values_list("pk", flat=True)))


@pytest.mark.django_db
def test_fs_state_found_file_matches(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    resources = FSProjectStateResources(
        plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = resources.resources.stores
    found_files = []
    for pp in stores.values_list("pootle_path", flat=True):
        fp = plugin.get_fs_path(pp)
        if fs_path and not fnmatch(fp, fs_path):
            continue
        if pootle_path and not fnmatch(pp, pootle_path):
            continue
        found_files.append((pp, fp))
    assert (
        sorted(resources.found_file_matches)
        == sorted(found_files))
    assert (
        resources.found_file_paths
        == [x[1] for x in resources.found_file_matches])


@pytest.mark.django_db
def test_fs_resources_cache_key(project_fs):
    plugin = project_fs
    resources = plugin.state().resources
    assert resources.ns == "pootle.fs.resources"
    assert resources.sw_version == PootleFSConfig.version
    assert (
        resources.fs_revision
        == resources.context.fs_revision)
    assert (
        resources.sync_revision
        == resources.context.sync_revision)
    assert (
        resources.cache_key
        == resources.context.cache_key)
