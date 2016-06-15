# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import FSAPISubCommand


class MergeCommand(FSAPISubCommand):
    help = "Merge translations between Pootle and FS."
    api_method = "merge"

    def add_arguments(self, parser):
        super(MergeCommand, self).add_arguments(parser)
        parser.add_argument(
            "--pootle-wins",
            action="store_true",
            dest="pootle_wins",
            help=("In the event of conflict, translation in Pootle is kept "
                  "and translation on disk is converted into a new suggestion "
                  "in Pootle"))
