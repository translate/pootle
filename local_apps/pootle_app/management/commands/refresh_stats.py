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

from pootle_app.management.commands import PootleCommand

class Command(PootleCommand):
    help = "Allow stats and text indices to be refreshed manually."

    def handle_translation_project(self, translation_project, **options):
        # This will force the indexer of a TranslationProject to be
        # initialized. The indexer will update the text index of the
        # TranslationProject if it is out of date.
        translation_project.indexer

    def handle_all_stores(self, translation_project, **options):
        translation_project.getcompletestats()
        translation_project.getquickstats()

    def handle_store(self, store, **options):
        store.getcompletestats()
        store.getquickstats()

