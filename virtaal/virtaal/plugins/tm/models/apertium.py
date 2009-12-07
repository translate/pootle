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

"""A TM provider that can query the web service for the Apertium software for
Machine Translation."""

import urllib

from basetmmodel import BaseTMModel, unescape_html_entities

from virtaal.support.httpclient import HTTPClient, RESTRequest


class TMModel(BaseTMModel):
    """This is the translation memory model."""

    __gtype_name__ = 'ApertiumTMModel'
    display_name = _('Apertium')
    description = _('Unreviewed machine translations from Apertium')

    default_config = {
        "host" : "xixona.dlsi.ua.es",
        "port" : "80",
    }

    # INITIALISERS #
    def __init__(self, internal_name, controller):
        self.internal_name = internal_name
        self.language_pairs = {}
        self.load_config()

        self.client = HTTPClient()
        self.url = "http://%s:%s/webservice/ws.php" % (self.config["host"], self.config["port"])
        langreq = RESTRequest(self.url, '', method='GET', data=urllib.urlencode(''), headers=None)
        self.client.add(langreq)
        langreq.connect(
            'http-success',
            lambda langreq, response: self.got_language_pairs(response)
        )

        super(TMModel, self).__init__(controller)


    # METHODS #
    def query(self, tmcontroller, query_str):
        """Send the query to the web service. The response is handled by means
        of a call-back because it happens asynchronously."""
        pair = '%s-%s' % (self.source_lang, self.target_lang)
        if pair not in self.language_pairs:
            return

        if self.cache.has_key(query_str):
            self.emit('match-found', query_str, self.cache[query_str])
        else:
            values = {
                'mode': pair,
                'text': query_str,
                'mark': 0,
                'format': 'html'
            }
            req = RESTRequest(self.url, '', method='POST', \
                    data=urllib.urlencode(values), headers=None)
            self.client.add(req)
            req.connect(
                'http-success',
                lambda req, response: self.got_translation(response, query_str)
            )

    def got_language_pairs(self, val):
        """Handle the response from the web service to set up language pairs."""
        #Pairs are given on lines ending in <br/>
        self.language_pairs = dict([(pair.strip(), None) for pair in val.split('<br/>\n')])

    def got_translation(self, val, query_str):
        """Handle the response from the web service now that it came in."""
        val = val[:-1] # Chop off \n
        val = unescape_html_entities(val)
        match = {
            'source': query_str,
            'target': val,
            #l10n: Try to keep this as short as possible. Feel free to transliterate in CJK languages for optimal vertical display.
            'tmsource': _('Apertium'),
        }
        self.cache[query_str] = [match]

        self.emit('match-found', query_str, [match])
