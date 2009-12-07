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
import urllib
import pycurl
# These two json modules are API compatible
try:
    import simplejson as json #should be a bit faster; needed for Python < 2.6
except ImportError:
    import json #available since Python 2.6

from basetmmodel import BaseTMModel, unescape_html_entities
from virtaal.support.httpclient import HTTPClient, RESTRequest

# We should ideally be obtaining a list from them, or use their API to see if
# something is supported.
_languages = {
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'ar': 'Arabic',
    'be': 'Belarusian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'zh': 'Chinese',
    'zh-CN': 'Chinese_simplified',
    'zh-TW': 'Chinese_traditional',
    'hr': 'Croatian',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'en': 'English',
    'et': 'Estonian',
    'fi': 'Finnish',
    'fr': 'French',
    'gl': 'Galician',
    'de': 'German',
    'el': 'Greek',
    'iw': 'Hebrew',
    'hi': 'Hindi',
    'hu': 'Hungarian',
    'is': 'Icelandic',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'mk': 'Macedonian',
    'ms': 'Malay',
    'mt': 'Maltese',
    'no': 'Norwegian',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sr': 'Serbian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'es': 'Spanish',
    'sw': 'Swahili',
    'sv': 'Swedish',
    'th': 'Thai',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'vi': 'Vietnamese',
    'cy': 'Welsh',
    'yi': 'Yiddish'
}

# Some codes are weird or can be reused for others
code_translation = {
    'fl': 'tl', # Filipino -> Tagalog
    'he': 'iw', # Weird code Google uses for Hebrew
}

virtaal_referrer = "http://virtaal.org/"

class TMModel(BaseTMModel):
    """This is a Google Translate translation memory model.

    The plugin uses the U{Google AJAX Languages API<http://code.google.com/apis/ajaxlanguage/>}
    to query Google's machine translation services.  The implementation makes use of the 
    U{RESTful<http://code.google.com/apis/ajaxlanguage/documentation/#fonje>} interface for 
    Non-JavaScript environments.
    """

    __gtype_name__ = 'GoogleTranslateTMModel'
    #l10n: The name of Google Translate in your language (translated in most languages). See http://translate.google.com/
    display_name = _('Google Translate')
    description = _("Unreviewed machine translations from Google's translation service")

    translate_url = "http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&q=%(message)s&langpair=%(from)s%%7C%(to)s"

    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        self.internal_name = internal_name
        super(TMModel, self).__init__(controller)
        self.client = HTTPClient()

    # METHODS #
    def query(self, tmcontroller, query_str):
        # Google's Terms of Service says no more than 5000 characters
        query_str = query_str[:5000]
        source_lang = code_translation.get(self.source_lang, self.source_lang)
        target_lang = code_translation.get(self.target_lang, self.target_lang)
        if source_lang not in _languages or target_lang not in _languages:
            logging.debug('language pair not supported')
            return

        if self.cache.has_key(query_str):
            self.emit('match-found', query_str, self.cache[query_str])
        else:
            real_url = self.translate_url % {
                'message': urllib.quote_plus(query_str),
                'from':    self.source_lang,
                'to':      self.target_lang,
            }

            req = RESTRequest(real_url, '', method='GET', data=urllib.urlencode(''), headers=None)
            self.client.add(req)
            # Google's Terms of Service says we need a proper HTTP referrer
            req.curl.setopt(pycurl.REFERER, virtaal_referrer)
            req.connect(
                'http-success',
                lambda req, response: self.got_translation(response, query_str)
            )

    def got_translation(self, val, query_str):
        """Handle the response from the web service now that it came in."""
        data = json.loads(val)

        if data['responseStatus'] != 200:
            logging.debug("Failed to translate '%s':\n%s", (query_str, data['responseDetails']))
            return

        target_unescaped = unescape_html_entities(data['responseData']['translatedText'])
        match = {
            'source': query_str,
            'target': target_unescaped,
            #l10n: Try to keep this as short as possible. Feel free to transliterate.
            'tmsource': _('Google')
        }
        self.cache[query_str] = [match]
        self.emit('match-found', query_str, [match])
