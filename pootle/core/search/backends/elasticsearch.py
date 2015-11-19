#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

import logging


__all__ = ('ElasticSearchBackend',)

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ElasticsearchException
except:
    Elasticsearch = None

from ..base import SearchBackend


logger = logging.getLogger(__name__)


class ElasticSearchBackend(SearchBackend):
    def __init__(self, config_name):
        super(ElasticSearchBackend, self).__init__(config_name)
        self._es = self._get_es_server()
        self._create_index_if_missing()
        self.weight = min(max(self._settings.get('WEIGHT', self.weight),
                              0.0), 1.0)

    def _get_es_server(self):
        return Elasticsearch([
            {'host': self._settings['HOST'],
             'port': self._settings['PORT']},
        ])

    def _create_index_if_missing(self):
        try:
            if not self._es.indices.exists(self._settings['INDEX_NAME']):
                self._es.indices.create(self._settings['INDEX_NAME'])
        except ElasticsearchException as e:
            self._log_error(e)

    def _is_valuable_hit(self, unit, hit):
        return str(unit.id) != hit['_id']

    def _es_call(self, cmd, *args, **kwargs):
        try:
            return getattr(self._es, cmd)(*args, **kwargs)
        except ElasticsearchException as e:
            self._log_error(e)
            return None

    def _log_error(self, e):
        logger.error("Elasticsearch error for server(%s:%s): %s"
                     % (self._settings.get("HOST"),
                        self._settings.get("PORT"),
                        e))

    def search(self, unit):
        counter = {}
        res = []
        language = unit.store.translation_project.language.code
        es_res = self._es_call(
            "search",
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

        if es_res is None:
            # ElasticsearchException - eg ConnectionError.
            return []
        elif es_res == "":
            # There seems to be an issue with urllib where an empty string is
            # returned
            logger.error("Elasticsearch search (%s:%s) returned an empty string: %s"
                         % (self._settings["HOST"],
                            self._settings["PORT"],
                            unit))
            return []

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
                        'iso_submitted_on': hit['_source'].get('iso_submitted_on', None),
                        'display_submitted_on': hit['_source'].get('display_submitted_on',
                                                                None),
                        'score': hit['_score'] * self.weight,
                    })
                else:
                    counter[translation_pair] += 1

        for item in res:
            item['count'] = counter[item['source']+item['target']]

        return res

    def update(self, language, obj):
        self._es_call(
            "index",
            index=self._settings['INDEX_NAME'],
            doc_type=language,
            body=obj,
            id=obj['id']
        )
