# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys

import pytest

from django.core.management import call_command, CommandError

from pootle_fs.utils import FSPlugin
from pootle_project.models import Project


@pytest.mark.django_db
@pytest.mark.cmd
def test_init_fs_project_cmd_bad_lang(capsys):
    fs_path = "/test/fs/path"
    tr_path = "<language_code>/<filename>.<ext>"

    with pytest.raises(CommandError):
        call_command("init_fs_project", "foo", fs_path, tr_path, "-l BAD_LANG")


@pytest.mark.django_db
@pytest.mark.cmd
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="broken on windows")
def test_init_fs_project_cmd_nosync(settings, test_fs, tmpdir, revision):
    settings.POOTLE_FS_WORKING_PATH = str(tmpdir)
    fs_path = test_fs.path("data/fs/example_fs/non_gnu_style_minimal/")
    tr_path = "<language_code>/<filename>.<ext>"
    call_command(
        "init_fs_project",
        "foo",
        fs_path,
        tr_path,
        "--nosync",
        "--checkstyle=standard",
        "--filetypes=po",
        "--source-language=en",
        "--name=Foo"
    )

    project = Project.objects.get(code='foo')
    assert project is not None
    assert project.code == "foo"
    assert project.fullname == "Foo"
    assert "po" in project.filetypes.values_list("name", flat=True)
    assert project.checkstyle == "standard"
    assert project.source_language.code == "en"

    assert project.config.get('pootle_fs.fs_type') == 'localfs'
    assert project.config.get('pootle_fs.fs_url') == fs_path
    assert project.config.get(
        'pootle_fs.translation_mappings')['default'] == tr_path

    assert project.translationproject_set.all().count() == 0
    plugin = FSPlugin(project)
    plugin.fetch()
    state = plugin.state()
    assert "fs_untracked: 1" in str(state)


@pytest.mark.django_db
@pytest.mark.cmd
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="broken on windows")
def test_init_fs_project_cmd(capsys, settings, test_fs, tmpdir, revision):
    settings.POOTLE_FS_WORKING_PATH = str(tmpdir)
    fs_path = test_fs.path("data/fs/example_fs/non_gnu_style_minimal/")
    tr_path = "<language_code>/<filename>.<ext>"
    call_command("init_fs_project", "foo", fs_path, tr_path)

    project = Project.objects.get(code='foo')
    assert project is not None

    assert project.config.get('pootle_fs.fs_type') == 'localfs'
    assert project.config.get('pootle_fs.fs_url') == fs_path
    assert project.config.get(
        'pootle_fs.translation_mappings')['default'] == tr_path

    assert project.translationproject_set.all().count() > 0
    state = FSPlugin(project).state()
    assert "Nothing to report" in str(state)


@pytest.mark.django_db
@pytest.mark.cmd
def test_init_fs_project_cmd_duplicated(capsys):
    fs_path = "/test/fs/path"
    tr_path = "<language_code>/<filename>.<ext>"
    call_command("init_fs_project", "foo", fs_path, tr_path, "--nosync")

    project = Project.objects.get(code='foo')
    assert project is not None

    with pytest.raises(CommandError):
        call_command("init_fs_project", "foo", fs_path, tr_path)


@pytest.mark.django_db
@pytest.mark.cmd
def test_cmd_init_fs_project_bad_filetype(capsys):
    fs_path = "/test/fs/path"
    tr_path = "<language_code>/<filename>.<ext>"

    with pytest.raises(CommandError):
        call_command(
            "init_fs_project",
            "foo",
            fs_path,
            tr_path,
            "--filetypes", "NO_SUCH_FILETYPE")


@pytest.mark.django_db
@pytest.mark.cmd
def test_cmd_init_fs_project_bad_filepath(capsys):
    fs_path = "/test/fs/path"
    tr_path = "<language_code>/<filename>.<ext>"

    with pytest.raises(CommandError) as e:
        call_command(
            "init_fs_project",
            "foo",
            fs_path,
            tr_path,
            "--filetypes", "po")
    assert not Project.objects.filter(code="foo").exists()
    assert "Source directory does not exist" in str(e)
