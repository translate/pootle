# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from translate.filters.checks import FilterFailure, projectcheckers

from django.core.management.base import CommandError, BaseCommand

from pootle_checks.utils import get_qualitychecks
from pootle_store.models import Unit


class Command(BaseCommand):
    help = "Tests quality checks against string pairs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='append',
            dest='checks',
            help='Check name to check for',
        )
        parser.add_argument(
            '--source',
            dest='source',
            help='Source string',
        )
        parser.add_argument(
            '--unit',
            dest='unit',
            help='Unit id',
        )
        parser.add_argument(
            '--target',
            dest='target',
            help='Translation string',
        )

    def handle(self, **options):
        # adjust debug level to the verbosity option
        debug_levels = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG
        }
        debug_level = debug_levels.get(options['verbosity'], logging.DEBUG)
        logging.getLogger().setLevel(debug_level)
        self.name = self.__class__.__module__.split('.')[-1]

        if ((options['unit'] is not None
             and (options['source'] or options['target']))
            or (options['unit'] is None
                and not options['source']
                and not options['target'])):
            raise CommandError("Either --unit or a pair of --source "
                               "and --target must be provided.")
        if bool(options['source']) != bool(options['target']):
            raise CommandError("Use a pair of --source and --target.")

        checks = options.get('checks', [])

        if options['unit'] is not None:
            try:
                unit = Unit.objects.get(id=options['unit'])
                source = unit.source
                target = unit.target
            except Unit.DoesNotExist as e:
                raise CommandError(e)
        else:
            source = options['source'].decode('utf-8')
            target = options['target'].decode('utf-8')

        checkers = [checker() for checker in projectcheckers.values()]

        if not checks:
            checks = get_qualitychecks().keys()

        error_checks = []
        for checker in checkers:
            for check in checks:
                filtermessage = ''
                filterresult = True
                if check in error_checks:
                    continue
                try:
                    if hasattr(checker, check):
                        test = getattr(checker, check)
                        try:
                            filterresult = test(source, target)
                        except AttributeError:
                            continue
                except FilterFailure as e:
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
