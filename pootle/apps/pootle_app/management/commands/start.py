#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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
