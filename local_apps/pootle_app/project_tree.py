#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import os
import cStringIO

from translate.lang    import data as langdata
from translate.convert import pot2po

from pootle_store.models      import Store
from pootle_store.util import absolute_real_path, relative_real_path
from pootle_app.models.directory  import Directory
from pootle_app.models.signals import post_template_update

def language_match_filename(language_code, path_name):
    name, ext = os.path.splitext(os.path.basename(path_name))
    return langdata.languagematch(language_code, name)

def direct_language_match_filename(language_code, path_name):
    name, ext = os.path.splitext(os.path.basename(path_name))
    return language_code == name

def match_template_filename(project, path_name):
    """test if path_name might point at a template file for given
    project"""
    name, ext = os.path.splitext(os.path.basename(path_name))
    #FIXME: is the test for matching extension redundant?
    if ext == os.path.extsep + project.get_template_filtetype():
        if ext != os.path.extsep + project.localfiletype:
            # template extension is distinct, surely file is a template
            return True
        elif not langdata.langcode_re.match(name):
            # file name can't possibly match any language, assume it is a template
            return True
    return False

def get_matching_language_dirs(project_dir, language):
    return [lang_dir for lang_dir in os.listdir(project_dir)
            if language.code == lang_dir]

def get_non_existant_language_dir(project_dir, language, file_style, make_dirs):
    if file_style == "gnu":
        return project_dir
    else:
        if make_dirs:
            language_dir = os.path.join(project_dir, language.code)
            os.mkdir(language_dir)
            return language_dir
        else:
            raise IndexError("directory not found for language %s, project %s" % (language.code, project_dir))

def get_or_make_language_dir(project_dir, language, file_style, make_dirs):
    matching_language_dirs = get_matching_language_dirs(project_dir, language)
    if len(matching_language_dirs) == 0:
        # if no matching directories can be found, check if it is a GNU-style project
        return get_non_existant_language_dir(project_dir, language, file_style, make_dirs)
    else:
        return os.path.join(project_dir, matching_language_dirs[0])

def get_language_dir(project_dir, language, file_style, make_dirs):
    language_dir = os.path.join(project_dir, language.code)
    if not os.path.exists(language_dir):
        return get_or_make_language_dir(project_dir, language, file_style, make_dirs)
    else:
        return language_dir


def get_translation_project_dir(language, project_dir, file_style, make_dirs=False):
    """returns the base directory containing po files for the project

    If make_dirs is True, then we will create project and language
    directories as necessary.
    """
    if file_style == 'gnu':
        return project_dir
    else:
        return get_language_dir(project_dir, language, file_style, make_dirs)

def is_hidden_file(path):
    return path[0] == '.'

def split_files_and_dirs(ignored_files, ext, real_dir, file_filter):
    files = []
    dirs = []
    for child_path in [child_path for child_path in os.listdir(real_dir)
                       if child_path not in ignored_files and not is_hidden_file(child_path)]:
        full_child_path = os.path.join(real_dir, child_path)
        if os.path.isfile(full_child_path) and full_child_path.endswith(ext) and file_filter(full_child_path):
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

def add_files(ignored_files, ext, real_dir, db_dir, file_filter=lambda _x: True):
    files, dirs = split_files_and_dirs(ignored_files, ext, real_dir, file_filter)
    existing_stores = dict((store.name, store) for store in db_dir.child_stores.all())
    existing_dirs = dict((dir.name, dir) for dir in db_dir.child_dirs.all())
    add_items(files, existing_stores,
              lambda name: Store(file = relative_real_path(os.path.join(real_dir, name)),
                                 parent    = db_dir,
                                 name      = name))

    db_subdirs = add_items(dirs, existing_dirs,
                           lambda name: Directory(name=name, parent=db_dir))

    for db_subdir in db_subdirs:
        fs_subdir = os.path.join(real_dir, db_subdir.name)
        add_files(ignored_files, ext, fs_subdir, db_subdir, file_filter)


