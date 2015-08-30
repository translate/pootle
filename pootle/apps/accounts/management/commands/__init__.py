#!/usr/bin/env python
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

    args = "user"

    def handle(self, *args, **kwargs):
        self.check_args(*args)

    def create_parser(self, prog_name, subcommand):
        self.prog_name = prog_name
        self.subcommand = subcommand
        return super(UserCommand, self).create_parser(prog_name, subcommand)

    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError("User %s does not exist" % username)

    def usage_string(self):
        return self.usage(self.subcommand).replace('%prog', self.prog_name)

    def check_args(self, *args):
        min_args = len([a for a in self.args.split(" ")
                        if not a.startswith("[")])
        max_args = len(self.args.split(" "))
        if not (min_args <= len(args) <= max_args):
            raise CommandError("Wrong number of arguments\n\n%s"
                               % self.usage_string())
