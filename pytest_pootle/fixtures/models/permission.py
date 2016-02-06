#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


def _require_permission(code, name):
    """Helper to get/create a new permission."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    args = {
        'app_label': 'pootle_app',
        'model': 'directory'}
    criteria = {
        'codename': code,
        'name': name,
        'content_type': ContentType.objects.get(**args)}
    permission, created = Permission.objects.get_or_create(**criteria)

    return permission


@pytest.fixture
def view():
    """Require the `view` permission."""
    return _require_permission('view', 'Can access a project')


@pytest.fixture
def hide():
    """Require the `hide` permission."""
    return _require_permission('hide', 'Cannot access a project')


@pytest.fixture
def suggest():
    """Require the `suggest` permission."""
    return _require_permission('suggest', 'Can make a suggestion')


@pytest.fixture
def translate():
    """Require the `translate` permission."""
    return _require_permission('translate', 'Can submit translations')


@pytest.fixture
def review():
    """Require the `review` permission."""
    return _require_permission('review', 'Can review translations')


@pytest.fixture
def administrate():
    """Require the `suggest` permission."""
    return _require_permission('administrate', 'Can administrate a TP')
