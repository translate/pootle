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

from Pootle import indexpage, pan_app, translatepage, projects, adminpages
from Pootle.misc.jtoolkit_django import process_django_request_args

from pootle_app.views.util import render_to_kid, render_jtoolkit
from pootle_app.views.auth import redirect
from pootle_app.core import Language, Project
from pootle_app.misc import strip_trailing_slash

def get_language(f):
    def decorated_f(request, language_code, *args, **kwargs):
        try:
            language = Language.objects.include_hidden().get(code=language_code)
            return f(request, language, *args, **kwargs)
        except Language.DoesNotExist:
            return redirect('/', message=_("The language %s is not defined for this Pootle installation" % language_code))
    return decorated_f

def get_project(f):
    def decorated_f(request, language, project_code, *args, **kwargs):
        try:
            project = Project.objects.get(code=project_code)
            return f(request, language, project, *args, **kwargs)
        except Project.DoesNotExist:
            return redirect('/', message=_("The project %s is not defined for this Pootle installation" % project_code))
    return decorated_f

def get_translation_project(f):
    @get_language
    @get_project
    def decorated_f(request, language, project, *args, **kwargs):
        try:
            return f(request, projects.get_translation_project(language, project), *args, **kwargs)
        except IndexError:
            return redirect('/%s' % language.code, message=_("The project %s does not exist for the language %s" % (project.code, language.code)))
    return decorated_f

@get_language
def language_index(request, language):
    return render_jtoolkit(indexpage.LanguageIndex(language, request))

@get_translation_project
def translation_project_admin(request, translation_project):
    return render_jtoolkit(adminpages.TranslationProjectAdminPage(translation_project, request, process_django_request_args(request)))

@get_translation_project
def translate_page(request, translation_project, dir_path):
    try:
        if dir_path is None:
            dir_path = ""
        return render_jtoolkit(translatepage.TranslatePage(translation_project, request, process_django_request_args(request), dir_path))
    except projects.RightsError, msg:
        return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), message=msg)

@get_translation_project
def project_index(request, translation_project):
    try:
        return render_jtoolkit(indexpage.ProjectIndex(translation_project, request, process_django_request_args(request)))
    except projects.RightsError, msg:
        return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), message=msg)

def handle_translation_file(request, arg_dict, translation_project, file_path):
    # Don't get confused here. request.GET contains HTTP
    # GET vars while get is a dictionary method
    if request.GET.get("translate", 0):
        try:
            return render_jtoolkit(translatepage.TranslatePage(translation_project, request, 
                                                               process_django_request_args(request),
                                                               dirfilter=file_path))
        except projects.RightsError, stoppedby:
            pathwords = file_path.split(os.sep)
            if len(pathwords) > 1:
                dirfilter = os.path.join(*pathwords[:-1])
            else:
                dirfilter = ""
            return redirect('/%s/%s/' % (translation_project.language.code, translation_project.project.code), 
                            message=stoppedby)
    # Don't get confused here. request.GET contains HTTP
    # GET vars while get is a dictionary method
    elif request.GET.get("index", 0):
        return indexpage.ProjectIndex(translation_project, request,
                                      process_django_request_args(request), 
                                      dirfilter=file_path)
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
    return HttpResponse(translation_project.getoo(), content_type="text/tab-seperated-values")

@get_translation_project
def handle_file(request, translation_project, file_path):
    arg_dict = process_django_request_args(request)
    if file_path.endswith("." + translation_project.fileext):
        return handle_translation_file(request, arg_dict, translation_project, file_path)
    elif file_path.endswith(".csv") or file_path.endswith(".xlf") or \
         file_path.endswith(".ts") or file_path.endswith(".po") or \
         file_path.endswith(".mo"):
        return handle_alternative_format(request, translation_project, file_path)
    elif file_path.endswith(".zip"):
        return handle_zip(request, arg_dict, translation_project, file_path)
    elif file_path.endswith(".sdf") or file_path.endswith(".sgi"):
        return handle_sdf(request, translation_project, file_path)
    else:
        # The Pootle code expects file_path to have its trailing slash stripped.
        return render_jtoolkit(indexpage.ProjectIndex(translation_project, request, arg_dict, strip_trailing_slash(file_path)))
