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

from pootle_app.core      import Project, Language
from pootle_app.fs_models import Directory, Store
from pootle_app.url_manip import strip_trailing_slash
from pootle_app.language  import try_language_code

from Pootle.pootlefile import absolute_real_path, relative_real_path

def get_project_code(base_dir, project_dir):
    return project_dir[len(base_dir):].split(os.sep)[1]

def get_project(base_dir, project_dir, project):
    project_code = get_project_code(strip_trailing_slash(base_dir), project_dir)
    if project is not None and project.code == project_code:
        return project
    else:
        return Project.objects.get(code=project_code)

def _search_file_style(project_dir, language_code, depth=0, max_depth=3, ext="po"):
    #Let's check to see if we specifically find the correct gnu file
    found_gnu_file = False
    if not os.path.isdir(project_dir):
        return None
    full_ext = os.extsep + ext
    dirs_to_inspect = []
    for path_name in os.listdir(project_dir):
        full_path_name = os.path.join(project_dir, path_name)
        if os.path.isdir(full_path_name):
            # if we have a language subdirectory, we're probably not GNU-style
            if langdata.languagematch(language_code, path_name):
                return "nongnu"
            #ignore hidden directories (like index directories)
            if path_name[0] == '.':
                continue
            dirs_to_inspect.append(full_path_name)
        elif path_name.endswith(full_ext):
            if langdata.languagematch(language_code, path_name[:-len(full_ext)]):
                found_gnu_file = True
            elif not langdata.languagematch(None, path_name[:-len(full_ext)]):
                return "nongnu"
    if depth < max_depth:
        for dir in dirs_to_inspect:
            style = _search_file_style(full_path_name, language_code, depth+1, max_depth, ext)
            if style == "nongnu":
                return style
            elif style == "gnu":
                found_gnu_file = True
    if found_gnu_file:
        return "gnu"
    else:
        return "nongnu"

def get_file_style(project_dir, language=None, project=None, depth=0, max_depth=3, ext="po"):
    def get_language_code(language):
        if language is not None:
            return language.code
        else:
            return None

    try:
        project = get_project(settings.PODIRECTORY, project_dir, project)
        style = project.treestyle
        if style in ("gnu", "nongnu"):
            return style
    except Project.DoesNotExist:
        pass
    return _search_file_style(project_dir, get_language_code(language), depth, max_depth, ext)

def get_project_dir(project, make_dirs=False):
    project_dir = absolute_real_path(project.code)
    if not os.path.exists(project_dir):
        if not make_dirs:
            raise IndexError("directory not found for project %s" % (project.code))
        else:
            os.mkdir(project_dir)
    return project_dir

def get_matching_language_dirs(project_dir, language_dir, language):
    return [lang_dir for lang_dir in os.listdir(project_dir)
            if langdata.languagematch(language.code, language_dir)]

def get_non_existant_language_dir(project_dir, language, file_style, make_dirs):
    if file_style == "gnu":
        return project_dir
    else:
        if make_dirs:
            os.mkdir(language_dir)
            return language_dir
        else:
            raise IndexError("directory not found for language %s, project %s" % (language.code, project_dir))

def get_or_make_language_dir(project_dir, language_dir, language, file_style, make_dirs):
    matching_language_dirs = get_matching_language_dirs(project_dir, language_dir, language)
    if len(matching_language_dirs) == 0:
        # if no matching directories can be found, check if it is a GNU-style project
        return get_non_existant_language_dir(project_dir, language, file_style, make_dirs)
    elif len(matching_language_dirs) == 1:
        return os.path.join(project_dir, matching_language_dirs[0])
    else:
        # TODO: handle multiple regions
        raise IndexError("multiple regions defined for language %s, project %s" % (language.code, project.code))

def get_language_dir(project_dir, language, file_style, make_dirs):
    language_dir = os.path.join(project_dir, language.code)
    if not os.path.exists(language_dir):
        return get_or_make_language_dir(project_dir, language_dir, language, file_style, make_dirs)
    else:
        return language_dir

def get_translation_project_dir(language, project_dir, file_style, make_dirs=False):
    """returns the base directory containing po files for the project

    If make_dirs is True, then we will create project and language
    directories as necessary.
    """
    return get_language_dir(project_dir, language, file_style, make_dirs)

