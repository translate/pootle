#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _

from pootle_app.models.directory import Directory
from pootle_app.models.permissions import (check_permission,
                                           get_matching_permissions)
from pootle_language.models import Language
from pootle_profile.models import get_profile
from pootle_project.models import Project
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


CLS2ATTR = {
    'TranslationProject': 'translation_project',
    'Project': 'project',
    'Language': 'language',
}


def get_path_obj(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        language_code = kwargs.pop('language_code', None)
        project_code = kwargs.pop('project_code', None)

        if language_code and project_code:
            try:
                path_obj = TranslationProject.objects.get(
                    language__code=language_code,
                    project__code=project_code
                )
            except TranslationProject.DoesNotExist:
                path_obj = None

            if path_obj is None:
                # Explicit selection via the UI: redirect either to
                # ``/language_code/`` or ``/projects/project_code/``.
                user_choice = request.COOKIES.get('user-choice', None)
                if user_choice and user_choice in ('language', 'project',):
                    url = {
                        'language': reverse('pootle-language-overview',
                                            args=[language_code]),
                        'project': reverse('pootle-project-overview',
                                           args=[project_code]),
                    }
                    response = redirect(url[user_choice])
                    response.delete_cookie('user-choice')

                    return response

                raise Http404
        elif language_code:
            path_obj = get_object_or_404(Language, code=language_code)
        elif project_code:
            path_obj = get_object_or_404(Project, code=project_code)
        else:  # No arguments: treat it like the root directory.
            path_obj = Directory.objects.root

        request.ctx_obj = path_obj

        return func(request, path_obj, *args, **kwargs)

    return wrapped


def get_resource_context(func):
    @wraps(func)
    def wrapped(request, path_obj, dir_path, *args, **kwargs):
        """Load :cls:`pootle_app.models.Directory` and
        :cls:`pootle_store.models.Store` models and populate the request
        object.

        :param path_obj: A path-like object object.
        :param dir_path: Path relative to the root of `path_obj`.
        :param filename: Optional filename.
        """
        filename = kwargs.pop('filename', '')

        ctx_path = path_obj.directory.pootle_path
        resource_path = dir_path
        pootle_path = ctx_path + dir_path

        directory = None
        store = None

        if filename:
            pootle_path = pootle_path + filename
            resource_path = resource_path + filename

            try:
                store = Store.objects.select_related(
                    'translation_project',
                    'parent',
                ).get(pootle_path=pootle_path)
                directory = store.parent
            except Store.DoesNotExist:
                raise Http404

        if directory is None:
            if dir_path:
                directory = get_object_or_404(Directory,
                                              pootle_path=pootle_path)
            else:
                directory = path_obj.directory

        request.store = store
        request.directory = directory
        request.pootle_path = pootle_path
        request.ctx_obj = store or directory
        request.ctx_path = ctx_path
        request.resource_path = resource_path

        return func(request, path_obj, dir_path, filename, *args, **kwargs)

    return wrapped


def permission_required(permission_codes):
    """Check for `permission_codes` in the current context.

    To retrieve the proper context, the `get_path_obj` decorator must be
    used along with this decorator.
    """
    def wrapped(func):
        @wraps(func)
        def _wrapped(request, *args, **kwargs):
            path_obj = args[0]
            directory = (path_obj if isinstance(path_obj, Directory)
                                  else path_obj.directory)

            # HACKISH: some old code relies on  `request.translation_project`,
            # `request.language` etc. being set, so we need to set that too.
            attr_name = CLS2ATTR.get(path_obj.__class__.__name__,
                                     'path_obj')
            setattr(request, attr_name, path_obj)

            request.profile = get_profile(request.user)
            request.permissions = get_matching_permissions(request.profile,
                                                           directory)

            if not permission_codes:
                return func(request, *args, **kwargs)

            permission_codes_list = permission_codes
            if isinstance(permission_codes, basestring):
                permission_codes_list = [permission_codes]

            for permission_code in permission_codes_list:
                if not check_permission(permission_code, request):
                    raise PermissionDenied(
                        _("Insufficient rights to access this page."),
                    )

            return func(request, *args, **kwargs)
        return _wrapped
    return wrapped


def admin_required(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied(
                _("You do not have rights to administer Pootle.")
            )
        return func(request, *args, **kwargs)

    return wrapped
