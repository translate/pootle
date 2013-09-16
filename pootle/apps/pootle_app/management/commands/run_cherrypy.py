#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
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
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import BaseRunCommand


class Command(BaseRunCommand):
    help = "Runs Pootle with the CherryPy server."

    option_list = BaseRunCommand.option_list + (
        make_option('--threads', action='store', dest='threads', default=5,
            type=int,
            help='Number of working threads. Default: 5'),
        make_option('--name', action='store', dest='server_name', default='',
            help='Name of the worker process.'),
        make_option('--queue', action='store', dest='request_queue_size',
            default=5, type=int,
            help='Maximum number of queued connections.'),
        make_option('--ssl_certificate', action='store',
            dest='ssl_certificate', default='',
            help='Path to the server\'s SSL certificate.'),
        make_option('--ssl_private_key', action='store',
            dest='ssl_private_key', default='',
            help='Path to the server\'s SSL private key.'),
    )

    def serve_forever(self, *args, **options):
        # Not using launch_server since we want further control over the
        # CherryPy WSGI server
        from translate.misc.wsgiserver import CherryPyWSGIServer as Server

        server = Server(
            (options['host'], int(options['port'])),
            self.get_app(),
            int(options['threads']),
            options['server_name'],
            request_queue_size=int(options['request_queue_size'])
        )

        if options['ssl_certificate'] and options['ssl_private_key']:
            server.ssl_certificate = options['ssl_certificate']
            server.ssl_private_key = options['ssl_private_key']

        import logging
        logging.info("Starting CherryPy server, listening on port %s",
                     options['port'])

        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
