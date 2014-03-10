#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

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
    return _require_permission('view', 'Can view a project',
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
    """Require the `suggest` permission."""
    return _require_permission('review', 'Can review translations',
                               pootle_content_type)


@pytest.fixture
def administrate(pootle_content_type):
    """Require the `suggest` permission."""
    return _require_permission('administrate', 'Can administrate a TP',
                               pootle_content_type)
