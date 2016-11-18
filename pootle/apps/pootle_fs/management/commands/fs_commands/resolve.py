# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import FSAPISubCommand


class ResolveCommand(FSAPISubCommand):
    help = "Resolve conflicting stores for sync to the filesystem."
    api_method = "resolve"

    def add_arguments(self, parser):
        super(ResolveCommand, self).add_arguments(parser)
        parser.add_argument(
            "--overwrite",
            action="store_false",
            dest="merge",
            help=("Overwrite the corresponding store or file"))
        parser.add_argument(
            "--pootle-wins",
            action="store_true",
            dest="pootle_wins",
            help=("Where units are conflicting use the version from Pootle"))
