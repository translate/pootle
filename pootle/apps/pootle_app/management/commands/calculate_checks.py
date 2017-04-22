# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle.core.signals import update_checks
from pootle_translationproject.models import TranslationProject

from . import PootleCommand


class Command(PootleCommand):
    help = "Allow checks to be recalculated manually."
    process_disabled_projects = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--check',
            action='append',
            dest='check_names',
            default=None,
            help='Check to recalculate',
        )

    def update_checks(self, check_names, translation_project=None):
        update_checks.send(
            TranslationProject,
            check_names=check_names,
            instance=translation_project,
            clear_unknown=True,
            update_data_after=True)

    def handle_all_stores(self, translation_project, **options):
        self.stdout.write(u"Running %s for %s" %
                          (self.name, translation_project))
        self.update_checks(options["check_names"], translation_project)

    def handle_all(self, **options):
        if not self.projects and not self.languages:
            self.stdout.write(u"Running %s (noargs)" % self.name)
            self.update_checks(options["check_names"])
        else:
            super(Command, self).handle_all(**options)
