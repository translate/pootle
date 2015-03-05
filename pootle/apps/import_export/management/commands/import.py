#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
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
from optparse import make_option
from zipfile import is_zipfile, ZipFile
from django.core.management.base import BaseCommand, CommandError

from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store
from import_export.views import _import_file


class Command(BaseCommand):
    args = "<file file ...>"
    help = "Import a translation file or a zip of translation files." \
           "X-Pootle-Path header must be present."

    def handle(self, *args, **options):
        for filename in args:
            if is_zipfile(filename):
                with ZipFile(filename, "r") as zf:
                    for path in zf.namelist():
                        with zf.open(path, "r") as f:
                            try:
                                _import_file(f)
                            except Exception as e:
                                self.stderr.write("Warning: %s" % (e))
            else:
                with open(filename, "r") as f:
                    try:
                        _import_file(f)
                    except Exception as e:
                        raise CommandError(e)
