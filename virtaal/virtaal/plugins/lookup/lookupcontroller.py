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
import os

from virtaal.common import GObjectWrapper
from virtaal.controllers import BaseController, PluginController

from lookupview import LookupView
from models.baselookupmodel import BaseLookupModel


class LookupController(BaseController):
    """The central connection between look-up back-ends and the rest of Virtaal."""

    __gtype_name__ = 'LookupController'
    __gsignals__ = {
        'lookup-query': (gobject.SIGNAL_RUN_FIRST, None, (object,))
    }

    # INITIALIZERS #
    def __init__(self, plugin, config):
        GObjectWrapper.__init__(self)

        self.config = config
        self.main_controller = plugin.main_controller
        self.plugin = plugin

        self.disabled_model_names = ['baselookupmodel'] + self.config.get('disabled_models', [])
        self._signal_ids = {}
        self.view = LookupView(self)
        self._load_models()

    def _load_models(self):
        self.plugin_controller = PluginController(self)
        self.plugin_controller.PLUGIN_CLASSNAME = 'LookupModel'
        self.plugin_controller.PLUGIN_CLASS_INFO_ATTRIBS = ['display_name', 'description']
        new_dirs = []
        for dir in self.plugin_controller.PLUGIN_DIRS:
           new_dirs.append(os.path.join(dir, 'lookup', 'models'))
        self.plugin_controller.PLUGIN_DIRS = new_dirs

        self.plugin_controller.PLUGIN_INTERFACE = BaseLookupModel
        self.plugin_controller.PLUGIN_MODULES = ['virtaal_plugins.lookup.models', 'virtaal.plugins.lookup.models']
        self.plugin_controller.get_disabled_plugins = lambda *args: self.disabled_model_names

        self.plugin_controller.load_plugins()


    # METHODS #
    def destroy(self):
        self.view.destroy()
        self.plugin_controller.shutdown()
