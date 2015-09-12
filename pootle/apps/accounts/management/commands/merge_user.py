#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from optparse import make_option

import accounts

from . import UserCommand


class Command(UserCommand):
    args = "user other_user"
    help = "Merge user to other_user"
    shared_option_list = (
        make_option("--no-delete",
                    dest='delete',
                    action="store_false",
                    default=True,
                    help="Don't delete user after merging."),
    )
    option_list = UserCommand.option_list + shared_option_list

    def handle(self, *args, **kwargs):
        super(Command, self).handle(*args, **kwargs)
        src_user = self.get_user(username=args[0])
        accounts.utils.UserMerger(src_user,
                                  self.get_user(username=args[1])).merge()

        if kwargs.get("delete"):
            self.stdout.write("Deleting user: %s...\n" % src_user.username)
            src_user.delete()
            self.stdout.write("User deleted: %s\n" % src_user.username)
