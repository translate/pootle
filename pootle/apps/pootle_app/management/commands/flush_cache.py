#!/usr/bin/env python
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

from django.core.management.base import BaseCommand, CommandError

from django_redis import get_redis_connection

from pootle.core.models import Revision
from pootle_store.models import Unit


class Command(BaseCommand):
    help = """Flush cache."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--django-cache',
            action='store_true',
            dest='flush_django_cache',
            default=False,
            help='Flush Django default cache.',
        )
        parser.add_argument(
            '--rqdata',
            action='store_true',
            dest='flush_rqdata',
            default=False,
            help=("Flush revision counter and all RQ data (queues, pending or "
                  "failed jobs, refresh_stats optimisation data). "
                  "Revision counter is restores automatically. "),
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            dest='flush_stats',
            default=False,
            help='Flush stats cache data.',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='flush_all',
            default=False,
            help='Flush all caches data.',
        )

    def handle(self, **options):
        if (not options['flush_stats'] and not options['flush_rqdata'] and
            not options['flush_django_cache'] and not options['flush_all']):
            raise CommandError("No options were provided. Use one of "
                               "--django-cache, --rqdata, --stats or --all.")

        self.stdout.write('Flushing cache...')

        if options['flush_stats'] or options['flush_all']:
            # Delete all stats cache data.
            r_con = get_redis_connection('stats')
            r_con.flushdb()
            self.stdout.write('All stats data removed.')

        if options['flush_rqdata'] or options['flush_all']:
            # Flush all rq data, dirty counter and restore Pootle revision
            # value.
            r_con = get_redis_connection('redis')
            r_con.flushdb()
            self.stdout.write('RQ data removed.')
            Revision.set(Unit.max_revision())
            self.stdout.write('Max unit revision restored.')

        if options['flush_django_cache'] or options['flush_all']:
            r_con = get_redis_connection('default')
            r_con.flushdb()
            self.stdout.write('All default Django cache data removed.')
