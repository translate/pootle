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

import os
from gobject import SIGNAL_RUN_FIRST
from translate.lang.identify import LanguageIdentifier

from virtaal.common import GObjectWrapper, pan_app
from virtaal.models import LanguageModel
from virtaal.views import LanguageView

from basecontroller import BaseController


class LanguageController(BaseController):
    """
    The logic behind language management in Virtaal.
    """

    __gtype_name__ = 'LanguageController'
    __gsignals__ = {
        'source-lang-changed': (SIGNAL_RUN_FIRST, None, (str,)),
        'target-lang-changed': (SIGNAL_RUN_FIRST, None, (str,)),
    }

    MODEL_DIR = LanguageIdentifier.MODEL_DIR
    CONF_FILE = LanguageIdentifier.CONF_FILE
    NUM_RECENT = 5
    """The number of recent language pairs to save/display."""

    # INITIALIZERS #
    def __init__(self, main_controller):
        GObjectWrapper.__init__(self)

        self.main_controller = main_controller
        self.main_controller.lang_controller = self
        self.lang_identifier = LanguageIdentifier(self.MODEL_DIR, self.CONF_FILE)
        self.new_langs = []
        self._init_langs()
        self.recent_pairs = self._load_recent()

        self.main_controller.store_controller.connect('store-loaded', self._on_store_loaded)
        self.main_controller.connect('quit', self._on_quit)
        self.connect('source-lang-changed', lambda *args: self.save_recent())
        self.connect('target-lang-changed', lambda *args: self.save_recent())

        self.view = LanguageView(self)
        self.view.show()

    def _init_langs(self):
        try:
            self._source_lang = LanguageModel(pan_app.settings.language['sourcelang'])
        except Exception:
            self._source_lang = None

        try:
            self._target_lang = LanguageModel(pan_app.settings.language['targetlang'])
        except Exception:
            self._target_lang = None

        # Load previously-saved (new) languages
        filename = os.path.join(pan_app.get_config_dir(), 'langs.ini')
        if os.path.isfile(filename):
            languages = pan_app.load_config(filename)
            for code in languages:
                languages[code] = (
                    languages[code]['name'],
                    int(languages[code]['nplurals']),
                    languages[code]['plural']
                )
            LanguageModel.languages.update(languages)


    # ACCESSORS #
    def _get_source_lang(self):
        return self._source_lang
    def _set_source_lang(self, lang):
        if isinstance(lang, basestring):
            lang = LanguageModel(lang)
        if not lang or lang == self._source_lang:
            return
        self._source_lang = lang
        self.emit('source-lang-changed', self._source_lang.code)
    source_lang = property(_get_source_lang, _set_source_lang)

    def _get_target_lang(self):
        return self._target_lang
    def _set_target_lang(self, lang):
        if isinstance(lang, basestring):
            lang = LanguageModel(lang)
        if not lang or lang == self._target_lang:
            return
        self._target_lang = lang
        self.emit('target-lang-changed', self._target_lang.code)
    target_lang = property(_get_target_lang, _set_target_lang)

    def set_language_pair(self, srclang, tgtlang):
        if isinstance(srclang, basestring):
            srclang = LanguageModel(srclang)
        if isinstance(tgtlang, basestring):
            tgtlang = LanguageModel(tgtlang)

        pair = (srclang, tgtlang)
        if pair in self.recent_pairs:
            self.recent_pairs.remove(pair)

        self.recent_pairs.insert(0, pair)
        self.recent_pairs = self.recent_pairs[:self.NUM_RECENT]

        self.source_lang = srclang
        self.target_lang = tgtlang
        self.view.update_recent_pairs()


    # METHODS #
    def get_detected_langs(self):
        store = self.main_controller.store_controller.store
        if not store:
            return None

        srccode = self.lang_identifier.identify_source_lang(store.get_units())
        tgtcode = self.lang_identifier.identify_target_lang(store.get_units())
        srclang = tgtlang = None
        if srccode:
            srclang = LanguageModel(srccode)
        if tgtcode:
            tgtlang = LanguageModel(tgtcode)

        return srclang, tgtlang

    def _load_recent(self):
        code_pairs = pan_app.settings.language['recentlangs'].split('|')
        codes = [pair.split(',') for pair in code_pairs]
        if codes == [['']]:
            return []

        recent_pairs = []
        for srccode, tgtcode in codes:
            srclang = LanguageModel(srccode)
            tgtlang = LanguageModel(tgtcode)
            recent_pairs.append((srclang, tgtlang))

        return recent_pairs

    def save_recent(self):
        pairs = [','.join([src.code, tgt.code]) for (src, tgt) in self.recent_pairs]
        recent = '|'.join(pairs)
        pan_app.settings.language['recentlangs'] = recent


    # EVENT HANDLERS #
    def _on_quit(self, main_controller):
        pan_app.settings.language['sourcelang'] = self.source_lang.code
        pan_app.settings.language['targetlang'] = self.target_lang.code

        if not self.new_langs:
            return

        langs = {}
        filename = os.path.join(pan_app.get_config_dir(), 'langs.ini')
        if os.path.isfile(filename):
            langs = pan_app.load_config(filename)

        newlangdict = {}
        for code in self.new_langs:
            newlangdict[code] = {}
            newlangdict[code]['name'] = LanguageModel.languages[code][0]
            newlangdict[code]['nplurals'] = LanguageModel.languages[code][1]
            newlangdict[code]['plural'] = LanguageModel.languages[code][2]
        langs.update(newlangdict)

        pan_app.save_config(filename, langs)

    def _on_store_loaded(self, store_controller):
        srclang = store_controller.store.get_source_language() or self.source_lang.code
        tgtlang = store_controller.store.get_target_language() or self.target_lang.code
        self.set_language_pair(srclang, tgtlang)
        self.target_lang.nplurals = self.target_lang.nplurals or store_controller.get_nplurals()

