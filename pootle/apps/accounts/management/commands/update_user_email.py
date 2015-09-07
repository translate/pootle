#!/usr/bin/env python
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

import accounts

from . import UserCommand


User = get_user_model()


class Command(UserCommand):
    args = "user email"
    help = "Update user email address"

    def handle(self, *args, **kwargs):
        super(Command, self).handle(*args, **kwargs)
        try:
            accounts.utils.update_user_email(self.get_user(args[0]), args[1])
        except ValidationError as e:
            raise CommandError(e.message)
        self.stdout.write("Email updated: %s, %s\n" % args)
