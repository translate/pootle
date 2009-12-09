#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of Virtaal.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import gobject
import logging
import pycurl
import xmlrpclib

from translate.lang import data
from translate.search.lshtein import LevenshteinComparer

from virtaal.support.httpclient import HTTPClient, RESTRequest

class OpenTranClient(gobject.GObject, HTTPClient):
    """CRUD operations for TM units and stores"""

    __gtype_name__ = 'OpenTranClient'
    __gsignals__ = {
        'source-lang-changed': (gobject.SIGNAL_RUN_LAST, None, (str,)),
        'target-lang-changed': (gobject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, url, max_candidates=3, min_similarity=75, max_length=1000):
        gobject.GObject.__init__(self)
        HTTPClient.__init__(self)

        self.max_candidates = max_candidates
        self.min_similarity = min_similarity
        self.comparer = LevenshteinComparer(max_length)
        self.last_suggestions = None

        self.url = url

        self.source_lang = None
        self.target_lang = None
        #detect supported language


    def translate_unit(self, unit_source, callback=None):
        if self.source_lang is None or self.target_lang is None:
            return
        if isinstance(unit_source, unicode):
            unit_source = unit_source.encode("utf-8")

        request_body = xmlrpclib.dumps(
            (unit_source, self.source_lang, self.target_lang), "suggest2"
        )
        request = RESTRequest(
            self.url, unit_source, "POST", request_body
        )
        request.curl.setopt(pycurl.URL, self.url)
        self.add(request)
        def call_callback(widget, response):
            return callback(
                widget, widget.id, self.format_suggestions(widget.id, response)
            )

        if callback:
            request.connect("http-success", call_callback)

    def lang_negotiate(self, language, callback):
        #Open-Tran uses codes such as pt_br, and zh_cn
        opentran_lang = language.lower().replace('-', '_').replace('@', '_')
        request_body = xmlrpclib.dumps((opentran_lang,), "supported")
        request = RESTRequest(
            self.url, language, "POST", request_body)
        request.curl.setopt(pycurl.URL, self.url)
        self.add(request)
        request.connect("http-success", callback)

    def set_source_lang(self, language):
        self.source_lang = None
        self.lang_negotiate(language, self._handle_source_lang)

    def set_target_lang(self, language):
        self.target_lang = None
        self.lang_negotiate(language, self._handle_target_lang)

    def _handle_target_lang(self, request, response):
        language = request.id
        (result,), fish = xmlrpclib.loads(response)
        if result:
            self.target_lang = language
            #logging.debug("target language %s supported" % language)
            self.emit('target-lang-changed', self.target_lang)
        else:
            lang = data.simplercode(language)
            if lang:
                self.lang_negotiate(lang, self._handle_target_lang)
            else:
                # language not supported
                self.source_lang = None
                logging.debug("target language %s not supported" % language)

    def _handle_source_lang(self, request, response):
        language = request.id
        (result,), fish = xmlrpclib.loads(response)
        if result:
            self.source_lang = language
            #logging.debug("source language %s supported" % language)
            self.emit('source-lang-changed', self.source_lang)
        else:
            lang = data.simplercode(language)
            if lang:
                self.lang_negotiate(lang, self._handle_source_lang)
            else:
                self.source_lang = None
                logging.debug("source language %s not supported" % language)

    def format_suggestions(self, id, response):
        """clean up open tran suggestion and use the same format as tmserver"""
        (suggestions,), fish = xmlrpclib.loads(response)
        self.last_suggestions = suggestions
        results = []
        for suggestion in suggestions:
            result = {}
            result['target'] = suggestion['text']
            if isinstance(result['target'], unicode):
                result['target'] = result['target'].encode("utf-8")
            result['tmsource'] = suggestion['projects'][0]['name']
            result['source'] = suggestion['projects'][0]['orig_phrase']
            #check for fuzzyness at the 'flag' member:
            for project in suggestion['projects']:
                if project['flags'] == 0:
                    break
            else:
                continue
            if isinstance(result['source'], unicode):
                result['source'] = result['source'].encode("utf-8")
            #open-tran often gives too many results with many which can't really be
            #considered to be suitable for translation memory
            result['quality'] = self.comparer.similarity(id, result['source'], self.min_similarity)
            if result['quality'] >= self.min_similarity:
                results.append(result)
        results.sort(key=lambda match: match['quality'], reverse=True)
        results = results[:self.max_candidates]
        return results
