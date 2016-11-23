# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


def _require_permission_set(user, directory, positive_permissions=None,
                            negative_permissions=None):
    """Helper to get/create a new PermissionSet."""
    from pootle_app.models.permissions import PermissionSet

    criteria = {
        'user': user,
        'directory': directory,
    }
    permission_set = PermissionSet.objects.get_or_create(**criteria)[0]
    if positive_permissions is not None:
        permission_set.positive_permissions.set(positive_permissions)
    if negative_permissions is not None:
        permission_set.negative_permissions.set(negative_permissions)

    permission_set.save()

    return permission_set
