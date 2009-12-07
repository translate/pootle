#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

from virtaal.controllers import BasePlugin

from tmcontroller import TMController


class Plugin(BasePlugin):
    display_name = _('Translation Memory')
    description = _('Translation memory suggestions')
    version = 0.1
    default_config = {
        'disabled_models': '_dummytm,libtranslate,remotetm,tinytm,apertium,google_translate,moses',
        'max_matches': '5',
        'min_quality': '70'
    }

    # INITIALIZERS #
    def __init__(self, internal_name, main_controller):
        self.configure_func = self.configure
        self.internal_name = internal_name
        self.main_controller = main_controller
        self._init_plugin()

    def _init_plugin(self):
        self.load_config()
        self.config['disabled_models'] = self.config['disabled_models'].split(',')
        self.config['max_matches'] = int(self.config['max_matches'])
        self.config['min_quality'] = int(self.config['min_quality'])

        self.tmcontroller = TMController(self.main_controller, self.config)


    # METHODS #
    def configure(self, parent):
        self.tmcontroller.view.select_backends(None)

    def destroy(self):
        self.config = self.tmcontroller.config
        self.save_config()
        self.tmcontroller.destroy()
