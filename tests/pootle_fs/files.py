#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from translate.storage.factory import getclass
from translate.storage.po import pofile

from pootle_fs.models import StoreFS

from pootle_fs.files import FSFile
from pootle_project.models import Project
from pootle_statistics.models import SubmissionTypes
from pootle_store.constants import POOTLE_WINS


@pytest.mark.django_db
def test_wrap_store_fs_bad(settings, tmpdir):

    with pytest.raises(TypeError):
        FSFile("NOT A STORE_FS")


@pytest.mark.django_db
def test_wrap_store_fs(settings, tmpdir):
    """Add a store_fs for a store that doesnt exist yet"""
    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir), "fs_file_test")
    project = Project.objects.get(code="project0")
    pootle_path = "/language0/%s/example.po" % project.code
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        pootle_path=pootle_path,
        path=fs_path)
    fs_file = FSFile(store_fs)
    assert (
        fs_file.file_path
        == os.path.join(
            settings.POOTLE_FS_WORKING_PATH, project.code,
            store_fs.path.strip("/")))
    assert fs_file.file_exists is False
    assert fs_file.latest_hash is None
    assert fs_file.pootle_changed is False
    assert fs_file.fs_changed is False
    assert fs_file.store is None
    assert fs_file.store_exists is False
    assert fs_file.deserialize() is None
    assert fs_file.serialize() is None
    assert str(fs_file) == "<FSFile: %s::%s>" % (pootle_path, fs_path)
    assert hash(fs_file) == hash(
        "%s::%s::%s::%s"
        % (fs_file.path,
           fs_file.pootle_path,
           fs_file.store_fs.last_sync_hash,
           fs_file.store_fs.last_sync_revision))
    assert fs_file == FSFile(store_fs)
    testdict = {}
    testdict[fs_file] = "foo"
    testdict[FSFile(store_fs)] = "bar"
    assert len(testdict.keys()) == 1
    assert testdict.values()[0] == "bar"


@pytest.mark.django_db
def test_wrap_store_fs_with_store(settings, tmpdir, tp0_store):
    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir), "fs_file_test")
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        path=fs_path,
        store=tp0_store)
    project = tp0_store.translation_project.project
    fs_file = FSFile(store_fs)
    assert (
        fs_file.file_path
        == os.path.join(
            settings.POOTLE_FS_WORKING_PATH, project.code,
            store_fs.path.strip("/")))
    assert fs_file.file_exists is False
    assert fs_file.latest_hash is None
    assert fs_file.fs_changed is False
    assert fs_file.pootle_changed is True
    assert fs_file.store == tp0_store
    assert fs_file.store_exists is True
    serialized = fs_file.serialize()
    assert serialized
    assert serialized == tp0_store.serialize()
    assert fs_file.deserialize() is None


@pytest.mark.django_db
def test_wrap_store_fs_with_file(settings, tmpdir, tp0_store, test_fs):
    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir), "fs_file_test")
    project = Project.objects.get(code="project0")
    pootle_path = "/language0/%s/example.po" % project.code
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        path=fs_path,
        pootle_path=pootle_path)
    fs_file = FSFile(store_fs)
    os.makedirs(os.path.dirname(fs_file.file_path))
    with test_fs.open("data/po/complex.po") as src:
        with open(fs_file.file_path, "w") as target:
            data = src.read()
            target.write(data)
    assert fs_file.pootle_changed is False
    assert fs_file.fs_changed is True
    assert fs_file.file_exists is True
    assert fs_file.latest_hash == str(os.stat(fs_file.file_path).st_mtime)
    assert isinstance(fs_file.deserialize(), pofile)
    assert str(fs_file.deserialize()) == data


@pytest.mark.django_db
def test_wrap_store_fs_push_no_store(store_fs_file):
    fs_file = store_fs_file
    assert fs_file.store_fs.last_sync_revision is None
    assert fs_file.store_fs.last_sync_hash is None
    # does nothing there is no store
    hashed = fs_file.latest_hash
    fs_file.push()
    assert fs_file.latest_hash == hashed
    assert fs_file.store_fs.last_sync_hash is None


