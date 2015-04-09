#!/usr/bin/env python

from __future__ import print_function

from django.db import connection
from elasticsearch import Elasticsearch
import sys
from hashlib import md5

# Hardcoded see config INDEX_NAME
INDEX_NAME = 'translations'
BULK_CHUNK_SIZE = 5000

opt_help = False
overwrite = False
rebuild = True
dry_run = False


es = Elasticsearch()

last_indexed_revision = (-1, )

if (rebuild and not dry_run):
    es.indices.delete(index=INDEX_NAME)

if (not rebuild and not overwrite):
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

print("Last indexed revision = %s" % last_indexed_revision)

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

if not total:
    print("No translations to index")
    sys.exit()
else:
    print("%s translations to index" % total)

if dry_run:
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
unit = translations.fetchone()
while (unit is not None):
    i+=1

    unit.keys()
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

    if ((i % 1000 == 0) or (i == total)):
        percent = "%.1f" % (i / total * 100)
        print("%s (%s%%)" % (i, percent), end="")

    unit = translations.fetchone()

print()

if (i != total):
    print("Oops.  Stopped at i = %s" % i)
