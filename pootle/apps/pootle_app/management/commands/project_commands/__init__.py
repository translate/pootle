# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.lru_cache import lru_cache

from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject
from pootle.core.delegate import tp_tool as tp_tool_getter


def get_project(project_code):
    try:
        return Project.objects.get(code=project_code)
    except Project.DoesNotExist as e:
        raise CommandError(e)


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
            required=True,
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

    @lru_cache()
    def get_project(self, project_code):
        return get_project(project_code)


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

    def handle(self, *args, **options):
        tp_tool = self.get_tp_tool(options['source_project'])
        target_project = self.get_project(options['target_project'])
        tp_query = tp_tool.tp_qs.all()

        if options['languages']:
            tp_query = tp_query.filter(language__code__in=options['languages'])

        for source_tp in tp_query:
            target_tps = tp_tool.get_tps(target_project)
            try:
                target_tp = target_tps.get(language__code=source_tp.language.code)
                tp_tool.update_from_tp(
                    source_tp,
                    target_tp,
                    allow_add_and_obsolete=not options['translations'],
                )
            except TranslationProject.DoesNotExist:
                logging.warning(
                    u"Translation project (/%s/%s) is missing." %
                    (source_tp.language.code, target_project.code)
                )
