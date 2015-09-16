#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from optparse import make_option

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.core.validators import ValidationError

from . import UserCommand
from ... import utils


class Command(UserCommand):
    args = "[user]"
    help = "Verify a user of the system without requiring email verification"
    shared_option_list = (
        make_option('--all', dest='all', action="store_true",
                    help='Verify all users'),
    )
    option_list = UserCommand.option_list + shared_option_list

    def handle(self, *args, **kwargs):
        self.check_args(*args)
        verify_all = kwargs.get("all")

        # Either [user] OR --all should be set
        both_or_neither = ((args and verify_all)
                           or (not args and not verify_all))
        if both_or_neither:
            raise CommandError("You must either provide a [user] to verify or "
                               "use '--all' to verify all users\n\n%s"
                               % self.usage_string())

        if verify_all:
            for user in get_user_model().objects.hide_meta():
                try:
                    utils.verify_user(user)
                    print("Verified user '%s'" % user.username)
                except (ValueError, ValidationError) as e:
                    print(e.message)
        else:
            try:
                utils.verify_user(self.get_user(args[0]))
                print("User '%s' has been verified" % args[0])
            except (ValueError, ValidationError) as e:
                raise CommandError(e.message)
