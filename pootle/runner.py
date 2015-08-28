#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import sys
from argparse import ArgumentParser

from django.core import management

import syspath_override


#: Length for the generated :setting:`SECRET_KEY`
KEY_LENGTH = 50

#: Default path for the settings file
DEFAULT_SETTINGS_PATH = '~/.pootle/pootle.conf'

#: Template that will be used to initialize settings from
SETTINGS_TEMPLATE_FILENAME = 'settings/90-local.conf.sample'

# Python 2+3 support for input()
if sys.version_info[0] < 3:
    input = raw_input


def init_settings(settings_filepath, template_filename, db="sqlite"):
    """Initializes a sample settings file for new installations.

    :param settings_filepath: The target file path where the initial settings
        will be written to.
    :param template_filename: Template file used to initialize settings from.
    """
    from base64 import b64encode

    dirname = os.path.dirname(settings_filepath)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    fp = open(settings_filepath, 'w')

    output = open(template_filename).read()
    # We can't use regular python string formatting here.
    output = output.replace("${default_key}",
                            b64encode(os.urandom(KEY_LENGTH)).decode("utf-8"))

    db_module = {
        'sqlite': 'sqlite3',
        'mysql': 'mysql',
        'postgresql': 'postgresql_psycopg2',
        }[db]

    output = output.replace("'ENGINE': 'transaction_hooks.backends.sqlite3'",
                            "'ENGINE': 'transaction_hooks.backends.%s'" % db_module)

    if db != "sqlite":
        output = output.replace("'NAME': working_path('dbs/pootle.db')",
                                "'NAME': ''")

    fp.write(output)
    fp.close()


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
        print(u"Configuration file does not exist at %r or "
              u"%r environment variable has not been set.\n"
              u"Use '%s init' to initialize the configuration file." %
                (config_path, settings_envvar, runner_name))
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
    runner_name = os.path.basename(sys.argv[0])

    parser = ArgumentParser()

    parser.add_argument("--config",
                        default=default_settings_path,
                        help=u"Use the specified configuration file.")
    parser.add_argument("--noinput", action="store_true", default=False,
                        help=u"Never prompt for input")
    parser.add_argument("--version", action="version", version=get_version())
    parser.add_argument("--db", default="sqlite",
                        help=u"Use the specified database backend")

    args, remainder = parser.parse_known_args(sys.argv[1:])

    # bit hacky
    if "init" in remainder:
        config_path = os.path.expanduser(args.config)

        if os.path.exists(config_path):
            resp = None
            if args.noinput:
                resp = 'n'
            else:
                resp = input("File already exists at %r, overwrite? [Ny] "
                             % config_path).lower()
            if resp not in ("y", "yes"):
                print("File already exists, not overwriting.")
                exit(2)

        if args.db not in ["mysql", "postgresql", "sqlite"]:
            raise management.CommandError("Unrecognised database '%s': should "
                                          "be one of 'sqlite', 'mysql' or "
                                          "'postgresql'" % args.db)

        try:
            init_settings(config_path, settings_template, args.db)
        except (IOError, OSError) as e:
            raise e.__class__('Unable to write default settings file to %r'
                % config_path)

        if args.db in ["mysql", "postgresql"]:
            print("Configuration file created at %r: you must now update "
                  "the settings for %s database" % (config_path, args.db))
        else:
            print("Configuration file created at %r" % config_path)
        exit(0)

    configure_app(project=project, config_path=args.config,
                  django_settings_module=django_settings_module,
                  runner_name=runner_name)

    command = [runner_name] + remainder

    # Respect the noinput flag
    if args.noinput:
        command += ["--noinput"]

    management.execute_from_command_line(command)
    sys.exit(0)


def get_version():
    from pootle import __version__
    from translate import __version__ as tt_version
    from django import get_version as django_version

    return ("Pootle %s (Django %s, Translate Toolkit %s)" %
            (__version__, django_version(), tt_version.sver))


def main():
    src_dir = os.path.abspath(os.path.dirname(__file__))
    settings_template = os.path.join(src_dir, SETTINGS_TEMPLATE_FILENAME)

    run_app(project='pootle',
            default_settings_path=DEFAULT_SETTINGS_PATH,
            settings_template=settings_template,
            django_settings_module='pootle.settings')


if __name__ == '__main__':
    main()
