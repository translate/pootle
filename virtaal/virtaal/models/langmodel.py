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

from translate.lang.data import languages as toolkit_langs, tr_lang
from translate.lang import data

from virtaal.common import pan_app

from basemodel import BaseModel


class LanguageModel(BaseModel):
    """
    A simple container for language information for use by the C{LanguageController}
    and C{LanguageView}.
    """

    __gtype_name__ = 'LanguageModel'

    languages = {}

    # INITIALIZERS #
    def __init__(self, langcode='und', more_langs={}):
        """Constructor.
            Looks up the language information based on the given language code
            (C{langcode})."""
        super(LanguageModel, self).__init__()
        self.gettext_lang = tr_lang()
        if not self.languages:
            self.languages.update(toolkit_langs)
        self.languages.update(more_langs)
        self.load(langcode)


    # SPECIAL METHODS #
    def __eq__(self, otherlang):
        """Check that the C{code}, C{nplurals} and C{plural} attributes are the
            same. The C{name} attribute may differ, seeing as it is localised.

            @type  otherlang: LanguageModel
            @param otherlang: The language to compare the current instance to."""
        return  isinstance(otherlang, LanguageModel) and \
                self.code     == otherlang.code and \
                self.nplurals == otherlang.nplurals and \
                self.plural   == otherlang.plural


    # METHODS #
    def load(self, langcode):
        #FIXME: what if we get language code with different capitalization?
        if langcode not in self.languages:
            try:
                langcode = self._match_normalized_langcode(langcode)
            except ValueError:
                langcode = data.simplify_to_common(langcode, self.languages)
                if langcode not in self.languages:
                    try:
                        langcode = self._match_normalized_langcode(langcode)
                    except ValueError:
                        logging.info("unkown language %s" % langcode)
                        self.name = langcode
                        self.code = langcode
                        self.nplurals = 0
                        self.plural = ""
                        return

        self.name = self.gettext_lang(self.languages[langcode][0])
        self.code = langcode
        self.nplurals = self.languages[langcode][1]
        self.plural = self.languages[langcode][2]

    def _match_normalized_langcode(self, langcode):
        languages_keys = self.languages.keys()
        normalized_keys = [data.normalize_code(lang) for lang in languages_keys]
        i =  normalized_keys.index(data.normalize_code(langcode))
        return languages_keys[i]

