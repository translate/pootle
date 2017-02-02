# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os

from django.core.management.base import BaseCommand, CommandError
from django.utils.lru_cache import lru_cache

from pootle.core.delegate import tp_tool as tp_tool_getter
from pootle_project.models import Project
from pootle_store.constants import SOURCE_WINS, POOTLE_WINS
from pootle_store.util import absolute_real_path
from pootle_translationproject.models import TranslationProject


class TPToolProjectSubCommand(BaseCommand):
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument(
            'source_project',
            type=str,
            help='Source Pootle project',
        )
        parser.add_argument(
            '--target-project',
            type=str,
            help='Target Pootle project',
        )
        parser.add_argument(
            '--language',
            action='append',
            dest='languages',
            help='Language to refresh',
        )
        super(TPToolProjectSubCommand, self).add_arguments(parser)

    @lru_cache()
    def get_tp_tool(self, project_code):
        project = self.get_project(project_code)
        return tp_tool_getter.get(Project)(project)

    def get_project(self, project_code):
        try:
            return Project.objects.get(code=project_code)
        except Project.DoesNotExist as e:
            raise CommandError(e)

    def get_target_project(self, project_code, languages=None):
        return self.get_project(project_code)

    def get_or_create_project(self, target_project_code):
        """Get existing or create an empty copy of project."""
        project = self.tp_tool.project
        try:
            return Project.objects.get(code=target_project_code)
        except Project.DoesNotExist:
            pass

        target_project_abs_path = absolute_real_path(target_project_code)
        if os.path.exists(target_project_abs_path):
            raise CommandError('Project <%s> code cannot be created from '
                               'project <%s> because "%s" directory already '
                               'exists.' % (target_project_code,
                                            project.code,
                                            target_project_abs_path))

        params = dict(
            code=target_project_code,
            fullname="%s (%s)" % (project.fullname, target_project_code),
            checkstyle=project.checkstyle,
            source_language=project.source_language,
            filetypes=project.filetypes.all(),
            treestyle=project.treestyle,
            ignoredfiles=project.ignoredfiles,
            disabled=project.disabled,
        )
        return Project.objects.create(**params)

    def handle(self, *args, **options):
        self.tp_tool = self.get_tp_tool(options['source_project'])
        target_project = self.get_target_project(options['target_project'],
                                                 options['languages'])
        tp_query = self.tp_tool.tp_qs.all()
        if options['languages']:
            tp_query = tp_query.filter(language__code__in=options['languages'])

        for source_tp in tp_query:
            try:
                self.handle_tp(source_tp, target_project)

            except ValueError as e:
                raise CommandError(e)


class MoveCommand(TPToolProjectSubCommand):

    def get_target_project(self, project_code, languages=None):
        project = self.tp_tool.project
        if project_code is None:
            return project

        if not languages:
            project.code = project_code
            project.save()
            #TODO move project directory
            return project
        else:
            return self.get_or_create_project(project_code)

    def handle_tp(self, tp, target_project):
        self.tp_tool.move(tp, language=tp.language, project=target_project)
        self.stdout.write('Translation project '
                          '"%s" has been moved.' % tp)


class CloneCommand(TPToolProjectSubCommand):

    def get_target_project(self, project_code, languages=None):
        return self.get_or_create_project(project_code)

    def handle_tp(self, tp, target_project):
        cloned = self.tp_tool.clone(tp, language=tp.language,
                                    project=target_project)
        self.stdout.write('Translation project '
                          '"%s" has been cloned.' % cloned)


class RemoveCommand(TPToolProjectSubCommand):
    help = """Remove project."""

    def handle(self, *args, **options):
        project = self.get_project(options['source_project'])
        project.delete()
        self.stdout.write('Project "%s" has been deleted.' % project)


class UpdateCommand(TPToolProjectSubCommand):
    help = """Update project."""

    def add_arguments(self, parser):
        super(UpdateCommand, self).add_arguments(parser)
        parser.add_argument(
            "--translations",
            action="store_true",
            default=False,
            dest="translations",
            help="Flag if allow to add new and make obsolete stores and units."
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            dest="overwrite",
            help="Flag if overwrite existing translations."
        )

    def handle(self, *args, **options):
        tp_tool = self.get_tp_tool(options['source_project'])
        target_project = self.get_project(options['target_project'])
        tp_query = tp_tool.tp_qs.all()

        if options['languages']:
            tp_query = tp_query.filter(language__code__in=options['languages'])

        for source_tp in tp_query:
            target_tps = tp_tool.get_tps(target_project)
            resolve_conflict = SOURCE_WINS if options['overwrite'] else POOTLE_WINS
            try:
                target_tp = target_tps.get(language__code=source_tp.language.code)
                tp_tool.update_from_tp(
                    source_tp,
                    target_tp,
                    allow_add_and_obsolete=not options['translations'],
                    resolve_conflict=resolve_conflict,
                )
            except TranslationProject.DoesNotExist:
                logging.warning(
                    u"Translation project (/%s/%s) is missing.",
                    source_tp.language.code, target_project.code
                )
