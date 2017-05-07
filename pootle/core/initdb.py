# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
from collections import OrderedDict

from translate.lang import data, factory

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import make_password
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from django.utils.translation import ugettext_noop as _

from pootle.core.delegate import formats
from pootle.core.models import Revision
from pootle_app.models import Directory
from pootle_app.models.permissions import PermissionSet, get_pootle_permission
from pootle_app.project_tree import get_translation_project_dir
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject
from staticpages.models import StaticPage as Announcement


logger = logging.getLogger(__name__)


class InitDB(object):

    def __init__(self, create_projects):
        self.create_projects = create_projects

    @cached_property
    def languages(self):
        langs = OrderedDict(
            templates=dict(
                code="templates",
                fullname="Templates"))
        for code in sorted(data.languages.keys()):
            ttk_lang = factory.getlanguage(code)
            langs[code] = {
                'code': code,
                'fullname': ttk_lang.fullname,
                'nplurals': ttk_lang.nplurals,
                'pluralequation': ttk_lang.pluralequation}
            if hasattr(ttk_lang, "specialchars"):
                langs[code]['specialchars'] = ttk_lang.specialchars
        return langs

    @cached_property
    def projects(self):
        projects = OrderedDict()
        if not self.create_projects:
            return {}
        for code in ["terminology", "tutorial"]:
            projects[code] = dict(
                code=code,
                fullname=code.capitalize(),
                checkstyle="standard",
                treestyle="auto")
            if code == "terminology":
                projects[code]["checkstyle"] = "terminology"
        return projects

    @cached_property
    def tps(self):
        projects = self.projects.keys()
        languages = self.languages.keys()
        return [
            (lang, proj)
            for proj
            in projects
            for lang
            in languages]

    @property
    def language_dirs(self):
        return set(
            "/%s/" % lang
            for lang
            in self.languages.keys())

    @property
    def project_dirs(self):
        return set(
            "/projects/%s/" % proj
            for proj
            in self.projects.keys())

    @property
    def tp_dirs(self):
        return set(
            ("/%s/%s/" % (lang, proj))
            for lang, proj
            in self.tps)

    def init_db(self, create_projects=True):

        """Populate the database with default initial data.

        This creates the default database to get a working Pootle installation.
        """
        formats = self.create_formats()
        self.create_revision()
        dirs = self.create_root_directories()
        self.create_essential_users()
        langs = self.create_site_languages(dirs)
        projs = self.create_site_projects(
            dirs=dirs,
            langs=langs,
            formats=formats)
        self.create_site_tps(
            dirs=dirs,
            projs=projs,
            langs=langs)
        self.create_pootle_permissions()
        self.create_pootle_permission_sets()
        self.create_project_announcements()

    def create_formats(self):
        registry = formats.get()
        registry.initialize()
        return {
            code: filetype["pk"]
            for code, filetype
            in registry.formats.items()}

    def _create_object(self, model_objects, **criteria):
        instance, created = model_objects.get_or_create(**criteria)
        if created:
            logger.debug(
                "Created %s: '%s'",
                instance.__class__.__name__, instance)
        else:
            logger.debug(
                "%s already exists - skipping: '%s'",
                instance.__class__.__name__, instance)
        return instance, created

    def _create_pootle_permission_set(self, permissions, **criteria):
        permission_set, created = self._create_object(
            PermissionSet.objects,
            **criteria)
        if created:
            permission_set.positive_permissions.set(permissions)
            permission_set.save()
        return permission_set

    def create_revision(self):
        Revision.initialize()

    def create_essential_users(self):
        """Create the 'default' and 'nobody' User instances.

        These users are required for Pootle's permission system.
        """
        User = get_user_model()
        users = []
        # The nobody user is used to represent an anonymous user in cases
        # where we need to associate model information with such a user. An
        # example is in the permission system: we need a way to store rights
        # for anonymous users; thus we use the nobody user.
        users.append(
            User(username=u"nobody",
                 full_name=u"any anonymous user",
                 is_active=True))

        # The 'default' user represents any valid, non-anonymous user and is
        # used to associate information any such user. An example is in the
        # permission system: we need a way to store default rights for users.
        # We use the 'default' user for this.
        #
        # In a future version of Pootle we should think about using Django's
        # groups to do better permissions handling.
        users.append(
            User(username=u"default",
                 full_name=u"any authenticated user",
                 is_active=True))
        for user in users:
            user.password = make_password(None)
        User.objects.bulk_create(users)

    def create_pootle_permissions(self):
        """Create Pootle's directory level permissions."""

        args = {
            'app_label': "pootle_app",
            'model': "directory",
        }

        pootle_content_type = self._create_object(ContentType.objects, **args)[0]
        pootle_content_type.save()

        # Create the permissions.
        permissions = [
            {
                'name': _("Can access a project"),
                'codename': "view",
            },
            {
                'name': _("Cannot access a project"),
                'codename': "hide",
            },
            {
                'name': _("Can make a suggestion for a translation"),
                'codename': "suggest",
            },
            {
                'name': _("Can submit a translation"),
                'codename': "translate",
            },
            {
                'name': _("Can review suggestions"),
                'codename': "review",
            },
            {
                'name': _("Can perform administrative tasks"),
                'codename': "administrate",
            },
        ]

        criteria = {
            'content_type': pootle_content_type,
        }

        for permission in permissions:
            criteria.update(permission)
            self._create_object(Permission.objects, **criteria)

    def create_pootle_permission_sets(self):
        """Create the default permission set for the 'nobody' and 'default' users.

        'nobody' is the anonymous (non-logged in) user, and 'default' is the
        logged in user.
        """
        User = get_user_model()

        nobody = User.objects.get(username='nobody')
        default = User.objects.get(username='default')

        view = get_pootle_permission('view')
        suggest = get_pootle_permission('suggest')
        translate = get_pootle_permission('translate')

        # Default permissions for tree root.
        criteria = {
            'user': nobody,
            'directory': Directory.objects.root,
        }
        self._create_pootle_permission_set([view, suggest], **criteria)

        criteria['user'] = default
        self._create_pootle_permission_set(
            [view, suggest, translate], **criteria)

        # Default permissions for templates language.
        # Override with no permissions for templates language.
        criteria = {
            'user': nobody,
            'directory': Directory.objects.get(pootle_path="/templates/"),
        }
        self._create_pootle_permission_set([], **criteria)

        criteria['user'] = default
        self._create_pootle_permission_set([], **criteria)

    def get_current_dirs(self):
        return {
            pootle_path: dir_id
            for pootle_path, dir_id
            in Directory.objects.values_list("pootle_path", "id").iterator()}

    def get_current_langs(self):
        return {
            code: lang_id
            for code, lang_id
            in Language.objects.values_list("code", "id").iterator()}

    def get_current_projs(self):
        return {
            code: proj_id
            for code, proj_id
            in Project.objects.values_list("code", "id").iterator()}

    def get_current_tps(self):
        return {
            pootle_path: tp_id
            for pootle_path, tp_id
            in TranslationProject.objects.values_list(
                "pootle_path", "id").iterator()}

    def create_root_directories(self):
        """Create the root Directory items."""
        root, created_ = Directory.objects.get_or_create(name="", parent=None)
        projects, created_ = Directory.objects.get_or_create(
            name="projects", pootle_path="/projects/", parent=root)
        current_dirs = set(self.get_current_dirs().keys())
        lang_dirs = self.language_dirs - current_dirs
        proj_dirs = self.project_dirs - current_dirs
        tp_dirs = self.tp_dirs - current_dirs
        dirs_to_create = [
            Directory(
                pootle_path=path,
                name=path.strip("/"),
                parent=root)
            for path in lang_dirs]
        dirs_to_create += [
            Directory(
                pootle_path=path,
                name=path.strip("/").split("/")[1],
                parent=projects)
            for path in proj_dirs]
        Directory.objects.bulk_create(dirs_to_create)
        current_dirs = self.get_current_dirs()
        dirs_to_create = [
            Directory(
                pootle_path=path,
                name=path.strip("/").split("/")[1],
                tp_path="",
                parent_id=current_dirs["/%s/" % path.strip("/").split("/")[0]])
            for path in tp_dirs]
        Directory.objects.bulk_create(dirs_to_create)
        return self.get_current_dirs()

    def create_site_languages(self, dirs):
        """Create the 'templates' and English languages.

        The 'templates' language is used to give users access to the
        untranslated template files.
        """
        current_langs = self.get_current_langs()
        languages = []
        for code, language in self.languages.items():
            if code in current_langs:
                continue
            language["directory_id"] = dirs["/%s/" % code]
            languages.append(language)
        Language.objects.bulk_create(
            Language(**language)
            for language
            in languages)
        return self.get_current_langs()

    def create_site_projects(self, dirs, langs, formats):
        """Create the terminology project.

        The terminology project is used to display terminology suggestions
        while translating.
        """
        ProjectFiletype = Project.filetypes.through
        current_projs = self.get_current_projs()
        projects = []
        filetypes = []
        for code, project in self.projects.items():
            if code in current_projs:
                continue
            project["directory_id"] = dirs["/projects/%s/" % code]
            project['source_language_id'] = langs["en"]
            projects.append(project)
        Project.objects.bulk_create(
            Project(**project)
            for project
            in projects)
        current_projs = self.get_current_projs()
        current_formats = {
            filetype.project_id: filetype.format_id
            for filetype
            in ProjectFiletype.objects.filter(
                project_id__in=[current_projs[pr["code"]] for pr in projects])}
        for project in projects:
            project_id = current_projs[project["code"]]
            if project_id in current_formats:
                continue
            filetypes.append(
                ProjectFiletype(
                    project_id=project_id,
                    format_id=formats[project.get("format", "po")]))
        if filetypes:
            ProjectFiletype.objects.bulk_create(filetypes)
        return current_projs

    def create_site_tps(self, dirs, langs, projs):
        tps = []
        current_tps = self.get_current_tps()
        update = []
        for lang, proj in self.tps:
            pootle_path = (
                "/%s/%s/"
                % (lang, proj))
            if pootle_path in current_tps:
                continue
            update.append(pootle_path)
            tps.append(
                TranslationProject(
                    language_id=langs[lang],
                    project_id=projs[proj],
                    directory_id=dirs[pootle_path],
                    pootle_path=pootle_path))
        if tps:
            TranslationProject.objects.bulk_create(tps)
        update_tps = TranslationProject.objects.select_related(
            "directory",
            "directory__parent",
            "directory__parent__parent").filter(pootle_path__in=update)
        seen_projs = []
        projects = Project.objects.in_bulk()
        languages = Language.objects.select_related("directory").in_bulk()
        for tp in update_tps.iterator():
            tp.project = projects[tp.project_id]
            tp.language = languages[tp.language_id]
            if tp.project.id not in seen_projs:
                requires_translation_directory = (
                    tp.project.treestyle != 'pootle_fs'
                    and not tp.project.disabled
                    and not tp.project.directory_exists_on_disk())
                if requires_translation_directory:
                    os.makedirs(tp.project.get_real_path())
                seen_projs.append(tp.project.id)
            tp.abs_real_path = get_translation_project_dir(
                tp.language,
                tp.project,
                tp.file_style,
                make_dirs=not tp.directory.obsolete)
            tp.update_from_disk()
        return self.get_current_tps()

    def create_project_announcements(self):
        if not self.create_projects:
            return
        self._create_object(
            Announcement.objects,
            **dict(
                active=True,
                title="Project instructions",
                body=(
                    '<div dir="ltr" lang="en">Tutorial project where users can '
                    'play with Pootle and learn more about translation and '
                    'localisation.<br />For more help on localisation, visit the '
                    '<a href="http://docs.translatehouse.org/projects/'
                    'localization-guide/en/latest/guide/start.html">localisation '
                    'guide</a>.</div>'),
                virtual_path="announcements/projects/tutorial"))
