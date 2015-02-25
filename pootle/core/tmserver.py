#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

try:
    from elasticsearch import Elasticsearch as ES
except:
    ES = None

from django.conf import settings


def get_params():
    params = getattr(settings, 'POOTLE_TM_SERVER', None)

    if params is not None:
        return params['default']

    return None


es_params = get_params()
# TODO support ENGINE param
# Elasticsearch is the only supported engine now
es = None
if es_params is not None and ES is not None:
    es = ES([{'host': es_params['HOST'], 'port': es_params['PORT']}, ])
    if not es.indices.exists(es_params['INDEX_NAME']):
        es.indices.create(es_params['INDEX_NAME'])


def update(language, obj):
    if es is not None:
        es.index(index=es_params['INDEX_NAME'],
                 doc_type=language,
                 body=obj,
                 id=obj['id'])


def is_valuable_hit(unit, hit):
    if str(unit.id) == hit['_id']:
        return False

    return True


def search(unit):
    if es is None:
        return None

    counter = {}
    res = []
    language = unit.store.translation_project.language.code
    es_res = es.search(index=es_params['INDEX_NAME'],
                       doc_type=language,
                       body={
                           "query": {
                               "match": {
                                   'source': {
                                       'query': unit.source,
                                       'fuzziness': es_params['MIN_SCORE'],
                                   }
                               }
                           }
                       })

    for hit in es_res['hits']['hits']:
        if is_valuable_hit(unit, hit):
            if hit['_source']['target'] not in counter:
                counter[hit['_source']['target']] = 1
                res.append({
                    'unit_id': hit['_id'],
                    'source': hit['_source']['source'],
                    'target': hit['_source']['target'],
                    'project': hit['_source']['project'],
                    'path': hit['_source']['path'],
                    'username': hit['_source']['username'],
                    'fullname': hit['_source']['fullname'],
                    'email_md5': hit['_source']['email_md5'],
                })
            else:
                counter[hit['_source']['target']] += 1

    for item in res:
        item['count'] = counter[item['target']]

    return res
