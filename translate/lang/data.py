#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""This module stores information and functionality that relates to plurals."""

import unicodedata

# The key is the language code, which may contain country codes and modifiers.
# The value is a tuple: (Full name in English, nplurals, plural equation)

languages = {
'af': ('Afrikaans', 2, '(n != 1)'),
'ak': ('Akan', 2, 'n > 1'),
'ar': ('Arabic', 6, 'n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n>=3 && n<=10 ? 3 : n>=11 && n<=99 ? 4 : 5'),
'az': ('Azerbaijani', 2, '(n != 1)'),
'be': ('Belarusian', 3, 'n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2'),
'bg': ('Bulgarian', 2, '(n != 1)'),
'bn': ('Bengali', 2, '(n != 1)'),
'bo': ('Tibetan', 1, '0'),
'bs': ('Bosnian', 3, 'n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2'),
'ca': ('Catalan', 2, '(n != 1)'),
'cs': ('Czech', 3, '(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'),
'cy': ('Welsh', 2, '(n==2) ? 1 : 0'),
'da': ('Danish', 2, '(n != 1)'),
'de': ('German', 2, '(n != 1)'),
'dz': ('Dzongkha', 1, '0'),
'el': ('Greek', 2, '(n != 1)'),
'en': ('English', 2, '(n != 1)'),
'en_UK': ('English (United Kingdom)', 2, '(n != 1)'),
'en_ZA': ('English (South Africa)', 2, '(n != 1)'),
'eo': ('Esperanto', 2, '(n != 1)'),
'es': ('Spanish', 2, '(n != 1)'),
'et': ('Estonian', 2, '(n != 1)'),
'eu': ('Basque', 2, '(n != 1)'),
'fa': ('Persian', 1, '0'),
'fi': ('Finnish', 2, '(n != 1)'),
'fo': ('Faroese', 2, '(n != 1)'),
'fr': ('French', 2, '(n > 1)'),
'fur': ('Friulian', 2, '(n != 1)'),
'fy': ('Frisian', 2, '(n != 1)'),
'ga': ('Irish', 3, 'n==1 ? 0 : n==2 ? 1 : 2'),
'gl': ('Galician', 2, '(n != 1)'),
'gu': ('Gujarati', 2, '(n != 1)'),
'he': ('Hebrew', 2, '(n != 1)'),
'hi': ('Hindi', 2, '(n != 1)'),
'hr': ('Croatian', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
'hu': ('Hungarian', 2, '(n != 1)'),
'id': ('Indonesian', 1, '0'),
'is': ('Icelandic', 2, '(n != 1)'),
'it': ('Italian', 2, '(n != 1)'),
'ja': ('Japanese', 1, '0'),
'ka': ('Georgian', 1, '0'),
'km': ('Khmer', 1, '0'),
'ko': ('Korean', 1, '0'),
'ku': ('Kurdish', 2, '(n != 1)'),
'lb': ('Letzeburgesch', 2, '(n != 1)'),
'ln': ('Lingala', 2, '(n > 1)'),
'lt': ('Lithuanian', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2)'),
'lv': ('Latvian', 3, '(n%10==1 && n%100!=11 ? 0 : n != 0 ? 1 : 2)'),
'mg': ('Malagasy', 2, '(n > 1)'),
'mn': ('Mongolian', 2, '(n != 1)'),
'mr': ('Marathi', 2, '(n != 1)'),
'ms': ('Malay', 1, '0'),
'mt': ('Maltese', 4, '(n==1 ? 0 : n==0 || ( n%100>1 && n%100<11) ? 1 : (n%100>10 && n%100<20 ) ? 2 : 3)'),
'nah': ('Nahuatl', 2, '(n != 1)'),
'nb': ('Norwegian Bokmal', 2, '(n != 1)'),
'ne': ('Nepali', 2, '(n != 1)'),
'nl': ('Dutch', 2, '(n != 1)'),
'nn': ('Norwegian Nynorsk', 2, '(n != 1)'),
'nso': ('Northern Sotho', 2, '(n > 1)'),
'or': ('Oriya', 2, '(n != 1)'),
'pa': ('Punjabi', 2, '(n != 1)'),
'pap': ('Papiamento', 2, '(n != 1)'),
'pl': ('Polish', 3, '(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
'pt': ('Portugese', 2, '(n != 1)'),
'pt_BR': ('Portugese (Brazil)', 2, '(n > 1)'),
'ro': ('Romanian', 3, '(n==1 ? 0 : (n==0 || (n%100 > 0 && n%100 < 20)) ? 1 : 2);'),
'ru': ('Russian', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
'sk': ('Slovak', 3, '(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'),
'sl': ('Slovenian', 4, '(n%100==1 ? 0 : n%100==2 ? 1 : n%100==3 || n%100==4 ? 2 : 3)'),
'sq': ('Albanian', 2, '(n != 1)'),
'sr': ('Serbian', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
'sv': ('Swedish', 2, '(n != 1)'),
'ta': ('Tamil', 2, '(n != 1)'),
'th': ('Thai', 1, '0'),
'tk': ('Turkmen', 2, '(n != 1)'),
'tr': ('Turkish', 1, '0'),
'uk': ('Ukrainian', 3, '(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'),
'vi': ('Vietnamese',1 , '0'),
'wa': ('Walloon', 2, '(n > 1)'),
# Chinese is difficult because the main divide is on script, not really 
# country. Simplified Chinese is used mostly in China, Singapore and Malaysia.
# Traditional Chinese is used mostly in Hong Kong, Taiwan and Macau.
'zh_CN': ('Chinese (China)', 1, '0'),
'zh_HK': ('Chinese (Hong Kong)', 1, '0'),
'zh_TW': ('Chinese (Taiwan)', 1, '0'),
}

def simplercode(code):
    """This attempts to simplify the given language code by ignoring country 
    codes, for example."""
    # Check http://www.rfc-editor.org/rfc/bcp/bcp47.txt for possible extra issues
    # http://www.rfc-editor.org/rfc/rfc4646.txt
    # http://www.w3.org/International/articles/language-tags/
    if not code:
        return code

    # The @ modifier is used for script variants of the same language, like 
    # sr@Latn or gez_ER@abegede
    modifier = code.rfind("@")
    if modifier >= 0:
        return code[:modifier]

    underscore = code.rfind("_")
    if underscore >= 0:
        return code[:underscore]


import gettext
import re

iso639 = {}
iso3166 = {}

dialectre = re.compile(r"([^(\s]+)\s*\(([^)]+)\)")

def tr_lang(langcode):
    """Gives a function that can translate a language name, even in the form 
        "language (country)"
    into the language with iso code langcode."""
    langfunc = gettext_lang(langcode)
    countryfunc = gettext_country(langcode)

    def handlelanguage(name):
        match = dialectre.match(name)
        if match:
            language, country = match.groups()
            return u"%s (%s)" % (langfunc(language), countryfunc(country))
        else:
            return langfunc(name)

    return handlelanguage

def gettext_lang(langcode):
    """Returns a gettext function to translate language names into the given 
    language."""
    if not langcode in iso639:
        t = gettext.translation('iso_639', languages=[langcode], fallback=True)
        iso639[langcode] = t.ugettext
    return iso639[langcode]

def gettext_country(langcode):
    """Returns a gettext function to translate country names into the given 
    language."""
    if not langcode in iso3166:
        t = gettext.translation('iso_3166', languages=[langcode], fallback=True)
        iso3166[langcode] = t.ugettext
    return iso3166[langcode]

def normalize(string, normal_form="NFC"):
    """Return a unicode string in its normalized form
    
    @param sting: The string to be normalized
    @param normal_form: NFC (default), NFD, NFCK, NFDK
    @return: Normalized string
    """
    return unicodedata.normalize(normal_form, string)

def forceunicode(string):
    """Helper method to ensure that the parameter becomes unicode if not yet"""
    if string is None:
        return None
    if isinstance(string, str):
        encoding = getattr(string, "encoding", "utf-8")
        string = string.decode(encoding)
    string = normalize(string)
    return string
    
