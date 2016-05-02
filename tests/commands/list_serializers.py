# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

from pootle.core.delegate import serializers, deserializers
from pootle.core.plugin import provider
from pootle_project.models import Project


class EGSerializer1(object):
    pass


class EGSerializer2(object):
    pass


class EGDeserializer1(object):
    pass


class EGDeserializer2(object):
    pass


def serializer_provider_factory(sender=None):

    @provider(serializers, sender=sender)
    def serializer_provider(**kwargs):
        return OrderedDict(
            (("serializer1", EGSerializer1),
             ("serializer2", EGSerializer2)))
    return serializer_provider


def deserializer_provider_factory(sender=None):

    @provider(deserializers, sender=sender)
    def deserializer_provider(**kwargs):
        return OrderedDict(
            (("deserializer1", EGDeserializer1),
             ("deserializer2", EGDeserializer2)))
    return deserializer_provider


def _test_serializer_list(out, err, model=None):
    NO_SERIALS = "There are no serializers set up on your system"

    serials = serializers.gather(model)

    expected = []

    if not serials.keys():
        expected.append(NO_SERIALS)

    if serials.keys():
        heading = "Serializers"
        expected.append("\n%s" % heading)
        expected.append("-" * len(heading))
        for name, klass in serials.items():
            expected.append("{: <30} {: <50} ".format(name, klass))
    assert out == "%s\n" % ("\n".join(expected))


def _test_deserializer_list(out, err, model=None):
    NO_DESERIALS = "There are no deserializers set up on your system"

    deserials = deserializers.gather(model)

    expected = []

    if not deserials.keys():
        expected.append(NO_DESERIALS)

    if deserials.keys():
        heading = "Deserializers"
        expected.append("\n%s" % heading)
        expected.append("-" * len(heading))
        for name, klass in deserials.items():
            expected.append("{: <30} {: <50} ".format(name, klass))
    assert out == "%s\n" % ("\n".join(expected))


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_list_serializers(capsys):

    # tests with no de/serializers set up
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # set up some serializers
    serial_provider = serializer_provider_factory()
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    serializers.disconnect(serial_provider)

    # set up some deserializers
    deserial_provider = deserializer_provider_factory()
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # empty again
    deserializers.disconnect(deserial_provider)
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # with both set up
    deserial_provider = deserializer_provider_factory()
    serial_provider = serializer_provider_factory()
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)
    serializers.disconnect(serial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_list_serializers_for_model(capsys):

    # tests with no de/serializers set up
    call_command("list_serializers", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err, Project)

    # set up some serializers
    serial_provider = serializer_provider_factory(Project)
    call_command("list_serializers", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err, Project)
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    serializers.disconnect(serial_provider)

    # set up some deserializers
    deserial_provider = deserializer_provider_factory(Project)
    call_command("list_serializers", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err, Project)
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # empty again
    deserializers.disconnect(deserial_provider)
    call_command("list_serializers", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err, Project)
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # with both set up
    deserial_provider = deserializer_provider_factory(Project)
    serial_provider = serializer_provider_factory(Project)
    call_command("list_serializers", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err, Project)
    call_command("list_serializers")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)
    serializers.disconnect(serial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_list_deserializers(capsys):

    # tests with no de/deserializers set up
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)

    # set up some deserializers
    deserial_provider = deserializer_provider_factory()
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)

    deserializers.disconnect(deserial_provider)

    # set up some deserializers
    deserial_provider = deserializer_provider_factory()
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)

    # empty again
    deserializers.disconnect(deserial_provider)
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)

    # with both set up
    deserial_provider = deserializer_provider_factory()
    deserial_provider = deserializer_provider_factory()
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)
    deserializers.disconnect(deserial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_list_deserializers_for_model(capsys):

    # tests with no de/deserializers set up
    call_command("list_serializers", "-d", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err, Project)

    # set up some deserializers
    deserial_provider = deserializer_provider_factory(Project)
    call_command("list_serializers", "-d", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err, Project)
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)

    deserializers.disconnect(deserial_provider)

    # set up some deserializers
    deserial_provider = deserializer_provider_factory(Project)
    call_command("list_serializers", "-d", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err, Project)
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)

    # empty again
    deserializers.disconnect(deserial_provider)
    call_command("list_serializers", "-d", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err, Project)
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)

    # with both set up
    deserial_provider = deserializer_provider_factory(Project)
    deserial_provider = deserializer_provider_factory(Project)
    call_command("list_serializers", "-d", "-m", "pootle_project.project")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err, Project)
    call_command("list_serializers", "-d")
    out, err = capsys.readouterr()
    _test_deserializer_list(out, err)
    deserializers.disconnect(deserial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_list_serializers_bad_models(capsys):
    with pytest.raises(CommandError):
        call_command("list_serializers", "-m", "foo")
    with pytest.raises(CommandError):
        call_command("list_serializers", "-m", "foo.bar")
