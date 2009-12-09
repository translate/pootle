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

"""Performs external look-ups on selected text."""

from virtaal.controllers import BasePlugin

from lookupcontroller import LookupController


class Plugin(BasePlugin):
    description = _('Perform look-ups on selected text')
    display_name = _('External Look-up')
    version = '0.1'

    default_config = {
        'backends_dialog_width': 450,
    }

    # INITIALIZERS #
    def __init__(self, internal_name, main_controller):
        self.configure_func = self.configure
        self.internal_name = internal_name
        self.main_controller = main_controller

        self.load_config()
        self.config['backends_dialog_width'] = int(self.config['backends_dialog_width'])
        self._init_plugin()

    def _init_plugin(self):
        self.controller = LookupController(self, self.config)


    # METHODS #
    def configure(self, parent):
        self.controller.view.select_backends(parent)

    def destroy(self):
        self.config = self.controller.config
        self.save_config()
        self.controller.destroy()
