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
from pootle_store.constants import POOTLE_WINS, SOURCE_WINS
from pootle_store.revision import StoreRevision


@pytest.mark.django_db
def test_wrap_store_fs_bad(settings, tmpdir):

    with pytest.raises(TypeError):
        FSFile("NOT A STORE_FS")


@pytest.mark.django_db
def test_wrap_store_fs(settings, tmpdir):
    """Add a store_fs for a store that doesnt exist yet
    """
    pootle_fs_path = os.path.join(str(tmpdir), "fs_file_test")
    settings.POOTLE_FS_PATH = pootle_fs_path
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
            pootle_fs_path, project.code,
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
    pootle_fs_path = os.path.join(str(tmpdir), "fs_file_test")
    settings.POOTLE_FS_PATH = pootle_fs_path
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        path=fs_path,
        store=tp0_store)
    project = tp0_store.translation_project.project
    fs_file = FSFile(store_fs)
    assert (
        fs_file.file_path
        == os.path.join(
            pootle_fs_path, project.code,
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
    pootle_fs_path = os.path.join(str(tmpdir), "fs_file_test")
    settings.POOTLE_FS_PATH = pootle_fs_path
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
def test_wrap_store_fs_fetch(store_fs_file):
    fs_file = store_fs_file
    fs_file.fetch()
    assert fs_file.store_fs.resolve_conflict == SOURCE_WINS


@pytest.mark.django_db
def test_wrap_store_fs_add(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.add()
    assert fs_file.store_fs.resolve_conflict == POOTLE_WINS


@pytest.mark.django_db
def test_wrap_store_fs_merge_pootle(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.merge(pootle_wins=True)
    assert fs_file.store_fs.resolve_conflict == POOTLE_WINS
    assert fs_file.store_fs.staged_for_merge is True


@pytest.mark.django_db
def test_wrap_store_fs_merge_fs(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.merge(pootle_wins=False)
    assert fs_file.store_fs.resolve_conflict == SOURCE_WINS
    assert fs_file.store_fs.staged_for_merge is True


@pytest.mark.django_db
def test_wrap_store_fs_rm(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.rm()
    assert fs_file.store_fs.staged_for_removal is True


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
    fs_file.on_sync()
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
    fs_file.on_sync()
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
    fs_file.fetch()
    fs_file.pull()
    fs_file.on_sync()
    assert fs_file.store_fs.resolve_conflict is None
    assert fs_file.store_fs.staged_for_merge is False
    assert fs_file.store_fs.last_sync_hash == fs_file.latest_hash
    assert (
        fs_file.store_fs.last_sync_revision
        == StoreRevision(fs_file.store).get_max_unit_revision())


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
    fs_file.add()
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
    # this ensures SOURCE_WINS
    fs_file.fetch()
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
def test_wrap_store_fs_pull_user(store_fs_file, member2):
    fs_file = store_fs_file
    fs_file.pull(user=member2)
    assert fs_file.store.units[0].submitted_by == member2


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
def test_wrap_store_fs_unstage_pootle_staged(store_fs_file_store):
    fs_file = store_fs_file_store
    assert fs_file.store_fs.pk
    fs_file.unstage()
    assert fs_file.store_fs.pk is None


@pytest.mark.django_db
def test_wrap_store_fs_unstage_fs_staged(store_fs_file):
    fs_file = store_fs_file
    assert fs_file.store_fs.pk
    fs_file.unstage()
    assert fs_file.store_fs.pk is None


@pytest.mark.django_db
def test_wrap_store_fs_unstage_merge_conflict_untracked(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.push()
    fs_file.merge(pootle_wins=True)

    # this is basically `staged_for_merge_pootle`, from `conflict_untracked`
    assert fs_file.store_fs.last_sync_hash is None
    assert fs_file.store_fs.last_sync_revision is None
    assert fs_file.store_fs.resolve_conflict == POOTLE_WINS
    assert fs_file.store_fs.staged_for_merge is True
    fs_file.unstage()
    assert fs_file.store_fs.last_sync_hash is None
    assert fs_file.store_fs.last_sync_revision is None
    assert fs_file.store_fs.resolve_conflict is None
    assert fs_file.store_fs.staged_for_merge is False
    # because the store_fs was `conflict_untracked` the store_fs is deleted
    # and the file/store are again `conflict_untracked`
    assert fs_file.store_fs.pk is None


@pytest.mark.django_db
def test_wrap_store_fs_unstage_merge_pootle(store_fs_file_store):
    fs_file = store_fs_file_store
    fs_file.push()
    fs_file.on_sync()
    with open(fs_file.file_path, "r") as f:
        ttk = getclass(f)(f.read())
    ttk.units[1].target = "NEW TARGET"
    with open(fs_file.file_path, "w") as f:
        f.write(str(ttk))
    unit = fs_file.store.units[0]
    unit.target = "CONFLICTING TARGET"
    unit.save()
    fs_file.merge(pootle_wins=True)
    assert fs_file.store_fs.last_sync_hash
    assert fs_file.store_fs.last_sync_revision
    assert fs_file.store_fs.resolve_conflict == POOTLE_WINS
    assert fs_file.store_fs.staged_for_merge is True
    fs_file.unstage()
    assert fs_file.store_fs.last_sync_hash
    assert fs_file.store_fs.last_sync_revision
    assert fs_file.store_fs.resolve_conflict is None
    assert fs_file.store_fs.staged_for_merge is False
    assert fs_file.store_fs.pk is not None
