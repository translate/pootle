# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command, CommandError

from pootle.core.plugin import provider
from pootle_fs.delegate import fs_plugins
from pootle_fs.plugin import Plugin
from pootle_fs.presets import FS_PRESETS
from pootle_project.models import Project


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_defaults(settings):
    call_command(
        "create_project",
        "foo0",
        "--preset-mapping=gnu")
    foo0 = Project.objects.get(code="foo0")
    assert foo0.fullname == "Foo0"
    assert foo0.checkstyle == "standard"
    assert foo0.filetypes.first().name == "po"
    assert foo0.source_language.code == "en"
    assert foo0.disabled is False
    assert foo0.report_email == ""

    assert (
        foo0.config["pootle_fs.translation_mapping"]
        == dict(default=FS_PRESETS["gnu"][0]))
    assert foo0.config["pootle_fs.fs_type"] == "localfs"
    assert (
        foo0.config["pootle_fs.fs_url"]
        == ("{POOTLE_TRANSLATION_DIRECTORY}%s"
            % foo0.code))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_existing_project(settings):
    call_command(
        "create_project",
        "foo0",
        "--preset-mapping=gnu")

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo0",
            "--preset-mapping=gnu")
    assert (
        "'code': [u'Project with this Code already exists.'"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_title(capfd):
    call_command(
        "create_project",
        "foo1",
        "--name=Bar1",
        "--preset-mapping=gnu")
    foo1 = Project.objects.get(code="foo1")
    assert foo1.fullname == "Bar1"


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_checkstyle(capfd):
    call_command(
        "create_project",
        "foo0",
        "--checkstyle=minimal",
        "--preset-mapping=gnu")
    foo0 = Project.objects.get(code="foo0")
    assert foo0.checkstyle == "minimal"

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo1",
            "--preset-mapping=gnu",
            "--checkstyle=DOESNOTEXIST")
    assert (
        "Error: argument --checkstyle: invalid choice: u'DOESNOTEXIST'"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_filetypes(capfd):
    call_command(
        "create_project",
        "foo0",
        "--filetype=ts",
        "--preset-mapping=gnu")
    foo0 = Project.objects.get(code="foo0")
    assert foo0.filetypes.first().name == "ts"
    call_command(
        "create_project",
        "foo1",
        "--filetype=ts",
        "--filetype=po",
        "--preset-mapping=gnu")
    foo1 = Project.objects.get(code="foo1")
    assert (
        list(foo1.filetypes.values_list("name", flat=True))
        == ["ts", "po"])

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo2",
            "--preset-mapping=gnu",
            "--filetype=DOESNOTEXIST")
    assert (
        "Error: argument --filetype: invalid choice: u'DOESNOTEXIST'"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_report_email(capfd):
    call_command(
        "create_project",
        "foo0",
        "--report-email=foo@bar.com",
        "--preset-mapping=gnu")
    foo0 = Project.objects.get(code="foo0")
    assert foo0.report_email == "foo@bar.com"

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo0",
            "--report-email=foo@bar",
            "--preset-mapping=gnu")
    assert (
        "CommandError: [u'Enter a valid email address.']"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_source_language(language0):
    call_command(
        "create_project",
        "foo0",
        "--preset-mapping=gnu",
        "--source-language=%s" % language0.code)
    foo0 = Project.objects.get(code="foo0")
    assert foo0.source_language == language0

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo0",
            "--preset-mapping=gnu",
            "--source-language=DOESNOTEXIST")
    assert (
        "CommandError: Source language DOESNOTEXIST does not exist"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_disabled():
    call_command(
        "create_project",
        "foo0",
        "--preset-mapping=gnu",
        "--disabled")
    foo0 = Project.objects.get(code="foo0")
    assert foo0.disabled is True


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_preset_mapping():
    call_command(
        "create_project",
        "foo0",
        "--preset-mapping=nongnu")
    foo0 = Project.objects.get(code="foo0")
    assert (
        foo0.config["pootle_fs.translation_mapping"]
        == dict(default=FS_PRESETS["nongnu"][0]))
    with pytest.raises(CommandError) as e:
        # cant specify both mapping and preset-mapping
        call_command(
            "create_project",
            "foo1",
            "--preset-mapping=gnu",
            "--mapping='/<language_code>/<dir_path>/<filename>.<ext>'")
    assert (
        "Error: argument --mapping: not allowed with argument --preset-mapping"
        in str(e))
    with pytest.raises(CommandError) as e:
        # must specify one or other mapping or preset
        call_command(
            "create_project",
            "foo1")
    assert (
        "Error: one of the arguments --preset-mapping --mapping is required"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_mapping():
    call_command(
        "create_project",
        "foo0",
        "--mapping=/<language_code>/<dir_path>/<filename>.<ext>")
    foo0 = Project.objects.get(code="foo0")
    assert (
        foo0.config["pootle_fs.translation_mapping"]
        == dict(default=u'/<language_code>/<dir_path>/<filename>.<ext>'))

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo1",
            "--mapping=NOTAMAPPING")
    assert (
        "Translation mapping 'NOTAMAPPING'"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_fs_type():

    class DummyPlugin(Plugin):
        pass

    @provider(fs_plugins)
    def dummy_fs_plugin(**kwargs):
        return dict(dummyfs=DummyPlugin)

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo0",
            "--preset-mapping=gnu",
            "--fs-type=dummyfs")
    assert (
        "Parameter --fs-url is mandatory when --fs-type is not `localfs`"
        in str(e))

    call_command(
        "create_project",
        "foo0",
        "--preset-mapping=gnu",
        "--fs-type=dummyfs",
        "--fs-url=DUMMYURL")
    foo0 = Project.objects.get(code="foo0")
    assert (
        foo0.config["pootle_fs.fs_type"]
        == "dummyfs")

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo1",
            "--preset-mapping=gnu",
            "--fs-type=DOESNOTEXIST")
    assert (
        "Error: argument --fs-type: invalid choice"
        in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_create_project_fs_url():
    call_command(
        "create_project",
        "foo0",
        "--preset-mapping=gnu",
        "--fs-url={POOTLE_TRANSLATION_DIRECTORY}special_foo0")
    foo0 = Project.objects.get(code="foo0")
    assert (
        foo0.config["pootle_fs.fs_url"]
        == "{POOTLE_TRANSLATION_DIRECTORY}special_foo0")

    call_command(
        "create_project",
        "foo1",
        "--preset-mapping=gnu",
        "--fs-url=/abs/path/to/foo1")
    foo1 = Project.objects.get(code="foo1")
    assert (
        foo1.config["pootle_fs.fs_url"]
        == "/abs/path/to/foo1")

    with pytest.raises(CommandError) as e:
        call_command(
            "create_project",
            "foo2",
            "--preset-mapping=gnu",
            "--fs-url=NOTANABSOLUTEPATH")
    assert (
        "Enter an absolute path "
        in str(e))
    with pytest.raises(Project.DoesNotExist):
        Project.objects.get(code="foo2")