def translation_project_should_exist(language, project):
    """tests if there are translation files corresponding to given
    language and project"""
    if project.get_treestyle() == "gnu":
        # GNU style projects are tricky

        if language.code == 'templates':
            # language is template look for template files
            for dirpath, dirnames, filenames in os.walk(project.get_real_path()):
                for filename in filenames:
                    if filename.endswith(os.path.extsep + project.get_template_filtetype()):
                        if project.get_template_filtetype() != project.localfiletype:
                            # templates and translation files have a
                            # different extension, easy to detect
                            # templates
                            return True
                        elif not langdata.langcode_re.match(os.path.splitext(filename)[0]):
                            # can't tell templates by their extension,
                            # assume any translation file that can't
                            # be a language name is a template
                            return True
        else:
            # find files with the language name in the project dir
            for dirpath, dirnames, filenames in os.walk(project.get_real_path()):
                for filename in filenames:
                    if project.file_belongs_to_project(filename, match_templates=False) and \
                           os.path.splitext(filename)[0] == language.code:
                        return True
    else:
        # find directory with the language name in the project dir
        dirpath, dirnames, filename = os.walk(project.get_real_path()).next()
        if language.code in dirnames:
            return True

    return False

def scan_translation_project_files(translation_project):
    """returns a list of po files for the project and language"""
    project       = translation_project.project
    real_path     = translation_project.abs_real_path
    directory     = translation_project.directory
    ignored_files = set(p.strip() for p in project.ignoredfiles.split(','))
    ext           = os.extsep + project.localfiletype

    # scan for pots if template project
    if translation_project.is_template_project:
        ext = os.extsep + project.get_template_filtetype()

    if translation_project.file_style == 'gnu':
        if translation_project.is_template_project:
            add_files(ignored_files, ext, real_path, directory,
                      lambda filename: match_template_filename(project, filename))
        else:
            add_files(ignored_files, ext, real_path, directory,
                      lambda filename: direct_language_match_filename(translation_project.language.code, filename))
    else:
        add_files(ignored_files, ext, real_path, directory)
    for store in translation_project.stores.all():
        store.file._delete_store_cache()


def get_extension(language, project):
    """file extension used for this project, returns pot if it's a po
    project and language is templates"""
    ext = project.localfiletype
    if language.code == 'templates' and ext == 'po':
        return 'pot'
    else:
        return ext

def ensure_target_dir_exists(target_path):
    target_dir = os.path.dirname(target_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

def read_original_target(target_path):
    try:
        return open(target_path, "rb")
    except:
        return None

def convert_template(template_path, target_path):
    ensure_target_dir_exists(target_path)
    template_file = open(template_path, "rb")
    target_file   = cStringIO.StringIO()
    original_file = read_original_target(target_path)
    pot2po.convertpot(template_file, target_file, original_file)
    try:
        output_file = open(target_path, "wb")
        output_file.write(target_file.getvalue())
    finally:
        output_file.close()

def get_translated_name_gnu(translation_project, store):
    path_parts = store.file.path.split(os.sep)
    path_parts[-1] =  "%s.%s" % (translation_project.language.code,
                                 translation_project.project.localfiletype)
    return os.sep.join(path_parts)

def get_translated_name(translation_project, store):
    name, ext = os.path.splitext(store.name)
    path_parts = store.file.name.split(os.sep)

    # replace language code
    path_parts[1] = translation_project.language.code
    # replace extension
    path_parts[-1] = name + '.' + translation_project.project.localfiletype

    return absolute_real_path(os.sep.join(path_parts))

def convert_templates(template_translation_project, translation_project):
    oldstats = translation_project.getquickstats()
    for store in template_translation_project.stores.all():
        if translation_project.file_style == 'gnu':
            new_store_path = get_translated_name_gnu(translation_project, store)
        else:
            new_store_path = get_translated_name(translation_project, store)
        convert_template(store.file.path, new_store_path)
    scan_translation_project_files(translation_project)
    newstats = translation_project.getquickstats()
    post_template_update.send(sender=translation_project, oldstats=oldstats, newstats=newstats)

