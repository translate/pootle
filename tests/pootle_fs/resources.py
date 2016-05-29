#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_fs.models import StoreFS
from pootle_fs.resources import FSProjectResources
from pootle_project.models import Project
from pootle_store.models import Store


@pytest.mark.django_db
def test_project_resources_instance():
    project = Project.objects.get(code="project0")
    resources = FSProjectResources(project)
    assert resources.project == project
    assert str(resources) == "<FSProjectResources(Project 0)>"


@pytest.mark.django_db
def test_project_resources_stores():
    project = Project.objects.get(code="project0")
    stores = Store.objects.filter(
        translation_project__project=project)
    assert list(FSProjectResources(project).stores) == list(stores)
    # mark some Stores obsolete - should still show
    store_count = stores.count()
    assert store_count
    for store in stores:
        store.makeobsolete()
    assert list(FSProjectResources(project).stores) == list(stores)
    assert stores.count() == store_count


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
