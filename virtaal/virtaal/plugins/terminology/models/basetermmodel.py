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

import os
import gobject

from virtaal.models import BaseModel
from virtaal.common import pan_app

class BaseTerminologyModel(BaseModel):
    """The base interface to be implemented by all terminology backend models."""

    __gtype_name__ = None
    __gsignals__ = {
        'match-found': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,))
    }

    configure_func = None
    """A function that starts the configuration, if available."""
    display_name = None
    """The backend's name, suitable for display."""
    default_config = {}
    """Default configuration shared by all terminology model plug-ins."""

    # INITIALIZERS #
    def __init__(self, controller):
        """Initialise the model and connects it to the appropriate events.

            Only call this from child classes once the object was successfully
            created and want to be connected to signals."""
        super(BaseTerminologyModel, self).__init__()
        self.config = {}
        self.controller = controller
        self._connect_ids = []

        #static suggestion cache for slow terminology queries
        #TODO: cache invalidation, maybe decorate query to automate cache handling?
        self.cache = {}


    # METHODS #
    def destroy(self):
        self.save_config()
        #disconnect all signals
        [widget.disconnect(cid) for (cid, widget) in self._connect_ids]

    def load_config(self):
        """Load terminology backend config from default location"""
        self.config = {}
        self.config.update(self.default_config)
        config_file = os.path.join(pan_app.get_config_dir(), "terminology.ini")
        self.config.update(pan_app.load_config(config_file, self.internal_name))

    def save_config(self):
        """Save terminology backend config to default location"""
        config_file = os.path.join(pan_app.get_config_dir(), "terminology.ini")
        pan_app.save_config(config_file, self.config, self.internal_name)