@pytest.mark.django_db
def test_wrap_store_fs_push(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.push()
    assert fs_file.file_exists is True
    assert fs_file.read()
    # after push the store and fs should always match
    assert fs_file.read() == fs_file.serialize()
    # pushing again does nothing once the Store and file are synced
    fs_file.on_sync(
        fs_file.latest_hash, fs_file.store.data.max_unit_revision)
    fs_file.push()
    assert fs_file.read() == fs_file.serialize()


@pytest.mark.django_db
def test_wrap_store_fs_pull(store_fs_file):
    fs_file = store_fs_file
    fs_file.pull()
    assert fs_file.store
    assert fs_file.serialize()
    unit_count = fs_file.store.units.count()
    assert unit_count == len(fs_file.deserialize().units) - 1
    # pulling again will do nothing once the Store and file are synced
    fs_file.on_sync(
        fs_file.latest_hash, fs_file.store.data.max_unit_revision)
    fs_file.pull()
    assert unit_count == len(fs_file.deserialize().units) - 1


@pytest.mark.django_db
def test_wrap_store_fs_read(store_fs_file):
    fs_file = store_fs_file
    with open(fs_file.file_path, "r") as src:
        assert fs_file.read() == src.read()
    fs_file.remove_file()
    assert fs_file.read() is None


@pytest.mark.django_db
def test_wrap_store_fs_remove_file(store_fs_file):
    fs_file = store_fs_file
    fs_file.remove_file()
    assert fs_file.file_exists is False


@pytest.mark.django_db
def test_wrap_store_fs_delete(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.push()
    assert fs_file.store
    assert fs_file.file_exists is True
    fs_file.delete()
    assert fs_file.store.obsolete is True
    assert fs_file.file_exists is False
    assert fs_file.store_fs.pk is None


@pytest.mark.django_db
def test_wrap_store_fs_readd(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.push()
    fs_file.store.makeobsolete()
    fs_file.pull()
    assert not fs_file.store.obsolete


@pytest.mark.django_db
def test_wrap_store_fs_bad_stage(store_fs_file_store, caplog):
    fs_file = store_fs_file_store
    fs_file._sync_to_pootle()
    rec = caplog.records.pop()
    assert "disappeared" in rec.message
    assert rec.levelname == "WARNING"


@pytest.mark.django_db
def test_wrap_store_fs_create_store(store_fs_file):
    fs_file = store_fs_file
    assert fs_file.store is None
    assert fs_file.store_exists is False
    fs_file.create_store()
    assert fs_file.store.pootle_path == fs_file.pootle_path
    assert fs_file.store_fs.store == fs_file.store
    assert fs_file.store.fs.get() == fs_file.store_fs


@pytest.mark.django_db
def test_wrap_store_fs_on_sync(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.pull()
    fs_file.on_sync(
        fs_file.latest_hash, fs_file.store.data.max_unit_revision)
    fs_file.store_fs.resolve_conflict = None
    fs_file.store_fs.staged_for_merge = False
    fs_file.store_fs.last_sync_hash = fs_file.latest_hash
    fs_file.store_fs.last_sync_revision = fs_file.store.get_max_unit_revision()


@pytest.mark.django_db
def test_wrap_store_fs_pull_merge_pootle_wins(store_fs_file):
    fs_file = store_fs_file
    fs_file.pull()
    unit = fs_file.store.units[0]
    unit.target = "FOO"
    unit.save()
    with open(fs_file.file_path, "r+") as target:
        ttk = getclass(target)(target.read())
        target.seek(0)
        ttk.units[1].target = "BAR"
        target.write(str(ttk))
        target.truncate()
    assert fs_file.fs_changed is True
    assert fs_file.pootle_changed is True
    # this ensures POOTLE_WINS
    fs_file.store_fs.resolve_conflict = POOTLE_WINS
    fs_file.pull(merge=True)
    assert fs_file.store.units[0].target == "FOO"
    assert fs_file.store.units[0].get_suggestions()[0].target == "BAR"


@pytest.mark.django_db
def test_wrap_store_fs_pull_merge_pootle_wins_again(store_fs_file):
    fs_file = store_fs_file
    fs_file.pull()
    unit = fs_file.store.units[0]
    unit.target = "FOO"
    unit.save()
    with open(fs_file.file_path, "r+") as target:
        ttk = getclass(target)(target.read())
        target.seek(0)
        ttk.units[1].target = "BAR"
        target.write(str(ttk))
        target.truncate()
    assert fs_file.fs_changed is True
    assert fs_file.pootle_changed is True
    fs_file.pull(merge=True, pootle_wins=True)
    assert fs_file.store.units[0].target == "FOO"
    assert fs_file.store.units[0].get_suggestions()[0].target == "BAR"


@pytest.mark.django_db
def test_wrap_store_fs_pull_merge_fs_wins(store_fs_file):
    fs_file = store_fs_file
    fs_file.pull()
    unit = fs_file.store.units[0]
    unit.target = "FOO"
    unit.save()
    with open(fs_file.file_path, "r+") as target:
        ttk = getclass(target)(target.read())
        target.seek(0)
        ttk.units[1].target = "BAR"
        target.write(str(ttk))
        target.truncate()
    assert fs_file.fs_changed is True
    assert fs_file.pootle_changed is True
    fs_file.pull(merge=True)
    assert fs_file.store.units[0].target == "BAR"
    assert fs_file.store.units[0].get_suggestions()[0].target == "FOO"


@pytest.mark.django_db
def test_wrap_store_fs_pull_merge_fs_wins_again(store_fs_file):
    fs_file = store_fs_file
    fs_file.pull()
    unit = fs_file.store.units[0]
    unit.target = "FOO"
    unit.save()
    with open(fs_file.file_path, "r+") as target:
        ttk = getclass(target)(target.read())
        target.seek(0)
        ttk.units[1].target = "BAR"
        target.write(str(ttk))
        target.truncate()
    assert fs_file.fs_changed is True
    assert fs_file.pootle_changed is True
    fs_file.pull(merge=True, pootle_wins=False)
    assert fs_file.store.units[0].target == "BAR"
    assert fs_file.store.units[0].get_suggestions()[0].target == "FOO"


@pytest.mark.django_db
def test_wrap_store_fs_pull_merge_default(store_fs_file):
    fs_file = store_fs_file
    fs_file.pull()
    unit = fs_file.store.units[0]
    unit.target = "FOO"
    unit.save()
    with open(fs_file.file_path, "r+") as target:
        ttk = getclass(target)(target.read())
        target.seek(0)
        ttk.units[1].target = "BAR"
        target.write(str(ttk))
        target.truncate()
    assert fs_file.fs_changed is True
    assert fs_file.pootle_changed is True
    fs_file.pull(merge=True)
    assert fs_file.store.units[0].target == "BAR"
    assert fs_file.store.units[0].get_suggestions()[0].target == "FOO"


@pytest.mark.django_db
def test_wrap_store_fs_pull_submission_type(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.push()
    with open(fs_file.file_path, "r+") as target:
        ttk = getclass(target)(target.read())
        target.seek(0)
        ttk.units[1].target = "BAR"
        target.write(str(ttk))
        target.truncate()
    fs_file.pull()
    assert (
        fs_file.store.units[0].submission_set.latest().type
        == SubmissionTypes.SYSTEM)


@pytest.mark.django_db
def test_fs_file_latest_author(system, member2):

    member2.email = "member2@poot.le"
    member2.save()

    class DummyPlugin(object):
        pootle_user = system

    class DummyFile(FSFile):

        _author_name = None
        _author_email = None

        def __init__(self):
            pass

        @property
        def plugin(self):
            return DummyPlugin()

        @property
        def latest_author(self):
            return self._author_name, self._author_email

    myfile = DummyFile()
    assert myfile.latest_user == system
    myfile._author_name = "DOES NOT EXIST"
    assert myfile.latest_user == system
    myfile._author_email = member2.email
    assert myfile.latest_user == member2
    myfile._author_name = member2.username
    assert myfile.latest_user == member2
    myfile._author_email = None
    assert myfile.latest_user == system
    myfile._author_email = "DOESNT@EXIST.EMAIL"
    assert myfile.latest_user == member2
    myfile._author_name = "DOES NOT EXIST"
    assert myfile.latest_user == system
