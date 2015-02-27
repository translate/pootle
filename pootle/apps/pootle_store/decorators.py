#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

from functools import wraps

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import (check_permission,
                                           get_matching_permissions)

from .models import Unit


def get_permission_message(permission_code):
    """Returns a human-readable message when `permission_code` is not met
    by the current context.
    """
    default_message = _("Insufficient rights to access this directory.")

    return {
        'suggest': _('Insufficient rights to access suggestion mode.'),
        'translate': _('Insufficient rights to access translation mode.'),
        'review': _('Insufficient rights to access review mode.'),
    }.get(permission_code, default_message)


def _common_context(request, translation_project, permission_codes):
    """Adds common context to request object and checks permissions."""
    request.translation_project = translation_project
    _check_permissions(request, translation_project.directory,
                       permission_codes)


def _check_permissions(request, directory, permission_code):
    """Checks if the current user has enough permissions defined by
    `permission_code` in the current`directory`.
    """
    User = get_user_model()
    request.profile = User.get(request.user)
    request.permissions = get_matching_permissions(request.profile,
                                                   directory)

    if not permission_code:
        return

    if not check_permission(permission_code, request):
        raise PermissionDenied(get_permission_message(permission_code))


def get_unit_context(permission_codes):

    def wrap_f(f):

        @wraps(f)
        def decorated_f(request, uid, *args, **kwargs):
            unit = get_object_or_404(
                    Unit.objects.select_related("store__translation_project",
                                                "store__parent"),
                    id=uid,
            )
            _common_context(request, unit.store.translation_project,
                            permission_codes)
            request.unit = unit
            request.store = unit.store
            request.directory = unit.store.parent

            return f(request, unit, *args, **kwargs)

        return decorated_f

    return wrap_f
