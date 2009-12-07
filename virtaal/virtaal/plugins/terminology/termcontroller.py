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

import gobject
import os.path
from translate.storage.placeables import terminology

from virtaal.common import GObjectWrapper, pan_app
from virtaal.controllers import BaseController, PluginController
from virtaal.views import placeablesguiinfo

import models
from models.basetermmodel import BaseTerminologyModel
from termview import TerminologyGUIInfo, TerminologyView


class TerminologyController(BaseController):
    """The logic-filled glue between the terminology view and -model."""

    __gtype_name__ = 'TerminologyController'
    __gsignals__ = {
        'start-query': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
    }

    # INITIALIZERS #
    def __init__(self, main_controller, config={}):
        GObjectWrapper.__init__(self)

        self.config = config
        self.main_controller = main_controller
        self.placeables_controller = main_controller.placeables_controller

        self.disabled_model_names = ['basetermmodel'] + self.config.get('disabled_models', [])
        self.placeables_controller.add_parsers(*terminology.parsers)
        self.placeables_controller.non_target_placeables.append(terminology.TerminologyPlaceable)
        self.placeables_controller.connect('parsers-changed', self._on_placeables_changed)

        if not (terminology.TerminologyPlaceable, TerminologyGUIInfo) in placeablesguiinfo.element_gui_map:
            placeablesguiinfo.element_gui_map.insert(0, (terminology.TerminologyPlaceable, TerminologyGUIInfo))

        self.view = TerminologyView(self)
        self._connect_signals()
        self._load_models()

    def _connect_signals(self):
        def lang_changed(ctrlr, lang):
            for src in self.main_controller.unit_controller.view.sources:
                src.elem.remove_type(terminology.TerminologyPlaceable)
                src.refresh()

        lang_controller = self.main_controller.lang_controller
        lang_controller.connect('source-lang-changed', lang_changed)
        lang_controller.connect('target-lang-changed', lang_changed)

    def _load_models(self):
        self.plugin_controller = PluginController(self)
        self.plugin_controller.PLUGIN_CLASSNAME = 'TerminologyModel'
        self.plugin_controller.PLUGIN_CLASS_INFO_ATTRIBS = ['description', 'display_name']
        new_dirs = []
        for dir in self.plugin_controller.PLUGIN_DIRS:
           new_dirs.append(os.path.join(dir, 'terminology', 'models'))
        self.plugin_controller.PLUGIN_DIRS = new_dirs

        self.plugin_controller.PLUGIN_INTERFACE = BaseTerminologyModel
        self.plugin_controller.PLUGIN_MODULES = ['virtaal_plugins.terminology.models', 'virtaal.plugins.terminology.models']
        self.plugin_controller.get_disabled_plugins = lambda *args: self.disabled_model_names
        self.plugin_controller.load_plugins()


    # METHODS #
    def destroy(self):
        self.view.destroy()
        self.plugin_controller.shutdown()
        self.placeables_controller.remove_parsers(terminology.parsers)


    # EVENT HANDLERS #
    def _on_placeables_changed(self, placeables_controller):
        for term_parser in terminology.parsers:
            if term_parser not in placeables_controller.parsers:
                placeables_controller.add_parsers(term_parser)
