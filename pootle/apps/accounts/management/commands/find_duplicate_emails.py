# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.utils import get_duplicate_emails


User = get_user_model()


class Command(BaseCommand):

    def handle(self, **options):
        duplicates = get_duplicate_emails()
        if not duplicates:
            self.stdout.write("There are no accounts with duplicate emails\n")
            return

        for email in duplicates:
            users = (User.objects.hide_meta()
                                 .filter(email=email).order_by("-last_login"))
            if email:
                self.stdout.write("The following users have the email: %s\n"
                                  % email)
            else:
                self.stdout.write("The following users have no email set:\n")
            for user in users:
                args = (user.username,
                        " " * (25 - len(user.username)),
                        user.last_login.strftime('%Y-%m-%d %H:%M')
                        if user.last_login is not None else "never logged in",
                        (user.is_superuser
                         and "\t\tthis user is a Superuser" or ""))
                self.stdout.write(" %s%slast login: %s%s\n" % args)
            self.stdout.write("\n")
