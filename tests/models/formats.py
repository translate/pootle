# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.db import IntegrityError

from pootle.core.delegate import formats
from pootle_format.default import POOTLE_FORMATS
from pootle_format.models import FileExtension, Format
from pootle_format.registry import FormatRegistry


def _test_formats(registry, keys):
    formats = registry.formats
    assert formats.keys() == keys
    assert (
        list(Format.objects.filter(enabled=True).values_list("name", flat=True))
        == keys)
    assert list(registry) == keys
    assert registry.keys() == keys
    assert registry.items() == formats.items()
    assert registry.values() == formats.values()
    for key in keys:
        filetype = Format.objects.get(name=key)
        assert formats[key] == registry[key]
        assert (
            sorted(formats[key].items())
            == sorted(
                dict(
                    pk=filetype.pk,
                    name=filetype.name,
                    display_title=str(filetype),
                    title=filetype.title,
                    extension=str(filetype.extension),
                    template_extension=str(filetype.template_extension)).items()))


@pytest.mark.django_db
def test_file_extension_instance():
    """Tests the creation of a file extension
    """
    ext = FileExtension.objects.create(name="foo")
    assert ext.name == "foo"
    assert str(ext) == "foo"


@pytest.mark.django_db
def test_file_extension_bad():
    """Test that you cant add a duplicate file extension
    """
    FileExtension.objects.create(name="foo")

    with pytest.raises(IntegrityError):
        FileExtension.objects.create(name="foo")


@pytest.mark.django_db
def test_format_instance():
    """Tests the creation of a file extension
    """
    ext = FileExtension.objects.create(name="foo")
    filetype = Format.objects.create(
        extension=ext, template_extension=ext)
    assert str(filetype.template_extension) == str(ext)
    assert str(filetype) == "%s (%s/%s)" % (filetype.title, ext, ext)


@pytest.mark.django_db
def test_format_registry_instance(no_formats):
    """Tests the creation of a file extension
    """
    registry = FormatRegistry()
    _test_formats(registry, [])
    filetype = registry.register("foo", "foo")
    assert isinstance(filetype, Format)
    assert filetype.name == "foo"
    assert filetype.title == "Foo"
    assert str(filetype.extension) == "foo"
    _test_formats(registry, ["foo"])


@pytest.mark.django_db
def test_format_registry_reregister(no_formats):
    """Tests the creation of a file extension
    """

    registry = FormatRegistry()
    filetype = registry.register("foo", "foo")

    # you can re-register the same format
    new_filetype = registry.register("foo", "foo")
    assert new_filetype == filetype
    _test_formats(registry, ["foo"])

    # but if you change anything it will be updated
    new_filetype = registry.register("foo", "foo", title="Bar")
    assert new_filetype == filetype
    assert new_filetype.title == "Bar"
    _test_formats(registry, ["foo"])

    new_filetype = registry.register("foo", "bar")
    assert new_filetype == filetype
    assert new_filetype.title == "Bar"
    assert str(new_filetype.extension) == "bar"
    _test_formats(registry, ["foo"])


@pytest.mark.django_db
def test_format_registry_extensions(no_formats):
    """Tests the creation of a file extension
    """
    registry = FormatRegistry()
    filetype = registry.register("foo", "foo")

    # 2 filetypes can have the same extension
    filetype2 = registry.register("special_foo", "foo")
    assert str(filetype.extension) == "foo"
    assert str(filetype2.extension) == "foo"
    _test_formats(registry, ["foo", "special_foo"])


@pytest.mark.django_db
def test_format_registry_template_extension(no_formats):
    """Tests the creation of a file extension
    """
    registry = FormatRegistry()
    filetype = registry.register(
        "foo", "foo", template_extension="bar")
    assert str(filetype.template_extension) == "bar"
    _test_formats(registry, ["foo"])

    # 2 filetypes can have the same template extensions
    filetype2 = registry.register(
        "special_foo", "foo", template_extension="bar")
    assert str(filetype.template_extension) == "bar"
    assert str(filetype2.template_extension) == "bar"
    _test_formats(registry, ["foo", "special_foo"])


@pytest.mark.django_db
def test_format_registry_object(no_formats):
    format_registry = formats.get()
    assert isinstance(format_registry, FormatRegistry)
    assert format_registry.keys() == []
    format_registry.initialize()
    assert set(format_registry.keys()) == set([x[0] for x in POOTLE_FORMATS])
    for filetype in POOTLE_FORMATS:
        format_registry[filetype[0]] == filetype[1]
