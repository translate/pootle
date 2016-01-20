#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
from zipfile import ZipFile, is_zipfile

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from import_export.utils import import_file


class Command(BaseCommand):
    help = "Import a translation file or a zip of translation files. " \
           "X-Pootle-Path header must be present."

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            nargs="+",
            help="file to import"
        )
        parser.add_argument(
            "--user",
            action="store",
            dest="user",
            help="Import translation file(s) as USER",
        )

    def handle(self, **options):
        user = None
        if options["user"] is not None:
            User = get_user_model()
            try:
                user = User.objects.get(username=options["user"])
            except User.DoesNotExist:
                raise CommandError("Unrecognised user: %s" % options["user"])

        for filename in options['file']:
            if is_zipfile(filename):
                with ZipFile(filename, "r") as zf:
                    for path in zf.namelist():
                        with zf.open(path, "r") as f:
                            if path.endswith("/"):
                                # is a directory
                                continue
                            try:
                                import_file(f, user=user)
                            except Exception as e:
                                self.stderr.write("Warning: %s" % (e))
            else:
                with open(filename, "r") as f:
                    try:
                        import_file(f, user=user)
                    except Exception as e:
                        raise CommandError(e)
