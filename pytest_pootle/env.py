# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from translate.storage.factory import getclass


class PootleTestEnv(object):

    methods = (
        "redis", "case_sensitive_schema", "formats", "site_root",
        "languages", "site_matrix", "system_users", "permissions",
        "site_permissions", "tps",
        "disabled_project", "subdirs", "submissions", "announcements",
        "terminology", "fs", "vfolders", "complex_po")

    def setup(self, **kwargs):
        for method in self.methods:
            should_setup = (
                method not in kwargs
                or kwargs[method])
            if should_setup:
                getattr(self, "setup_%s" % method)()

    def setup_formats(self):
        from pootle.core.delegate import formats

        formats.get().initialize()

    def setup_complex_po(self):
        import pytest_pootle
        from pytest_pootle.factories import StoreDBFactory
        from pootle_translationproject.models import TranslationProject

        po_file = os.path.join(
            os.path.dirname(pytest_pootle.__file__),
            *("data", "po", "complex.po"))
        with open(po_file) as f:
            ttk = getclass(f)(f.read())

        tp = TranslationProject.objects.get(
            project__code="project0",
            language__code="language0")

        store = StoreDBFactory(
            parent=tp.directory,
            translation_project=tp,
            name="complex.po")
        store.update(ttk)

    def setup_announcements(self):
        from pytest_pootle.factories import AnnouncementFactory

        from pootle_project.models import Project
        from pootle_language.models import Language
        from pootle_translationproject.models import TranslationProject

        for language in Language.objects.all():
            AnnouncementFactory(
                title="Language announcement for: %s" % language,
                body=(
                    '<div dir="ltr" lang="en">This is an example announcements. '
                    'Just like a real announcement it contains text and some '
                    'markup, and even a random link about localisation.<br />'
                    '<a href="http://docs.translatehouse.org/languages/'
                    'localization-guide/en/latest/guide/start.html">localisation '
                    'guide</a>.</div>'),
                virtual_path="announcements/%s" % language.code)

        for project in Project.objects.all():
            AnnouncementFactory(
                title="Project announcement for: %s" % project,
                body=(
                    '<div dir="ltr" lang="en">This is an example announcements. '
                    'Just like a real announcement it contains text and some '
                    'markup, and even a random link about localisation.<br />'
                    '<a href="http://docs.translatehouse.org/projects/'
                    'localization-guide/en/latest/guide/start.html">localisation '
                    'guide</a>.</div>'),
                virtual_path="announcements/projects/%s" % project.code)

        for tp in TranslationProject.objects.all():
            AnnouncementFactory(
                title="TP announcement for: %s" % tp,
                body=(
                    '<div dir="ltr" lang="en">This is an example announcements. '
                    'Just like a real announcement it contains text and some '
                    'markup, and even a random link about localisation.<br />'
                    '<a href="http://docs.translatehouse.org/tps/'
                    'localization-guide/en/latest/guide/start.html">localisation '
                    'guide</a>.</div>'),
                virtual_path="announcements/%s/%s"
                % (tp.language.code, tp.project.code))

    def setup_case_sensitive_schema(self):
        from django.db import connection
        from django.apps import apps

        from pootle.core.utils.db import set_mysql_collation_for_column

        cursor = connection.cursor()

        # Language
        set_mysql_collation_for_column(
            apps,
            cursor,
            "pootle_language.Language",
            "code",
            "utf8_general_ci",
            "varchar(50)")

        # Project
        set_mysql_collation_for_column(
            apps,
            cursor,
            "pootle_project.Project",
            "code",
            "utf8_bin",
            "varchar(255)")

        # Directory
        set_mysql_collation_for_column(
            apps,
            cursor,
            "pootle_app.Directory",
            "pootle_path",
            "utf8_bin",
            "varchar(255)")
        set_mysql_collation_for_column(
            apps,
            cursor,
            "pootle_app.Directory",
            "name",
            "utf8_bin",
            "varchar(255)")

        # Store
        set_mysql_collation_for_column(
            apps,
            cursor,
            "pootle_store.Store",
            "pootle_path",
            "utf8_bin",
            "varchar(255)")
        set_mysql_collation_for_column(
            apps,
            cursor,
            "pootle_store.Store",
            "name",
            "utf8_bin",
            "varchar(255)")

    def setup_permissions(self):
        from django.contrib.contenttypes.models import ContentType

        from .fixtures.models.permission import _require_permission

        args = {
            'app_label': 'pootle_app',
            'model': 'directory'}
        pootle_content_type = ContentType.objects.get(**args)

        _require_permission(
            'view',
            'Can access a project',
            pootle_content_type)
        _require_permission(
            'hide',
            'Cannot access a project',
            pootle_content_type)
        _require_permission(
            'suggest',
            'Can make a suggestion',
            pootle_content_type)
        _require_permission(
            'translate',
            'Can submit translations',
            pootle_content_type)
        _require_permission(
            'review',
            'Can review translations',
            pootle_content_type)
        _require_permission(
            'administrate',
            'Can administrate a TP',
            pootle_content_type)

    def setup_fs(self):
        from pytest_pootle.utils import add_store_fs

        from pootle_project.models import Project
        from pootle_fs.utils import FSPlugin

        project = Project.objects.get(code="project0")
        project.config["pootle_fs.fs_type"] = "localfs"
        project.config["pootle_fs.translation_mappings"] = {
            "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
        project.config["pootle_fs.fs_url"] = "/tmp/path/for/setup"
        plugin = FSPlugin(project)
        for store in plugin.resources.stores:
            add_store_fs(
                store=store,
                fs_path=plugin.get_fs_path(store.pootle_path),
                synced=True)

    def setup_languages(self):
        from .fixtures.models.language import _require_language
        _require_language('en', 'English')

    def setup_redis(self):
        from pootle.core.models import Revision

        Revision.initialize(force=True)

    def setup_system_users(self):
        from .fixtures.models.user import TEST_USERS, _require_user

        for username, user_params in TEST_USERS.items():
            user = _require_user(username=username, **user_params)
            TEST_USERS[username]["user"] = user

    def setup_site_permissions(self):
        from django.contrib.auth import get_user_model

        from pootle_app.models import Directory, PermissionSet

        User = get_user_model()

        nobody = User.objects.get_nobody_user()
        default = User.objects.get_default_user()

        from django.contrib.auth.models import Permission

        view = Permission.objects.get(codename="view")
        suggest = Permission.objects.get(codename="suggest")
        translate = Permission.objects.get(codename="translate")

        criteria = {
            'user': nobody,
            'directory': Directory.objects.root}
        permission_set, created = PermissionSet.objects.get_or_create(**criteria)
        if created:
            permission_set.positive_permissions = [view, suggest]
            permission_set.save()

        criteria['user'] = default
        permission_set, created = PermissionSet.objects.get_or_create(**criteria)
        if created:
            permission_set.positive_permissions = [view, suggest, translate]
            permission_set.save()

    def setup_site_root(self):
        from pytest_pootle.factories import DirectoryFactory

        DirectoryFactory(
            name="projects",
            parent=DirectoryFactory(parent=None, name=""))

    def setup_site_matrix(self):
        from pytest_pootle.factories import ProjectDBFactory, LanguageDBFactory

        from pootle_format.models import Format
        from pootle_language.models import Language

        # add 2 languages
        for i_ in range(0, 2):
            LanguageDBFactory()

        source_language = Language.objects.get(code="en")
        po = Format.objects.get(name="po")
        for i_ in range(0, 2):
            # add 2 projects
            project = ProjectDBFactory(
                source_language=source_language,
                treestyle='pootle_fs')
            project.filetypes.add(po)

    def setup_terminology(self):
        from pytest_pootle.factories import (ProjectDBFactory,
                                             TranslationProjectFactory)
        from pootle_language.models import Language

        source_language = Language.objects.get(code="en")
        terminology = ProjectDBFactory(code="terminology",
                                       checkstyle="terminology",
                                       fullname="Terminology",
                                       source_language=source_language)
        for language in Language.objects.all():
            TranslationProjectFactory(project=terminology, language=language)

    def setup_disabled_project(self):
        from pytest_pootle.factories import (DirectoryFactory,
                                             ProjectDBFactory,
                                             TranslationProjectFactory)

        from pootle_format.models import Format
        from pootle_language.models import Language

        source_language = Language.objects.get(code="en")
        project = ProjectDBFactory(code="disabled_project0",
                                   fullname="Disabled Project 0",
                                   source_language=source_language)
        project.filetypes.add(Format.objects.get(name="po"))
        project.disabled = True
        project.save()
        language = Language.objects.get(code="language0")
        tp = TranslationProjectFactory(project=project, language=language)
        tp_dir = tp.directory
        tp_dir.obsolete = False
        tp_dir.save()
        self._add_stores(tp, n=(1, 1))
        subdir0 = DirectoryFactory(name="subdir0", parent=tp.directory, tp=tp)
        self._add_stores(tp, n=(1, 1), parent=subdir0)

    def setup_subdirs(self):
        from pytest_pootle.factories import DirectoryFactory

        from pootle_translationproject.models import TranslationProject

        for tp in TranslationProject.objects.all():
            subdir0 = DirectoryFactory(name="subdir0", parent=tp.directory, tp=tp)
            subdir1 = DirectoryFactory(name="subdir1", parent=subdir0, tp=tp)
            self._add_stores(tp, n=(2, 1), parent=subdir0)
            self._add_stores(tp, n=(1, 1), parent=subdir1)

    def setup_submissions(self):
        from pootle.core.contextmanagers import update_data_after
        from pootle_store.models import Store, Unit
        from django.utils import timezone

        year_ago = timezone.now() - relativedelta(years=1)
        Unit.objects.update(creation_time=year_ago)

        stores = Store.objects.select_related(
            "translation_project__project",
            "translation_project__language")

        for store in stores.all():
            with update_data_after(store):
                for unit in store.unit_set.all():
                    unit.store = store
                    self._add_submissions(unit, year_ago)

    def setup_tps(self):
        from pootle_project.models import Project
        from pootle_language.models import Language
        from pytest_pootle.factories import TranslationProjectFactory

        for project in Project.objects.all():
            for language in Language.objects.exclude(code="en"):
                # add a TP to the project for each language
                tp = TranslationProjectFactory(project=project, language=language)
                # As there are no files on the FS we have to currently unobsolete
                # the directory
                tp_dir = tp.directory
                tp_dir.obsolete = False
                tp_dir.save()
                self._add_stores(tp)

    def _add_stores(self, tp, n=(3, 2), parent=None):
        from pytest_pootle.factories import StoreDBFactory, UnitDBFactory

        from pootle_store.constants import UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE

        for i_ in range(0, n[0]):
            # add 3 stores
            if parent is None:
                store = StoreDBFactory(translation_project=tp)
            else:
                store = StoreDBFactory(translation_project=tp, parent=parent)
            store.filetype = tp.project.filetype_tool.choose_filetype(store.name)
            store.save()

            # add 8 units to each store
            for state in [UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE]:
                for i_ in range(0, n[1]):
                    UnitDBFactory(store=store, state=state)

    def _update_submission_times(self, unit, update_time, last_update=None):
        submissions = unit.submission_set.all()
        if last_update:
            submissions = submissions.exclude(
                creation_time__lte=last_update)
        submissions.update(creation_time=update_time)

    def _add_submissions(self, unit, created):
        from pootle.core.delegate import review
        from pootle_statistics.models import SubmissionTypes
        from pootle_store.constants import UNTRANSLATED, FUZZY, OBSOLETE
        from pootle_store.models import Suggestion, Unit

        from django.contrib.auth import get_user_model
        from django.utils import timezone

        original_state = unit.state
        unit.created = created

        User = get_user_model()
        admin = User.objects.get(username="admin")
        member = User.objects.get(username="member")
        member2 = User.objects.get(username="member2")

        first_modified = created + relativedelta(months=unit.index, days=10)

        # add suggestion at first_modified
        suggestion_review = review.get(Suggestion)
        suggestion, created_ = suggestion_review().add(
            unit,
            "Suggestion for %s" % (unit.target or unit.source),
            user=member,
            touch=False)
        self._update_submission_times(unit, first_modified, created)

        # accept the suggestion 7 days later if not untranslated
        next_time = first_modified + timedelta(days=7)
        if original_state == UNTRANSLATED:
            suggestion_review([suggestion], reviewer=admin).reject()
        else:
            suggestion_review([suggestion], reviewer=admin).accept()
            Unit.objects.filter(pk=unit.pk).update(
                submitted_on=next_time, mtime=next_time)
        self._update_submission_times(
            unit, next_time, first_modified)

        # add another suggestion as different user 7 days later
        suggestion2_, created_ = suggestion_review().add(
            unit,
            "Suggestion 2 for %s" % (unit.target or unit.source),
            user=member2,
            touch=False)
        self._update_submission_times(
            unit,
            first_modified + timedelta(days=14),
            next_time)

        # mark FUZZY
        if original_state == FUZZY:
            unit.markfuzzy()

        # mark OBSOLETE
        elif original_state == OBSOLETE:
            unit.makeobsolete()

        elif unit.target:
            # Re-edit units with translations, adding some submissions
            # of SubmissionTypes.EDIT_TYPES
            old_target = unit.target
            old_state = unit.state
            current_time = timezone.now() - timedelta(days=14)

            unit.target_f = "Updated %s" % old_target
            unit.store.record_submissions(
                unit,
                old_target,
                old_state,
                current_time,
                member,
                SubmissionTypes.NORMAL,
                target_updated=True)
            unit.save(target_updated=True)

    def setup_vfolders(self):
        from pytest_pootle.factories import VirtualFolderDBFactory

        from django.db import connection
        from django.apps import apps

        from pootle.core.utils.db import set_mysql_collation_for_column
        from pootle_language.models import Language
        from pootle_project.models import Project

        cursor = connection.cursor()

        # VirtualFolder
        set_mysql_collation_for_column(
            apps,
            cursor,
            "virtualfolder.VirtualFolder",
            "name",
            "utf8_bin",
            "varchar(70)")

        project0 = Project.objects.get(code="project0")
        language0 = Language.objects.get(code="language0")
        VirtualFolderDBFactory(filter_rules="store0.po")
        VirtualFolderDBFactory(filter_rules="store1.po")
        vf = VirtualFolderDBFactory(
            all_languages=True,
            is_public=False,
            filter_rules="store0.po")
        vf.projects.add(project0)
        vf.save()
        vf = VirtualFolderDBFactory(
            all_languages=True,
            is_public=False,
            filter_rules="store1.po")
        vf.projects.add(project0)
        vf.save()
        vf = VirtualFolderDBFactory(
            filter_rules="subdir0/store4.po")
        vf.languages.add(language0)
        vf.projects.add(project0)
        vf.save()
