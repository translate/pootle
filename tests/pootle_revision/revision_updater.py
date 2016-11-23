# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import revision, revision_updater
from pootle_app.models import Directory
from pootle_revision.utils import UnitRevisionUpdater
from pootle_store.models import Store, Unit


def _test_revision_updater(updater):
    revisions = revision.get(Directory)
    for parent in updater.parents:
        assert not revisions(parent).get(key="foo")
        assert not revisions(parent).get(key="bar")
    updater.update(keys=["foo"])
    keys = dict(foo={}, bar={})
    for parent in updater.parents:
        keys["foo"][parent.id] = revisions(parent).get(key="foo")
        assert revisions(parent).get(key="foo")
        assert not revisions(parent).get(key="bar")
    updater.update(keys=["bar"])
    for parent in updater.parents:
        keys[parent.id] = revisions(parent).get(key="foo")
        assert revisions(parent).get(key="foo") == keys["foo"][parent.id]
        assert revisions(parent).get(key="bar")


@pytest.mark.django_db
def test_revision_unit_updater(store0):
    assert revision_updater.get() is None
    unit = store0.units.first()
    updater_class = revision_updater.get(unit.__class__)
    assert updater_class is UnitRevisionUpdater
    updater = updater_class(object_list=store0.units)
    all_pootle_paths = updater.object_list.values_list(
        "store__parent__pootle_path", flat=True)
    assert (
        list(updater.all_pootle_paths)
        == list(
            set(all_pootle_paths)))
    assert (
        list(updater.parents)
        == list(
            Directory.objects.filter(
                pootle_path__in=updater.get_parent_paths(
                    updater.all_pootle_paths))))


def test_revision_unit_updater_parent_paths():
    updater_class = revision_updater.get(Unit)
    updater = updater_class([])
    paths = updater.get_parent_paths(
        ["/foo/bar/path/foo.po",
         "/foo/bar2/path/foo.po",
         "/foo2/bar/path/foo.po",
         "/foo/bar/baz/some/other/baz.po"])
    assert (
        sorted(paths)
        == [u"/foo/",
            u"/foo/bar/",
            u"/foo/bar/baz/",
            u"/foo/bar/baz/some/",
            u"/foo/bar/baz/some/other/",
            u"/foo/bar/path/",
            u"/foo/bar2/",
            u"/foo/bar2/path/",
            u"/foo2/",
            u"/foo2/bar/",
            u"/foo2/bar/path/",
            u"/projects/",
            u"/projects/bar/",
            u"/projects/bar2/"])


@pytest.mark.django_db
def test_revision_unit_updater_update(store0):
    updater_class = revision_updater.get(Unit)
    updater = updater_class(object_list=store0.units)
    _test_revision_updater(updater)


@pytest.mark.django_db
def test_revision_unit_updater_update_single(store0):
    updater_class = revision_updater.get(Unit)
    updater = updater_class(store0.units.select_related("store__parent").first())
    _test_revision_updater(updater)


@pytest.mark.django_db
def test_revision_store_updater_update(tp0):
    updater_class = revision_updater.get(Store)
    updater = updater_class(object_list=tp0.stores)
    _test_revision_updater(updater)


@pytest.mark.django_db
def test_revision_store_updater_update_single(store0):
    updater_class = revision_updater.get(Store)
    updater = updater_class(store0)
    _test_revision_updater(updater)


@pytest.mark.django_db
def test_revision_directory_updater_single(subdir0):
    updater_class = revision_updater.get(Directory)
    updater = updater_class(subdir0)
    _test_revision_updater(updater)


@pytest.mark.django_db
def test_revision_directory_updater_update():
    updater_class = revision_updater.get(Directory)
    updater = updater_class(
        object_list=Directory.objects.filter(name="subdir0"))
    _test_revision_updater(updater)
