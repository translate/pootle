#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand


class Command(PootleCommand):
    help = "Flush stats cache."

    def handle_all_stores(self, translation_project, **options):
        translation_project.clear_all_cache()

    def handle_language(self, lang, **options):
        lang.clear_all_cache(children=False)

    def handle_project(self, prj, **options):
        prj.clear_all_cache(children=False)