def has_project(language, project):
    try:
        get_translation_project_dir(language, project)
        return True
    except IndexError:
        return False

def is_hidden_file(path):
    return path[0] == '.'

def split_files_and_dirs(ignored_files, ext, real_dir):
    files = []
    dirs = []
    for child_path in [child_path for child_path in os.listdir(real_dir)
                       if child_path not in ignored_files and not is_hidden_file(child_path)]:
        full_child_path = os.path.join(real_dir, child_path)
        if os.path.isfile(full_child_path) and full_child_path.endswith(ext):
            files.append(child_path)
        elif os.path.isdir(full_child_path):
            dirs.append(child_path)
    return files, dirs

def add_items(fs_items, db_items, create_db_item):
    items = []
    fs_items_set = set(fs_items)
    db_items_set = set(db_items)

    items_to_delete = db_items_set - fs_items_set
    items_to_create = fs_items_set - db_items_set

    for name in items_to_delete:
        db_items[name].delete()

    for name in db_items_set - items_to_delete:
        items.append(db_items[name])

    for name in items_to_create:
        item = create_db_item(name)
        items.append(item)
        item.save()

    return items

def add_files(ignored_files, ext, real_dir, db_dir):
    files, dirs = split_files_and_dirs(ignored_files, ext, real_dir)
    existing_stores = dict((store.name, store) for store in db_dir.child_stores.all())
    existing_dirs = dict((dir.name, dir) for dir in db_dir.child_dirs.all())

    add_items(files, existing_stores,
              lambda name: Store(real_path = relative_real_path(os.path.join(real_dir, name)),
                                 parent    = db_dir,
                                 name      = name))

    db_subdirs = add_items(dirs, existing_dirs,
                           lambda name: Directory(name=name, parent=db_dir))

    for db_subdir in db_subdirs:
        fs_subdir = os.path.join(real_dir, db_subdir.name)
        add_files(ignored_files, ext, fs_subdir, db_subdir)

def add_gnu_items(ext, fs_dirs, db_dirs, real_dir, db_dir):
    fs_dirs_set = set(fs_dirs)
    db_dirs_set = set(db_dirs)

    dirs_to_delete = db_dirs_set - fs_dirs_set
    dirs_to_create = fs_dirs_set - db_dirs_set

    for name in dirs_to_delete:
        directory = db_dirs[name]
        for store in directory.child_stores.all():
            store.delete()
        directory.delete()

    for name in dirs_to_create:
        directory = Directory(name=name, parent=db_dir)
        directory.save()
        store_name = name + ext
        store = Store(real_path = relative_real_path(os.path.join(real_dir, store_name)),
                      parent    = directory,
                      name      = store_name)
        store.save()

def add_gnu_files(ignored_files, ext, real_dir, db_dir):
    """adds the files to the set of files for this project"""
    files, dirs = split_files_and_dirs(ignored_files, ext, real_dir)
    fake_language_dirs = [filename[:-len(ext)] for filename in files]
    db_dirs = dict((dir.name, dir) for dir in db_dir.child_dirs.all())
    add_gnu_items(ext, fake_language_dirs, db_dirs, real_dir, db_dir)
    for dirname in dirs:
        fs_subdir = os.path.join(real_dir, dirname)
        db_subdir = db_dir.get_or_make_subdir(dirname)
        add_gnu_files(ignored_files, ext, fs_subdir, db_subdir)

def get_translation_project_root(translation_project):
    return Directory.objects.root.get_or_make_subdir(translation_project.project.code).get_subdir(translation_project.language.code)

def scan_translation_project_files(translation_project):
    """returns a list of po files for the project and language"""
    project       = translation_project.project
    real_path     = translation_project.abs_real_path
    directory     = translation_project.directory
    ignored_files = set(p.strip() for p in project.ignoredfiles.split(','))
    ext           = os.extsep + translation_project.project.localfiletype
    if translation_project.file_style == 'gnu':
        add_gnu_files(ignored_files, ext, real_path, directory)
    else:
        add_files(ignored_files, ext, real_path, directory)

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
                    return try_language_code(code,
                                             lambda code: code in code_language_map,
                                             lambda code: code)
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

