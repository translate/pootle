# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import CommandError

from pootle_format.models import Format
from pootle_project.models import Project

from . import PootleCommand


class Command(PootleCommand):
    help = "Manage Store formats."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            'filetype',
            action='store',
            help="File type to set")
        parser.add_argument(
            '--from-filetype',
            action='store',
            help="Only convert Stores of this file type")
        parser.add_argument(
            '--matching',
            action='store',
            help="Glob match Store path excluding extension")

    def get_projects(self):
        if not self.projects:
            return Project.objects.all()

        return Project.objects.filter(code__in=self.projects)

    def get_filetype(self, name):
        try:
            return Format.objects.get(name=name)
        except Format.DoesNotExist:
            raise CommandError("Unrecognized filetype '%s'" % name)

    def handle_all(self, **options):
        filetype = self.get_filetype(options["filetype"])
        from_filetype = (
            options["from_filetype"]
            and self.get_filetype(options["from_filetype"])
            or None)
        for project in self.get_projects():
            # add the filetype to project, and convert the stores
            project.filetype_tool.add_filetype(filetype)
            project.filetype_tool.set_filetypes(
                filetype,
                from_filetype=from_filetype,
                matching=options["matching"])
