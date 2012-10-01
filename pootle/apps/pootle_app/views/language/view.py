#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
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

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from translate.misc.decorators import decorate

from pootle_app.models.directory import Directory
from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission)
from pootle_misc.baseurl import redirect
from pootle_profile.models import get_profile
from pootle_store.models import Store
from pootle_store.views import (translate_page, get_failing_checks,
                                get_view_units)
from pootle_translationproject.models import TranslationProject


def get_stats_headings():
    """returns a dictionary of localised headings"""
    return {
        "name":                   _("Name"),
        "translated":             _("Translated"),
        "translatedpercentage":   _("Translated percentage"),
        "translatedwords":        _("Translated words"),
        "fuzzy":                  _("Fuzzy"),
        "fuzzypercentage":        _("Fuzzy percentage"),
        "fuzzywords":             _("Fuzzy words"),
        "untranslated":           _("Untranslated"),
        "untranslatedpercentage": _("Untranslated percentage"),
        "untranslatedwords":      _("Untranslated words"),
        "total":                  _("Total"),
        "totalwords":             _("Total Words"),
        # Translators: noun. The graphical representation of translation status
        "progress":               _("Progress"),
        "summary":                _("Summary"),
        "need_translation":       _("Need Translation"),
        # Translators: The number of suggestions pending review
        "suggestions": _("Suggestions"),
        }


@decorate
def get_translation_project(f):
    def decorated_f(request, language_code, project_code, *args, **kwargs):
        translation_project = get_object_or_404(
            TranslationProject,
            language__code=language_code,
            project__code=project_code
        )

        return f(request, translation_project, *args, **kwargs)

    return decorated_f


@decorate
def set_request_context(f):
    def decorated_f(request, translation_project, *args, **kwargs):
        # For now, all permissions in a translation project are
        # relative to the root of that translation project.
        request.profile = get_profile(request.user)
        request.permissions = get_matching_permissions(
            request.profile, translation_project.directory
        )
        request.translation_project = translation_project

        return f(request, translation_project, *args, **kwargs)

    return decorated_f


@get_translation_project
@set_request_context
def translate(request, translation_project, dir_path=None):
    if dir_path:
        pootle_path = translation_project.pootle_path + dir_path
        request.directory = Directory.objects.get(pootle_path=pootle_path)
    else:
        request.directory = translation_project.directory

    return translate_page(request)


@get_translation_project
@set_request_context
def get_failing_checks_dir(request, translation_project, dir_path):
    if dir_path:
        pootle_path = translation_project.pootle_path + dir_path
        pathobj = Directory.objects.get(pootle_path=pootle_path)
    else:
        pathobj = translation_project

    return get_failing_checks(request, pathobj)


@get_translation_project
@set_request_context
def get_view_units_dir(request, translation_project, dir_path):
    if not check_permission("view", request):
        raise PermissionDenied(_("You do not have rights to access this "
                                 "translation project."))

    units_query = translation_project.units
    if dir_path:
        pootle_path = translation_project.pootle_path + dir_path
        units_query = units_query.filter(store__pootle_path__startswith=pootle_path)

    return get_view_units(request, units_query, store=False)


@get_translation_project
@set_request_context
def commit_file(request, translation_project, file_path):
    if not check_permission("commit", request):
        raise PermissionDenied(_("You do not have rights to commit files here"))

    pootle_path = translation_project.directory.pootle_path + file_path
    store = get_object_or_404(Store, pootle_path=pootle_path)
    result = translation_project.commit_file(request.user, store, request)

    return redirect(translation_project.directory.pootle_path)


@get_translation_project
@set_request_context
def update_file(request, translation_project, file_path):
    if not check_permission("commit", request):
        raise PermissionDenied(_("You do not have rights to update files here"))

    pootle_path = translation_project.directory.pootle_path + file_path
    store = get_object_or_404(Store, pootle_path=pootle_path)
    result = translation_project.update_file(request, store)

    return redirect(translation_project.directory.pootle_path)
