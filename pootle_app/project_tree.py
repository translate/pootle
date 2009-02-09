#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
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

import os.path
from django.conf import settings

from translate.lang import data as langdata

from pootle_app.core import Project, Language
from pootle_app.misc import strip_trailing_slash

def get_project_code(base_dir, project_dir):
    project_dir[len(base_dir):].split(os.sep)[1]

def get_project(base_dir, project_dir, project):
    project_code = get_project_code(strip_trailing_slash(base_dir), project_dir)
    if project is not None and project.code == project_code:
        return project
    else:
        return Project.objects.get(code=project_code)

def get_file_style(project_dir, language=None, project=None, depth=0, max_depth=3, ext="po"):
    try:
        if (project_dir.startswith(settings.PODIRECTORY)):
            style = get_project(settings.PODIRECTORY, project_dir, project).treestyle
            if style in ("gnu", "nongnu"):
                return style
            else:
                print "Unsupported treestyle value (project %s): %s" % (projectcode, style)
    except Project.DoesNotExist:
        pass

    #Let's check to see if we specifically find the correct gnu file
    found_gnu_file = False
    if not os.path.isdir(project_dir):
        return None
    full_ext = os.extsep + ext
    for path_name in os.listdir(project_dir):
        full_path_name = os.path.join(project_dir, path_name)
        if os.path.isdir(full_path_name):
            # if we have a language subdirectory, we're probably not GNU-style
            if langdata.languagematch(language.code, path_name):
                return None
            #ignore hidden directories (like index directories)
            if path_name[0] == '.':
                continue
            if depth < max_depth:
                style = get_file_style(full_path_name, language, project, depth+1, max_depth, ext)
                if style == "nongnu":
                    return style
                elif style == "gnu":
                    found_gnu_file = True
        elif path_name.endswith(full_ext):
            if langdata.languagematch(language.code, path_name[:-len(full_ext)]):
                found_gnu_file = True
            elif not langdata.languagematch(None, path_name[:-len(full_ext)]):
                return "nongnu"
    if found_gnu_file:
        return "gnu"
    else:
        return None

def get_project_dir(language, project, make_dirs=False):
    """returns the base directory containing po files for the project

    If make_dirs is True, then we will create project and language
    directories as necessary.
    """
    project_dir = os.path.join(settings.PODIRECTORY, project.code)
    if not os.path.exists(project_dir):
        if not make_dirs:
            raise IndexError("directory not found for project %s" % (projectcode))
        else:
            os.mkdir(project_dir)
    language_dir = os.path.join(project_dir, language.code)
    if not os.path.exists(language_dir):
        language_dirs = [lang_dir for lang_dir in os.listdir(project_dir)
                         if langdata.languagematch(language.code, language_dir)]
        if not language_dirs:
            # if no matching directories can be found, check if it is a GNU-style project
            if get_file_style(project_dir, language, project) == "gnu":
                return project_dir
            if make_dirs:
                os.mkdir(language_dir)
                return language_dir
            raise IndexError("directory not found for language %s, project %s" % (language.code, project.code))
        # TODO: handle multiple regions
        if len(language_dirs) > 1:
            raise IndexError("multiple regions defined for language %s, project %s" % (language.code, project.code))
        language_dir = os.path.join(project_dir, language_dirs[0])
    return language_dir

def has_project(language, project):
    try:
        get_project_dir(language, project)
        return True
    except IndexError:
        return False

def get_project_files(language, project, ext="po"):
    """returns a list of po files for the project and language"""
    filenames = []
    prefix = os.curdir + os.sep

    def addfiles(podir, dirname, fnames):
        """adds the files to the set of files for this project"""
        # Remove the files we want to ignore
        fnames = set(fnames) - set(p.strip() for p in project.ignoredfiles.split(','))
        if dirname == os.curdir:
            basedirname = ""
        else:
            basedirname = dirname.replace(prefix, "", 1)
        for fname in fnames:
            # check that it actually exists (to avoid problems with broken symbolic
            # links, for example)
            fpath = os.path.join(basedirname, fname)
            if fname.endswith(os.extsep + ext):
                filenames.append(fpath)

    def addgnufiles(podir, dirname, fnames):
        """adds the files to the set of files for this project"""
        basedirname = dirname.replace(podir, "", 1)
        while basedirname.startswith(os.sep):
            basedirname = basedirname.replace(os.sep, "", 1)
        full_ext = os.extsep + ext
        ponames = [fn for fn in fnames if fn.endswith(full_ext) and langdata.languagematch(language.code, fn[:-len(full_ext)])]
        filenames.extend([os.path.join(basedirname, poname) for poname in ponames])

    project_dir = get_project_dir(language, project)
    if get_file_style(project_dir, language, project) == 'gnu':
        os.path.walk(project_dir, addgnufiles, project_dir)
    else:
        pwd = os.path.abspath(os.curdir)
        os.chdir(project_dir)
        os.path.walk(os.curdir, addfiles, None)
        os.chdir(pwd)
    return filenames

def get_projects(language=None):
    if language is None:
        return Project.objects.all()
    else:
        return [project for project in Project.objects.all() if has_project(language, project)]

def get_languages(project=None):
    """returns a list of valid languagecodes for a given project or
    all projects"""
    if project is None:
        return Language.objects.all()
    else:
        project_dir = os.path.join(settings.PODIRECTORY, project.code)
        if not os.path.exists(project_dir):
            return []
        if project.treestyle == "gnu":
            return [language for language in Language.objects.all()
                    if has_project(language, project)]
        else:
            def get_matching_code(code, code_language_map):
                if langdata.languagematch(None, code):
                    if code in code_language_map:
                        return code
                    elif "-" in code and code[:code.find('-')] in code_language_map:
                        return code[:code.find('-')]
                    elif "_" in code and code[:code.find('_')] in code_language_map:
                        return code[:code.find('_')]
                else:
                    return None

            # Build a (language_code -> language) map
            code_language_map = dict((language.code, language) for language in Language.objects.all())
            # Build a list of subdirectories
            subdirs = [path_entry for path_entry in os.listdir(project_dir)
                       if os.path.isdir(os.path.join(project_dir, path_entry))]
            # For each subdirectory in subdirs, convert the potential
            # language code that it represents to an existing language
            # code. This will for example convert pt_BR to pt, if
            # there is a directory called 'pt_BR', but only a language
            # defined as 'pt'.
            matching_codes = set(get_matching_code(code, code_language_map) for code in subdirs)
            # get_matching_code returns None if there is no matching
            # language defined for a subdirectory. This means that
            # None might appear in our set. Remove it, if it's in
            # there.
            matching_codes.remove(None)
            # Return a list of languages sorted in order of their
            # language codes.
            return [code_language_map[code] for code in sorted(matching_codes)]

