# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture(scope="session")
def pootle_content_type():
    """Require the pootle ContentType."""
    from django.contrib.contenttypes.models import ContentType

    args = {
        'app_label': 'pootle_app',
        'model': 'directory',
    }
    return ContentType.objects.get(**args)


def _require_permission(code, name, content_type):
    """Helper to get/create a new permission."""
    from django.contrib.auth.models import Permission

    criteria = {
        'codename': code,
        'name': name,
        'content_type': content_type,
    }
    permission = Permission.objects.get_or_create(**criteria)[0]

    return permission


@pytest.fixture(scope="session")
def view(pootle_content_type):
    """Require the `view` permission."""
    return _require_permission('view', 'Can access a project',
                               pootle_content_type)


@pytest.fixture(scope="session")
def hide(pootle_content_type):
    """Require the `hide` permission."""
    return _require_permission('hide', 'Cannot access a project',
                               pootle_content_type)


@pytest.fixture(scope="session")
def administrate(pootle_content_type):
    """Require the `suggest` permission."""
    return _require_permission('administrate', 'Can administrate a TP',
                               pootle_content_type)


@pytest.fixture
def translate():
    """Require the `translate` permission."""
    from django.contrib.auth.models import Permission

    return Permission.objects.get(codename="translate")
