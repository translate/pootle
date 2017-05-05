#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ValidationError

from pytest_pootle.factories import (
    LanguageDBFactory, ProjectDBFactory, StoreDBFactory,
    TranslationProjectFactory)
from pytest_pootle.utils import setup_store

from pootle.core.delegate import config
from pootle.core.plugin import getter, provider
from pootle_fs.delegate import fs_file, fs_plugins
from pootle_fs.files import FSFile
from pootle_fs.models import StoreFS
from pootle_project.models import Project


@pytest.mark.django_db
def test_add_new_store_fs(settings, project0):
    """Add a store_fs for a store that doesnt exist yet
    """
    pootle_path = "/language0/%s/example.po" % project0.code
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        pootle_path=pootle_path,
        path=fs_path)
    assert store_fs.project == project0
    assert store_fs.store is None
    assert store_fs.pootle_path == pootle_path
    assert store_fs.path == fs_path
    assert store_fs.last_sync_hash is None
    assert store_fs.last_sync_mtime is None
    assert store_fs.last_sync_revision is None


@pytest.mark.django_db
def test_add_store_fs_by_path(po_directory, english):
    """Add a store_fs for pootle_path
    """
    project = ProjectDBFactory(source_language=english)
    language = LanguageDBFactory()
    tp = TranslationProjectFactory(project=project, language=language)
    store = StoreDBFactory(
        translation_project=tp,
        parent=tp.directory,
        name="example_store.po")
    conf = config.get(tp.project.__class__, instance=tp.project)
    conf.set_config("pootle_fs.fs_type", "localfs")
    conf.set_config("pootle_fs.fs_url", "foo")
    fs_path = "/some/fs/example_store.po"
    pootle_path = store.pootle_path
    store_fs = StoreFS.objects.create(
        pootle_path=pootle_path,
        path=fs_path)
    assert store_fs.project == project
    assert store_fs.store == store
    assert store_fs.pootle_path == pootle_path
    assert store_fs.path == fs_path
    assert store_fs.last_sync_hash is None
    assert store_fs.last_sync_mtime is None
    assert store_fs.last_sync_revision is None


@pytest.mark.django_db
def test_add_store_fs_by_store(po_directory, english):
    """Add a store_fs using store= rather than pootle_path
    """
    fs_path = "/some/fs/example_store.po"
    project = ProjectDBFactory(source_language=english)
    language = LanguageDBFactory()
    tp = TranslationProjectFactory(project=project, language=language)
    store = StoreDBFactory(
        translation_project=tp,
        parent=tp.directory,
        name="example_store.po")
    conf = config.get(tp.project.__class__, instance=tp.project)
    conf.set_config("pootle_fs.fs_type", "localfs")
    conf.set_config("pootle_fs.fs_url", "foo")
    store_fs = StoreFS.objects.create(
        store=store,
        path=fs_path)
    assert store_fs.project == project
    assert store_fs.store == store
    assert store_fs.pootle_path == store.pootle_path
    assert store_fs.path == fs_path
    assert store_fs.last_sync_hash is None
    assert store_fs.last_sync_mtime is None
    assert store_fs.last_sync_revision is None


@pytest.mark.django_db
def test_add_store_bad(po_directory, english):
    """Try to create a store_fs by pootle_path for a non existent project
    """
    project0 = Project.objects.get(code="project0")
    project = ProjectDBFactory(source_language=english)

    # project doesnt exist
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            pootle_path="/en/project0_BAD/example.po",
            path="/some/fs/example.po")

    # pootle_path must match project_code
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            project=project0,
            pootle_path="/en/%s/en.po" % project.code,
            path="/locales/en.po")

    # need both pootle_path and fs_path - somehow
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            project=project0,
            pootle_path="/language0/%s/en.po" % project0.code)
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            project=project0,
            path="/locales/en.po")
    store = setup_store("/language0/project0/en.po")
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            store=store,
            pootle_path=store.pootle_path)


@pytest.mark.django_db
def test_add_store_bad_lang(project0):
    """Try to create a store_fs by pootle_path for a non existent language
    """
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            pootle_path="/fr/%s/example.po" % project0.code,
            path="/some/fs/example.po")


