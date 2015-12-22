#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle.core.checks.checker import QualityCheckUpdater

from . import PootleCommand


class Command(PootleCommand):
    help = "Allow checks to be recalculated manually."

    shared_option_list = (
        make_option(
            '--check',
            action='append',
            dest='check_names',
            default=None,
            help='Check to recalculate'
        ),
    )
    option_list = PootleCommand.option_list + shared_option_list
    process_disabled_projects = True

    def handle_all_stores(self, translation_project, **options):
        logging.info(
            u"Running %s for %s",
            self.name, translation_project)
        QualityCheckUpdater(
            options['check_names'],
            translation_project).update()

    def handle_all(self, **options):
        if not self.projects and not self.languages:
            logging.info(u"Running %s (noargs)", self.name)
            QualityCheckUpdater(options['check_names']).update()
        else:
            super(Command, self).handle_all(**options)
