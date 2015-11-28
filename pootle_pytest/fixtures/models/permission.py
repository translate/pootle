#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def pootle_content_type(db):
    """Require the pootle ContentType."""
    from django.contrib.contenttypes.models import ContentType

    args = {
        'app_label': 'pootle_app',
        'model': 'directory',
    }
    content_type, created = ContentType.objects.get_or_create(**args)
    content_type.name = 'pootle'
    content_type.save()

    return content_type


def _require_permission(code, name, content_type):
    """Helper to get/create a new permission."""
    from django.contrib.auth.models import Permission

    criteria = {
        'codename': code,
        'name': name,
        'content_type': content_type,
    }
    permission, created = Permission.objects.get_or_create(**criteria)

    return permission


@pytest.fixture
def view(pootle_content_type):
    """Require the `view` permission."""
    return _require_permission('view', 'Can access a project',
                               pootle_content_type)


@pytest.fixture
def hide(pootle_content_type):
    """Require the `hide` permission."""
    return _require_permission('hide', 'Cannot access a project',
                               pootle_content_type)


@pytest.fixture
def suggest(pootle_content_type):
    """Require the `suggest` permission."""
    return _require_permission('suggest', 'Can make a suggestion',
                               pootle_content_type)


@pytest.fixture
def translate(pootle_content_type):
    """Require the `translate` permission."""
    return _require_permission('translate', 'Can submit translations',
                               pootle_content_type)


@pytest.fixture
def review(pootle_content_type):
    """Require the `review` permission."""
    return _require_permission('review', 'Can review translations',
                               pootle_content_type)


@pytest.fixture
def administrate(pootle_content_type):
    """Require the `suggest` permission."""
    return _require_permission('administrate', 'Can administrate a TP',
                               pootle_content_type)
