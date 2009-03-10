#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

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
from pootle_app.url_manip   import read_all_state
from pootle_app.permissions import get_matching_permissions, PermissionError
from pootle_app.profile     import get_profile

from project_index import view as project_index_view
from translate_page import find_and_display
from admin import view as translation_project_admin_view

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
                return redirect('/', message=_("The language %s is not defined for this Pootle installation" % language_code))
            # ...or if the language exists, maybe the project code is
            # invalid...
            elif Project.objects.filter(code=project_code).count() == 0:
                return redirect('/', message=_("The project %s is not defined for this Pootle installation" % project_code))
            # ...but if both the language and project codes are valid,
            # then we simply don't have a corresponding
            # TranslationProject
            else:
                return redirect('/%s' % language_code, message=_("The project %s does not exist for the language %s" % (project_code, language_code)))
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
    url_state = read_all_state(request.GET)
    search = search_from_state(translation_project, url_state['search'])
    try:
        def next_store_item(store_name, item):
            return store_iteration.get_next_match(directory,
                                                  store_name,
                                                  item,
                                                  search)

        def prev_store_item(store_name, item):
            return store_iteration.get_prev_match(directory,
                                                  store_name,
                                                  item,
                                                  search)

        directory = translation_project.directory.get_relative(dir_path)
        return find_and_display(request, directory, next_store_item, prev_store_item)

    except projects.RightsError, msg:
        return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), message=msg)

@get_translation_project
@set_request_context
def project_index(request, translation_project):
    try:
        return project_index_view(request, translation_project, translation_project.directory)
    except projects.RightsError, msg:
        return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), message=msg)

def handle_translation_file(request, translation_project, file_path):
    # Don't get confused here. request.GET contains HTTP
    # GET vars while get is a dictionary method
    url_state = read_all_state(request.GET)
    if url_state['translate_display'].view_mode != 'raw':
        # TBD: Ensure that store is a Store object
        pootle_path = translation_project.directory.pootle_path + (file_path or '')
        store = Store.objects.get(pootle_path=pootle_path)
        search = search_from_state(translation_project, url_state['search'])

        try:
            def get_item(itr, item):
                try:
                    return itr.next()
                except StopIteration:
                    return item

            def next_store_item(store_name, item):
                return store, get_item(search.next_matches(store, item), item - 1)

            def prev_store_item(store_name, item):
                if item > 0:
                    return store, get_item(search.prev_matches(store, item), item + 1)
                else:
                    return store, 0

            return find_and_display(request, store.parent, next_store_item, prev_store_item)
        except PermissionError, e:
            return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), 
                            message=e.args[0])
    else:
        pofile = translation_project.getpofile(file_path, freshen=False)
        encoding = getattr(pofile, "encoding", "UTF-8")
        content_type = "text/plain; charset=%s" % encoding
        return HttpResponse(open(pofile.filename).read(), content_type=content_type)

def handle_alternative_format(request, translation_project, file_path):
    basename, extension = os.path.splitext(file_path)
    pofilename = basename + os.extsep + translation_project.fileext
    extension = extension[1:]
    if extension == "mo":
        if not "pocompile" in translation_project.getrights(request.user):
            return redirect('/%s/%s' % (translation_project.language.code, translation_project.project.code), 
                            message=_('You do not have the right to create MO files.'))
    etag, filepath_or_contents = translation_project.convert(pofilename, extension)
    if etag:
        contents = open(filepath_or_contents).read()
    else:
        contents = filepath_or_contents
    content_type = ""
    if extension == "po":
        content_type = "text/x-gettext-translation; charset=UTF-8"
    elif extension == "csv":
        content_type = "text/csv; charset=UTF-8"
    elif extension == "xlf":
        content_type = "application/x-xliff; charset=UTF-8"
    elif extension == "ts":
        content_type = "application/x-linguist; charset=UTF-8"
    elif extension == "mo":
        content_type = "application/x-gettext-translation"
    return HttpResponse(contents, content_type=content_type)

def handle_zip(request, arg_dict, translation_project, file_path):
    if not "archive" in translation_project.getrights(request.user):
        return redirect('/%s/%s' % (translation_project.language.code, translation_project.project.code),
                        message=_('You do not have the right to create ZIP archives.'))
    pathwords = file_path.split(os.sep)
    if len(pathwords) > 1:
        pathwords = file_path.split(os.sep)
        dirfilter = os.path.join(*pathwords[:-1])
    else:
        dirfilter = None
    goal = arg_dict.get("goal", None)
    if goal:
        goalfiles = translation_project.getgoalfiles(goal)
        pofilenames = []
        for goalfile in goalfiles:
            pofilenames.extend(translation_project.browsefiles(goalfile))
    else:
        pofilenames = translation_project.browsefiles(dirfilter)
    archivecontents = translation_project.getarchive(pofilenames)
    return HttpResponse(archivecontents, content_type="application/zip")

def handle_sdf(request, translation_project, file_path):
    if not "pocompile" in translation_project.getrights(request.user):
        return redirect('/%s/%s' % (translation_project.language.code, translation_project.project.code),
                        message=_('You do not have the right to create SDF files.'))
    return HttpResponse(translation_project.getoo(), content_type="text/tab-separated-values")

@get_translation_project
@set_request_context
def handle_file(request, translation_project, file_path):
    arg_dict = process_django_request_args(request)
    if file_path.endswith("." + translation_project.project.localfiletype):
        return handle_translation_file(request, translation_project, file_path)
    elif file_path.endswith(".csv") or file_path.endswith(".xlf") or \
         file_path.endswith(".ts") or file_path.endswith(".po") or \
         file_path.endswith(".mo"):
        return handle_alternative_format(request, translation_project, file_path)
    elif file_path.endswith(".zip"):
        return handle_zip(request, arg_dict, translation_project, file_path)
    elif file_path.endswith(".sdf") or file_path.endswith(".sgi"):
        return handle_sdf(request, translation_project, file_path)
    else:
        if file_path.endswith("index.html"):
            file_path = file_path[:-len("index.html")]

        # The Pootle code expects file_path to have its trailing slash stripped.
        directory = translation_project.directory.get_relative(file_path)
        return project_index_view(request, translation_project, directory)
