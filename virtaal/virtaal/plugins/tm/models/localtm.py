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

import logging
import os
import subprocess
import socket
import random
from virtaal.support import tmclient

from virtaal.common import pan_app
from basetmmodel import BaseTMModel
import remotetm


class TMModel(remotetm.TMModel):
    """This is the translation memory model."""

    __gtype_name__ = 'LocalTMModel'
    display_name = _('Local Translation Memory')
    description = _('Previous translations you have made')
    #l10n: Try to keep this as short as possible.
    shortname = _('Local TM')

    default_config = {
        "tmserver_bind" : "localhost",
        "tmserver_port" : "55555",
        "tmdb" : os.path.join(pan_app.get_config_dir(), "tm.db")
    }

    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        self.internal_name = internal_name
        self.load_config()

        # test if port specified in config is free
        self.config["tmserver_port"] = int(self.config["tmserver_port"])
        if test_port(self.config["tmserver_bind"], self.config["tmserver_port"]):
            port = self.config["tmserver_port"]
        else:
            port = find_free_port(self.config["tmserver_bind"], 49152, 65535)
        if os.name == "nt":
            executable = os.path.abspath(os.path.join(pan_app.main_dir, "tmserver.exe"))
        else:
            executable = "tmserver"

        command = [
            executable,
            "-b", self.config["tmserver_bind"],
            "-p", str(port),
            "-d", self.config["tmdb"],
            "--min-similarity=%d" % controller.min_quality,
            "--max-candidates=%d" % controller.max_matches,
        ]

        if pan_app.DEBUG:
            command.append("--debug")

        logging.debug("launching tmserver with command %s" % " ".join(command))
        try:
            self.tmserver = subprocess.Popen(command)
            url = "http://%s:%d/tmserver" % (self.config["tmserver_bind"], port)

            self.tmclient = tmclient.TMClient(url)
        except OSError, e:
            message = "Failed to start TM server: %s" % str(e)
            logging.exception('Failed to start TM server')
            raise

        # Do not use super() here, as remotetm.TMModel does a bit more than we
        # want in this case.
        BaseTMModel.__init__(self, controller)
        self._connect_ids.append((
            self.controller.main_controller.store_controller.connect("store-saved", self.push_store),
            self.controller.main_controller.store_controller
        ))


    def destroy(self):
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.TerminateProcess(int(self.tmserver._handle), -1)
        else:
            import signal
            os.kill(self.tmserver.pid, signal.SIGTERM)


def test_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        return True
    except socket.error:
        return False

def find_free_port(host, min_port, max_port):
    port_range = range(min_port, max_port)
    random.shuffle(port_range)
    for port in port_range:
        if test_port(host, port):
            return port
    #FIXME: shall we throw an exception if no free port is found?
    return None
