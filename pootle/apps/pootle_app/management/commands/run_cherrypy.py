#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from optparse import make_option

from pootle_app.management.commands import BaseRunCommand


class Command(BaseRunCommand):
    help = "Runs Pootle with the CherryPy server."

    option_list = BaseRunCommand.option_list + (
        make_option(
            '--threads',
            action='store',
            dest='threads',
            default=5,
            type=int,
            help='Number of working threads. Default: %default',
        ),
        make_option(
            '--name',
            action='store',
            dest='server_name',
            default='',
            help='Name of the worker process.',
        ),
        make_option(
            '--queue',
            action='store',
            dest='request_queue_size',
            default=5,
            type=int,
            help='Maximum number of queued connections.',
        ),
        make_option(
            '--ssl_certificate',
            action='store',
            dest='ssl_certificate',
            default='',
            help="Path to the server's SSL certificate.",
        ),
        make_option(
            '--ssl_private_key',
            action='store',
            dest='ssl_private_key',
            default='',
            help="Path to the server's SSL private key.",
        ),
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
