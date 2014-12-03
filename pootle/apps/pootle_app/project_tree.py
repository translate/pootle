#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

import logging
import os
import re
import shutil

from pootle_app.models.directory import Directory
from pootle_language.models import Language
from pootle_store.models import Store, PARSED
from pootle_store.util import absolute_real_path, add_trailing_slash


#: Case insensitive match for language codes
LANGCODE_RE = re.compile('^[a-z]{2,3}([_-][a-z]{2,3})?(@[a-z0-9]+)?$',
                         re.IGNORECASE)
#: Case insensitive match for language codes as postfix
LANGCODE_POSTFIX_RE = re.compile('^.*?[-_.]([a-z]{2,3}([_-][a-z]{2,3})?(@[a-z0-9]+)?)$',
                                 re.IGNORECASE)


def direct_language_match_filename(language_code, path_name):
    name, ext = os.path.splitext(os.path.basename(path_name))
    if name == language_code or name.lower() == language_code.lower():
        return True

    # Check file doesn't match another language.
    if Language.objects.filter(code__iexact=name).count():
        return False

    detect = LANGCODE_POSTFIX_RE.split(name)
    return (len(detect) > 1 and
            (detect[1] == language_code or
             detect[1].lower() == language_code.lower()))


def match_template_filename(project, filename):
    """Test if :param:`filename` might point at a template file for a given
    :param:`project`.
    """
    name, ext = os.path.splitext(os.path.basename(filename))

    #FIXME: is the test for matching extension redundant?
    if ext == os.path.extsep + project.get_template_filetype():
        if ext != os.path.extsep + project.localfiletype:
            # Template extension is distinct, surely file is a template.
            return True
        elif not find_lang_postfix(filename):
            # File name can't possibly match any language, assume it is a
            # template.
            return True

    return False


def get_matching_language_dirs(project_dir, language):
    return [lang_dir for lang_dir in os.listdir(project_dir)
            if language.code == lang_dir]


def get_non_existant_language_dir(project_dir, language, file_style, make_dirs):
    if file_style == "gnu":
        return project_dir
    elif make_dirs:
        language_dir = os.path.join(project_dir, language.code)
        os.mkdir(language_dir)
        return language_dir
    else:
        raise IndexError("Directory not found for language %s, project %s" %
                         (language.code, project_dir))


def get_or_make_language_dir(project_dir, language, file_style, make_dirs):
    matching_language_dirs = get_matching_language_dirs(project_dir, language)
    if len(matching_language_dirs) == 0:
        # If no matching directories can be found, check if it is a GNU-style
        # project.
        return get_non_existant_language_dir(project_dir, language, file_style,
                                             make_dirs)
    else:
        return os.path.join(project_dir, matching_language_dirs[0])


def get_language_dir(project_dir, language, file_style, make_dirs):
    language_dir = os.path.join(project_dir, language.code)
    if not os.path.exists(language_dir):
        return get_or_make_language_dir(project_dir, language, file_style,
                                        make_dirs)
    else:
        return language_dir


