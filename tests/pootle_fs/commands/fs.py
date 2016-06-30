# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import ProjectDBFactory

from django.core.management import call_command, CommandError

from pootle.core.delegate import config
from pootle.core.exceptions import NotConfiguredError, MissingPluginError
from pootle_fs.display import ResponseDisplay, StateDisplay
from pootle_fs.management.commands import FSAPISubCommand
from pootle_fs.management.commands.fs_commands.state import StateCommand
from pootle_fs.utils import FSPlugin
from pootle_project.models import Project


@pytest.mark.django_db
def test_fs_cmd(project_fs, capsys):
    call_command("fs")
    out, err = capsys.readouterr()
    expected = []
    for project in Project.objects.order_by("pk"):
        try:
            plugin = FSPlugin(project)
            expected.append(
                "%s\t%s"
                % (project.code, plugin.fs_url))
        except (MissingPluginError, NotConfiguredError):
            pass
    expected = (
        "%s\n"
        % '\n'.join(expected))
    assert out == expected


@pytest.mark.django_db
def test_fs_cmd_info(project_fs, capsys):
    call_command("fs", "info", project_fs.project.code)
    out, err = capsys.readouterr()
    lines = []
    lines.append(
        "Project: %s"
        % project_fs.project.code)
    lines.append("type: %s" % project_fs.fs_type)
    lines.append("URL: %s" % project_fs.fs_url)
    assert out == "%s\n" % ("\n".join(lines))


@pytest.mark.django_db
def test_fs_cmd_no_projects(capsys):
    for project in Project.objects.all():
        conf = config.get(Project, instance=project)
        conf.clear_config("pootle_fs.fs_type")
        conf.clear_config("pootle_fs.fs_url")
    call_command("fs")
    out, err = capsys.readouterr()
    assert out == "No projects configured\n"


@pytest.mark.django_db
def test_fs_cmd_bad_project(project_fs, capsys, english):
    with pytest.raises(CommandError):
        call_command(
            "fs", "state", "BAD_PROJECT_CODE")

    with pytest.raises(CommandError):
        call_command(
            "fs", "BAD_SUBCOMMAND", "project0")

    with pytest.raises(CommandError):
        call_command(
            "fs", "state",
            ProjectDBFactory(source_language=english).code)


@pytest.mark.django_db
def test_fs_cmd_unstage_response(capsys, localfs_envs):
    state_type, plugin = localfs_envs
    action = "unstage"
    original_state = plugin.state()
    call_command("fs", action, plugin.project.code)
    out, err = capsys.readouterr()
    plugin_response = getattr(plugin, action)(state=original_state)
    display = ResponseDisplay(plugin_response)
    assert out.strip() == str(display).strip()


@pytest.mark.django_db
def test_fs_cmd_unstage_staged_response(capsys, localfs_staged_envs):
    state_type, plugin = localfs_staged_envs
    action = "unstage"
    original_state = plugin.state()
    call_command("fs", action, plugin.project.code)
    out, err = capsys.readouterr()
    plugin_response = getattr(plugin, action)(
        state=original_state)
    display = ResponseDisplay(plugin_response)
    assert out.strip() == str(display).strip()


@pytest.mark.django_db
def test_fs_cmd_api(capsys, dummy_cmd_response, fs_path_qs, possible_actions):
    __, cmd, cmd_args, plugin_kwargs = possible_actions
    __, pootle_path, fs_path = fs_path_qs
    dummy_response, api_call = dummy_cmd_response
    project = dummy_response.context.context.project
    if fs_path:
        cmd_args += ["-p", fs_path]
    if pootle_path:
        cmd_args += ["-P", pootle_path]
    forceable = ["add", "fetch", "rm"]
    if cmd in forceable and not plugin_kwargs.get("force"):
        plugin_kwargs["force"] = False
    plugin_kwargs["pootle_path"] = pootle_path
    plugin_kwargs["fs_path"] = fs_path
    api_call(dummy_response, cmd, **plugin_kwargs)
    call_command("fs", cmd, project.code, *cmd_args)
    out, err = capsys.readouterr()
    assert out == str(ResponseDisplay(dummy_response))


@pytest.mark.django_db
def test_fs_cmd_state(capsys, dummy_cmd_state, fs_path_qs):
    __, pootle_path, fs_path = fs_path_qs
    plugin, state_class = dummy_cmd_state
    project = plugin.project
    cmd = "state"
    cmd_args = []
    plugin_kwargs = {}
    if fs_path:
        cmd_args += ["-p", fs_path]
    if pootle_path:
        cmd_args += ["-P", pootle_path]
    if pootle_path:
        plugin_kwargs["pootle_path"] = pootle_path
    if fs_path:
        plugin_kwargs["fs_path"] = fs_path
    dummy_state = state_class(
        plugin, pootle_path=pootle_path, fs_path=fs_path)
    call_command("fs", cmd, project.code, *cmd_args)
    out, err = capsys.readouterr()
    assert out == str(StateDisplay(dummy_state))


def test_fs_cmd_state_colors():
    state_cmd = StateCommand()
    for k, (pootle_style, fs_style) in state_cmd.colormap.items():
        if pootle_style:
            pootle_style = getattr(state_cmd.style, "FS_%s" % pootle_style)
        if fs_style:
            fs_style = getattr(state_cmd.style, "FS_%s" % fs_style)
        assert state_cmd.get_style(k) == (pootle_style, fs_style)


def test_fs_cmd_response_colors():
    sub_cmd = FSAPISubCommand()
    for k, (pootle_style, fs_style) in sub_cmd.colormap.items():
        if pootle_style:
            pootle_style = getattr(sub_cmd.style, "FS_%s" % pootle_style)
        if fs_style:
            fs_style = getattr(sub_cmd.style, "FS_%s" % fs_style)
        assert sub_cmd.get_style(k) == (pootle_style, fs_style)
