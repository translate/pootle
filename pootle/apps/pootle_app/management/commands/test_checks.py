#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
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

import logging
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from optparse import make_option

from translate.filters.checks import FilterFailure

from django.core.management.base import NoArgsCommand, CommandError

from pootle_misc.checks import ENChecker, get_qualitychecks
from pootle_store.models import Unit


class Command(NoArgsCommand):
    help = "Tests quality checks against string pairs."

    shared_option_list = (
        make_option('--check', action='append', dest='checks',
                    help='Check name to check for'),
        make_option('--source', dest='source', help='Source string'),
        make_option('--unit', dest='unit', help='Unit id'),
        make_option('--target', dest='target',
                    help='Translation string'),
        )
    option_list = NoArgsCommand.option_list + shared_option_list

    def handle_noargs(self, **options):
        # adjust debug level to the verbosity option
        verbosity = int(options.get('verbosity', 1))
        debug_levels = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG
        }
        debug_level = debug_levels.get(verbosity, logging.DEBUG)
        logging.getLogger().setLevel(debug_level)
        self.name = self.__class__.__module__.split('.')[-1]

        source = options.get('source', '')
        target = options.get('target', '')
        unit_id = options.get('unit', '')
        checks = options.get('checks', [])

        if (source and target) == bool(unit_id):
            raise CommandError("Either --unit or a pair of --source "
                               "and --target must be provided.")

        if unit_id:
            try:
                unit = Unit.objects.get(id=unit_id)
                source = unit.source
                target = unit.target
            except Unit.DoesNotExist, e:
                raise CommandError(e.message)

        checker = ENChecker()

        if not checks:
            checks = get_qualitychecks().keys()

        error_checks = []
        for check in checks:
            filtermessage = ''
            try:
                test = getattr(checker, check)
                filterresult = test(source, target)
            except FilterFailure, e:
                filterresult = False
                filtermessage = unicode(e)

            message = "%s - %s" % (filterresult, check)
            if filtermessage:
                message += ": %s" % filtermessage
            logging.info(message)

            if not filterresult:
                error_checks.append(check)

        if error_checks:
            self.stdout.write('Failing checks: %s' % ', '.join(error_checks))
        else:
            self.stdout.write('No errors found.')
