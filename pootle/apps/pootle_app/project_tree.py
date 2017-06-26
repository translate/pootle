# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import errno
import logging
import os
import re

from django.conf import settings

from pootle.core.log import STORE_RESURRECTED, store_log
from pootle_app.models.directory import Directory
from pootle_language.models import Language
from pootle_store.models import Store
from pootle_store.util import absolute_real_path, relative_real_path


#: Case insensitive match for language codes
LANGCODE_RE = re.compile('^[a-z]{2,3}([_-][a-z]{2,3})?(@[a-z0-9]+)?$',
                         re.IGNORECASE)
#: Case insensitive match for language codes as postfix
LANGCODE_POSTFIX_RE = re.compile(
    '^.*?[-_.]([a-z]{2,3}([_-][a-z]{2,3})?(@[a-z0-9]+)?)$', re.IGNORECASE)


def direct_language_match_filename(language_code, path_name):
    name = os.path.splitext(os.path.basename(path_name))[0]
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
    ext = os.path.splitext(os.path.basename(filename))[1][1:]

    # FIXME: is the test for matching extension redundant?
    if ext in project.filetype_tool.template_extensions:
        if ext not in project.filetype_tool.filetype_extensions:
            # Template extension is distinct, surely file is a template.
            return True
        elif not find_lang_postfix(project, filename):
            # File name can't possibly match any language, assume it is a
            # template.
            return True

    return False


def get_matching_language_dirs(project_dir, upstream_language_code):
    return [lang_dir for lang_dir in os.listdir(project_dir)
            if upstream_language_code == lang_dir]


def get_non_existant_language_dir(project_dir, upstream_language_code,
                                  file_style, make_dirs):
    if file_style == "gnu":
        return project_dir
    elif make_dirs:
        language_dir = os.path.join(project_dir, upstream_language_code)
        os.mkdir(language_dir)
        return language_dir
    else:
        raise IndexError("Directory not found for language %s, project %s" %
                         (upstream_language_code, project_dir))


def get_or_make_language_dir(project_dir, upstream_language_code,
                             file_style, make_dirs):
    matching_language_dirs = get_matching_language_dirs(project_dir,
                                                        upstream_language_code)
    if len(matching_language_dirs) == 0:
        # If no matching directories can be found, check if it is a GNU-style
        # project.
        return get_non_existant_language_dir(project_dir, upstream_language_code,
                                             file_style, make_dirs)
    else:
        return os.path.join(project_dir, matching_language_dirs[0])


def get_language_dir(project, language, file_style, make_dirs):
    project_dir = project.get_real_path()
    upstream_lang_code = project.lang_mapper.get_upstream_code(language.code)
    language_dir = os.path.join(project_dir, upstream_lang_code)
    if not os.path.exists(language_dir):
        return get_or_make_language_dir(project_dir, upstream_lang_code,
                                        file_style, make_dirs)
    else:
        return language_dir


def get_translation_project_dir(language, project, file_style,
                                make_dirs=False):
    """Returns the base directory containing translations files for the
    project.

    :param make_dirs: if ``True``, project and language directories will be
                      created as necessary.
    """
    if file_style == 'gnu':
        return project.get_real_path()
    else:
        return get_language_dir(project, language, file_style, make_dirs)


def is_hidden_file(path):
    return path[0] == '.'


def split_files_and_dirs(ignored_files, exts, real_dir, file_filter):
    files = []
    dirs = []
    child_paths = [
        child_path
        for child_path
        in os.listdir(real_dir)
        if (child_path not in ignored_files
            and not is_hidden_file(child_path))]
    for child_path in child_paths:
        full_child_path = os.path.join(real_dir, child_path)
        should_include_file = (
            os.path.isfile(full_child_path)
            and os.path.splitext(full_child_path)[1][1:] in exts
            and file_filter(full_child_path))
        if should_include_file:
            files.append(child_path)
        elif os.path.isdir(full_child_path):
            dirs.append(child_path)
    return files, dirs


