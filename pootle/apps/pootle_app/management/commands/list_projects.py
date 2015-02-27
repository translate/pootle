#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import NoArgsCommandMixin
from pootle_project.models import Project


class Command(NoArgsCommandMixin):

    def handle_noargs(self, **options):
        super(Command, self).handle_noargs(**options)
        self.list_projects(**options)

    def list_projects(self, **options):
        """List all projects on the server."""

        for project in Project.objects.all():
            self.stdout.write(project.code)
