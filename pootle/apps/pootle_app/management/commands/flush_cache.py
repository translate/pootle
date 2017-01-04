# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import sys

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand, CommandError

from django_redis import get_redis_connection

from pootle.core.models import Revision
from pootle.core.utils.redis_rq import rq_workers_are_running
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
                  "failed jobs). Revision counter is restores automatically."),
        )
        parser.add_argument(
            '--lru',
            action='store_true',
            dest='flush_lru',
            default=False,
            help="Flush lru cache.",
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='flush_all',
            default=False,
            help='Flush all caches data.',
        )

    def handle(self, **options):
        if (not options['flush_rqdata'] and
            not options['flush_lru'] and
            not options['flush_django_cache'] and
            not options['flush_all']):
            raise CommandError("No options were provided. Use one of "
                               "--django-cache, --rqdata, --lru "
                               "or --all.")

        if options['flush_rqdata'] or options['flush_all']:
            if rq_workers_are_running():
                self.stdout.write("Nothing has been flushed. "
                                  "Stop RQ workers before running this "
                                  "command with --rqdata or --all option.")
                sys.exit()

        self.stdout.write('Flushing cache...')
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

        if options['flush_lru'] or options['flush_all']:
            r_con = get_redis_connection('lru')
            r_con.flushdb()
            self.stdout.write('All lru cache data removed.')
