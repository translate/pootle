# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
import shutil

from django.core.management.base import BaseCommand, CommandError
from django.utils.lru_cache import lru_cache

from pootle.core.delegate import revision_updater, tp_tool as tp_tool_getter
from pootle_app.models import Directory
from pootle_language.models import Language
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
            '--language',
            action='append',
            dest='languages',
            help='Language to handle',
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

    def get_language(self, language_code):
        try:
            return Language.objects.get(code=language_code)
        except Language.DoesNotExist as e:
            raise CommandError(e)

    def check_no_project(self, project_code):
        if Project.objects.filter(code=project_code).exists():
            raise CommandError('Project <%s> already exists.' % project_code)

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
            filetypes=project.filetypes.values_list('name'),
            treestyle=project.treestyle,
            ignoredfiles=project.ignoredfiles,
            disabled=project.disabled,
        )
        return Project.objects.create(**params)

    def post_handle(self):
        pass

    def handle(self, *args, **options):
        self.check_options(**options)
        self.tp_tool = self.get_tp_tool(options['source_project'])
        self.target_project = self.get_target_project(options['target_project'],
                                                      options['languages'])
        tp_query = self.tp_tool.tp_qs.all()
        if options['languages']:
            tp_query = tp_query.filter(language__code__in=options['languages'])

        target_language = None
        if options['target_language']:
            target_language = self.get_language(options['target_language'])
        for source_tp in tp_query:
            self.handle_tp(source_tp, self.target_project,
                           target_language=target_language)

        self.post_handle()


class TPToolSubCommand(TPToolProjectSubCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--target-language',
            type=str,
            dest='target_language',
            help='Target language',
        )
        parser.add_argument(
            '--target-project',
            type=str,
            help='Target project',
        )

        super(TPToolSubCommand, self).add_arguments(parser)

    def check_options(self, **options):
        one_language = options['languages'] and len(options['languages']) == 1
        if options['target_language'] and not one_language:
            raise CommandError('You can only set one source language '
                               'via --language option.')
        if not options['target_language'] and not options['target_project']:
            raise CommandError('At least one of --target-language and '
                               '--target-project is required.')

class MoveCommand(TPToolSubCommand):
    def get_target_project(self, project_code, languages=None):
        project = self.tp_tool.project
        if project_code is None:
            return project

        if languages is None:
            self.check_no_project(project_code)
        return self.get_or_create_project(project_code)

    def handle_tp(self, tp, target_project, target_language=None):
        old_tp = '%s' % tp
        old_tp_path = tp.abs_real_path
        old_project = tp.project
        if target_language is None:
            target_language = tp.language
        self.tp_tool.move(tp, language=target_language, project=target_project)
        if old_project.treestyle != 'pootle_fs':
            shutil.rmtree(old_tp_path)
        self.stdout.write('Translation project '
                          '"%s" has been moved into "%s".' % (old_tp, tp))

    def post_handle(self):
        revision_updater.get(Directory)(
            context=self.tp_tool.project.directory).update(keys=["stats",
                                                                 "checks"])
        if self.target_project.code != self.tp_tool.project.code:
            if not self.tp_tool.project.translationproject_set.exists():
                project_path = self.tp_tool.project.get_real_path()
                self.tp_tool.project.delete()
                if self.tp_tool.project.treestyle != 'pootle_fs':
                    shutil.rmtree(project_path)


class CloneCommand(TPToolSubCommand):
    def get_target_project(self, project_code, languages=None):
        if languages is None:
            self.check_no_project(project_code)
        return self.get_or_create_project(project_code)

    def handle_tp(self, tp, target_project, target_language=None):
        if target_language is None:
            target_language = tp.language
        cloned = self.tp_tool.clone(tp, language=target_language,
                                    project=target_project)
        self.stdout.write('Translation project '
                          '"%s" has been cloned into "%s".' % (tp, cloned))


class RemoveCommand(TPToolProjectSubCommand):
    help = """Remove project."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            dest="force",
            help="Flag if remove project directory from disk."
        )
        super(RemoveCommand, self).add_arguments(parser)

    def handle(self, *args, **options):
        if not options['languages']:
            project = self.get_project(options['source_project'])
            project_path = project.get_real_path()
            project.delete()
            if options['force']:
                if os.path.exists(project_path):
                    shutil.rmtree(project_path)
            self.stdout.write('Project "%s" has been deleted.' % project)
            return

        tp_tool = self.get_tp_tool(options['source_project'])
        tp_query = tp_tool.tp_qs.all()
        if options['languages']:
            tp_query = tp_query.filter(language__code__in=options['languages'])
            for tp in tp_query:
                tp.delete()
                self.stdout.write('Translation project "%s" has been deleted.'
                                  % tp)
            revision_updater.get(Directory)(
                context=tp_tool.project.directory
            ).update(
                keys=["stats", "checks"]
            )


class UpdateCommand(TPToolSubCommand):
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
        self.check_options(**options)
        tp_tool = self.get_tp_tool(options['source_project'])
        target_project = self.get_project(options['target_project'])
        tp_query = tp_tool.tp_qs.all()

        if options['languages']:
            tp_query = tp_query.filter(language__code__in=options['languages'])

        for source_tp in tp_query:
            target_tps = tp_tool.get_tps(target_project)
            resolve_conflict = SOURCE_WINS if options['overwrite'] else POOTLE_WINS
            target_language_code = source_tp.language.code
            if options['target_language']:
                target_language_code = options['target_language']
            try:
                target_tp = target_tps.get(language__code=target_language_code)
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
