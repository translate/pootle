# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
from datetime import datetime, timedelta

from django.utils.functional import cached_property


class PootleTestEnv(object):

    methods = (
        "case_sensitive_schema", "content_type", "site_root", "system_users",
        "permissions", "site_permissions", "tps", "languages", "vfolders",
        "subdirs", "submissions", "announcements")

    def __init__(self, request):
        self.request = request

    @cached_property
    def dirs(self):
        from pootle_app.models import Directory

        dirs = Directory.objects

        # create root and projects directories, first clear the class cache
        if "root" in dirs.__dict__:
            del dirs.__dict__['root']
        if "projects" in dirs.__dict__:
            del dirs.__dict__['projects']
        return dirs

    def setup(self):
        [getattr(self, "setup_%s" % method)()
         for method
         in self.methods]
        self.request.addfinalizer(self.teardown)

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
        content_type.save()

        return content_type

    def setup_permissions(self):
        from .fixtures.models.permission import _require_permission

        _require_permission(
            'view',
            'Can access a project')
        _require_permission(
            'hide',
            'Cannot access a project')
        _require_permission(
            'suggest',
            'Can make a suggestion')
        _require_permission(
            'translate',
            'Can submit translations')
        _require_permission(
            'review',
            'Can review translations')
        _require_permission(
            'administrate',
            'Can administrate a TP')

    def setup_languages(self):
        from .fixtures.models.language import _require_language
        _require_language('en', 'English')

    def setup_system_users(self):
        from .fixtures.models.user import _require_user

        _require_user('nobody', 'Nobody')
        _require_user('system', 'System')
        _require_user(
            'default', 'Default', password='')

        _require_user(
            'admin', 'Admin',
            password='admin',
            is_superuser=True,
            email="admin@poot.le")
        _require_user(
            'member', 'Member',
            password='')
        _require_user(
            'member2', 'Member 2',
            password='')

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
        permission_set = PermissionSet.objects.create(**criteria)
        permission_set.positive_permissions = [view, suggest]
        permission_set.save()

        criteria['user'] = default
        permission_set = PermissionSet.objects.create(**criteria)
        permission_set.positive_permissions = [view, suggest, translate]
        permission_set.save()

    def setup_site_root(self):

        from pytest_pootle.factories import (
            ProjectFactory, DirectoryFactory, LanguageFactory)

        DirectoryFactory(
            name="projects",
            parent=DirectoryFactory(parent=None, name=""))

        # add 2 languages
        languages = [LanguageFactory() for i in range(0, 2)]

        for i in range(0, 2):
            # add 2 projects
            ProjectFactory(source_language=languages[0])

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

    def teardown(self):
        from django.conf import settings

        if "root" in self.dirs.__dict__:
            del self.dirs.__dict__['root']
        if "projects" in self.dirs.__dict__:
            del self.dirs.__dict__['projects']
        # required to get clean slate 8/
        for trans_dir in os.listdir(settings.POOTLE_TRANSLATION_DIRECTORY):
            if trans_dir.startswith("project"):
                shutil.rmtree(
                    os.path.join(
                        settings.POOTLE_TRANSLATION_DIRECTORY, trans_dir))

    def setup_tps(self):
        from pootle_project.models import Project
        from pootle_language.models import Language
        from pytest_pootle.factories import TranslationProjectFactory

        for project in Project.objects.all():
            for language in Language.objects.all():
                # add a TP to the project for each language
                tp = TranslationProjectFactory(project=project, language=language)
                # As there are no files on the FS we have to currently unobsolete
                # the directory
                tp_dir = tp.directory
                tp_dir.obsolete = False
                tp_dir.save()
                self._add_stores(tp)

    def setup_vfolders(self):
        from pytest_pootle.factories import VirtualFolderFactory

        VirtualFolderFactory(filter_rules="store0.po")
        VirtualFolderFactory(filter_rules="store1.po")
        vfolder2 = VirtualFolderFactory(
            location='/{LANG}/project0/',
            filter_rules="store0.po")
        vfolder3 = VirtualFolderFactory(
            location='/{LANG}/project0/',
            filter_rules="store1.po")

        vfolder2.is_public = False
        vfolder2.save()
        vfolder3.is_public = False
        vfolder3.save()

    def _add_stores(self, tp, n=(3, 2), parent=None):
        from pytest_pootle.factories import StoreFactory, UnitFactory

        from pootle_store.models import UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE

        for i in range(0, n[0]):
            # add 3 stores
            if parent is None:
                store = StoreFactory(translation_project=tp)
            else:
                store = StoreFactory(translation_project=tp, parent=parent)

            # add 8 units to each store
            for state in [UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE]:
                for i in range(0, n[1]):
                    UnitFactory(store=store, state=state)

    def _update_submission_times(self, update_time, last_update=None):
        from pootle_statistics.models import Submission

        submissions = Submission.objects.all()
        if last_update:
            submissions = submissions.exclude(
                creation_time__lte=last_update)
        submissions.update(creation_time=update_time)

    def _add_submissions(self, unit, created):
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
            "Suggestion for %s" % unit.source,
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
            "Suggestion 2 for %s" % unit.source,
            user=member2,
            touch=False)
        self._update_submission_times(
            first_modified + timedelta(days=14),
            next_time)

        # mark FUZZY
        if original_state == FUZZY:
            unit.markfuzzy()

        # mark OBSOLETE
        if original_state == OBSOLETE:
            unit.makeobsolete()
