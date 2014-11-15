#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
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
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
import subprocess

from optparse import make_option


from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Builds and bundles static assets using webpack'

    option_list = BaseCommand.option_list + (
        make_option('--dev',
            action='store_true',
            dest='dev',
            default=False,
            help='Enable development builds and watch for changes.'),
        )

    def handle(self, *args, **options):
        default_static_dir = os.path.join(settings.WORKING_DIR, 'static')
        custom_static_dirs = filter(lambda x: x != default_static_dir,
                                    settings.STATICFILES_DIRS)

        webpack_config_file = os.path.join(default_static_dir,
                                   'js/webpack.config.js')

        webpack_cmd = 'webpack'
        if os.name == 'nt':
            webpack_cmd = '%s.cmd' % webpack_cmd

        args = [webpack_cmd, '--config=%s' % webpack_config_file, '--progress',
                '--colors']

        if options['dev']:
            args.extend(['-d', '--watch'])
        else:
            os.environ['NODE_ENV'] = 'production'
            args.append('-p')

        if custom_static_dirs:
            # XXX: review this for css
            # Append `js/` so that it's not necessary to reference it
            # from the `webpack.config.js` file
            custom_static_dirs = map(lambda x: os.path.join(x, 'js/'),
                                     custom_static_dirs)
            os.environ['WEBPACK_ROOT'] = ':'.join(custom_static_dirs)

        try:
            subprocess.call(args)
        except OSError:
            raise CommandError(
                'webpack executable not found.\n'
                'Make sure to install it globally by running '
                '`npm install -g webpack`'
            )
            sys.exit(0)
