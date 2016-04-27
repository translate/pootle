# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


User = get_user_model()


class UserCommand(BaseCommand):
    """Base class for handling user commands."""

    def add_arguments(self, parser):
        parser.add_argument(
            "user",
            nargs='+',
            help="Username of account",
        )

    def handle(self, **options):
        raise NotImplementedError

    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError("User %s does not exist" % username)
