# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.core.validators import ValidationError

from . import UserCommand
from ... import utils


class Command(UserCommand):
    help = "Verify a user of the system without requiring email verification"

    def add_arguments(self, parser):
        parser.add_argument(
            "user",
            nargs='*',  # Allow 0 in case --all is used
            help="Username of account",
        )
        parser.add_argument(
            '--all',
            dest='all',
            action="store_true",
            default=False,
            help='Verify all users',
        )

    def handle(self, **options):
        if bool(options['user']) == options['all']:
            raise CommandError("Either provide a 'user' to verify or "
                               "use '--all' to verify all users")

        if options['all']:
            for user in get_user_model().objects.hide_meta():
                try:
                    utils.verify_user(user)
                    self.stdout.write("Verified user '%s'" % user.username)
                except (ValueError, ValidationError) as e:
                    self.stderr.write(e[0])

        if options['user']:
            for user in options['user']:
                try:
                    utils.verify_user(self.get_user(user))
                    self.stdout.write("User '%s' has been verified" % user)
                except (ValueError, ValidationError) as e:
                    self.stderr.write(e[0])
