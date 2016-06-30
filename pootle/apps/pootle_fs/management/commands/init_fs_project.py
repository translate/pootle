# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.core.management import BaseCommand, CommandError
from django.db import IntegrityError

from pootle_fs.utils import FSPlugin, parse_fs_url
from pootle_language.models import Language
from pootle_project.models import Project


logger = logging.getLogger('pootle.fs')


class Command(BaseCommand):
    help = "Init a new Pootle FS project."

    def add_arguments(self, parser):
        parser.add_argument(
            'code',
            metavar='CODE',
            help='Project code'
        )
        parser.add_argument(
            'fs',
            metavar='FS_URL',
            help='FS url "filesystem_type+/repo/path/"'
        )
        parser.add_argument(
            'translation_path',
            help='Translation path "<language_code>/<filename>.<ext>"',
            metavar='TRANSLATION_PATH'
        )
        parser.add_argument(
            '-n', '--name',
            action='store',
            dest='name',
            nargs='?',
            help='Project name',
        )
        parser.add_argument(
            '--file-type',
            action='store',
            dest='file_type',
            help='File type',
            nargs='?',
            default='po'
        )
        parser.add_argument(
            '--checkstyle',
            action='store',
            dest='checkstyle',
            help='Checkstyle',
            nargs='?',
            default='standard'
        )
        parser.add_argument(
            '-l', '--source-language',
            action='store',
            dest='source_language',
            help="Code for the project's source language",
            nargs='?',
            default='en'
        )
        parser.add_argument(
            '--nosync',
            action='store_false',
            dest='sync',
            help='Flag if sync is unnecessary',
            default=True
        )

    def handle(self, **options):
        source_language_code = options['source_language']
        try:
            source_language = Language.objects.get(code=source_language_code)
        except Language.DoesNotExist as e:
            self.stdout.write('%s: Unknown language code.' %
                              source_language_code)
            raise CommandError(e)

        fs_type, fs_url = parse_fs_url(options['fs'])
        code = options['code']
        name = options['name'] or code.capitalize()

        try:
            project = Project.objects.create(
                code=code,
                fullname=name,
                localfiletype=options['file_type'],
                treestyle='none',
                checkstyle=options['checkstyle'],
                source_language=source_language
            )
            project.update_all_cache()
        except IntegrityError as e:
            self.stdout.write('Project code "%s" already exists.'
                              % options['code'])
            raise CommandError(e)

        project.config['pootle_fs.fs_type'] = fs_type
        project.config['pootle_fs.fs_url'] = fs_url
        project.config['pootle_fs.translation_paths'] = {
            'default': options['translation_path']
        }

        if options['sync']:
            plugin = FSPlugin(project)
            plugin.fetch()
            plugin.sync()
