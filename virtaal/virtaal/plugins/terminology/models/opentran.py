#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import logging
import os
import re
from translate.search.match import terminologymatcher
from translate.storage.placeables.terminology import TerminologyPlaceable
from translate.storage.base import TranslationStore, TranslationUnit
from translate.lang import data

from virtaal.support import opentranclient

from basetermmodel import BaseTerminologyModel

MIN_TERM_LENGTH = 4

caps_re = re.compile('([a-z][A-Z])|([A-Z]{2,})')
def is_case_sensitive(text):
    """Tries to detect camel or other cases where casing might be significant."""
    return caps_re.search(text) is not None

class TerminologyModel(BaseTerminologyModel):
    """
    Terminology model that queries Open-tran.eu for terminology results.
    """

    __gtype_name__ = 'OpenTranTerminology'
    display_name = _('Open-Tran.eu')
    description = _('Terms from Open-Tran.eu')

    default_config = { "url" : "http://open-tran.eu/RPC2" }

    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        super(TerminologyModel, self).__init__(controller)

        self.internal_name = internal_name
        self.load_config()

        self.main_controller = controller.main_controller
        self.term_controller = controller
        self.matcher = None
        self._init_matcher()

        self.opentrantm = self._find_opentran_tm()
        if self.opentrantm is None:
            self._init_opentran_client()
        else:
            self.opentrantm.connect('match-found', self._on_match_found)
            self.__setup_opentrantm_lang_watchers()

    def _find_opentran_tm(self):
        """
        Try and find an existing OpenTranClient instance, used by the OpenTran
        TM model.
        """
        plugin_ctrl = self.main_controller.plugin_controller
        if 'tm' not in plugin_ctrl.plugins:
            return None

        tm_ctrl = plugin_ctrl.plugins['tm'].tmcontroller
        if 'opentran' not in tm_ctrl.plugin_controller.plugins:
            return None

        return tm_ctrl.plugin_controller.plugins['opentran']

    def _init_matcher(self):
        """
        Initialize the matcher to be used by the C{TerminologyPlaceable} parser.
        """
        if self.matcher in TerminologyPlaceable.matchers:
            TerminologyPlaceable.matchers.remove(self.matcher)

        self.store = TranslationStore()
        self.store.makeindex()
        self.matcher = terminologymatcher(self.store)
        TerminologyPlaceable.matchers.append(self.matcher)

    def _init_opentran_client(self):
        """
        Create and initialize a new Open-Tran client. This should only happen
        when the Open-Tran TM model plug-in is not loaded.
        """
        plugin_ctrlr = self.main_controller.plugin_controller
        lang_ctrlr = self.main_controller.lang_controller
        # The following two values were copied from plugins/tm/__init__.py
        max_candidates = 5
        min_similarity = 70

        # Try to get max_candidates and min_quality from the TM plug-in
        if 'tm' in plugin_ctrlr.plugins:
            max_candidates = plugin_ctrlr.plugins['tm'].config['max_matches']
            min_similarity = plugin_ctrlr.plugins['tm'].config['min_quality']

        self.opentranclient = opentranclient.OpenTranClient(
            self.config['url'],
            max_candidates=max_candidates,
            min_similarity=min_similarity
        )
        self.opentranclient.source_lang = lang_ctrlr.source_lang.code
        self.opentranclient.target_lang = lang_ctrlr.target_lang.code

        self.__setup_lang_watchers()
        self.__setup_cursor_watcher()

    def __setup_cursor_watcher(self):
        unitview = self.main_controller.unit_controller.view
        def cursor_changed(cursor):
            self.__start_query()

        store_ctrlr = self.main_controller.store_controller
        def store_loaded(store_ctrlr):
            if hasattr(self, '_cursor_connect_id'):
                self.cursor.disconnect(self._cursor_connect_id)
            self.cursor = store_ctrlr.cursor
            self._cursor_connect_id = self.cursor.connect('cursor-changed', cursor_changed)
            cursor_changed(self.cursor)

        store_ctrlr.connect('store-loaded', store_loaded)
        if store_ctrlr.store:
            store_loaded(store_ctrlr)

    def __setup_lang_watchers(self):
        def client_lang_changed(client, lang):
            self.cache = {}
            self._init_matcher()
            self.__start_query()

        self._connect_ids.append((
            self.opentranclient.connect('source-lang-changed', client_lang_changed),
            self.opentranclient
        ))
        self._connect_ids.append((
            self.opentranclient.connect('target-lang-changed', client_lang_changed),
            self.opentranclient
        ))

        lang_controller = self.main_controller.lang_controller
        self._connect_ids.append((
            lang_controller.connect(
                'source-lang-changed',
                lambda _c, lang: self.opentranclient.set_source_lang(lang)
            ),
            lang_controller
        ))
        self._connect_ids.append((
            lang_controller.connect(
                'target-lang-changed',
                lambda _c, lang: self.opentranclient.set_target_lang(lang)
            ),
            lang_controller
        ))

    def __setup_opentrantm_lang_watchers(self):
        def set_lang(ctrlr, lang):
            self.cache = {}
            self._init_matcher()

        self._connect_ids.append((
            self.opentrantm.tmclient.connect('source-lang-changed', set_lang),
            self.opentrantm.tmclient
        ))
        self._connect_ids.append((
            self.opentrantm.tmclient.connect('target-lang-changed', set_lang),
            self.opentrantm.tmclient
        ))

    def __start_query(self):
        unitview = self.main_controller.unit_controller.view
        query_str = unitview.sources[0].get_text()
        if not self.cache.has_key(query_str):
            self.cache[query_str] = None
            logging.debug('Query string: %s (target lang: %s)' % (query_str, self.opentranclient.target_lang))
            self.opentranclient.translate_unit(query_str, lambda *args: self.add_last_suggestions(self.opentranclient))


    # METHODS #
    def add_last_suggestions(self, opentranclient):
        """Grab the last suggestions from the TM client."""
        if opentranclient.last_suggestions is not None:
            added = False
            for sugg in opentranclient.last_suggestions:
                units = self.create_suggestions(sugg)
                if units:
                    for u in units:
                        self.store.addunit(u)
                        self.store.add_unit_to_index(u)
                    added = True
            if added:
                self.matcher.inittm(self.store)
        unitview = self.main_controller.unit_controller.view
        self.main_controller.placeables_controller.apply_parsers(
            elems=[src.elem for src in unitview.sources],
            parsers=[TerminologyPlaceable.parse]
        )
        for src in unitview.sources:
            src.refresh()

    def create_suggestions(self, suggestion):
        # Skip any suggestions where the suggested translation contains parenthesis
        if re.match(r'\(.*\)', suggestion['text']):
            return []

        units = []

        for proj in suggestion['projects']:
            # Skip fuzzy matches:
            if proj['flags'] != 0:
                continue

            source = proj['orig_phrase'].strip()
            # Skip strings that are too short
            if len(source) < MIN_TERM_LENGTH:
                continue
            # Skip any units containing parenthesis
            if re.match(r'\(.*\)', source):
                continue
            unit = TranslationUnit(source)

            target = suggestion['text'].strip()

            # Skip phrases already found:
            old_unit = self.store.findunit(proj['orig_phrase'])
            if old_unit and old_unit.target == target:
                continue
            # We mostly want to work with lowercase strings, but in German (and
            # some languages with a related writing style), this will probably
            # irritate more often than help, since nouns are always written to
            # start with capital letters.
            target_lang_code = self.main_controller.lang_controller.target_lang.code
            if not data.normalize_code(target_lang_code) in ('de', 'de-de', 'lb', 'als', 'ksh', 'stq', 'vmf'):
                # unless the string contains multiple consecutive uppercase
                # characters or using some type of camel case, we take it to
                # lower case
                if not is_case_sensitive(target):
                    target = target.lower()
            unit.target = target
            units.append(unit)
        return units

    def destroy(self):
        super(TerminologyModel, self).destroy()
        if self.matcher in TerminologyPlaceable.matchers:
            TerminologyPlaceable.matchers.remove(self.matcher)


    # EVENT HANDLERS #
    def _on_match_found(self, *args):
        self.add_last_suggestions(self.opentrantm.tmclient)
