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

from elasticsearch import Elasticsearch

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

    def handle(self, *args, **options):
        if not getattr(settings, 'POOTLE_TM_SERVER', False):
            raise CommandError("POOTLE_TM_SERVER is missing from your settings.")

        INDEX_NAME = settings.POOTLE_TM_SERVER['default']['INDEX_NAME']
        es = Elasticsearch([{
            'host': settings.POOTLE_TM_SERVER['default']['HOST'],
            'port': settings.POOTLE_TM_SERVER['default']['PORT']
        },
        ])

        last_indexed_revision = -1

        if options['rebuild'] and not options['dry_run']:
            if es.indices.exists(INDEX_NAME):
                es.indices.delete(index=INDEX_NAME)

        if (not options['rebuild'] and
            not options['overwrite'] and
            es.indices.exists(INDEX_NAME)):
            result = es.search(
                index=INDEX_NAME,
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
            last_indexed_revision = result['facets']['stat1']['max']

        self.stdout.write("Last indexed revision = %s" % last_indexed_revision)


        units_qs = Unit.objects.exclude(target_f__isnull=True) \
                               .exclude(target_f__exact='') \
                               .filter(revision__gt=last_indexed_revision)

        total = units_qs.count()

        if total == 0:
            self.stdout.write("No translations to index")
            sys.exit()

        self.stdout.write("%s translations to index" % total)

        if options['dry_run']:
            sys.exit()

        for i, unit in enumerate(units_qs.iterator(), start=1):
            email_md5 = None
            username = None
            fullname = None
            submitter = unit.submitted_by

            if submitter:
                username = submitter.username
                fullname = submitter.full_name or username

                if submitter.email:
                    email_md5 = md5(submitter.email).hexdigest()

            es.index(
                index=INDEX_NAME,
                doc_type=unit.store.translation_project.language.code,
                id=unit.id,
                body={
                    'revision': int(unit.revision),
                    'project': unit.store.translation_project.project.fullname,
                    'path': unit.store.pootle_path,
                    'username': username,
                    'fullname': fullname,
                    'email_md5': email_md5,
                    'source': unit.source_f,
                    'target': unit.target_f,
                }
            )

            if (i % 1000 == 0) or (i == total):
                percent = "%.1f" % (i * 100.0 / total)
                self.stdout.write("%s (%s%%)" % (i, percent), ending='\r')
                self.stdout.flush()

        self.stdout.write("")

        if i != total:
            self.stdout.write("Expected %d, loaded %d." % (total, i))
