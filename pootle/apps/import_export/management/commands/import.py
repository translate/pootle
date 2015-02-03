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
from translate.storage import po

class Command(BaseCommand):
    args = "<file file ...>"
    help = "Import a translation file or a zip of translation files." \
           "X-Pootle-Path header must be present."

    def _export_file(self, file):
        pofile = po.pofile(file.read())
        pootle_path = pofile.parseheader().get("X-Pootle-Path")
        if not pootle_path:
            self.stderr.write("File %r missing X-Pootle-Path header\n" % (file.name))
            return

        try:
            store, created = Store.objects.get_or_create(pootle_path=pootle_path)
        except Exception as e:
            raise CommandError("Could not import %r. Bad X-Pootle-Path? (%s)" %
                               (file.name, e))
        store.update(store=pofile)
        self.stdout.write("Imported %s to %r\n" % (pootle_path, store))

    def handle(self, *args, **options):
        for filename in args:
            if is_zipfile(filename):
                with ZipFile(filename, "r") as zf:
                    for path in zf.namelist():
                        with zf.open(path, "r") as f:
                            self._export_file(f)
            else:
                with open(filename, "r") as f:
                    self._export_file(f)
