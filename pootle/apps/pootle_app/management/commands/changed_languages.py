# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand
from django.db.models import Max

from pootle.core.models import Revision
from pootle_store.models import Store, Unit


class Command(BaseCommand):
    help = "List languages that were changed since last synchronization"

    def add_arguments(self, parser):
        parser.add_argument(
            '--after-revision',
            action='store',
            dest='after_revision',
            type=int,
            help='Show languages changed after any arbitrary revision',
        )

    def handle(self, **options):
        last_known_revision = Revision.get()

        if options['after_revision'] is not None:
            after_revision = int(options['after_revision'])
        else:
            after_revision = Store.objects.all().aggregate(
                Max('last_sync_revision'))['last_sync_revision__max'] or -1

        self.stderr.write(
            'Will show languages changed between revisions %s (exclusive) '
            'and %s (inclusive)' %
            (after_revision, last_known_revision)
        )

        # if the requested revision is the same or is greater than the last
        # known one, return nothing
        if after_revision >= last_known_revision:
            self.stderr.write('(no known changes)')
            return

        q = Unit.objects.filter(
            revision__gt=after_revision
        ).values(
            'store__translation_project__language__code',
        ).order_by(
            'store__translation_project__language__code',
        ).distinct()

        languages = q.values_list('store__translation_project__language__code',
                                  flat=True)

        # list languages separated by comma for easy parsing
        self.stdout.write(','.join(languages))
