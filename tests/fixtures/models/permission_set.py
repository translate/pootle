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


def _require_permission_set(user, directory, permissions):
    """Helper to get/create a new PermissionSet."""
    from pootle_app.models.permissions import PermissionSet

    criteria = {
        'user': user,
        'directory': directory,
    }
    permission_set, created = PermissionSet.objects.get_or_create(**criteria)
    if created:
        permission_set.positive_permissions = permissions
        permission_set.save()

    return permission_set


@pytest.fixture
def nobody_ps(db, nobody, root, view, suggest):
    """Require permission sets at the root for the `nobody` user."""
    return _require_permission_set(nobody, root, [view, suggest])


@pytest.fixture
def default_ps(default, root, view, suggest, translate):
    """Require permission sets at the root for the `default` user."""
    return _require_permission_set(default, root, [view, suggest, translate])
