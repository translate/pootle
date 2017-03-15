# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


class LogEvent(object):

    def __init__(self, unit, user, timestamp, action, value,
                 old_value=None, revision=None, **kwargs):
        self.unit = unit
        self.user = user
        self.timestamp = timestamp
        self.action = action
        self.value = value
        self.old_value = old_value
        self.revision = revision
