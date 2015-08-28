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
SETTINGS_TEMPLATE_FILENAME = 'settings/90-local.conf.template'

# Python 2+3 support for input()
if sys.version_info[0] < 3:
    input = raw_input


def init_settings(settings_filepath, template_filename,
                  db="sqlite", db_name="dbs/pootle.db", db_user="",
                  db_password="", db_host="", db_port=""):
    """Initializes a sample settings file for new installations.

    :param settings_filepath: The target file path where the initial settings
        will be written to.
    :param template_filename: Template file used to initialize settings from.
    :param db: Database engine to use
        (default=sqlite, choices=[mysql, postgresql]).
    :param db_name: Database name (default: pootledb) or path to database file
        if using sqlite (default: dbs/pootle.db)
    :param db_user: Name of the database user. Not used with sqlite.
    :param db_password: Password for the database user. Not used with sqlite.
    :param db_host: Database host. Defaults to localhost. Not used with sqlite.
    :param db_port: Database port. Defaults to backend default. Not used with
        sqlite.
    """
    from base64 import b64encode

    dirname = os.path.dirname(settings_filepath)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    if db == "sqlite":
        db_name = "working_path('%s')" % (db_name or "dbs/pootle.db")
        db_user = db_password = db_host = db_port = "''"
    else:
        db_name = "'%s'" % (db_name or "pootledb")
        db_user = "'%s'" % (db_user or "pootle")
        db_password = "'%s'" % db_password
        db_host = "'%s'" % db_host
        db_port = "'%s'" % db_port

    db_module = {
        'sqlite': 'sqlite3',
        'mysql': 'mysql',
        'postgresql': 'postgresql_psycopg2',
        }[db]

    context = {
        "default_key": ("'%s'"
                        % b64encode(os.urandom(KEY_LENGTH)).decode("utf-8")),
        "db_engine": "'transaction_hooks.backends.%s'" % db_module,
        "db_name": db_name,
        "db_user": db_user,
        "db_password": db_password,
        "db_host": db_host,
        "db_port": db_port,
    }

    with open(settings_filepath, 'w') as settings:
        with open(template_filename) as template:
            settings.write(template.read() % context)


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
    src_dir = os.path.abspath(os.path.dirname(__file__))

    parser = ArgumentParser()

    parser.add_argument("--config",
                        default=default_settings_path,
                        help=u"Use the specified configuration file.")
    parser.add_argument("--noinput", action="store_true", default=False,
                        help=u"Never prompt for input")
    parser.add_argument("--version", action="version", version=get_version())

    parser.add_argument("--db", default="sqlite",
                        help=(u"Use the specified database backend (default: "
                              "'sqlite'; other options: 'mysql', "
                              "'postgresql')."))
    parser.add_argument("--db-name", default="",
                        help=(u"Database name (default: 'pootledb') or path "
                              "to database file if using sqlite (default: "
                              "'%s/dbs/pootle.db')" % src_dir))
    parser.add_argument("--db-user", default="",
                        help=(u"Name of the database user. Not used with "
                              "sqlite."))
    parser.add_argument("--db-password", default="",
                        help=(u"Password for the database user. Not used with "
                              "sqlite."))
    parser.add_argument("--db-host", default="",
                        help=(u"Database host. Defaults to localhost. Not "
                              "used with sqlite."))
    parser.add_argument("--db-port", default="",
                        help=(u"Database port. Defaults to backend default. "
                              "Not used with sqlite."))

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
            init_settings(config_path, settings_template,
                          args.db, args.db_name, args.db_user,
                          args.db_password, args.db_host, args.db_port)
        except (IOError, OSError) as e:
            raise e.__class__('Unable to write default settings file to %r'
                % config_path)

        if args.db in ['mysql', 'postgresql'] and not args.db_password:
            print("Configuration file created at %r. You have not specified a "
                  "password for your database. You may want to update the "
                  "database settings now" % config_path)
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
