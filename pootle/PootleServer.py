#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2010 Zuza Software Foundation
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

# TODO: Make this less ugly
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

import optparse

import django
from django.core.servers.basehttp import AdminMediaHandler
from django.core.handlers.wsgi import WSGIHandler
from django.core.management import call_command

from translate import __version__ as toolkitversion
from translate.misc import wsgi

class PootleOptionParser(optparse.OptionParser):

    def __init__(self):
        optparse.OptionParser.__init__(self)
        self.set_default('instance', 'Pootle')
        self.add_option('',
             '--version',
             dest='action',
             action='store_const',
             const='version',
             default='runwebserver',
             help="show version information then exit",
        )
        self.add_option(
            '',
            '--refreshstats',
            dest='action',
            action='store_const',
            const='refreshstats',
            default='runwebserver',
            help='refresh the stats files instead of running the webserver',
            )
        self.add_option(
            '',
            '--port',
            action='store',
            type='int',
            dest='port',
            default='8080',
            help='The TCP port on which the server should listen for new connections.',
            )

def checkversions():
    """Checks that version dependencies are met."""
    # Old versions of the toolkit might not have .build or .sver, so we try to
    # be careful here so that our check doesn't cause an exception.
    if not hasattr(toolkitversion, 'build') or toolkitversion.ver < (1,5,0):
        raise RuntimeError('requires Translate Toolkit version >= 1.5.0.  Current installed version is: %s'
                            % getattr(toolkitversion, "sver", toolkitversion.ver))

def display_versions():
    from pootle.__version__ import sver as pootle_ver
    from translate.__version__ import sver as translate_ver
    from django import get_version as django_ver
    print "Pootle %s" % pootle_ver
    print "Translate Toolkit %s" % translate_ver
    print "Django %s" % django_ver()

def run_pootle(options, args):
    """Run the requested action."""
    if options.action == 'runwebserver':
        path = django.__path__[0] + '/contrib/admin/media'
        handler = AdminMediaHandler(WSGIHandler(), path)
        wsgi.launch_server('0.0.0.0', options.port, handler)
    elif options.action == 'refreshstats':
        call_command('refresh_stats')
    elif options.action == 'version':
        display_versions()

def main():
    # run the web server
    checkversions()
    parser = PootleOptionParser()
    (options, args) = parser.parse_args()
    if options.action != 'runwebserver':
        options.servertype = 'dummy'
    else:
        print "Starting server, listening on port %d." % options.port
    run_pootle(options, args)

if __name__ == '__main__':
    main()
