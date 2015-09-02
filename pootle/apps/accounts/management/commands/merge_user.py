#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import accounts

from . import UserCommand


class Command(UserCommand):
    args = "user other_user"
    help = "Merge user to other_user"

    def handle(self, *args, **kwargs):
        super(Command, self).handle(*args, **kwargs)
        accounts.utils.UserMerger(self.get_user(username=args[0]),
                                  self.get_user(username=args[1])).merge()
