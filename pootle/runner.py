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

import os
import sys
from optparse import OptionParser

from django.core import management

import syspath_override


#: Length for the generated :setting:`SECRET_KEY`
KEY_LENGTH = 50

#: Default path for the settings file
DEFAULT_SETTINGS_PATH = '~/.pootle/pootle.conf'

#: Template that will be used to initialize settings from
SETTINGS_TEMPLATE_FILENAME = 'settings/90-local.conf.sample'


def init_settings(settings_filepath, template_filename):
    """Initializes a sample settings file for new installations.

    :param settings_filepath: The target file path where the initial settings
        will be written to.
    :param template_filename: Template file used to initialize settings from.
    """
    dirname = os.path.dirname(settings_filepath)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    fp = open(settings_filepath, 'w')

    import base64
    output = open(template_filename).read()
    output = output % {
            'default_key': base64.b64encode(os.urandom(KEY_LENGTH)),
    }

    fp.write(output)
    fp.close()


def parse_args(args):
    """Parses the given arguments.

    :param args: List of command-line arguments as got from sys.argv.
    :return: 3-element tuple: (args, command, command_args)
    """
    index = None
    for i, arg in enumerate(args):
        if not arg.startswith('-'):
            index = i
            break

    if index is None:
        return (args, None, [])

    return (args[:index], args[index], args[(index + 1):])


def configure_app(project, config_path, django_settings_module, runner_name):
    """Determines which settings file to use and sets environment variables
    accordingly.

    :param project: Project's name. Will be used to generate the settings
        environment variable.
    :param config_path: The path to the user's configuration file.
    :param django_settings_module: The module that ``DJANGO_SETTINGS_MODULE``
        will be set to.
    :param runner_name: The name of the running script.
    """
    settings_envvar = project.upper() + '_SETTINGS'

    # Normalize path and expand ~ constructions
    config_path = os.path.normpath(os.path.abspath(
            os.path.expanduser(config_path),
        )
    )

    if not (os.path.exists(config_path) or
            os.environ.get(settings_envvar, None)):
        print u"Configuration file does not exist at %r or " \
              u"%r environment variable has not been set.\n" \
              u"Use '%s init' to initialize the configuration file." % \
                (config_path, settings_envvar, runner_name)
        sys.exit(2)

    os.environ.setdefault(settings_envvar, config_path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', django_settings_module)


def run_app(project, default_settings_path, settings_template,
            django_settings_module):
    """Wrapper around django-admin.py.

    :param project: Project's name.
    :param default_settings_path: Default filepath to search for custom
        settings. This will also be used as a default location for writing
        initial settings.
    :param settings_template: Template file for initializing settings from.
    :param django_settings_module: The module that ``DJANGO_SETTINGS_MODULE``
        will be set to.
    """
    sys_args = sys.argv
    runner_name = os.path.basename(sys_args[0])

    (args, command, command_args) = parse_args(sys_args[1:])

    if not (command or args):
        # XXX: Should we display a more verbose help/usage message?
        print "Usage: %s [--config=/path/to/settings.conf] [command] " \
              "[options]" % runner_name
        sys.exit(2)

    if command == 'init':
        noinput = '--noinput' in command_args
        if noinput:
            command_args.remove('--noinput')

        # Determine which config file to write
        try:
            import re
            config_path = command_args[0]
            # Remove possible initial dashes
            config_path = re.sub('^-+', '', config_path)
        except IndexError:
            config_path = default_settings_path

        config_path = os.path.expanduser(config_path)

        if os.path.exists(config_path):
            resp = None
            if noinput:
                resp = 'n'
            while resp not in ('Y', 'n'):
                resp = raw_input('File already exists at %r, overwrite? [nY] ' \
                                 % config_path)
            if resp == 'n':
                print "File already exists, not overwriting."
                return

        try:
            init_settings(config_path, settings_template)
        except (IOError, OSError) as e:
            raise e.__class__, 'Unable to write default settings file to %r' \
                                % config_path

        print "Configuration file created at %r" % config_path

        return

    parser = OptionParser()

    parser.add_option('--config', metavar='CONFIG',
                      default=default_settings_path,
                      help=u'Use the specified configuration file.')
    parser.add_option('-v', '--version', action='store_true',
                      default=False,
                      help=u'Display version information and exit.')

    (opts, opt_args) = parser.parse_args(args)

    if opts.version:
        from pootle import __version__
        from translate import __version__ as tt_version
        from django import get_version

        print "Pootle %s" % __version__.sver
        print "Translate Toolkit %s" % tt_version.sver
        print "Django %s" % get_version()

        return

    configure_app(project=project, config_path=opts.config,
                  django_settings_module=django_settings_module,
                  runner_name=runner_name)

    management.execute_from_command_line([runner_name, command] + command_args)

    sys.exit(0)


def main():
    src_dir = os.path.abspath(os.path.dirname(__file__))
    settings_template = os.path.join(src_dir, SETTINGS_TEMPLATE_FILENAME)

    run_app(project='pootle',
            default_settings_path=DEFAULT_SETTINGS_PATH,
            settings_template=settings_template,
            django_settings_module='pootle.settings')


if __name__ == '__main__':
    main()
