# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from functools import wraps

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


def get_most_important_permission(permission_codes):
    if 'review' in permission_codes:
        return 'review'
    if 'translate' in permission_codes:
        return 'translate'
    return 'suggest'


def get_unit_context(permission_codes=None):

    def wrap_f(f):

        @wraps(f)
        def decorated_f(request, uid, *args, **kwargs):
            unit = get_object_or_404(
                Unit.objects.select_related("store__translation_project",
                                            "store__parent"),
                id=uid,
            )

            tp = unit.store.translation_project
            request.translation_project = tp

            request.permissions = get_matching_permissions(request.user,
                                                           tp.directory)

            if permission_codes is not None:
                perms = permission_codes
                if isinstance(perms, basestring):
                    perms = list(perms)

                if not any(check_permission(code, request) for code in perms):
                    raise PermissionDenied(get_permission_message(
                        get_most_important_permission(perms)))

            request.unit = unit
            request.store = unit.store
            request.directory = unit.store.parent

            return f(request, unit, *args, **kwargs)

        return decorated_f

    return wrap_f
