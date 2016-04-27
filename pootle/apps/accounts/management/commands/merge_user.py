# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from . import UserCommand
from ... import utils


class Command(UserCommand):
    help = "Merge user to other_user"

    def add_arguments(self, parser):
        parser.add_argument(
            "user",
            nargs=1,
            help="Username of account to merge from",
        )
        parser.add_argument(
            "other_user",
            nargs=1,
            help="Username of account to merge into",
        )

        parser.add_argument(
            "--no-delete",
            dest='delete',
            action="store_false",
            default=True,
            help="Don't delete user after merging.",
        )

    def handle(self, **options):
        src_user = self.get_user(username=options['user'][0])
        utils.UserMerger(src_user,
                         self.get_user(username=options['other_user'][0])).merge()

        if options["delete"]:
            self.stdout.write("Deleting user: %s...\n" % src_user.username)
            src_user.delete()
            self.stdout.write("User deleted: %s\n" % src_user.username)
