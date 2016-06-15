# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import FSAPISubCommand


class AddCommand(FSAPISubCommand):
    help = "Stage untracked stores for sync to the filesystem."
    api_method = "add"

    def add_arguments(self, parser):
        super(AddCommand, self).add_arguments(parser)
        parser.add_argument(
            "--force",
            action="store_true",
            dest="force",
            help=("Stage conflicting files on the filesystem to be "
                  "overwritten with the Pootle store"))
