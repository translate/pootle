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
import subprocess
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from pootle_misc.baseurl import l


class Command(BaseCommand):
    help = 'Builds and bundles static assets using webpack'
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument(
            '--dev',
            action='store_true',
            dest='dev',
            default=False,
            help='Enable development builds and watch for changes.',
        )

    def handle(self, **options):
        default_static_dir = os.path.join(settings.WORKING_DIR, 'static')
        custom_static_dirs = filter(lambda x: x != default_static_dir,
                                    settings.STATICFILES_DIRS)
        default_js_dir = os.path.join(default_static_dir, 'js')

        webpack_config_file = os.path.join(default_js_dir, 'webpack.config.js')

        webpack_bin = os.path.join(default_js_dir, 'node_modules/.bin/webpack')
        if os.name == 'nt':
            webpack_bin = '%s.cmd' % webpack_bin

        webpack_args = [webpack_bin, '--config=%s' % webpack_config_file,
                        '--progress', '--colors']

        if options['dev']:
            webpack_args.extend(['--watch', '--display-error-details'])
        else:
            os.environ['NODE_ENV'] = 'production'

        static_base = l(settings.STATIC_URL)
        suffix = 'js/' if static_base.endswith('/') else '/js/'
        os.environ['WEBPACK_PUBLIC_PATH'] = static_base + suffix

        if custom_static_dirs:
            # XXX: review this for css
            # Append `js/` so that it's not necessary to reference it from the
            # `webpack.config.js` file
            custom_static_dirs = map(lambda x: os.path.join(x, 'js/'),
                                     custom_static_dirs)
            os.environ['WEBPACK_ROOT'] = ':'.join(custom_static_dirs)

        try:
            subprocess.call(webpack_args)
        except OSError:
            raise CommandError(
                'webpack executable not found.\n'
                'Make sure to install it by running '
                '`cd %s && npm install`' % default_js_dir
            )
            sys.exit(0)
