# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime, timedelta


TEST_USERS = {
    'nobody': dict(
        fullname='Nobody',
        password=''),
    'system': dict(
        fullname='System',
        password=''),
    'default': dict(
        fullname='Default',
        password=''),
    'admin': dict(
        fullname='Admin',
        password='admin',
        is_superuser=True,
        email="admin@poot.le"),
    'member': dict(
        fullname='Member',
        password=''),
    'member2': dict(
        fullname='Member2',
        password=''),
}


class PootleTestEnv(object):

    methods = (
        "redis", "case_sensitive_schema", "content_type", "site_root",
        "languages", "site_matrix", "system_users", "permissions",
        "site_permissions", "tps", "disabled_project", "vfolders",
        "subdirs", "submissions", "announcements", "terminology")

    def __init__(self, request):
        self.request = request

    def setup(self):
        [getattr(self, "setup_%s" % method)()
         for method
         in self.methods]

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

        # VirtualFolderTreeItem
        set_mysql_collation_for_column(
            apps,
            cursor,
            "virtualfolder.VirtualFolderTreeItem",
            "pootle_path",
            "utf8_bin",
            "varchar(255)")

        # VirtualFolder
        set_mysql_collation_for_column(
            apps,
            cursor,
            "virtualfolder.VirtualFolder",
            "name",
            "utf8_bin",
            "varchar(70)")
        set_mysql_collation_for_column(
            apps,
            cursor,
            "virtualfolder.VirtualFolder",
            "location",
            "utf8_bin",
            "varchar(255)")

    def setup_content_type(self):
        from django.contrib.contenttypes.models import ContentType

        args = {
            'app_label': 'pootle_app',
            'model': 'directory'}
        content_type, created = ContentType.objects.get_or_create(**args)
        if created:
            content_type.save()

        return content_type

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

    def setup_languages(self):
        from .fixtures.models.language import _require_language
        _require_language('en', 'English')

    def setup_redis(self):
        from pootle.core.models import Revision

        Revision.initialize(force=True)

    def setup_system_users(self):
        from .fixtures.models.user import _require_user

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

        from pootle_language.models import Language

        # add 2 languages
        for i in range(0, 2):
            LanguageDBFactory()

        source_language = Language.objects.get(code="en")
        for i in range(0, 2):
            # add 2 projects
            ProjectDBFactory(source_language=source_language)

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

        from pootle_language.models import Language

        source_language = Language.objects.get(code="en")
        project = ProjectDBFactory(code="disabled_project0",
                                   fullname="Disabled Project 0",
                                   source_language=source_language)
        project.disabled = True
        project.save()
        language = Language.objects.get(code="language0")
        tp = TranslationProjectFactory(project=project, language=language)
        tp_dir = tp.directory
        tp_dir.obsolete = False
        tp_dir.save()
        self._add_stores(tp, n=(1, 1))
        subdir0 = DirectoryFactory(name="subdir0", parent=tp.directory)
        self._add_stores(tp, n=(1, 1), parent=subdir0)

    def setup_subdirs(self):
        from pytest_pootle.factories import DirectoryFactory

        from pootle_translationproject.models import TranslationProject

        for tp in TranslationProject.objects.all():
            subdir0 = DirectoryFactory(name="subdir0", parent=tp.directory)
            subdir1 = DirectoryFactory(name="subdir1", parent=subdir0)
            self._add_stores(tp, n=(2, 1), parent=subdir0)
            self._add_stores(tp, n=(1, 1), parent=subdir1)

    def setup_submissions(self):
        from pootle_store.models import Unit

        year_ago = datetime.now() - timedelta(days=365)
        Unit.objects.update(creation_time=year_ago)

        for unit in Unit.objects.all():
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

    def setup_vfolders(self):
        from pytest_pootle.factories import VirtualFolderDBFactory

        VirtualFolderDBFactory(filter_rules="store0.po")
        VirtualFolderDBFactory(filter_rules="store1.po")
        VirtualFolderDBFactory(
            location='/{LANG}/project0/',
            is_public=False,
            filter_rules="store0.po")
        VirtualFolderDBFactory(
            location='/{LANG}/project0/',
            is_public=False,
            filter_rules="store1.po")
        VirtualFolderDBFactory(
            location='/language0/project0/',
            filter_rules="subdir0/store4.po")

    def _add_stores(self, tp, n=(3, 2), parent=None):
        from pytest_pootle.factories import StoreDBFactory, UnitDBFactory

        from pootle_store.models import UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE

        for i in range(0, n[0]):
            # add 3 stores
            if parent is None:
                store = StoreDBFactory(translation_project=tp)
            else:
                store = StoreDBFactory(translation_project=tp, parent=parent)

            # add 8 units to each store
            for state in [UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE]:
                for i in range(0, n[1]):
                    UnitDBFactory(store=store, state=state)

    def _update_submission_times(self, update_time, last_update=None):
        from pootle_statistics.models import Submission

        submissions = Submission.objects.all()
        if last_update:
            submissions = submissions.exclude(
                creation_time__lte=last_update)
        submissions.update(creation_time=update_time)

    def _add_submissions(self, unit, created):
        from pootle_statistics.models import SubmissionTypes
        from pootle_store.models import UNTRANSLATED, FUZZY, OBSOLETE, Unit

        from django.contrib.auth import get_user_model

        original_state = unit.state
        unit.created = created

        User = get_user_model()
        admin = User.objects.get(username="admin")
        member = User.objects.get(username="member")
        member2 = User.objects.get(username="member2")

        first_modified = created + timedelta(days=((30 * unit.index) + 10))

        # add suggestion at first_modified
        suggestion, _ = unit.add_suggestion(
            "Suggestion for %s" % (unit.target or unit.source),
            user=member,
            touch=False)
        self._update_submission_times(first_modified, created)

        # accept the suggestion 7 days later if not untranslated
        next_time = first_modified + timedelta(days=7)
        if original_state == UNTRANSLATED:
            unit.reject_suggestion(
                suggestion, unit.store.translation_project, admin)
        else:
            unit.accept_suggestion(
                suggestion, unit.store.translation_project, admin)
            Unit.objects.filter(pk=unit.pk).update(
                submitted_on=next_time, mtime=next_time)
        self._update_submission_times(
            next_time, first_modified)

        # add another suggestion as different user 7 days later
        suggestion2, _ = unit.add_suggestion(
            "Suggestion 2 for %s" % (unit.target or unit.source),
            user=member2,
            touch=False)
        self._update_submission_times(
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
            current_time = datetime.now() - timedelta(days=14)

            unit.target_f = "Updated %s" % old_target
            unit._target_updated = True
            unit.store.record_submissions(
                unit, old_target, old_state,
                current_time, member, SubmissionTypes.NORMAL)
            unit.save()
