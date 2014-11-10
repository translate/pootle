#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import (check_permission,
                                           get_matching_permissions)

from .models import Unit, Store


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
    request.permissions = get_matching_permissions(request.user, directory)

    if not permission_code:
        return

    if not check_permission(permission_code, request):
        raise PermissionDenied(get_permission_message(permission_code))


def get_store_context(permission_codes):

    def wrap_f(f):

        @wraps(f)
        def decorated_f(request, pootle_path, *args, **kwargs):
            if pootle_path[0] != '/':
                pootle_path = '/' + pootle_path
            try:
                store = Store.objects.select_related('translation_project',
                                                     'parent') \
                                     .get(pootle_path=pootle_path)
            except Store.DoesNotExist:
                raise Http404

            _common_context(request, store.translation_project, permission_codes)
            request.store = store
            request.directory = store.parent

            return f(request, store, *args, **kwargs)

        return decorated_f

    return wrap_f


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
