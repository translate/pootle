# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fixtures.core.utils.wordcount import wordcount_names
from fixtures.models.directory import projects, root
from fixtures.models.language import (
    english, templates, afrikaans, arabic, french, spanish, italian, russian,
    fish, klingon, klingon_vpw)
from fixtures.models.permission import (
    pootle_content_type, view, hide, suggest, translate, review, administrate)
from fixtures.models.project import (
    tutorial, tutorial_disabled, project_foo, project_bar, vfolder_test)
from fixtures.models.store import (
    po_directory, af_tutorial_po, en_tutorial_po, en_tutorial_po_no_file,
    en_tutorial_po_member_updated, it_tutorial_po, af_tutorial_subdir_po,
    issue_2401_po, test_get_units_po, fr_tutorial_subdir_to_remove_po,
    fr_tutorial_remove_sync_po, es_tutorial_subdir_remove_po, ru_tutorial_po,
    ru_update_save_changed_units_po, ru_update_set_last_sync_revision_po,
    af_vfolder_test_browser_defines_po,
    param_update_store_test, store_diff_tests)
from fixtures.models.translation_project import (
    afrikaans_tutorial, arabic_tutorial_obsolete, english_tutorial,
    french_tutorial, spanish_tutorial, italian_tutorial, russian_tutorial,
    afrikaans_vfolder_test, templates_tutorial)
from fixtures.models.user import (
    default, system, nobody, admin, member, trans_member,
    member_with_email, member2, member2_with_email, evil_member,
    no_perms_user)
from fixtures.search import units_text_searches
from fixtures.cache import delete_pattern
from fixtures.import_export_fixtures import (
    file_import_failure, ts_directory, en_tutorial_ts)
from fixtures.revision import revision
from fixtures.site import (
    no_extra_users,
    no_projects, no_permissions, no_permission_sets, no_submissions, no_users,
    post_db_setup)
from fixtures.views import (
    bad_views, language_views, project_views, tp_views,
    tp_view_test_names, tp_view_usernames)


__all__ = (
    'admin', 'default', 'evil_member', 'member', 'member2', 'no_perms_user',
    'member_with_email', 'member2_with_email', 'nobody', 'system',
    'trans_member', 'projects', 'root',
    'afrikaans', 'arabic', 'english', 'fish', 'french', 'italian', 'klingon',
    'klingon_vpw', 'russian', 'spanish', 'templates', 'administrate', 'hide',
    'pootle_content_type', 'review', 'suggest', 'translate', 'view',
    'project_bar', 'project_foo', 'tutorial',
    'tutorial_disabled', 'vfolder_test', 'af_tutorial_po',
    'af_tutorial_subdir_po', 'af_vfolder_test_browser_defines_po',
    'en_tutorial_po', 'en_tutorial_po_member_updated',
    'en_tutorial_po_no_file', 'es_tutorial_subdir_remove_po',
    'fr_tutorial_remove_sync_po', 'fr_tutorial_subdir_to_remove_po',
    'issue_2401_po', 'it_tutorial_po', 'param_update_store_test',
    'po_directory', 'ru_tutorial_po', 'ru_update_save_changed_units_po',
    'ru_update_set_last_sync_revision_po', 'store_diff_tests',
    'test_get_units_po', 'afrikaans_tutorial',
    'afrikaans_vfolder_test', 'arabic_tutorial_obsolete', 'english_tutorial',
    'french_tutorial', 'italian_tutorial', 'russian_tutorial',
    'spanish_tutorial', 'templates_tutorial', 'delete_pattern',
    'en_tutorial_ts', 'file_import_failure', 'ts_directory', 'revision',
    'project_views', 'tp_views', 'language_views',
    'bad_views', 'post_db_setup', 'no_projects', 'no_permission_sets',
    'no_permissions', 'no_submissions', 'no_users', 'no_extra_users',
    'units_text_searches', 'wordcount_names', 'tp_view_test_names',
    'tp_view_usernames')
