#!/usr/bin/env python
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

from virtualfolder.models import VirtualFolder


class Command(BaseCommand):
    help = "Add virtual folders from file."

    def add_arguments(self, parser):
        parser.add_argument(
            "vfolder",
            nargs=1,
            help="JSON vfolder configuration file",
        )

    def handle(self, **options):
        """Add virtual folders from file."""

        try:
            inputfile = open(options['vfolder'], "r")
            vfolders = json.load(inputfile)
            inputfile.close()
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
            vfolder_item['name'] = vfolder_item['name'].lower()

            # Put all the files for each virtual folder as a list and save it
            # as its filter rules.
            vfolder_item['filter_rules'] = ','.join(
                vfolder_item['filters']['files'])

            if 'filters' in vfolder_item:
                del vfolder_item['filters']

            # Now create or update the virtual folder.
            try:
                # Retrieve the virtual folder if it exists.
                vfolder = VirtualFolder.objects.get(
                    name=vfolder_item['name'],
                    location=vfolder_item['location'],
                )
            except VirtualFolder.DoesNotExist:
                # If the virtual folder doesn't exist yet then create it.
                try:
                    self.stdout.write(u'Adding new virtual folder %s...' %
                                      vfolder_item['name'])
                    vfolder = VirtualFolder(**vfolder_item)
                    vfolder.save()
                except ValidationError as e:
                    errored_count += 1
                    self.stdout.write('FAILED')
                    self.stderr.write(e)
                else:
                    self.stdout.write('DONE')
                    added_count += 1
            else:
                # Update the already existing virtual folder.
                changed = False

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
