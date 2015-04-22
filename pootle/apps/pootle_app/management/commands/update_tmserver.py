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
from django.db import connection


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

        last_indexed_revision = (-1, )

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
            last_indexed_revision = (result['facets']['stat1']['max'], )

        self.stdout.write("Last indexed revision = %s" % last_indexed_revision)

        sqlquery = """
        SELECT COUNT(*)
        FROM pootle_store_unit
        WHERE target_f IS NOT NULL AND target_f != ''
        AND revision > ?
        """

        cursor = connection.cursor()
        result = cursor.execute(sqlquery, last_indexed_revision)

        total = 0

        count = result.fetchone()
        if count:
            total = count[0]

        if total == 0:
            self.stdout.write("No translations to index")
            sys.exit()

        self.stdout.write("%s translations to index" % total)

        if options['dry_run']:
            sys.exit()

        sqlquery = """
        SELECT u.id, u.revision, u.source_f AS source, u.target_f AS target,
           pu.username, pu.full_name, pu.email,
           p.fullname AS project, s.pootle_path AS path,
           l.code AS language
        FROM pootle_store_unit u
        LEFT OUTER JOIN accounts_user pu ON u.submitted_by_id = pu.id
        JOIN pootle_store_store s on s.id = u.store_id
        JOIN pootle_app_translationproject tp on tp.id = s.translation_project_id
        JOIN pootle_app_language l on l.id = tp.language_id
        JOIN pootle_app_project p on p.id = tp.project_id
        WHERE u.target_f IS NOT NULL AND u.target_f != ''
        AND revision > ?
        """

        cursor = connection.cursor()
        translations = cursor.execute(sqlquery, last_indexed_revision)

        i = 0
        desc = cursor.description
        unit = translations.fetchone()
        while (unit is not None):
            i += 1

            unit = dict(zip([col[0] for col in desc], unit))
            fullname = unit['full_name'] or unit['username']
            email_md5 = None
            if unit['email']:
                email_md5 = md5(unit['email']).hexdigest()

            es.index(
                index=INDEX_NAME,
                doc_type=unit['language'],
                id=unit['id'],
                body={
                    'revision': int(unit['revision']),
                    'project': unit['project'],
                    'path': unit['path'],
                    'username': unit['username'],
                    'fullname': fullname,
                    'email_md5': email_md5,
                    'source': unit['source'],
                    'target': unit['target'],
                }
            )

            if (i % 1000 == 0) or (i == total):
                percent = "%.1f" % (i * 100.0 / total)
                self.stdout.write("%s (%s%%)" % (i, percent), ending='\r')
                self.stdout.flush()

            unit = translations.fetchone()

        self.stdout.write("")

        if i != total:
            self.stdout.write("Expected %d, loaded %d." % (total, i))
