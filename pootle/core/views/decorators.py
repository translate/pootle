# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools

from django.core.exceptions import PermissionDenied

from pootle.i18n.gettext import ugettext as _
from pootle_app.models.permissions import get_matching_permissions


def check_directory_permission(permission_codename, request, directory):
    """Checks if the current user has `permission_codename`
    permissions for a given directory.
    """
    if request.user.is_superuser:
        return True

    if permission_codename == 'view':
        context = None

        context = getattr(directory, "tp", None)
        if context is None:
            context = getattr(directory, "project", None)

        if context is None:
            return True

        return context.is_accessible_by(request.user)

    return (
        "administrate" in request.permissions
        or permission_codename in request.permissions)


def set_permissions(f):

    @functools.wraps(f)
    def method_wrapper(self, request, *args, **kwargs):
        if not hasattr(request, "permissions"):
            request.permissions = get_matching_permissions(
                request.user,
                self.permission_context) or []
        return f(self, request, *args, **kwargs)
    return method_wrapper


def requires_permission(permission):

    def class_wrapper(f):

        @functools.wraps(f)
        def method_wrapper(self, request, *args, **kwargs):
            directory_permission = check_directory_permission(
                permission, request, self.permission_context)
            check_class_permission = (
                directory_permission
                and hasattr(self, "required_permission")
                and permission != self.required_permission)
            if check_class_permission:
                directory_permission = check_directory_permission(
                    self.required_permission, request, self.permission_context)
            if not directory_permission:
                raise PermissionDenied(
                    _("Insufficient rights to access this page."), )
            return f(self, request, *args, **kwargs)
        return method_wrapper
    return class_wrapper