@pytest.mark.django_db
def test_add_store_bad_path(po_directory, english):
    """Try to create a store_fs where pootle_path and store.pootle_path dont
    match.
    """
    fs_path = "/some/fs/example.po"
    project = ProjectDBFactory(source_language=english)
    language = LanguageDBFactory()
    tp = TranslationProjectFactory(project=project, language=language)
    conf = config.get(project.__class__, instance=project)
    conf.set_config("pootle_fs.fs_type", "localfs")
    conf.set_config("pootle_fs.fs_url", "foo")
    store = StoreDBFactory(
        translation_project=tp,
        parent=tp.directory,
        name="example_store.po")
    with pytest.raises(ValidationError):
        StoreFS.objects.create(
            store=store,
            pootle_path="/some/other/path.po",
            path=fs_path)


@pytest.mark.django_db
def test_save_store_fs_change_pootle_path_or_store(po_directory, tp0_store_fs):
    """You cant change a pootle_path if a store is associated
    unless you also remove the store association - and vice versa
    """
    fs_store = tp0_store_fs
    store = fs_store.store
    other_path = "/en/project0/other.po"

    fs_store.pootle_path = other_path
    with pytest.raises(ValidationError):
        fs_store.save()
    fs_store.store = None
    fs_store.save()

    assert fs_store.store is None
    assert fs_store.pootle_path == other_path

    fs_store.store = store
    with pytest.raises(ValidationError):
        fs_store.save()

    fs_store.pootle_path = store.pootle_path
    fs_store.save()

    assert fs_store.store == store
    assert fs_store.pootle_path == store.pootle_path


@pytest.mark.django_db
def test_save_store_fs_bad_lang(po_directory, tp0_store_fs):
    """Try to save a store with a non-existent lang code"""
    tp0_store_fs.store = None
    tp0_store_fs.pootle_path = "/fr/project0/example.po"

    with pytest.raises(ValidationError):
        tp0_store_fs.save()


@pytest.mark.django_db
def test_save_store_fs_bad_lang_with_store(po_directory, tp0_store, tp0_store_fs):
    """Try to save a store with a pootle_path that is different from the
    associated Store.
    """
    tp0_store_fs.store = tp0_store
    tp0_store_fs.pootle_path = "/language1/project0/example.po"
    with pytest.raises(ValidationError):
        tp0_store_fs.save()


@pytest.mark.django_db
def test_save_store_fs_bad_project(po_directory, tp0_store_fs):
    """Try to create a store_fs by pootle_path for a non existent project
    """
    tp0_store_fs.store = None
    tp0_store_fs.pootle_path = "/en/project0_BAD/example.po"
    with pytest.raises(ValidationError):
        tp0_store_fs.save()


@pytest.mark.django_db
def test_store_fs_plugin(po_directory, tp0_store_fs, no_fs_plugins, no_fs_files):
    store_fs = tp0_store_fs

    class DummyPlugin(object):

        file_class = FSFile

        def __init__(self, project):
            self.project = project

        def foo(self):
            return "bar"

    project = store_fs.project
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"

    with no_fs_plugins():
        with no_fs_files():

            @provider(fs_plugins, weak=False, sender=Project)
            def provide_plugin(**kwargs):
                return dict(dummyfs=DummyPlugin)

            @getter(fs_file, weak=False, sender=DummyPlugin)
            def fs_files_getter(**kwargs):
                return FSFile
            assert store_fs.plugin.project == project
            assert store_fs.plugin.foo() == "bar"
            assert isinstance(store_fs.file, FSFile)


@pytest.mark.django_db
def test_store_fs_plugin_bad(po_directory, tp0_store_fs):
    store_fs = tp0_store_fs
    project = store_fs.project
    project.config["pootle_fs.fs_type"] = None
    project.config["pootle_fs.fs_url"] = None
    # no plugin hooked up
    assert store_fs.plugin is None
    assert store_fs.file is None
    # plugin not recognised
    project.config["pootle_fs.fs_type"] = "PLUGIN_DOES_NOT_EXIST"
    project.config["pootle_fs.fs_url"] = "/foo/bar"
    del store_fs.__dict__["plugin"]
    del store_fs.__dict__["file"]
    assert store_fs.plugin is None
    assert store_fs.file is None