def add_items(fs_items_set, db_items, create_or_resurrect_db_item, parent):
    """Add/make obsolete the database items to correspond to the filesystem.

    :param fs_items_set: items (dirs, files) currently in the filesystem
    :param db_items: dict (name, item) of items (dirs, stores) currently in the
        database
    :create_or_resurrect_db_item: callable that will create a new db item
        or resurrect an obsolete db item with a given name and parent.
    :parent: parent db directory for the items
    :return: list of all items, list of newly added items
    :rtype: tuple
    """
    items = []
    new_items = []
    db_items_set = set(db_items)

    items_to_delete = db_items_set - fs_items_set
    items_to_create = fs_items_set - db_items_set

    for name in items_to_delete:
        db_items[name].makeobsolete()

    for name in db_items_set - items_to_delete:
        items.append(db_items[name])

    for name in items_to_create:
        item = create_or_resurrect_db_item(name)
        items.append(item)
        new_items.append(item)
        try:
            item.save()
        except Exception:
            logging.exception('Error while adding %s', item)

    return items, new_items


def create_or_resurrect_store(f, parent, name, translation_project):
    """Create or resurrect a store db item with given name and parent."""
    try:
        store = Store.objects.get(parent=parent, name=name)
        store.resurrect(save=False)
        store_log(user='system', action=STORE_RESURRECTED,
                  path=store.pootle_path, store=store.id)
    except Store.DoesNotExist:
        store = Store.objects.create(
            file=f, parent=parent,
            name=name, translation_project=translation_project)
    return store


def create_or_resurrect_dir(tp, name, parent):
    """Create or resurrect a directory db item with given name and parent."""
    try:
        directory = Directory.objects.get(parent=parent, name=name)
        directory.obsolete = False
    except Directory.DoesNotExist:
        directory = Directory(name=name, parent=parent, tp=tp)
    return directory


# TODO: rename function or even rewrite it
def add_files(translation_project, ignored_files, exts, relative_dir, db_dir,
              file_filter=lambda _x: True):
    podir_path = to_podir_path(relative_dir)
    files, dirs = split_files_and_dirs(
        ignored_files, exts, podir_path, file_filter)
    file_set = set(files)
    dir_set = set(dirs)

    existing_stores = dict((store.name, store) for store in
                           db_dir.child_stores.live().exclude(file='')
                                                     .iterator())
    existing_dirs = dict((dir.name, dir) for dir in
                         db_dir.child_dirs.live().iterator())

    files, new_files = add_items(
        file_set,
        existing_stores,
        lambda name: create_or_resurrect_store(
            f=os.path.join(relative_dir, name),
            parent=db_dir,
            name=name,
            translation_project=translation_project,
        ),
        db_dir,
    )

    db_subdirs, new_db_subdirs_ = add_items(
        dir_set,
        existing_dirs,
        lambda name: create_or_resurrect_dir(
            tp=translation_project, name=name, parent=db_dir),
        db_dir,
    )

    is_empty = len(files) == 0
    for db_subdir in db_subdirs:
        fs_subdir = os.path.join(relative_dir, db_subdir.name)
        _files, _new_files, _is_empty = add_files(
            translation_project,
            ignored_files,
            exts,
            fs_subdir,
            db_subdir,
            file_filter)
        files += _files
        new_files += _new_files
        is_empty &= _is_empty

    if is_empty:
        db_dir.makeobsolete()

    return files, new_files, is_empty


def to_podir_path(path):
    path = relative_real_path(path)
    return os.path.join(settings.POOTLE_TRANSLATION_DIRECTORY, path)


def find_lang_postfix(project, filename):
    """Finds the language code at end of a filename."""
    name = os.path.splitext(os.path.basename(filename))[0]
    if LANGCODE_RE.match(name):
        return project.lang_mapper.get_pootle_code(name)

    match = LANGCODE_POSTFIX_RE.match(name)
    if match:
        return project.lang_mapper.get_pootle_code(match.groups()[0])

    for code in Language.objects.values_list('code', flat=True):
        code = project.lang_mapper.get_upstream_code(code)
        if (name.endswith('-'+code) or name.endswith('_'+code) or
            name.endswith('.'+code) or
            name.lower().endswith('-'+code.lower()) or
            name.endswith('_'+code) or name.endswith('.'+code)):
            return code


