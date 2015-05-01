#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

__all__ = ('ElasticSearchBackend',)

try:
    from elasticsearch import Elasticsearch
except:
    Elasticsearch = None

from ..base import SearchBackend


class ElasticSearchBackend(SearchBackend):
    def __init__(self, config_name):
        super(ElasticSearchBackend, self).__init__(config_name)
        self.es = None
        if self._settings is not None and Elasticsearch is not None:
            self.es = Elasticsearch([{'host': self._settings['HOST'], 'port': self._settings['PORT']}, ])
        if self.es.ping():
            if not self.es.indices.exists(self._settings['INDEX_NAME']):
                self.es.indices.create(self._settings['INDEX_NAME'])

    def _is_valuable_hit(self, unit, hit):
        if str(unit.id) == hit['_id']:
            return False

        return True

    def search(self, unit):
        if self.es is None or not self.es.ping():
            return []

        counter = {}
        res = []
        language = unit.store.translation_project.language.code
        es_res = self.es.search(index=self._settings['INDEX_NAME'],
                                doc_type=language,
                                body={
                                    "query": {
                                        "match": {
                                            'source': {
                                                'query': unit.source,
                                                'fuzziness': self._settings['MIN_SCORE'],
                                            }
                                        }
                                    }
                                })

        for hit in es_res['hits']['hits']:
            if self._is_valuable_hit(unit, hit):
                translation_pair = hit['_source']['source'] + hit['_source']['target']
                if translation_pair not in counter:
                    counter[translation_pair] = 1
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
                    counter[translation_pair] += 1

        for item in res:
            item['count'] = counter[item['source']+item['target']]

        return res

    def update(self, language, obj):
        if self.es is not None and self.es.ping():
            self.es.index(
                index=self._settings['INDEX_NAME'],
                doc_type=language,
                body=obj,
                id=obj['id']
            )
