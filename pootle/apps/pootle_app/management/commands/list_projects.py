#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import (NoArgsCommandMixin,
                                            ModifiedSinceMixin)
from pootle_project.models import Project


class Command(ModifiedSinceMixin, NoArgsCommandMixin):

    def handle_noargs(self, **options):
        super(Command, self).handle_noargs(**options)
        self.list_projects(**options)

    def list_projects(self, **options):
        """List all projects on the server."""
        change_id = options.get('modified_since', 0)

        if change_id:
            from pootle_translationproject.models import TranslationProject
            projects = TranslationProject.objects \
                                         .filter(submission__id__gt=change_id) \
                                         .distinct() \
                                         .values('project__code')

            for project in projects:
                self.stdout.write(project["project__code"])
        else:
            for project in Project.objects.all():
                self.stdout.write(project.code)
