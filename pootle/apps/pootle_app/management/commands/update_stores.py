# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand
from pootle_language.models import Language
from pootle_fs.utils import FSPlugin
from pootle_project.models import Project


logger = logging.getLogger(__name__)


class Command(PootleCommand):
    help = "Update database stores from files."
    process_disabled_projects = True
    log_name = "update"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help="Don't just update untranslated units "
                 "and add new units, but overwrite database "
                 "translations to reflect state in files.",
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="This option has been removed.")

    def handle_translation_project(self, translation_project, **options):
        """
        """
        path_glob = "%s*" % translation_project.pootle_path
        plugin = FSPlugin(translation_project.project)
        plugin.add(pootle_path=path_glob, update="pootle")
        plugin.rm(pootle_path=path_glob, update="pootle")
        plugin.resolve(
            pootle_path=path_glob,
            merge=not options["overwrite"])
        plugin.sync(pootle_path=path_glob, update="pootle")

    def _parse_tps_to_create(self, project):
        plugin = FSPlugin(project)
        plugin.fetch()
        untracked_languages = set(
            fs.pootle_path.split("/")[1]
            for fs
            in plugin.state()["fs_untracked"])
        new_langs = (
            [lang for lang
             in untracked_languages
             if lang in self.languages]
            if self.languages
            else untracked_languages)
        return Language.objects.filter(
            code__in=new_langs).exclude(
                code__in=project.translationproject_set.values_list(
                    "language__code", flat=True))

    def _create_tps_for_project(self, project):
        for language in self._parse_tps_to_create(project):
            project.translationproject_set.create(
                language=language,
                project=project)

    def handle_all(self, **options):
        logger.warn(
            "The update_stores command is deprecated, use pootle fs instead")
        if options["force"]:
            logger.warn(
                "The force option no longer has any affect on this command")
        projects = (
            Project.objects.filter(code__in=self.projects)
            if self.projects
            else Project.objects.all())
        for project in projects.iterator():
            self._create_tps_for_project(project)
        super(Command, self).handle_all(**options)
