#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

import cStringIO
import os

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import ugettext as _

from Pootle import indexpage, pan_app, projects
from Pootle.misc.jtoolkit_django import process_django_request_args

from pootle_app.views.util  import render_to_kid, render_jtoolkit
from pootle_app.views.auth  import redirect
from pootle_app.core        import Language, Project
from pootle_app.fs_models   import Store, Directory, Search, search_from_state
from pootle_app.url_manip   import strip_trailing_slash
from pootle_app             import store_iteration
from pootle_app.translation_project import TranslationProject
from pootle_app.permissions import get_matching_permissions, PermissionError, check_permission
from pootle_app.profile     import get_profile
from pootle_app.views.language import dispatch
from pootle_app.convert     import convert_table

from project_index import view as project_index_view
from translate_page import find_and_display
from admin import view as translation_project_admin_view

from Pootle import pootlefile

################################################################################

def get_language(f):
    def decorated_f(request, language_code, *args, **kwargs):
        try:
            language = Language.objects.get(code=language_code)
            return f(request, language, *args, **kwargs)
        except Language.DoesNotExist:
            return redirect('/', message=_("The language %s is not defined for this Pootle installation" % language_code))                    
    return decorated_f

def get_translation_project(f):
    def decorated_f(request, language_code, project_code, *args, **kwargs):
        try:
            translation_project = TranslationProject.objects.select_related(depth=1).get(language__code=language_code,
                                                                                         project__code=project_code)
            return f(request, translation_project, *args, **kwargs)
        except TranslationProject.DoesNotExist:
            # No such TranslationProject.  It might be because the
            # language code doesn't exist...
            if Language.objects.filter(code=language_code).count() == 0:
                return redirect('/', message=_('The language "%s" is not defined for this Pootle installation' % language_code))
            # ...or if the language exists, maybe the project code is
            # invalid...
            elif Project.objects.filter(code=project_code).count() == 0:
                return redirect('/', message=_('The project "%s" is not defined for this Pootle installation' % project_code))
            # ...but if both the language and project codes are valid,
            # then we simply don't have a corresponding
            # TranslationProject
            else:
                return redirect('/%s' % language_code, message=_('The project "%s" does not exist for the language %s' % (project_code, language_code)))
    return decorated_f

def set_request_context(f):
    def decorated_f(request, translation_project, *args, **kwargs):
        # For now, all permissions in a translation project are
        # relative to the root of that translation project.
        request.permissions = get_matching_permissions(
            get_profile(request.user), translation_project.directory)
        request.translation_project = translation_project
        return f(request, translation_project, *args, **kwargs)
    return decorated_f

################################################################################

@get_language
def language_index(request, language):
    return render_jtoolkit(indexpage.LanguageIndex(language, request))

@get_translation_project
@set_request_context
def translation_project_admin(request, translation_project):
    return translation_project_admin_view(request, translation_project)

@get_translation_project
@set_request_context
def translate_page(request, translation_project, dir_path):
    try:
        def next_store_item(search, store_name, item):
            return store_iteration.get_next_match(directory,
                                                  store_name,
                                                  item,
                                                  search)

        def prev_store_item(search, store_name, item):
            return store_iteration.get_prev_match(directory,
                                                  store_name,
                                                  item,
                                                  search)

        directory = translation_project.directory.get_relative(dir_path)
        return find_and_display(request, directory, next_store_item, prev_store_item)
    except PermissionError, msg:
        return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), message=msg)

@get_translation_project
@set_request_context
def project_index(request, translation_project, dir_path):
    directory = Directory.objects.get(pootle_path=translation_project.directory.pootle_path + dir_path)
    try:
        return project_index_view(request, translation_project, directory)
    except PermissionError, msg:
        return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), message=msg)

def handle_translation_file(request, translation_project, file_path):
    pootle_path = translation_project.directory.pootle_path + (file_path or '')
    store = Store.objects.get(pootle_path=pootle_path)
    try:
        def get_item(itr, item):
            try:
                return itr.next()
            except StopIteration:
                return item

        def next_store_item(search, store_name, item):
            return store, get_item(search.next_matches(store, item), item - 1)

        def prev_store_item(search, store_name, item):
            if item > 0:
                return store, get_item(search.prev_matches(store, item), item + 1)
            else:
                return store, 0

        return find_and_display(request, store.parent, next_store_item, prev_store_item)
    except PermissionError, e:
        return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), 
                        message=e.args[0])

@get_translation_project
@set_request_context
def export_zip(request, translation_project, file_path):
    if not check_permission("archive", request):
        return redirect('/%s/%s' % (translation_project.language.code, translation_project.project.code),
                        message=_('You do not have the right to create ZIP archives.'))
    pootle_path = translation_project.directory.pootle_path + (file_path or '')
    try:
        path_obj = Directory.objects.get(pootle_path=pootle_path)
    except Directory.DoesNotExist:
        path_obj = Store.objects.get(pootle_path=pootle_path[:-1])
    stores = store_iteration.iter_stores(path_obj, Search.from_request(request))
    archivecontents = translation_project.get_archive(stores)
    return HttpResponse(archivecontents, content_type="application/zip")

@get_translation_project
@set_request_context
def export_sdf(request, translation_project, file_path):
    if not check_permission("pocompile", request):
        return redirect('/%s/%s' % (translation_project.language.code, translation_project.project.code),
                        message=_('You do not have the right to create SDF files.'))
    return HttpResponse(translation_project.getoo(), content_type="text/tab-separated-values")

MIME_TYPES = {
    "po":  "text/x-gettext-translation; charset=%(encoding)s",
    "csv": "text/csv; charset=%(encoding)s",
    "xlf": "application/x-xliff; charset=%(encoding)s",
    "ts":  "application/x-linguist; charset=%(encoding)s",
    "mo":  "application/x-gettext-translation" }

@get_translation_project
@set_request_context
def export(request, translation_project, file_path, format):
    def send(pootle_file):
        encoding = getattr(pootle_file, "encoding", "UTF-8")
        content_type = MIME_TYPES[format] % dict(encoding=encoding)
        if format == translation_project.project.localfiletype:
            return HttpResponse(str(pootle_file), content_type=content_type)
        else:
            convert_func = convert_table[translation_project.project.localfiletype, format]
            output_file = cStringIO.StringIO()
            input_file  = cStringIO.StringIO(str(pootle_file))
            convert_func(input_file, output_file, None)
            return HttpResponse(output_file.getvalue(), content_type=content_type)
    store = Store.objects.get(pootle_path=translation_project.directory.pootle_path + file_path)
    return pootlefile.with_store(translation_project, store, send)

@get_translation_project
@set_request_context
def handle_file(request, translation_project, file_path):
    return handle_translation_file(request, translation_project, file_path)
