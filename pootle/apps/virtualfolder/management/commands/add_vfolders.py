# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from pootle.core.url_helpers import split_pootle_path
from pootle_language.models import Language
from pootle_project.models import Project
from virtualfolder.models import VirtualFolder


class Command(BaseCommand):
    help = "Add virtual folders from file."

    def add_arguments(self, parser):
        parser.add_argument(
            "vfolder",
            nargs=1,
            help="JSON vfolder configuration file",
        )

    def parse_vfolder_rules(self, location, old_rules):
        """Extract languages, projects and new rules from location and rules."""
        languages = set()
        projects = set()
        new_rules = set()

        full_rules = [location + old_rule.strip() for old_rule in old_rules]

        for full_rule in full_rules:
            lang_code, proj_code, dir_path, fname = split_pootle_path(full_rule)
            if fname:
                new_rules.add(dir_path + fname)
            else:
                new_rules.add(dir_path + "*")
            languages.add(lang_code)
            projects.add(proj_code)

        if "{LANG}" in languages:
            languages = set()

        if "{PROJ}" in projects:
            projects = set()

        new_rules = ",".join(new_rules)

        return languages, projects, new_rules

    def handle(self, **options):
        """Add virtual folders from file."""

        try:
            with open(options['vfolder'][0], "r") as inputfile:
                vfolders = json.load(inputfile)
        except IOError as e:
            raise CommandError(e)
        except ValueError as e:
            raise CommandError("Please check if the JSON file is malformed. "
                               "Original error:\n%s" % e)

        for vfolder_item in vfolders:
            try:
                temp = ','.join(vfolder_item['filters']['files'])
                if not temp:
                    raise ValueError
            except (KeyError, ValueError):
                raise CommandError("Virtual folder '%s' has no filtering "
                                   "rules." % vfolder_item['name'])

        self.stdout.write("Importing virtual folders...")

        added_count = 0
        updated_count = 0
        errored_count = 0

        for vfolder_item in vfolders:
            vfolder_item['name'] = vfolder_item['name'].strip().lower()

            # Put all the files for each virtual folder as a list and save it
            # as its filter rules.
            languages, projects, new_rules = self.parse_vfolder_rules(
                vfolder_item['location'].strip(),
                vfolder_item['filters']['files']
            )

            vfolder_item['filter_rules'] = new_rules

            if 'filters' in vfolder_item:
                del vfolder_item['filters']

            # Now create or update the virtual folder.
            try:
                # Retrieve the virtual folder if it exists.
                vfolder = VirtualFolder.objects.get(name=vfolder_item['name'])
            except VirtualFolder.DoesNotExist:
                # If the virtual folder doesn't exist yet then create it.
                try:
                    self.stdout.write(u'Adding new virtual folder %s...' %
                                      vfolder_item['name'])
                    vfolder_item['all_projects'] = not projects
                    vfolder_item['all_languages'] = not languages
                    vfolder = VirtualFolder(**vfolder_item)
                    vfolder.save()
                except ValidationError as e:
                    errored_count += 1
                    self.stdout.write('FAILED')
                    self.stderr.write(e)
                else:
                    if projects:
                        vfolder.projects.add(
                            *Project.objects.filter(code__in=projects)
                        )
                    if languages:
                        vfolder.languages.add(
                            *Language.objects.filter(code__in=languages)
                        )
                    self.stdout.write('DONE')
                    added_count += 1
            else:
                # Update the already existing virtual folder.
                changed = False

                if not projects:
                    vfolder.all_projects = True
                    changed = True
                    logging.debug("'All projects' for virtual folder '%s' "
                                  "will be changed.", vfolder.name)

                if not languages:
                    vfolder.all_languages = True
                    changed = True
                    logging.debug("'All languages' for virtual folder '%s' "
                                  "will be changed.", vfolder.name)

                if projects:
                    vfolder.projects.set(
                        *Project.objects.filter(code__in=projects)
                    )
                if languages:
                    vfolder.languages.set(
                        *Language.objects.filter(code__in=languages)
                    )

                if vfolder.filter_rules != vfolder_item['filter_rules']:
                    vfolder.filter_rules = vfolder_item['filter_rules']
                    changed = True
                    logging.debug("Filter rules for virtual folder '%s' will "
                                  "be changed.", vfolder.name)

                if ('priority' in vfolder_item and
                    vfolder.priority != vfolder_item['priority']):

                    vfolder.priority = vfolder_item['priority']
                    changed = True
                    logging.debug("Priority for virtual folder '%s' will be "
                                  "changed to %f.", vfolder.name,
                                  vfolder.priority)

                if ('is_public' in vfolder_item and
                    vfolder.is_public != vfolder_item['is_public']):

                    vfolder.is_public = vfolder_item['is_public']
                    changed = True
                    logging.debug("is_public status for virtual folder "
                                  "'%s' will be changed.", vfolder.name)

                if ('description' in vfolder_item and
                    vfolder.description.raw != vfolder_item['description']):

                    vfolder.description = vfolder_item['description']
                    changed = True
                    logging.debug("Description for virtual folder '%s' will "
                                  "be changed.", vfolder.name)

                if changed:
                    try:
                        self.stdout.write(u'Updating virtual folder %s...' %
                                          vfolder_item['name'])
                        vfolder.save()
                    except ValidationError as e:
                        errored_count += 1
                        self.stdout.write('FAILED')
                        self.stderr.write(e)
                    else:
                        self.stdout.write('DONE')
                        updated_count += 1

        self.stdout.write("\nErrored: %d\nAdded: %d\n"
                          "Updated: %d\nUnchanged: %d" %
                          (errored_count, added_count, updated_count,
                           len(vfolders) - errored_count - added_count -
                           updated_count))
