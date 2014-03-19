#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_store.util import OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED
from pootle_store.caching import count_words
from pootle_app.management.commands import PootleCommand


class Command(PootleCommand):
    help = "Allow stats to be refreshed manually."

    def handle_store(self, store, **options):
        print("Processing %r" % (store))
        store.total_wordcount = 0
        store.translated_wordcount = 0
        store.fuzzy_wordcount = 0

        for unit in store.units.all():
            wordcount = count_words(unit.source_f.strings)
            store.total_wordcount += wordcount
            if unit.state == TRANSLATED:
                store.translated_wordcount += wordcount
            elif unit.state == FUZZY:
                store.fuzzy_wordcount += wordcount

        store.save()