def get_translation_project_dir(language, project_dir, file_style,
                                make_dirs=False):
    """Returns the base directory containing translations files for the
    project.

    :param make_dirs: if ``True``, project and language directories will be
                      created as necessary.
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
                       if child_path not in ignored_files and
                       not is_hidden_file(child_path)]:
        full_child_path = os.path.join(real_dir, child_path)
        if (os.path.isfile(full_child_path) and
            full_child_path.endswith(ext) and file_filter(full_child_path)):
            files.append(child_path)
        elif os.path.isdir(full_child_path):
            dirs.append(child_path)

    return files, dirs


def recursive_files_and_dirs(ignored_files, ext, real_dir, file_filter):
    """Traverses :param:`real_dir` searching for files and directories.

    :param ignored_files: List of files that will be ignored.
    :param ext: Only files ending with this extension will be considered.
    :param real_dir:
    :param file_filter: Filtering function applied to the list of files found.
    :return: A tuple of lists of files and directories found when traversing the
        given path and after applying the given restrictions.
    """
    real_dir = add_trailing_slash(real_dir)
    files = []
    dirs = []

    for _path, _dirs, _files in os.walk(real_dir, followlinks=True):
        # Make it relative:
        _path = _path[len(real_dir):]
        files += [os.path.join(_path, f) for f in filter(file_filter, _files)
                  if f.endswith(ext) and f not in ignored_files]

        # Edit _dirs in place to avoid further recursion into hidden directories
        for d in _dirs:
            if is_hidden_file(d):
                _dirs.remove(d)

        dirs += _dirs

    return files, dirs


def add_items(fs_items, db_items, create_db_item):
    """Add/remove the database items to correspond to the filesystem.

    :param fs_items: entries currently in the filesystem
    :param db_items: entries currently in the database
    :create_db_item: callable that will create a new db item with a given name
    :return: list of all items, list of newly added items
    :rtype: tuple
    """
    items = []
    new_items = []
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
        new_items.append(item)
        try:
            item.save()
        except Exception:
            logging.exception('Error while adding %s', item)

    return items, new_items


def add_files(translation_project, ignored_files, ext, relative_dir, db_dir,
              file_filter=lambda _x: True):
    from pootle_misc import versioncontrol
    podir_path = versioncontrol.to_podir_path(relative_dir)
    files, dirs = split_files_and_dirs(ignored_files, ext, podir_path,
                                       file_filter)
    file_set = set(files)
    dir_set = set(dirs)

    existing_stores = dict((store.name, store) for store in
                           db_dir.child_stores.exclude(file='').iterator())
    existing_dirs = dict((dir.name, dir) for dir in
                         db_dir.child_dirs.iterator())
    files, new_files = add_items(
        file_set,
        existing_stores,
        lambda name: Store(
             file=os.path.join(relative_dir, name),
             parent=db_dir,
             name=name,
             translation_project=translation_project,
        )
    )

    db_subdirs, new_db_subdirs = add_items(
        dir_set,
        existing_dirs,
        lambda name: Directory(name=name, parent=db_dir)
    )

    for db_subdir in db_subdirs:
        fs_subdir = os.path.join(relative_dir, db_subdir.name)
        _files, _new_files = add_files(translation_project, ignored_files, ext,
                                       fs_subdir, db_subdir, file_filter)
        files += _files
        new_files += _new_files

    return files, new_files


def sync_from_vcs(ignored_files, ext, relative_dir,
                  file_filter=lambda _x: True):
    """Recursively synchronise the PO directory from the VCS directory.

    This brings over files from VCS, and removes files in PO directory that
    were removed in VCS.
    """
    from pootle_misc import versioncontrol
    if not versioncontrol.hasversioning(relative_dir):
        return

    podir_path = versioncontrol.to_podir_path(relative_dir)
    vcs_path = versioncontrol.to_vcs_path(relative_dir)
    vcs_files, vcs_dirs = recursive_files_and_dirs(ignored_files, ext,
                                                   vcs_path, file_filter)
    files, dirs = recursive_files_and_dirs(ignored_files, ext, podir_path,
                                           file_filter)

    vcs_file_set = set(vcs_files)
    vcs_dir_set = set(vcs_dirs)
    file_set = set(files)
    dir_set = set(dirs)

    for d in vcs_dir_set - dir_set:
        new_path = os.path.join(podir_path, d)
        os.makedirs(new_path)

    # copy into podir
    for f in vcs_file_set - file_set:
        vcs_f = os.path.join(vcs_path, f)
        new_path = os.path.join(podir_path, f)
        shutil.copy2(vcs_f, new_path)

    # remove from podir
    #TODO: review this carefully, as we are now deleting stuff
    for f in file_set - vcs_file_set:
        remove_path = os.path.join(podir_path, f)
        os.remove(remove_path)

    for d in dir_set - vcs_dir_set:
        remove_path = os.path.join(podir_path, d)
        shutil.rmtree(remove_path)


def find_lang_postfix(filename):
    """Finds the language code at end of a filename."""
    name = os.path.splitext(os.path.basename(filename))[0]
    if LANGCODE_RE.match(name):
        return name

    match = LANGCODE_POSTFIX_RE.match(name)
    if match:
        return match.groups()[0]

    for code in Language.objects.values_list('code', flat=True):
        if (name.endswith('-'+code) or name.endswith('_'+code) or
            name.endswith('.'+code) or
            name.lower().endswith('-'+code.lower()) or
            name.endswith('_'+code) or name.endswith('.'+code)):
            return code


def translation_project_should_exist(language, project):
    """Tests if there are translation files corresponding to the given
    :param:`language` and :param:`project`.
    """
    if project.get_treestyle() == "gnu":
        # GNU style projects are tricky

        if language.code == 'templates':
            # Language is template look for template files
            for dirpath, dirnames, filenames in os.walk(project.get_real_path()):
                for filename in filenames:
                    if project.file_belongs_to_project(filename, match_templates=True) and \
                           match_template_filename(project, filename):
                        return True
        else:
            # find files with the language name in the project dir
            for dirpath, dirnames, filenames in os.walk(project.get_real_path()):
                for filename in filenames:
                    #FIXME: don't reuse already used file
                    if project.file_belongs_to_project(filename, match_templates=False) and \
                           direct_language_match_filename(language.code, filename):
                        return True
    else:
        # find directory with the language name in the project dir
        try:
            dirpath, dirnames, filename = os.walk(project.get_real_path()).next()
            if language.code in dirnames:
                return True
        except StopIteration:
            pass

    return False


def ensure_target_dir_exists(target_path):
    target_dir = os.path.dirname(target_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)


def convert_template(translation_project, template_store, target_pootle_path,
                     target_path, monolingual=False):
    """Run pot2po to update or initialize the file on `target_path` with
    `template_store`.
    """

    ensure_target_dir_exists(target_path)

    if template_store.file:
        template_file = template_store.file.store
    else:
        template_file = template_store

    try:
        store = Store.objects.get(pootle_path=target_pootle_path)

        if monolingual and store.state < PARSED:
            #HACKISH: exploiting update from templates to parse monolingual files
            store.update(store=template_file)
            store.update(update_translation=True)
            return

        if not store.file or monolingual:
            original_file = store
        else:
            original_file = store.file.store
    except Store.DoesNotExist:
        original_file = None
        store = None

    from translate.convert import pot2po
    from pootle_store.filetypes import factory_classes
    output_file = pot2po.convert_stores(template_file, original_file,
                                        fuzzymatching=False,
                                        classes=factory_classes)
    if template_store.file:
        if store:
            store.update(update_structure=True, update_translation=True,
                         store=output_file, fuzzy=True)
        output_file.settargetlanguage(translation_project.language.code)
        output_file.savefile(target_path)
    elif store:
        store.mergefile(output_file, None, allownewstrings=True,
                        suggestions=False, notranslate=False,
                        obsoletemissing=True)
    else:
        output_file.translation_project = translation_project
        output_file.name = template_store.name
        output_file.parent = translation_project.directory
        output_file.state = PARSED
        output_file.save()

    # pot2po modifies its input stores so clear caches is needed
    if template_store.file:
        template_store.file._delete_store_cache()
    if store and store.file:
        store.file._delete_store_cache()


def get_translated_name_gnu(translation_project, store):
    """Given a template :param:`store` and a :param:`translation_project` return
    target filename.
    """
    pootle_path_parts = store.pootle_path.split('/')
    pootle_path_parts[1] = translation_project.language.code
    pootle_path = '/'.join(pootle_path_parts[:-1])
    if not pootle_path.endswith('/'):
        pootle_path = pootle_path + '/'

    suffix = translation_project.language.code + os.extsep + \
             translation_project.project.localfiletype
    # try loading file first
    try:
        target_store = translation_project.stores.get(
                parent__pootle_path=pootle_path,
                name__iexact=suffix,
        )
        return (target_store.pootle_path,
                target_store.file and target_store.file.path)
    except Store.DoesNotExist:
        target_store = None

    # is this GNU-style with prefix?
    use_prefix = store.parent.child_stores.exclude(file="").count() > 1 or \
                 translation_project.stores.exclude(name__iexact=suffix).exclude(file="").count()
    if not use_prefix:
        # let's make sure
        for tp in translation_project.project.translationproject_set.exclude(language__code='templates').iterator():
            temp_suffix = tp.language.code + os.extsep + translation_project.project.localfiletype
            if tp.stores.exclude(name__iexact=temp_suffix).exclude(file="").count():
                use_prefix = True
                break

    if use_prefix:
        if store.translation_project.language.code == 'templates':
            tprefix = os.path.splitext(store.name)[0]
            #FIXME: we should detect seperator
            prefix = tprefix + '-'
        else:
            prefix = os.path.splitext(store.name)[0][:-len(store.translation_project.language.code)]
            tprefix = prefix[:-1]

        try:
            target_store = translation_project.stores.filter(
                    parent__pootle_path=pootle_path,
                    name__in=[
                        tprefix + '-' + suffix,
                        tprefix + '_' + suffix,
                        tprefix + '.' + suffix,
                        tprefix + '-' + suffix.lower(),
                        tprefix + '_' + suffix.lower(),
                        tprefix + '.' + suffix.lower(),
                    ],
            )[0]

            return (target_store.pootle_path,
                    target_store.file and target_store.file.path)
        except (Store.DoesNotExist, IndexError):
            pass
    else:
        prefix = ""

    if store.file:
        path_parts = store.file.path.split(os.sep)
        name = prefix + suffix
        path_parts[-1] = name
        pootle_path_parts[-1] = name
    else:
        path_parts = store.parent.get_real_path().split(os.sep)
        path_parts.append(store.name)

    return '/'.join(pootle_path_parts), os.sep.join(path_parts)


def get_translated_name(translation_project, store):
    name, ext = os.path.splitext(store.name)

    if store.file:
        path_parts = store.file.name.split(os.sep)
    else:
        path_parts = store.parent.get_real_path().split(os.sep)
        path_parts.append(store.name)

    pootle_path_parts = store.pootle_path.split('/')

    # Replace language code
    path_parts[1] = translation_project.language.code
    pootle_path_parts[1] = translation_project.language.code

    # Replace extension
    path_parts[-1] = name + '.' + translation_project.project.localfiletype
    pootle_path_parts[-1] = name + '.' + \
                            translation_project.project.localfiletype

    return ('/'.join(pootle_path_parts),
            absolute_real_path(os.sep.join(path_parts)))
