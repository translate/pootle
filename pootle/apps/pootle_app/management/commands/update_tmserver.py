#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5
from optparse import make_option
import os
import sys

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from elasticsearch import helpers, Elasticsearch

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from pootle_store.models import Unit


BULK_CHUNK_SIZE = 5000


class Command(BaseCommand):
    help = "Load Local Translation Memory"
    option_list = BaseCommand.option_list + (
        make_option('--overwrite',
                    action="store_true",
                    dest='overwrite',
                    default=False,
                    help='Process all items, not just the new ones (useful to '
                         'overwrite properties while keeping the index in a '
                         'working condition)'),
        make_option('--rebuild',
                    action="store_true",
                    dest='rebuild',
                    default=False,
                    help='Drop the entire index on start and update '
                         'everything from scratch'),
        make_option('--dry-run',
                    action="store_true",
                    dest='dry_run',
                    default=False,
                    help='Report only the number of translations to index '
                         'and quit'),
    )

    def _parse_translations(self, **options):

        units_qs = Unit.simple_objects \
            .exclude(target_f__isnull=True) \
            .exclude(target_f__exact='') \
            .filter(revision__gt=self.last_indexed_revision) \
            .select_related(
                'submitted_by',
                'store',
                'store__translation_project__project',
                'store__translation_project__language'
            ).values(
                'id',
                'revision',
                'source_f',
                'target_f',
                'submitted_by__username',
                'submitted_by__full_name',
                'submitted_by__email',
                'store__translation_project__project__fullname',
                'store__pootle_path',
                'store__translation_project__language__code'
            ).order_by()

        total = units_qs.count()

        if total == 0:
            self.stdout.write("No translations to index")
            sys.exit()

        self.stdout.write("%s translations to index" % total)

        if options['dry_run']:
            sys.exit()

        self.stdout.write("")

        for i, unit in enumerate(units_qs.iterator(), start=1):
            fullname = (unit['submitted_by__full_name'] or
                        unit['submitted_by__username'])
            project = unit['store__translation_project__project__fullname']

            email_md5 = None
            if unit['submitted_by__email']:
                email_md5 = md5(unit['submitted_by__email']).hexdigest()

            if (i % 1000 == 0) or (i == total):
                percent = "%.1f" % (i * 100.0 / total)
                self.stdout.write("%s (%s%%)" % (i, percent), ending='\r')
                self.stdout.flush()

            yield {
                "_index": self.INDEX_NAME,
                "_type": unit['store__translation_project__language__code'],
                "_id": unit['id'],
                'revision': int(unit['revision']),
                'project': project,
                'path': unit['store__pootle_path'],
                'username': unit['submitted_by__username'],
                'fullname': fullname,
                'email_md5': email_md5,
                'source': unit['source_f'],
                'target': unit['target_f'],
            }

        if i != total:
            self.stdout.write("Expected %d, loaded %d." % (total, i))


    def handle(self, *args, **options):
        if not getattr(settings, 'POOTLE_TM_SERVER', False):
            raise CommandError("POOTLE_TM_SERVER is missing from your settings.")

        self.INDEX_NAME = settings.POOTLE_TM_SERVER['default']['INDEX_NAME']
        es = Elasticsearch([{
                'host': settings.POOTLE_TM_SERVER['default']['HOST'],
                'port': settings.POOTLE_TM_SERVER['default']['PORT']
            }],
            retry_on_timeout=True
        )

        self.last_indexed_revision = -1

        if options['rebuild'] and not options['dry_run']:
            if es.indices.exists(self.INDEX_NAME):
                es.indices.delete(index=self.INDEX_NAME)

        if (not options['rebuild'] and
            not options['overwrite'] and
            es.indices.exists(self.INDEX_NAME)):
            result = es.search(
                index=self.INDEX_NAME,
                body={
                    'query': {
                        'match_all': {}
                    },
                    'facets': {
                        'stat1': {
                            'statistical': {
                                'field': 'revision'
                            }
                        }
                    }
                }
            )
            self.last_indexed_revision = result['facets']['stat1']['max']

        self.stdout.write("Last indexed revision = %s" % self.last_indexed_revision)

        success, _ = helpers.bulk(es, self._parse_translations(**options))
