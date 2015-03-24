#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<server>'
    help = 'Starts the Pootle server'

    def handle(self, server_name='cherrypy', **options):
        # XXX: Find a cleaner way to handle these and their custom options
        servers = {
            'cherrypy': 'run_cherrypy',
            'fcgi': 'runfcgi',
            'gunicorn': 'run_gunicorn',
        }

        try:
            server_command = servers[server_name]
        except KeyError:
            raise CommandError('%s is not a valid server' % server_name)

        call_command(server_command)
