#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import NoArgsCommand
from pootle_project.models import Project
from pootle_translationproject.models import update_against_templates


class Command(NoArgsCommand):
    help = "Mass update against templates."

    def handle_noargs(self, **args):
        verbosity = int(args.get("verbosity", 1))
        debug_levels = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: logging.DEBUG
        }
        debug_level = debug_levels.get(verbosity, logging.DEBUG)
        logging.getLogger().setLevel(debug_level)
        project_query = Project.objects.all()
        for project in project_query.all():
            template_tp = project.get_template_translationproject()
            tp_query = project.translationproject_set.order_by("language__code")

            # update the template translation project first
            if template_tp:
                update_against_templates(project, [template_tp])

            update_against_templates(project, tp_query, verbose=True)
