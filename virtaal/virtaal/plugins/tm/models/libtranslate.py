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

import ctypes.util
from ctypes import *
if not ctypes.util.find_library("translate"):
    raise ImportError("libtranslate not found")

import logging
from translate.misc import quote

from virtaal.common import pan_app

from basetmmodel import BaseTMModel


class TMModel(BaseTMModel):
    """This is a libtranslate translation memory model.

    The plugin does the following: intialise libtranslate, get the services, get a session.
    During operartion is simply queries libtranslate for a translation.  This follows the
    pattern outlined in file:///usr/share/gtk-doc/html/libtranslate/tutorials.html (sorry
    no online version found, use the one packaged with libtranslate).
    """

    __gtype_name__ = 'LibtranslateTMModel'
    #l10n: This is the name of a software library. You almost definitely don't want to translate this. The lower case 'l' is intentional.
    display_name = _('libtranslate')
    description = _('Unreviewed machine translations from various services')

    # TODO - allow the user to configure which systems to query for translations, default will be all`


    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        self.internal_name = internal_name

        self.lt = cdll.LoadLibrary(ctypes.util.find_library("translate"))

        # Define all used functions
        self.lt.translate_init.argtypes = [c_int]
        self.lt.translate_init.restype = c_int
        self.lt.translate_get_services.restype = c_int
        self.lt.translate_session_new.argtype = [c_int]
        self.lt.translate_session_new.restype = c_int
        self.lt.translate_session_translate_text.argtype = [c_int, c_char_p, c_char_p, c_char_p, c_int, c_int, c_int]
        self.lt.translate_session_translate_text.restype = c_char_p

        # Initialise libtranslate
        err = c_int()
        if not self.lt.translate_init(err):
            # TODO: cleanup memory used by err
            raise Exception("Unable to initialise libtranslate: %s" % err)

        services = self.lt.translate_get_services()
        self.session = self.lt.translate_session_new(services)
        # TODO see file:///usr/share/gtk-doc/html/libtranslate/tutorials.html
        # g_slist_foreach(services, (GFunc) g_object_unref, NULL);
        # g_slist_free(services);

        super(TMModel, self).__init__(controller)


    # METHODS #
    def query(self, tmcontroller, query_str):
        translation = []
        err = c_int()
        result = self.lt.translate_session_translate_text(
            self.session, query_str,
            self.source_lang, self.target_lang,
            None, None, err
        )
        if result is None:
            # TODO handle errors and cleanup errors
            logging.warning("An error occured while getting a translation: %s" % err)
            return
        translation.append({
            'source': query_str,
            'target': quote.rstripeol(result),
            #l10n: Try to keep this as short as possible. Feel free to transliterate in CJK languages for vertical display optimization.
            'tmsource': _('libtranslate')
        })

        # TODO: drop any memory used by 'result'
        self.emit('match-found', query_str, translation)
