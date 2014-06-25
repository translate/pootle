#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

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


def update(language, obj):
    if es is not None:
        es.index(index=es_params['INDEX_NAME'],
                 doc_type=language,
                 body=obj,
                 id=obj['id'])

def search(language, source):
    if es is not None:
        res = []
        es_res = es.search(index=es_params['INDEX_NAME'],
                        doc_type=language,
                        body={"query": {"match": {'source': source}}})

        max_score = es_res['hits']['max_score']
        for hit in es_res['hits']['hits']:
            res.append({
                'unit_id': ['_id'],
                'quality': 100 * hit['_score'] / max_score,
                'source': hit['_source']['source'],
                'target': hit['_source']['target'],
                'project': hit['_source']['project'],
                'path': hit['_source']['path'],
                'username': hit['_source']['username'],
                'fullname': hit['_source']['fullname'],
                'email_md5': hit['_source']['email_md5'],
            })

        return res

    return None