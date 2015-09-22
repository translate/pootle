#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

__all__ = ('ElasticSearchBackend',)

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ConnectionError
except:
    Elasticsearch = None

from ..base import SearchBackend


class ElasticSearchBackend(SearchBackend):
    def __init__(self, config_name):
        super(ElasticSearchBackend, self).__init__(config_name)
        self._es = self._get_es_server()
        self._create_index_if_missing()

    def _server_setup_and_alive(self):
        if self._es is None:
            return False
        try:
            return self._es.ping()
        except ConnectionError:
            return False

    def _get_es_server(self):
        if self._settings is None or Elasticsearch is None:
            return None
        return Elasticsearch([
            {'host': self._settings['HOST'],
             'port': self._settings['PORT']},
        ])

    def _create_index_if_missing(self):
        if self._server_setup_and_alive():
            if not self._es.indices.exists(self._settings['INDEX_NAME']):
                self._es.indices.create(self._settings['INDEX_NAME'])

    def _is_valuable_hit(self, unit, hit):
        return str(unit.id) != hit['_id']

    def search(self, unit):
        if not self._server_setup_and_alive():
            return []

        counter = {}
        res = []
        language = unit.store.translation_project.language.code
        es_res = self._es.search(
            index=self._settings['INDEX_NAME'],
            doc_type=language,
            body={
                "query": {
                    "match": {
                        "source": {
                            "query": unit.source,
                            "fuzziness": self._settings['MIN_SCORE'],
                        }
                    }
                }
            }
        )

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
        if self._server_setup_and_alive():
            self._es.index(
                index=self._settings['INDEX_NAME'],
                doc_type=language,
                body=obj,
                id=obj['id']
            )
