# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import time
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from pootle.i18n.gettext import ugettext as _
from pootle_app.models.permissions import (check_permission,
                                           get_matching_permissions)
from pootle_project.models import Project, ProjectSet

from .cache import get_cache
from .exceptions import Http400
from .url_helpers import split_pootle_path


logger = logging.getLogger(__name__)


CLS2ATTR = {
    'TranslationProject': 'translation_project',
    'Project': 'project',
    'Language': 'language',
}


def get_path_obj(func):
    from pootle_language.models import Language
    from pootle_translationproject.models import TranslationProject

    @wraps(func)
    def wrapped(request, *args, **kwargs):
        if request.is_ajax():
            pootle_path = request.GET.get('path', None)
            if pootle_path is None:
                raise Http400(_('Arguments missing.'))

            language_code, project_code, dir_path, filename = \
                split_pootle_path(pootle_path)
            kwargs['dir_path'] = dir_path
            kwargs['filename'] = filename

            # Remove potentially present but unwanted args
            try:
                del kwargs['language_code']
                del kwargs['project_code']
            except KeyError:
                pass
        else:
            language_code = kwargs.pop('language_code', None)
            project_code = kwargs.pop('project_code', None)

        if language_code and project_code:
            try:
                path_obj = TranslationProject.objects.get_for_user(
                    user=request.user,
                    language_code=language_code,
                    project_code=project_code,
                )
            except TranslationProject.DoesNotExist:
                path_obj = None

            if path_obj is None:
                if not request.is_ajax():
                    # Explicit selection via the UI: redirect either to
                    # ``/language_code/`` or ``/projects/project_code/``
                    user_choice = request.COOKIES.get('user-choice', None)
                    if user_choice and user_choice in ('language', 'project',):
                        url = {
                            'language': reverse('pootle-language-browse',
                                                args=[language_code]),
                            'project': reverse('pootle-project-browse',
                                               args=[project_code, '', '']),
                        }
                        response = redirect(url[user_choice])
                        response.delete_cookie('user-choice')

                        return response

                raise Http404
        elif language_code:
            user_projects = Project.accessible_by_user(request.user)
            language = get_object_or_404(Language, code=language_code)
            children = language.children \
                               .filter(project__code__in=user_projects)
            language.set_children(children)
            path_obj = language
        elif project_code:
            try:
                path_obj = Project.objects.get_for_user(project_code,
                                                        request.user)
            except Project.DoesNotExist:
                raise Http404
        else:  # No arguments: all user-accessible projects
            user_projects = Project.objects.for_user(request.user)
            path_obj = ProjectSet(user_projects)

        request.ctx_obj = path_obj
        request.ctx_path = path_obj.pootle_path
        request.resource_obj = path_obj
        request.pootle_path = path_obj.pootle_path

        return func(request, path_obj, *args, **kwargs)

    return wrapped


def permission_required(permission_code):
    """Checks for `permission_code` in the current context.

    To retrieve the proper context, the `get_path_obj` decorator must be
    used along with this decorator.
    """
    def wrapped(func):
        @wraps(func)
        def _wrapped(request, *args, **kwargs):
            path_obj = args[0]
            directory = getattr(path_obj, 'directory', path_obj)

            # HACKISH: some old code relies on
            # `request.translation_project`, `request.language` etc.
            # being set, so we need to set that too.
            attr_name = CLS2ATTR.get(path_obj.__class__.__name__,
                                     'path_obj')
            setattr(request, attr_name, path_obj)

            request.permissions = get_matching_permissions(request.user,
                                                           directory)

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


class persistent_property(object):
    """
    Similar to cached_property, except it caches in the memory cache rather
    than on the instance if possible.

    By default it will look on the class for an attribute `cache_key` to get
    the class cache_key. The attribute can be changed by setting the `key_attr`
    parameter in the decorator.

    The class cache_key is combined with the name of the decorated property
    to get the final cache_key for the property.

    If no cache_key attribute is present or returns None, it will use instance
    caching by default. This behaviour can be switched off by setting
    `always_cache` to False in the decorator.
    """

    def __init__(self, func, name=None, key_attr=None, always_cache=True,
                 ns_attr=None, version_attr=None):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = name or func.__name__
        self.ns_attr = ns_attr or "ns"
        self.key_attr = key_attr or "cache_key"
        self.version_attr = version_attr or "sw_version"
        self.always_cache = always_cache

    def _get_cache_key(self, instance):
        ns = getattr(instance, self.ns_attr, "pootle.core")
        sw_version = getattr(instance, self.version_attr, "")
        cache_key = getattr(instance, self.key_attr, None)
        if cache_key:
            return (
                "%s.%s.%s.%s"
                % (ns, sw_version, cache_key, self.name))

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        cache_key = self._get_cache_key(instance)
        if cache_key:
            cache = get_cache('lru')
            cached = cache.get(cache_key)
            if cached is not None:
                # cache hit
                return cached
            # cache miss
            start = time.time()
            res = self.func(instance)
            timetaken = time.time() - start
            cache.set(cache_key, res)
            logger.debug(
                "[cache] generated %s in %s seconds",
                cache_key, timetaken)
            return res
        elif self.always_cache:
            res = instance.__dict__[self.name] = self.func(instance)
            return res
        return self.func(instance)
