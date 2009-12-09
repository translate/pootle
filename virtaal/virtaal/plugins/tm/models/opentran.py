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

from virtaal.support import opentranclient

from virtaal.common import pan_app

from basetmmodel import BaseTMModel


class TMModel(BaseTMModel):
    """This is the translation memory model."""

    __gtype_name__ = 'OpenTranTMModel'
    display_name = _('Open-Tran.eu')
    description = _('Previous translations for Free and Open Source Software')

    default_config = { "url" : "http://open-tran.eu/RPC2" }

    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        self.internal_name = internal_name
        self.load_config()

        self.tmclient = opentranclient.OpenTranClient(
            self.config["url"],
            max_candidates=controller.max_matches,
            min_similarity=controller.min_quality
        )

        super(TMModel, self).__init__(controller)


    # METHODS #
    def set_source_lang(self, language):
        self.tmclient.set_source_lang(language)

    def set_target_lang(self, language):
        self.tmclient.set_target_lang(language)

    def query(self, tmcontroller, query_str):
        if self.cache.has_key(query_str):
            self.emit('match-found', query_str, self.cache[query_str])
        else:
            self.tmclient.translate_unit(query_str, self._handle_matches)

    def _handle_matches(self, widget, query_str, matches):
        """Handle the matches when returned from self.tmclient."""
        for match in matches:
            if 'tmsource' in match:
                #l10n: Try to keep this as short as possible. Feel free to transliterate in CJK languages for vertical display optimization.
                match['tmsource'] = _('OpenTran') + '\n' + match['tmsource']
            else:
                match['tmsource'] = _('OpenTran')
        self.cache[query_str] = matches
        self.emit('match-found', query_str, matches)
