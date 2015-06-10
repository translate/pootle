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
from pootle_project.models import Project, ProjectResource
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .exceptions import Http400
from .url_helpers import split_pootle_path


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
        pootle_path = request.GET.get('path', None)
        if pootle_path is not None:
            language_code, project_code, dir_path, filename = \
                split_pootle_path(pootle_path)
            kwargs['dir_path'] = dir_path
            kwargs['filename'] = filename

        if language_code and project_code:
            try:
                path_obj = TranslationProject.objects.live().get(
                    language__code=language_code,
                    project__code=project_code,
                    project__disabled=False
                )
            except TranslationProject.DoesNotExist:
                path_obj = None

            if path_obj is None and not request.is_ajax():
                # Explicit selection via the UI: redirect either to
                # ``/language_code/`` or ``/projects/project_code/``.
                user_choice = request.COOKIES.get('user-choice', None)
                if user_choice and user_choice in ('language', 'project',):
                    url = {
                        'language': reverse('pootle-language-overview',
                                            args=[language_code]),
                        'project': reverse('pootle-project-overview',
                                           args=[project_code, '', '']),
                    }
                    response = redirect(url[user_choice])
                    response.delete_cookie('user-choice')

                    return response

                raise Http404
        elif language_code:
            path_obj = get_object_or_404(Language, code=language_code)
        elif project_code:
            path_obj = get_object_or_404(Project, code=project_code,
                                         disabled=False)
        else:  # No arguments: all user-accessible projects
            user_projects = Project.accessible_by_user(request.user)
            user_projects = Project.objects.enabled() \
                                   .filter(code__in=user_projects)

            path_obj = ProjectSet(user_projects, '/projects/')

            # HACKISH: inject directory so that permissions can be
            # queried
            directory = Directory.objects.get(pootle_path='/projects/')
            setattr(path_obj, 'directory', directory)

        request.ctx_obj = path_obj
        request.ctx_path = path_obj.pootle_path
        request.resource_obj = path_obj
        request.pootle_path = path_obj.pootle_path

        return func(request, path_obj, *args, **kwargs)

    return wrapped


def set_resource(request, path_obj, dir_path, filename):
    """Load :cls:`pootle_app.models.Directory` and
    :cls:`pootle_store.models.Store` models and populate the request
    object.

    :param path_obj: A path-like object object.
    :param dir_path: Path relative to the root of `path_obj`.
    :param filename: Optional filename.
    """
    obj_directory = getattr(path_obj, 'directory', path_obj)
    ctx_path = obj_directory.pootle_path
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
            directory = obj_directory

    request.store = store
    request.directory = directory
    request.pootle_path = pootle_path

    request.resource_obj = store or (directory if dir_path else path_obj)
    request.resource_path = resource_path
    request.ctx_obj = path_obj or request.resource_obj
    request.ctx_path = ctx_path


def set_project_resource(request, path_obj, dir_path, filename):
    """Loads :cls:`pootle_app.models.Directory` and
    :cls:`pootle_store.models.Store` models and populates the
    request object.

    This is the same as `set_resource` but operates at the project level
    across all languages.

    :param path_obj: A :cls:`pootle_project.models.Project` object.
    :param dir_path: Path relative to the root of `path_obj`.
    :param filename: Optional filename.
    """
    query_ctx_path = ''.join(['/%/', path_obj.code, '/'])
    query_pootle_path = query_ctx_path + dir_path

    obj_directory = getattr(path_obj, 'directory', path_obj)
    ctx_path = obj_directory.pootle_path
    resource_path = dir_path
    pootle_path = ctx_path + dir_path

    if filename:
        query_pootle_path = query_pootle_path + filename
        pootle_path = pootle_path + filename
        resource_path = resource_path + filename

        resources = Store.objects.extra(
            where=[
                'pootle_store_store.pootle_path LIKE %s',
                'pootle_store_store.pootle_path NOT LIKE %s',
            ], params=[query_pootle_path, '/templates/%']
        ).select_related('translation_project__language')
    else:
        resources = Directory.objects.extra(
            where=[
                'pootle_app_directory.pootle_path LIKE %s',
                'pootle_app_directory.pootle_path NOT LIKE %s',
            ], params=[query_pootle_path, '/templates/%']
        ).select_related('parent')

    if not resources.exists():
        raise Http404

    request.store = None
    request.directory = None
    request.pootle_path = pootle_path

    request.resource_obj = ProjectResource(resources, pootle_path)
    request.resource_path = resource_path
    request.ctx_obj = path_obj or request.resource_obj
    request.ctx_path = ctx_path


def get_resource(func):
    @wraps(func)
    def wrapped(request, path_obj, dir_path, *args, **kwargs):
        """Get resources associated to the current context."""
        filename = kwargs.pop('filename', '')

        try:
            directory = getattr(path_obj, 'directory', path_obj)
            if directory.is_project() and (dir_path or filename):
                set_project_resource(request, path_obj, dir_path, filename)
            else:
                set_resource(request, path_obj, dir_path, filename)
        except Http404:
            if not request.is_ajax():
                user_choice = request.COOKIES.get('user-choice', None)
                if user_choice and user_choice in ('language', 'resource',):
                    project = (path_obj if isinstance(path_obj, Project)
                                        else path_obj.project)
                    url = reverse('pootle-project-overview',
                                  args=[project.code, dir_path, filename])
                    response = redirect(url)
                    response.delete_cookie('user-choice')

                    return response

            raise Http404

        return func(request, path_obj, dir_path=dir_path, filename=filename, *args, **kwargs)

    return wrapped


def permission_required(permission_code):
    """Check for `permission_code` in the current context.

    To retrieve the proper context, the `get_path_obj` decorator must be
    used along with this decorator.
    """
    def wrapped(func):
        @wraps(func)
        def _wrapped(request, *args, **kwargs):
            path_obj = args[0]
            directory = getattr(path_obj, 'directory', path_obj)

            # HACKISH: some old code relies on  `request.translation_project`,
            # `request.language` etc. being set, so we need to set that too.
            attr_name = CLS2ATTR.get(path_obj.__class__.__name__,
                                     'path_obj')
            setattr(request, attr_name, path_obj)

            request.permissions = get_matching_permissions(request.user, directory)

            if not permission_code:
                return func(request, *args, **kwargs)

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
