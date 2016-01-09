# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fixtures.models.directory import projects, root
from fixtures.models.language import (
    english, templates, afrikaans, arabic, french, spanish, italian, russian,
    fish, klingon, klingon_vpw)
from fixtures.models.permission import (
    pootle_content_type, view, hide, suggest, translate, review, administrate)
from fixtures.models.permission_set import nobody_ps, default_ps
from fixtures.models.project import (
    tutorial, tutorial_disabled, project_foo, project_bar, vfolder_test)
from fixtures.models.store import (
    UPDATE_STORE_TESTS,
    po_directory, af_tutorial_po, en_tutorial_po, en_tutorial_po_no_file,
    en_tutorial_po_member_updated, it_tutorial_po, af_tutorial_subdir_po,
    issue_2401_po, test_get_units_po, fr_tutorial_subdir_to_remove_po,
    fr_tutorial_remove_sync_po, es_tutorial_subdir_remove_po, ru_tutorial_po,
    ru_update_save_changed_units_po, ru_update_set_last_sync_revision_po,
    af_vfolder_test_browser_defines_po, templates_tutorial_pot,
    param_update_store_test, store_diff_tests)
from fixtures.models.translation_project import (
    afrikaans_tutorial, arabic_tutorial_obsolete, english_tutorial,
    french_tutorial, spanish_tutorial, italian_tutorial, russian_tutorial,
    afrikaans_vfolder_test, templates_tutorial)
from fixtures.models.user import (
    default, system, nobody, trans_nobody, admin, member, trans_member,
    trans_system, member_with_email, member2, evil_member)
from fixtures.models.unit import (
    UNIT_PATH_RESOLVER_TESTS, unit_path_resolver_tests)

from fixtures.cache import delete_pattern
from fixtures.import_export_fixtures import (
    FILE_IMPORT_FAIL_TESTS,
    file_import_failure, ts_directory, en_tutorial_ts)
from fixtures.revision import revision
from fixtures.site import (
    site_matrix, site_matrix_with_subdirs, site_matrix_with_vfolders,
    site_matrix_with_announcements, site_root, site_permissions)
from fixtures.views import (
    BAD_VIEW_TESTS, bad_views,
    LANGUAGE_VIEW_TESTS, language_views,
    PROJECT_VIEW_TESTS, project_views,
    TP_VIEW_TESTS, tp_views,
    admin_client)
from fixtures.core.utils.wordcount import WORDCOUNT_TESTS


__all__ = (
    'admin', 'default', 'evil_member', 'member', 'member2',
    'member_with_email', 'nobody', 'system', 'trans_member', 'trans_nobody',
    'trans_system', 'projects', 'root', 'afrikaans', 'arabic', 'english',
    'fish', 'french', 'italian', 'klingon', 'klingon_vpw', 'russian',
    'spanish', 'templates', 'administrate', 'hide', 'pootle_content_type',
    'review', 'suggest', 'translate', 'view', 'default_ps', 'nobody_ps',
    'project_bar', 'project_foo', 'tutorial', 'tutorial_disabled',
    'vfolder_test', 'af_tutorial_po', 'af_tutorial_subdir_po',
    'af_vfolder_test_browser_defines_po', 'en_tutorial_po',
    'en_tutorial_po_member_updated', 'en_tutorial_po_no_file',
    'es_tutorial_subdir_remove_po', 'fr_tutorial_remove_sync_po',
    'fr_tutorial_subdir_to_remove_po', 'issue_2401_po', 'it_tutorial_po',
    'param_update_store_test', 'po_directory', 'ru_tutorial_po',
    'ru_update_save_changed_units_po', 'ru_update_set_last_sync_revision_po',
    'store_diff_tests', 'templates_tutorial_pot', 'test_get_units_po',
    'afrikaans_tutorial', 'afrikaans_vfolder_test', 'arabic_tutorial_obsolete',
    'english_tutorial', 'french_tutorial', 'italian_tutorial',
    'russian_tutorial', 'spanish_tutorial', 'templates_tutorial',
    'delete_pattern', 'en_tutorial_ts', 'file_import_failure', 'ts_directory',
    'revision', 'admin_client', 'site_matrix', 'site_matrix_with_subdirs',
    'site_root', 'site_matrix_with_vfolders', 'site_matrix_with_announcements',
    'site_permissions', 'project_views', 'tp_views', 'language_views',
    'bad_views', 'unit_path_resolver_tests')


PARAMETERS = (
    ("update_store_test_names", UPDATE_STORE_TESTS),
    ("file_import_failure_names", FILE_IMPORT_FAIL_TESTS),
    ("wordcount_names", WORDCOUNT_TESTS),
    ("project_view_names", PROJECT_VIEW_TESTS),
    ("language_view_names", LANGUAGE_VIEW_TESTS),
    ("tp_view_names", TP_VIEW_TESTS),
    ("bad_view_names", BAD_VIEW_TESTS),
    ("unit_path_resolver_names", UNIT_PATH_RESOLVER_TESTS))


def pytest_generate_tests(metafunc):
    for name, params in PARAMETERS:
        if name in metafunc.fixturenames:
            metafunc.parametrize(name, params)
