#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

import logging
import os
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from pootle_project.models import Project
from pootle_store.models import Store
from pootle_tagging.models import Goal, slugify_tag_name


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--project', dest='project_name',
                        help='Project to add project goals to'),
            make_option('-f', '--filename', dest='goals_file', metavar='FILE',
                        help='File with filenames and applied goals'),
    )
    help = "Add project goals from file to a project."

    def handle(self, *args, **options):
        """Add project goals from file to the given project."""
        project_name = options.get('project_name', None)
        goals_filename = options.get('goals_file', None)

        if project_name is None:
            raise CommandError("A project must be provided.")
        elif goals_filename is None:
            raise CommandError("A filename must be provided.")
        elif not os.path.isfile(goals_filename):
            raise CommandError("Filename '%s' doesn't point to an existing "
                               "file." % goals_filename)

        try:
            project = Project.objects.get(code=project_name)
        except Project.DoesNotExist:
            raise CommandError("Project '%s' does not exist." %
                               project_name)

        template_tp = project.get_template_translationproject()

        if not template_tp:
            raise CommandError("Project '%s' doesn't have a template "
                               "translation project." % project_name)

        try:
            inputfile = open(goals_filename, "r")
            inputlines = inputfile.readlines()
            inputfile.close()
        except IOError as e:
            raise CommandError("Some error occurred while handling the file: "
                               "%s" % e.strerror)

        line_number = 0
        goals_dict = {}
        template_language = template_tp.language.code

        for line in inputlines:
            line_number += 1
            line.strip()

            try:
                goal_name, filename = line.split("\t")
            except ValueError:
                raise CommandError("Wrong syntax at line %d." % line_number)

            # Polish the goal name and filename before working with them.
            filename = filename.strip().lstrip("./")
            filename = "/".join([project_name, template_language, filename])
            goal_name = goal_name.lower()

            if not goal_name.startswith("goal:"):
                goal_name = "goal:" + goal_name

            try:
                goals_dict[goal_name].append(filename)
            except KeyError:
                goals_dict[goal_name] = [filename]

        logging.info("\nParsed %d lines from '%s'\n", line_number,
                     goals_filename)

        # First check if any of the goals already exists and it is not a
        # project goal, in order to abort before creating or adding any of the
        # goals to the files.
        for goal_name in goals_dict.keys():
            try:
                goal = Goal.objects.get(name=goal_name)

                if not goal.project_goal:
                    raise CommandError("The goal '%s' already exists but it "
                                       "isn't a project goal." % goal)
            except Goal.DoesNotExist:
                pass

        # Criteria to get all the items in a random goal that correspond to
        # stores in the 'templates' translation project.
        #
        # It is used several lines below, but here is possible to calculate it
        # just once.
        stores_criteria = {
            'content_type': ContentType.objects.get_for_model(Store),
            'object_id__in': template_tp.stores.values_list('pk', flat=True),
        }

        applied_goals = set()

        # Now apply the goal to each of the stores.
        for goal_name in goals_dict.keys():
            try:
                # Retrieve the goal if it already exists.
                goal = Goal.objects.get(name=goal_name)

                # Unapply the goal from all the stores in the 'templates'
                # translation project to which the goal is currently applied.
                goal.items_with_goal.filter(**stores_criteria).delete()
            except Goal.DoesNotExist:
                # If the goal doesn't exist yet then create it.
                criteria = {
                    'name': goal_name,
                    # Note: for some unknown reason it is necessary to provide
                    # the slug instead of letting the model create it.
                    'slug': slugify_tag_name(goal_name),
                    'project_goal': True,
                }

                try:
                    # Get the goal priority from the end of the goal name.
                    criteria['priority'] = int(goal_name[-1])
                except ValueError:
                    pass

                goal = Goal(**criteria)
                goal.save()

            for filename in goals_dict[goal_name]:
                try:
                    store = template_tp.stores.get(file=filename)
                    store.goals.add(goal)
                    applied_goals.add(goal_name)
                    logging.info("Goal '%s' applied to '%s'.", goal_name,
                                 filename)
                except ObjectDoesNotExist:
                    logging.warning("File '%s' is not on the template "
                                    "language. Skipping it.\n", filename)

        logging.info("\nSucessfully added %d project goals to project '%s'.",
                     len(applied_goals), project_name)
