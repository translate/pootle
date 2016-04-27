# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from . import UserCommand


class Command(UserCommand):
    help = "Delete user and all related objects"

    def handle(self, **options):
        for user in options['user']:
            self.get_user(user).delete(purge=True)
