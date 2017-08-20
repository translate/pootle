# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ValidationError

from pootle_app.models.directory import Directory


@pytest.mark.django_db
def test_directory_create_name_with_slashes_or_backslashes(root):
    """Test Directories are not created with (back)slashes on their name."""

    with pytest.raises(ValidationError):
        Directory.objects.create(name="slashed/name", parent=root)

    with pytest.raises(ValidationError):
        Directory.objects.create(name="backslashed\\name", parent=root)


@pytest.mark.django_db
def test_directory_create_bad(root):
    """Test directory cannot be created with name and no parent or without name
    but no parent.
    """
    with pytest.raises(ValidationError):
        Directory.objects.create(name="name", parent=None)

    with pytest.raises(ValidationError):
        Directory.objects.create(name="", parent=root)


@pytest.mark.django_db
def test_dir_get_or_make_subdir(project0, language0, tp0, subdir0):
    foo = project0.directory.get_or_make_subdir("foo")
    assert not foo.tp
    assert foo == project0.directory.get_or_make_subdir("foo")

    foo = language0.directory.get_or_make_subdir("foo")
    assert not foo.tp
    assert foo == language0.directory.get_or_make_subdir("foo")

    foo = tp0.directory.get_or_make_subdir("foo")
    assert foo.tp == tp0
    assert foo == tp0.directory.get_or_make_subdir("foo")

    foo = subdir0.get_or_make_subdir("foo")
    assert foo.tp == subdir0.tp
    assert foo == subdir0.get_or_make_subdir("foo")
