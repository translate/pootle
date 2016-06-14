# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

from pootle.core.delegate import config
from pootle_project.models import Project


def _repr_value(value):
    if not isinstance(value, (str, unicode)):
        value_class = type(value).__name__
        return (
            "%s(%s)"
            % (value_class,
               json.dumps(value)))
    return value


def _test_config_get(out, key, model=None, instance=None, as_repr=False):
    expected = ""
    conf = config.get(model, instance=instance)
    expected = conf.get_config(key)
    expected_class = type(expected).__name__
    expected = json.dumps(expected)
    if not as_repr:
        expected = "%s(%s)" % (expected_class, expected)
    assert expected == out


def _test_config_list(out, model=None, instance=None, object_field=None):
    conf_list = config.get(model, instance=instance).list_config()
    if model:
        item_name = str(model._meta)
        if instance:
            if object_field:
                identifier = getattr(instance, object_field)
            else:
                identifier = instance.pk
            item_name = "%s[%s]" % (item_name, identifier)
    else:
        item_name = "Pootle"
    expected = []
    items = []
    name_col = 25
    key_col = 25
    for k, v in conf_list:
        if model:
            ct = str(model._meta)
            if instance:
                if object_field:
                    pk = getattr(
                        instance,
                        object_field)
                else:
                    pk = instance.pk
                name = "%s[%s]" % (ct, pk)
            else:
                name = ct
        else:
            name = "Pootle"
        if len(name) > name_col:
            name_col = len(name)
        if len(k) > key_col:
            key_col = len(k)
        items.append((name, k, v))
    format_string = "{: <%d} {: <%d} {: <30}" % (name_col, key_col)
    for name, key, value in items:
        expected.append(
            format_string.format(
                item_name, k, _repr_value(v)))
    if not items:
        assert out == "No configuration found\n"
    else:
        assert out == "%s\n" % ("\n".join(expected))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_list(capfd):
    # no config set for anything
    call_command("config")
    out, err = capfd.readouterr()
    _test_config_list(out)

    # no config set for key foo
    call_command("config", "-l", "foo")
    out, err = capfd.readouterr()
    _test_config_list(out)

    config.get().set_config("foo", ["bar"])

    call_command("config")
    out, err = capfd.readouterr()
    _test_config_list(out)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_list_model(capfd):
    # no config set for anything
    call_command("config", "pootle_project.project")
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project)

    # no config set for key foo
    call_command("config", "pootle_project.project", "-l", "foo")
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project)

    config.get(Project).set_config("foo", ["bar"])

    call_command("config", "pootle_project.project")
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_list_instance(no_config_env, capfd):
    project = Project.objects.get(code="project0")

    # no config set for anything
    call_command("config", "pootle_project.project", str(project.pk))
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project, instance=project)

    # no config set for key foo
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-l", "foo")
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project, instance=project)

    config.get(Project, instance=project).set_config("foo", ["bar"])

    call_command("config", "pootle_project.project", str(project.pk))
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project, instance=project)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_list_instance_object_field(no_config_env, capfd):
    project = Project.objects.get(code="project0")

    # no config set for anything
    call_command(
        "config",
        "pootle_project.project",
        project.code,
        "-o", "code")
    out, err = capfd.readouterr()
    _test_config_list(
        out,
        model=Project,
        instance=project,
        object_field="code")

    # no config set for key foo
    call_command(
        "config",
        "pootle_project.project",
        project.code,
        "-o", "code",
        "-l", "foo")
    out, err = capfd.readouterr()
    _test_config_list(
        out,
        model=Project,
        instance=project,
        object_field="code")

    config.get(Project, instance=project).set_config("foo", ["bar"])

    call_command(
        "config",
        "pootle_project.project",
        project.code,
        "-o", "code")
    out, err = capfd.readouterr()
    _test_config_list(
        out,
        model=Project,
        instance=project,
        object_field="code")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_get(capfd):
    # -g requires a key
    with pytest.raises(CommandError):
        call_command("config", "-g")

    # no config set for key foo
    call_command("config", "-g", "foo")
    out, err = capfd.readouterr()
    _test_config_get(out, "foo")

    config.get().set_config("foo", ["bar"])

    call_command("config", "-g", "foo")
    out, err = capfd.readouterr()
    _test_config_get(out, "foo")

    config.get().append_config("foo", ["bar"])
    # multiple objects
    with pytest.raises(CommandError):
        call_command("config", "-g", "foo")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_get_model(capfd):
    # -g requires a key
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-g")
    # no config set for key foo
    call_command(
        "config",
        "pootle_project.project",
        "-g", "foo")
    out, err = capfd.readouterr()
    _test_config_get(out, "foo", model=Project)
    config.get(Project).set_config("foo", ["bar"])
    call_command(
        "config",
        "pootle_project.project",
        "-g", "foo")
    out, err = capfd.readouterr()
    _test_config_get(out, "foo", model=Project)

    config.get(Project).append_config("foo", ["bar"])
    # multiple objects
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-g", "foo")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_get_instance(capfd):
    project = Project.objects.get(code="project0")
    # -g requires a key
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-g")
    # no config set for key foo
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-g", "foo")
    out, err = capfd.readouterr()
    _test_config_get(
        out, "foo", model=Project, instance=project)
    config.get(Project, instance=project).set_config("foo", ["bar"])
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-g", "foo")
    out, err = capfd.readouterr()
    _test_config_get(
        out, "foo", model=Project, instance=project)

    config.get(Project, instance=project).append_config("foo", ["bar"])
    # multiple objects
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-g", "foo")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_set(capfd):

    # -s requires a key and value
    with pytest.raises(CommandError):
        call_command("config", "-s")
    with pytest.raises(CommandError):
        call_command("config", "-s", "foo")

    call_command("config", "-s", "foo", "bar")
    assert config.get().get_config("foo") == "bar"

    # we can set it something else
    call_command("config", "-s", "foo", "bar2")
    assert config.get().get_config("foo") == "bar2"

    config.get().append_config("foo", "bar3")
    # key must be unique for -s or non-existent
    with pytest.raises(CommandError):
        call_command("config", "-s", "foo", "bar")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_set_model(capfd):

    # -s requires a key and value
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-s")
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-s", "foo")

    call_command(
        "config",
        "pootle_project.project",
        "-s", "foo", "bar")
    assert config.get(Project).get_config("foo") == "bar"

    # we can set it something else
    call_command(
        "config",
        "pootle_project.project",
        "-s", "foo", "bar2")
    assert config.get(Project).get_config("foo") == "bar2"

    config.get(Project).append_config("foo", "bar3")
    # key must be unique for -s or non-existent
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-s", "foo", "bar")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_set_instance(capfd):
    project = Project.objects.get(code="project0")

    # -s requires a key and value
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-s")
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-s", "foo")

    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-s", "foo", "bar")
    assert config.get(
        Project,
        instance=project).get_config("foo") == "bar"

    # we can set it something else
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-s", "foo", "bar2")
    assert config.get(
        Project,
        instance=project).get_config("foo") == "bar2"

    config.get(
        Project,
        instance=project).append_config("foo", "bar3")
    # key must be unique for -s or non-existent
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-s", "foo", "bar")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_append(capfd):

    # -s requires a key and value
    with pytest.raises(CommandError):
        call_command("config", "-a")
    with pytest.raises(CommandError):
        call_command("config", "-a", "foo")

    call_command("config", "-a", "foo", "bar")
    assert config.get().get_config("foo") == "bar"

    # we can add another with same k/v
    call_command("config", "-a", "foo", "bar")

    assert config.get().list_config("foo") == [
        (u'foo', u'bar'), (u'foo', u'bar')]

    # and another with different v
    call_command("config", "-a", "foo", "bar2")
    assert config.get().list_config("foo") == [
        (u'foo', u'bar'),
        (u'foo', u'bar'),
        (u'foo', u'bar2')]

    # and another with different k
    call_command("config", "-a", "foo2", "bar3")
    assert config.get().get_config("foo2") == "bar3"


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_append_model(capfd):

    # -s requires a key and value
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-a")
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-a", "foo")

    call_command(
        "config",
        "pootle_project.project",
        "-a", "foo", "bar")
    assert config.get(Project).get_config("foo") == "bar"

    # we can add another with same k/v
    call_command(
        "config",
        "pootle_project.project",
        "-a", "foo", "bar")
    assert config.get(Project).list_config("foo") == [
        (u'foo', u'bar'), (u'foo', u'bar')]

    # and another with different v
    call_command(
        "config",
        "pootle_project.project",
        "-a", "foo", "bar2")
    assert config.get(Project).list_config("foo") == [
        (u'foo', u'bar'),
        (u'foo', u'bar'),
        (u'foo', u'bar2')]

    # and another with different k
    call_command(
        "config",
        "pootle_project.project",
        "-a", "foo2", "bar3")
    assert config.get(Project).get_config("foo2") == "bar3"


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_append_instance(capfd):
    project = Project.objects.get(code="project0")

    # -s requires a key and value
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-a")
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-a", "foo")

    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-a", "foo", "bar")
    assert config.get(
        Project,
        instance=project).get_config("foo") == "bar"

    # we can add another with same k/v
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-a", "foo", "bar")
    assert config.get(Project, instance=project).list_config("foo") == [
        (u'foo', u'bar'), (u'foo', u'bar')]

    # and another with different v
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-a", "foo", "bar2")
    assert config.get(Project, instance=project).list_config("foo") == [
        (u'foo', u'bar'),
        (u'foo', u'bar'),
        (u'foo', u'bar2')]

    # and another with different k
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-a", "foo2", "bar3")
    assert config.get(Project, instance=project).get_config("foo2") == "bar3"


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_clear(capfd):

    # -c requires a key and it should exist
    with pytest.raises(CommandError):
        call_command("config", "-c")

    # you can clear nothing
    call_command("config", "-c", "foo")

    # lets add a config and clear it
    config.get().append_config("foo", "bar")
    call_command("config", "-c", "foo")

    assert config.get().get_config("foo") is None

    # lets add 2 config and clear them
    config.get().append_config("foo", "bar")
    config.get().append_config("foo", "bar")
    call_command("config", "-c", "foo")
    assert config.get().get_config("foo") is None

    # lets add 2 config with diff v and clear them
    config.get().append_config("foo", "bar")
    config.get().append_config("foo", "bar2")
    call_command("config", "-c", "foo")
    assert config.get().get_config("foo") is None

    # lets add 2 config with diff k and clear one
    config.get().set_config("foo", "bar")
    config.get().set_config("foo2", "bar2")
    call_command("config", "-c", "foo")
    assert config.get().get_config("foo2") == "bar2"


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_clear_model(capfd):

    # -c requires a key
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "-c")

    # you can clear nothing
    call_command(
        "config",
        "pootle_project.project",
        "-c", "foo")

    # lets add a config and clear it
    config.get(Project).append_config("foo", "bar")
    call_command(
        "config",
        "pootle_project.project",
        "-c", "foo")

    assert config.get(Project).get_config("foo") is None

    # lets add 2 config and clear them
    config.get(Project).append_config("foo", "bar")
    config.get(Project).append_config("foo", "bar")
    call_command(
        "config",
        "pootle_project.project",
        "-c", "foo")

    assert config.get(Project).get_config("foo") is None

    # lets add 2 config with diff v and clear them
    config.get(Project).append_config("foo", "bar")
    config.get(Project).append_config("foo", "bar2")
    call_command(
        "config",
        "pootle_project.project",
        "-c", "foo")

    assert config.get(Project).get_config("foo") is None

    # lets add 2 config with diff k and clear one
    config.get(Project).set_config("foo", "bar")
    config.get(Project).set_config("foo2", "bar2")
    call_command(
        "config",
        "pootle_project.project",
        "-c", "foo")
    assert config.get(Project).get_config("foo2") == "bar2"


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_clear_instance(capfd):
    project = Project.objects.get(code="project0")

    # -c requires a key
    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            str(project.pk),
            "-c")

    # you can clear nothing
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-c", "foo")

    # lets add a config and clear it
    config.get(Project, instance=project).append_config("foo", "bar")
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-c", "foo")

    assert config.get(Project, instance=project).get_config("foo") is None

    # lets add 2 config and clear them
    config.get(Project, instance=project).append_config("foo", "bar")
    config.get(Project, instance=project).append_config("foo", "bar")
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-c", "foo")
    assert config.get(Project, instance=project).get_config("foo") is None

    # lets add 2 config with diff v and clear them
    config.get(Project, instance=project).append_config("foo", "bar")
    config.get(Project, instance=project).append_config("foo", "bar2")
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-c", "foo")
    assert config.get(Project, instance=project).get_config("foo") is None

    # lets add 2 config with diff k and clear one
    config.get(Project, instance=project).set_config("foo", "bar")
    config.get(Project, instance=project).set_config("foo2", "bar2")
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk),
        "-c", "foo")
    assert config.get(Project, instance=project).get_config("foo2") == "bar2"


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_config_bad(capfd):
    project = Project.objects.get(code="project0")

    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project")

    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.DOESNT_EXIST")

    with pytest.raises(CommandError):
        call_command(
            "config",
            "",
            str(project.pk))

    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "DOES_NOT_EXIST",
            "-o", "code")

    with pytest.raises(CommandError):
        # non-unique
        call_command(
            "config",
            "pootle_project.project",
            "po",
            "-o", "localfiletype")

    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            project.code,
            "-o", "OBJECT_FIELD_NOT_EXIST")

    with pytest.raises(CommandError):
        call_command(
            "config",
            "-j",
            "-s", "foo", "[BAD JSON]")

    with pytest.raises(CommandError):
        call_command(
            "config",
            "pootle_project.project",
            "asdf")


