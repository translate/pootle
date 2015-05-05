#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import NoArgsCommand

from pootle_project.models import Project


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        self.list_projects(**options)

    def list_projects(self, **options):
        """List all projects on the server."""

        for project in Project.objects.all():
            self.stdout.write(project.code)