def translation_project_dir_exists(language, project):
    """Tests if there are translation files corresponding to the given
    :param:`language` and :param:`project`.
    """
    if project.get_treestyle() == "gnu":
        # GNU style projects are tricky

        if language.code == 'templates':
            # Language is template look for template files
            for dirpath_, dirnames, filenames in os.walk(
                    project.get_real_path()):
                for filename in filenames:
                    if (project.file_belongs_to_project(filename,
                                                        match_templates=True)
                            and match_template_filename(project, filename)):
                        return True
        else:
            # find files with the language name in the project dir
            for dirpath_, dirnames, filenames in os.walk(
                    project.get_real_path()):
                for filename in filenames:
                    # FIXME: don't reuse already used file
                    filename_matches = (
                        project.file_belongs_to_project(
                            filename,
                            match_templates=False)
                        and direct_language_match_filename(
                            project.lang_mapper.get_upstream_code(language.code),
                            filename))
                    if filename_matches:
                        return True
    else:
        # find directory with the language name in the project dir
        try:
            dirpath_, dirnames, filename = os.walk(
                project.get_real_path()).next()
            lang_code = project.lang_mapper.get_upstream_code(language.code)
            if lang_code in dirnames:
                return True
        except StopIteration:
            pass

    return False


def init_store_from_template(translation_project, template_store):
    """Initialize a new file for `translation_project` using `template_store`.
    """
    if translation_project.file_style == 'gnu':
        target_path = get_translated_name_gnu(
            translation_project, template_store)
    else:
        target_path = get_translated_name(
            translation_project, template_store)

    # Create the missing directories for the new TP.
    target_dir = os.path.dirname(target_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    output_file = template_store.file.store
    output_file.settargetlanguage(translation_project.language.code)
    output_file.savefile(target_path)


def get_translated_name_gnu(translation_project, store):
    """Given a template :param:`store` and a :param:`translation_project` return
    target filename.
    """
    language_code = translation_project.language.code
    project = translation_project.project
    pootle_path_parts = store.pootle_path.split('/')
    pootle_path_parts[1] = language_code
    pootle_path = '/'.join(pootle_path_parts[:-1])
    if not pootle_path.endswith('/'):
        pootle_path = pootle_path + '/'

    upstream_lang_code = project.lang_mapper.get_upstream_code(language_code)
    suffix = (
        "%s%s%s"
        % (upstream_lang_code,
           os.extsep,
           store.filetype.extension))
    # try loading file first
    try:
        target_store = translation_project.stores.live().get(
            parent__pootle_path=pootle_path,
            name__iexact=suffix,
        )
        return target_store.file and target_store.file.path
    except Store.DoesNotExist:
        target_store = None

    # is this GNU-style with prefix?
    use_prefix = (store.parent.child_stores.live().exclude(file="").count() > 1
                  or translation_project.stores.live().exclude(
                      name__iexact=suffix, file='').count())
    if not use_prefix:
        # let's make sure
        for tp in project.translationproject_set.exclude(
                language__code='templates').iterator():
            temp_suffix = (
                "%s%s%s"
                % (tp.language.code,
                   os.extsep,
                   store.filetype.template_extension))
            if tp.stores.live().exclude(
                    name__iexact=temp_suffix).exclude(file="").count():
                use_prefix = True
                break

    if use_prefix:
        if store.translation_project.language.code == 'templates':
            tprefix = os.path.splitext(store.name)[0]
            # FIXME: we should detect separator
            prefix = tprefix + '-'
        else:
            prefix = os.path.splitext(store.name)[0][:-len(
                upstream_lang_code)]
            tprefix = prefix[:-1]

        try:
            target_store = translation_project.stores.live().filter(
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

            return target_store.file and target_store.file.path
        except (Store.DoesNotExist, IndexError):
            pass
    else:
        prefix = ""

    if store.file:
        path_parts = store.file.path.split(os.sep)
        name = prefix + suffix
        path_parts[-1] = name
    else:
        path_parts = store.parent.get_real_path().split(os.sep)
        path_parts.append(store.name)

    return os.sep.join(path_parts)


def get_translated_name(translation_project, store):
    name = os.path.splitext(store.name)[0]
    language_code = translation_project.language.code
    project = translation_project.project

    if store.file:
        path_parts = store.file.name.split(os.sep)
    else:
        path_parts = store.parent.get_real_path().split(os.sep)
        path_parts.append(store.name)

    # Replace language code
    path_parts[1] = project.lang_mapper.get_upstream_code(language_code)

    # Replace extension
    path_parts[-1] = (
        "%s.%s"
        % (name,
           store.filetype.extension))

    return absolute_real_path(os.sep.join(path_parts))


def does_not_exist(path):
    if os.path.exists(path):
        return False

    try:
        os.stat(path)
        # what the hell?
    except OSError as e:
        if e.errno == errno.ENOENT:
            # explicit no such file or directory
            return True