@pytest.mark.django_db
def test_cmd_config_set_json(capfd, json_objects):
    call_command(
        "config",
        "-j",
        "-s", "foo", json.dumps(json_objects))
    if isinstance(json_objects, tuple):
        json_objects = list(json_objects)
    assert config.get(key="foo") == json_objects
    capfd.readouterr()
    call_command(
        "config",
        "-j",
        "-g", "foo")
    out, err = capfd.readouterr()
    assert json.loads(out) == json_objects
    call_command(
        "config",
        "-g", "foo")
    out, err = capfd.readouterr()
    assert out == _repr_value(json_objects)


@pytest.mark.django_db
def test_cmd_config_append_json(capfd, json_objects):
    call_command(
        "config",
        "pootle_project.project",
        "-j",
        "-a", "foo", json.dumps(json_objects))
    if isinstance(json_objects, tuple):
        json_objects = list(json_objects)
    assert config.get(Project, key="foo") == json_objects
    capfd.readouterr()
    call_command(
        "config",
        "pootle_project.project",
        "-j",
        "-g", "foo")
    out, err = capfd.readouterr()
    assert json.loads(out) == json_objects

    call_command(
        "config",
        "pootle_project.project",
        "-g", "foo")
    out, err = capfd.readouterr()
    assert out == _repr_value(json_objects)


@pytest.mark.django_db
def test_cmd_config_bad_flags(capfd, bad_config_flags):
    with pytest.raises(CommandError):
        call_command(
            "config",
            *bad_config_flags)


@pytest.mark.django_db
def test_cmd_config_long_instance_name(no_config_env, capfd):
    project = Project.objects.get(code="project0")
    project.code = "foobar" * 10
    project.save()
    config.get(Project, instance=project).append_config("foo", "bar")
    config.get(Project, instance=project).append_config("foo", "bar")
    call_command(
        "config",
        "pootle_project.project",
        project.code,
        "-o", "code")
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project, instance=project, object_field="code")


@pytest.mark.django_db
def test_cmd_config_long_key_name(no_config_env, capfd):
    project = Project.objects.get(code="project0")
    config.get(Project, instance=project).append_config("foobar" * 10, "bar")
    call_command(
        "config",
        "pootle_project.project",
        str(project.pk))
    out, err = capfd.readouterr()
    _test_config_list(out, model=Project, instance=project)
