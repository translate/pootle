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

import os
import gobject
import htmlentitydefs
import re

from virtaal.models import BaseModel
from virtaal.common import pan_app


#http://effbot.org/zone/re-sub.htm#unescape-html
def unescape_html_entities(text):
    def fixup(m):
        text = m.group(0)
        entity = htmlentitydefs.entitydefs.get(text[1:-1])
        if not entity:
            if text[:2] == "&#":
                try:
                    return unichr(int(text[2:-1]))
                except ValueError:
                    pass
        else:
            return unicode(entity, "iso-8859-1")
    return re.sub("&(#[0-9]+|\w+);", fixup, text)


class BaseTMModel(BaseModel):
    """The base interface to be implemented by all TM backend models."""

    __gtype_name__ = None
    __gsignals__ = {
        'match-found': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,))
    }

    description = ""
    """A description of the backend. Will be displayed to users."""
    display_name = None
    """The backend's name, suitable for display."""

    default_config = {}
    """Default configuration shared by all TM model plug-ins."""

    # INITIALIZERS #
    def __init__(self, controller):
        """Initialise the model and connects it to the appropriate events.

            Only call this from child classes once the object was successfully
            created and want to be connected to signals."""
        super(BaseTMModel, self).__init__()
        self.config = {}
        self.controller = controller
        self._connect_ids = []
        self._connect_ids.append((self.controller.connect('start-query', self.query), self.controller))

        #static suggestion cache for slow TM queries
        #TODO: cache invalidation, maybe decorate query to automate cache handling?
        self.cache = {}

        self.source_lang = None
        self.target_lang = None
        lang_controller = self.controller.main_controller.lang_controller
        self._set_source_lang(None, lang_controller.source_lang.code)
        self._set_target_lang(None, lang_controller.target_lang.code)
        self._connect_ids.append((lang_controller.connect('source-lang-changed', self._set_source_lang), lang_controller))
        self._connect_ids.append((lang_controller.connect('target-lang-changed', self._set_target_lang), lang_controller))


    # METHODS #
    def destroy(self):
        self.save_config()
        #disconnect all signals
        [widget.disconnect(cid) for (cid, widget) in self._connect_ids]

    def query(self, tmcontroller, query_str):
        """Attempt to give suggestions applicable to query_str.

        All tm backends must implement this method, check for
        suggested translations to query_str, emit match-found on success.
        Note that query_str is from gobject, therefore not unicode."""
        pass

    def load_config(self):
        """load TM backend config from default location"""
        self.config = {}
        self.config.update(self.default_config)
        config_file = os.path.join(pan_app.get_config_dir(), "tm.ini")
        self.config.update(pan_app.load_config(config_file, self.internal_name))

    def save_config(self):
        """save TM backend config to default location"""
        config_file = os.path.join(pan_app.get_config_dir(), "tm.ini")
        pan_app.save_config(config_file, self.config, self.internal_name)

    def set_source_lang(self, language):
        """models override this to implement their own
        source-lang-changed event handlers"""
        pass

    def set_target_lang(self, language):
        """models override this to implement their own
        target-lang-changed event handlers"""
        pass

    def _set_source_lang(self, controller, language):
        """private method for baseline handling of source language
        change events"""
        if (language != self.source_lang):
            self.source_lang = language
            self.cache = {}
            self.set_source_lang(language)

    def _set_target_lang(self, controller, language):
        """private method for baseline handling of target language change events"""
        if (language != self.target_lang):
            self.target_lang = language
            self.cache = {}
            self.set_target_lang(language)
