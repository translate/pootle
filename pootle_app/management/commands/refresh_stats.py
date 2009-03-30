#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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
os.environ['DJANGO_SETTINGS_MODULE'] = 'Pootle.settings'

from optparse import make_option

from django.core.management.base import NoArgsCommand
from pootle_app.models import TranslationProject, Store, store_file

_translation_project_cache = {}

# A simply function to keep a cache of TranslationProjects that have
# already been opened. This is just to speed things up a bit.
def get_translation_project(language_code, project_code):
    try:
        return _translation_project_cache[language_code, project_code]
    except KeyError:
        translation_project = TranslationProject.objects.get(language__code=language_code, project__code=project_code)
        _translation_project_cache[language_code, project_code] = translation_project
        # This will force the indexer of a TranslationProject to be
        # initialized. The indexer will update the text index of the
        # TranslationProject if it is out of date.
        translation_project.indexer
        return translation_project

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--directory', action='store', dest='directory', default='',
                    help='Pootle directory to refresh'),
        make_option('--recompute', action='store_true', dest='recompute', default=False,
                    help='Update the mtime of file, thereby forcing stats and index recomputation.'),
        )
    help = "Allow stats and text indices to be refreshed manually."

    def handle_noargs(self, **options):
        def print_message(pootle_file):
            print "Updating stats for %s" % pootle_file.store.real_path

        refresh_path = options.get('directory', '')
        recompute = options.get('recompute', False)

        # We force stats and indexing information to be recomputed by
        # updating the mtimes of the files whose information we want
        # to update.
        if recompute:
            for store in Store.objects.filter(pootle_path__startswith=refresh_path):
                print "Resetting mtime for %s to now" % store.real_path
                os.utime(store.abs_real_path, None)

        for store in Store.objects.filter(pootle_path__startswith=refresh_path):
            # Get a path such as /<language>/<project>/...
            components = store.pootle_path.split('/')
            # Split the path into ['', <language>, <project>, ...]
            language_code, project_code = components[1:3]
            try:
                translation_project = get_translation_project(language_code, project_code)
                # Simply by opening a file, we'll trigger the
                # machinery that looks at its mtime and decides
                # whether its stats should be updated
                store_file.with_store(translation_project, store, print_message)
            except TranslationProject.DoesNotExist:
                pass

            
