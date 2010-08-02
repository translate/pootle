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
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

import logging
from optparse import make_option

from django.core.management.base import NoArgsCommand

from pootle_translationproject.models import TranslationProject

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--directory', action='store', dest='directory', default='',
                    help='directory to refresh relative to po directory'),
        make_option('--recompute', action='store_true', dest='recompute', default=False,
                    help='Update the mtime of file, thereby forcing stats and index recomputation.'),
        )
    help = "Allow stats and text indices to be refreshed manually."

    def handle_noargs(self, **options):
        refresh_path = options.get('directory', '')
        recompute = options.get('recompute', False)

        # reduce size of parse pool early on
        from pootle_store.fields import  TranslationStoreFieldFile
        TranslationStoreFieldFile._store_cache.maxsize = 2
        TranslationStoreFieldFile._store_cache.cullsize = 2


        for translation_project in TranslationProject.objects.filter(real_path__startswith=refresh_path).iterator():
            if not os.path.isdir(translation_project.abs_real_path):
                # translation project no longer exists
                translation_project.delete()
                continue

            # rescan translation_projects
            translation_project.scan_files()
            if recompute:
                for store in translation_project.stores.iterator():
                    # We force stats and indexing information to be recomputed by
                    # updating the mtimes of the files whose information we want
                    # to update.
                    logging.info("Resetting mtime for %s to now", store.real_path)
                    os.utime(store.abs_real_path, None)

            # This will force the indexer of a TranslationProject to be
            # initialized. The indexer will update the text index of the
            # TranslationProject if it is out of date.
            translation_project.indexer

            logging.info("Updating stats for %s", translation_project.fullname.encode("utf-8"))
            translation_project.getcompletestats()
            translation_project.getquickstats()
