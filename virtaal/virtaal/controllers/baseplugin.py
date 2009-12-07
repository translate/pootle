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

import os

from virtaal.common import pan_app

class BasePlugin(object):
    """The base interface to be implemented by all plug-ins."""

    configure_func = None
    """A function that starts the plug-in's configuration, if available."""
    description = ''
    """A description about the plug-in's purpose."""
    display_name = ''
    """The plug-in's name, suitable for display."""
    version = 0
    """The plug-in's version number."""
    default_config = {}

    # INITIALIZERS #
    def __new__(cls, *args, **kwargs):
        """Create a new plug-in instance and check that it is valid."""
        if not cls.display_name:
            raise Exception('No name specified')
        if cls.version <= 0:
            raise Exception('Invalid version number specified')
        return super(BasePlugin, cls).__new__(cls)

    def __init__(self):
        raise NotImplementedError('This interface cannot be instantiated.')

    # METHODS #
    def destroy(self):
        """This method is called by C{PluginController.shutdown()} and should be
            implemented by all plug-ins that need to do clean-up."""
        pass

    def load_config(self):
        """Load plugin config from default location."""
        self.config = {}
        self.config.update(self.default_config)
        config_file = os.path.join(pan_app.get_config_dir(), "plugins.ini")
        self.config.update(pan_app.load_config(config_file, self.internal_name))

    def save_config(self):
        """Save plugin config to default location."""
        config_file = os.path.join(pan_app.get_config_dir(), "plugins.ini")
        pan_app.save_config(config_file, self.config, self.internal_name)
